from __future__ import annotations

import logging
import re
import struct
from collections.abc import Collection
from typing import TYPE_CHECKING, NamedTuple

from NetUtils import ClientStatus, NetworkItem
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from . import ram
from .items import GAME_NAME, ITEM_NAME_TO_ID, KEY_ITEMS, item_slot
from .location_data import HIDDEN_ITEM_SCRIPTS, ITEM_SLOTS, LOCATIONS
from .locations import LOCATION_ID_BASE, ORIGINAL_ITEM_LOCATION_IDS
from .rom import PATCH_FILE_ENDING

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

MAP_CODE = re.compile(rb"[a-z]{3}\d\d_\d\d")
IN_BATTLE = b"\xff\xff"
ITEM_NAMES = {ap_id: name for name, ap_id in ITEM_NAME_TO_ID.items()}
ORIGINAL_ITEM_CODES = {data.flag: ram.item_code(ram.ItemCategory(ITEM_SLOTS[data.item][0]), ITEM_SLOTS[data.item][1])
                       for data in LOCATIONS}
"""Game flag of a chest or hidden item -> code of the item it holds in the original game."""
GENERIC_ITEM_NAMES = {b"Petit haricot": b"Objet Archipelago", b"Kleine Bohne": b"Archipelago-Gegenstand",
                      b"Senzu piccolo": b"Oggetto Archipelago", b"Semilla peque": b"Objeto Archipelago"}
"""Name of the first use item in each language of the release -> name given to the generic item."""
GENERIC_ITEM_NAME = b"Archipelago Item"
RECENT_PICKUPS = 8
"""Pick-ups kept while waiting for a location flag (a hidden item's flag is set when its message closes)."""
GENERIC_NAME_SPACE = 32
"""Bytes after the generic item's empty name that must be free (zero) before the client writes it there."""


def in_game(map_code: bytes, running: bytes) -> bool:
    """A save is loaded and the player is on a map. After a defeat the game restarts from the logos: the map code
    stays in memory, only ram.GAME_RUNNING tells the title screen apart."""
    return int.from_bytes(running, "little") == 1 and MAP_CODE.fullmatch(map_code) is not None


def map_key(team: int, slot: int) -> str:
    """Data storage key holding the code of the player's current map, read by the PopTracker pack to open its tab."""
    return f"dbz_aots_map_{team}_{slot}"


def shown_item_code(item: NetworkItem, own_slot: int, generic: int | None, highest: int = 0xFFFF) -> int | None:
    """Code of the game item a location should give: the real item when it is one of ours and the location can hold its
    code, otherwise the generic item (None when it has no name in this game)."""
    if item.player == own_slot:
        try:
            category, index = item_slot(item.item)
        except ValueError:
            return generic
        code = ram.item_code(category, index)
        if code <= highest:
            return code
    return generic


def chest_rewrites(records: list[bytes], wanted: dict[int, int]) -> dict[int, tuple[int, int]]:
    """Object slot -> (item code, new code), for each closed chest whose flag is in `wanted` (flag -> code) and which
    still holds its original item. `records` are the chest fields of the object slots (ram.CHEST_FIELDS_OFFSET)."""
    rewrites: dict[int, tuple[int, int]] = {}
    for slot, record in enumerate(records):
        item, state, _, flag = struct.unpack("<4I", record)
        if flag in wanted and state == 0 and item == ORIGINAL_ITEM_CODES[flag] and item != wanted[flag]:
            rewrites[slot] = (item, wanted[flag])
    return rewrites


def hidden_item_rewrites(map_code: bytes, wanted: dict[int, int]) -> list[tuple[int, int, int]]:
    """(position in the map script, original code, new code) of the hidden items of the current map to rewrite."""
    rewrites = []
    for flag, (spot_map, positions) in HIDDEN_ITEM_SCRIPTS.items():
        if spot_map.encode() == map_code and flag in wanted and wanted[flag] != ORIGINAL_ITEM_CODES[flag]:
            rewrites += [(position, ORIGINAL_ITEM_CODES[flag], wanted[flag]) for position in positions]
    return rewrites


def find_text_table(heads: list[bytes], name: bytes) -> int | None:
    """Index of the table called `name`, from the first bytes of every table of ram.TEXT_TABLES."""
    for index, head in enumerate(heads):
        if head[:4] == b"BDAT":
            name_offset = int.from_bytes(head[6:8], "little")
            if head[name_offset:name_offset + len(name) + 1] == name + b"\0":
                return index
    return None


def generic_item_name(first_item_name: bytes) -> bytes:
    """Name of the generic item in the language of the game, told by the name of its first use item."""
    for known, generic in GENERIC_ITEM_NAMES.items():
        if first_item_name.startswith(known):
            return generic
    return GENERIC_ITEM_NAME


def flag_is_set(flags: bytes, flag: int) -> bool:
    return 0 <= flag < len(flags) * 8 and flags[flag // 8] >> (flag % 8) & 1 == 1


def opened_locations(flags: bytes, location_ids: Collection[int]) -> set[int]:
    """Locations among `location_ids` whose game flag is set in the flag block `flags`."""
    opened: set[int] = set()
    for location_id in location_ids:
        if flag_is_set(flags, location_id - LOCATION_ID_BASE):
            opened.add(location_id)
    return opened


def picked_up_items(before: bytes, after: bytes) -> list[int]:
    """Inventory offsets of the items picked up between two readings: every change is a gain of exactly 1.

    Anything else (a state was loaded, a battle ended at the same moment...) gives nothing rather than a guess.
    """
    changed = [offset for offset in range(len(after)) if after[offset] != before[offset]]
    if any(after[offset] != before[offset] + 1 for offset in changed):
        return []
    return changed


def items_to_take_back(expected: list[set[int]], pickups: list[int]) -> list[int]:
    """One inventory offset per opened location whose item is among the recent `pickups` (most recent first).

    `expected` holds, for each opened location, the offsets its item may be at (original item, or the one the client
    put there). A hidden item is given before its flag is set, when its message closes: hence the recent pick-ups.
    """
    left, chosen = list(pickups), []
    for offsets in expected:
        match = next((offset for offset in left if offset in offsets), None)
        if match is not None:
            left.remove(match)
            chosen.append(match)
    return chosen


def items_to_give(inventory: bytes, received_ids: list[int], already_given: int) -> dict[int, int]:
    """Inventory offset -> new quantity, once every received item after the first `already_given` is added."""
    quantities: dict[int, int] = {}
    for ap_id in received_ids[already_given:]:
        try:
            category, index = item_slot(ap_id)
        except ValueError:
            logger.warning(f"Received an unknown item ID {ap_id}, skipped")
            continue
        offset = ram.INVENTORY_OFFSET[category] + index
        quantities[offset] = min(quantities.get(offset, inventory[offset]) + 1, ram.MAX_QUANTITY)
    return quantities


def key_item_corrections(inventory: bytes, received_ids: list[int]) -> dict[int, int]:
    """Inventory offset -> quantity, for the shuffled key items whose quantity differs from the number received.

    A story scene gives the original key item: it must go away until the key arrives from the server (D46).
    """
    corrections: dict[int, int] = {}
    for name, index in KEY_ITEMS.items():
        wanted = min(received_ids.count(ITEM_NAME_TO_ID[name]), 1)
        offset = ram.INVENTORY_OFFSET[ram.ItemCategory.KEY_ITEM] + index
        if inventory[offset] != wanted:
            corrections[offset] = wanted
    return corrections


class Progress(NamedTuple):
    level: int
    experience: int
    to_next: int
    """Experience still needed for the next level."""
    ap: int


def read_progress(sheets: bytes) -> list[Progress]:
    """Level, experience and AP of each character, from the block read at ram.CHARACTER_SHEETS."""
    progress = []
    for character in range(ram.CHARACTER_COUNT):
        sheet = character * ram.CHARACTER_SHEET_SIZE
        values = [int.from_bytes(sheets[sheet + offset:sheet + offset + 4], "little")
                  for offset in (ram.EXPERIENCE_OFFSET, ram.EXPERIENCE_TO_NEXT_OFFSET, ram.AP_OFFSET)]
        progress.append(Progress(sheets[sheet + ram.LEVEL_OFFSET], *values))
    return progress


def battle_bonus(before: Progress, after: Progress, multiplier: int, reserve: int) -> tuple[int, int, int]:
    """(experience to add, AP to add, experience kept in reserve) for one character after a battle.

    Only a real battle gain counts: experience went up by as much as the "to next level" counter went down, or the
    character gained one level. The added experience leaves at least 1 in that counter, so the game itself does every
    level up (research/decisions.md, D38); the rest waits in reserve for the next battles.
    """
    gained = after.experience - before.experience
    if gained <= 0 or not (after.level == before.level + 1 or before.to_next - after.to_next == gained):
        return 0, 0, reserve
    wanted = gained * (multiplier - 1) + reserve
    experience = max(0, min(wanted, after.to_next - 1))
    ap = max(0, min((after.ap - before.ap) * (multiplier - 1), ram.MAX_AP - after.ap))
    return experience, ap, wanted - experience


def party_hp_addresses(slots: bytes) -> list[int]:
    """Main RAM address of the current HP of each character in the party slots read at ram.PARTY."""
    addresses = []
    for slot in range(ram.PARTY_SLOT_COUNT):
        sheet = int.from_bytes(slots[slot * 4:slot * 4 + 4], "little")
        if ram.DS_MAIN_RAM_START <= sheet < ram.DS_MAIN_RAM_START + 0x400000:
            addresses.append(sheet - ram.DS_MAIN_RAM_START + ram.SHEET_ADDRESS_TO_CURRENT_HP)
    return addresses


def party_defeated(hp: list[int]) -> bool:
    """Every fighter is down. Not a death by itself: a story battle may be lost on purpose."""
    return len(hp) > 0 and all(value == 0 for value in hp)


def game_over(party_was_defeated: bool | None, still_in_game: bool) -> bool:
    """A real defeat: the "Defeat" banner is followed by a restart from the logos (research/decisions.md, C37).
    Checking that every fighter was down just before keeps a soft reset by the player from counting as a death."""
    return party_was_defeated is True and not still_in_game


class DbzAotsClient(BizHawkClient):
    game = GAME_NAME
    system = "NDS"
    patch_suffix = PATCH_FILE_ENDING

    def __init__(self) -> None:
        super().__init__()
        self.previous_map: bytes | None = None
        self.previous_flags: bytes | None = None
        self.previous_inventory: bytes | None = None
        self.recent_pickups: list[int] = []
        """Items picked up on this map and not matched to a location yet, most recent first."""
        self.shown_codes: dict[int, int] = {}
        """Game flag -> item code put in that location by show_real_items."""
        self.was_in_battle = False
        self.progress_before_battle: list[Progress] | None = None
        self.experience_reserve = [0] * ram.CHARACTER_COUNT
        self.party_was_defeated: bool | None = None
        self.previous_death_link = 0.0
        self.death_pending = False
        self.ignore_next_defeat = False
        self.sent_map: bytes | None = None
        self.scouted = False
        self.generic_name: tuple[int, bytes] | None = None
        """Address and name of the generic item, once written in the text tables of the game."""
        self.generic_name_failed = False

    async def validate_rom(self, ctx: BizHawkClientContext) -> bool:
        try:
            header = (await bizhawk.read(
                ctx.bizhawk_ctx, [(ram.ROM_HEADER_COPY, len(ram.EXPECTED_HEADER), ram.MAIN_RAM)]
            ))[0]
        except bizhawk.RequestFailedError:
            return False
        if header != ram.EXPECTED_HEADER:
            return False
        ctx.game = self.game
        ctx.items_handling = 0b111  # every item comes from the server, own world included (chests are emptied)
        ctx.want_slot_data = True  # goal, experience multiplier and DeathLink
        ctx.watcher_timeout = 0.5
        return True

    def on_package(self, ctx: BizHawkClientContext, cmd: str, args: dict) -> None:
        if cmd == "Connected":
            self.sent_map = None  # send the current map again to the server just connected to
            self.scouted = False
            self.generic_name_failed = False

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.server is None or ctx.server.socket.closed or ctx.slot is None:
            return
        try:
            running, map_code, battle, flags, inventory, counter, sheets, party = await bizhawk.read(ctx.bizhawk_ctx, [
                (ram.GAME_RUNNING, 4, ram.MAIN_RAM),
                (ram.CURRENT_MAP, ram.MAP_CODE_LENGTH, ram.MAIN_RAM),
                (ram.BATTLE_STATE, len(IN_BATTLE), ram.MAIN_RAM),
                (ram.FLAGS, ram.FLAGS_SIZE, ram.MAIN_RAM),
                (ram.INVENTORY, ram.INVENTORY_SIZE, ram.MAIN_RAM),
                (ram.RECEIVED_ITEMS_COUNTER, 4, ram.MAIN_RAM),
                (ram.CHARACTER_SHEETS, ram.CHARACTER_SHEETS_SIZE, ram.MAIN_RAM),
                (ram.PARTY, ram.PARTY_SLOT_COUNT * 4, ram.MAIN_RAM),
            ])
            if not in_game(map_code, running):
                await self.send_death_on_game_over(ctx)
                self.previous_map = self.previous_flags = self.previous_inventory = None
                self.was_in_battle, self.progress_before_battle = False, None
                self.party_was_defeated = None
                return

            await self.send_map(ctx, map_code)
            opened = opened_locations(flags, ctx.server_locations)
            new_checks = opened - ctx.locations_checked
            if new_checks:
                ctx.locations_checked |= new_checks
                await ctx.check_locations(new_checks)
                await self.tell_found_items(ctx, new_checks)

            inventory = await self.take_back_original_items(ctx, map_code, flags, inventory)

            goal_flag = (ctx.slot_data or {}).get("goal_flag", ram.GOAL_FLAG)
            if not ctx.finished_game and flag_is_set(flags, goal_flag):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True

            if battle != IN_BATTLE:
                await self.show_real_items(ctx, map_code, battle)
                await self.give_items(ctx, map_code, battle, inventory, counter)
                await self.sync_key_items(ctx, map_code, battle)
            await self.multiply_experience(ctx, map_code, battle, sheets)
            await self.handle_death_link(ctx, map_code, battle, party)
        except bizhawk.RequestFailedError:
            pass

    async def send_map(self, ctx: BizHawkClientContext, map_code: bytes) -> None:
        """Store the current map in the server's data storage when it changes, for the PopTracker pack."""
        if map_code == self.sent_map:
            return
        await ctx.send_msgs([{"cmd": "Set", "key": map_key(ctx.team, ctx.slot), "default": "", "want_reply": False,
                              "operations": [{"operation": "replace", "value": map_code.decode("ascii")}]}])
        self.sent_map = map_code

    async def show_real_items(self, ctx: BizHawkClientContext, map_code: bytes, battle: bytes) -> None:
        """Put in the chests and hidden items of the map the item they hold in the multiworld: ours, or the generic
        item for another player's. The game shows and gives it, take_back_original_items removes it, and the server
        sends ours back as for any received item (research/decisions.md, C55)."""
        if not self.scouted:
            await ctx.send_msgs([{"cmd": "LocationScouts", "locations": sorted(ctx.server_locations),
                                  "create_as_hint": 0}])
            self.scouted = True
        if not ctx.locations_info:
            return
        generic = ram.GENERIC_ITEM_CODE if await self.name_generic_item(ctx) else None
        chests: dict[int, int] = {}
        spots: dict[int, int] = {}
        for location_id, item in ctx.locations_info.items():
            flag = location_id - LOCATION_ID_BASE
            if flag in HIDDEN_ITEM_SCRIPTS:
                code = shown_item_code(item, ctx.slot, generic, ram.HIGHEST_HIDDEN_ITEM_CODE)
                if code is not None:
                    spots[flag] = code
            elif flag in ORIGINAL_ITEM_CODES:
                code = shown_item_code(item, ctx.slot, generic)
                if code is not None:
                    chests[flag] = code
        self.shown_codes = chests | spots

        slots = [ram.OBJECT_POOL + slot * ram.OBJECT_SIZE + ram.CHEST_FIELDS_OFFSET for slot in range(ram.OBJECT_SLOTS)]
        records = await bizhawk.read(ctx.bizhawk_ctx, [(address, ram.CHEST_FIELDS_SIZE, ram.MAIN_RAM)
                                                       for address in slots])
        writes, guards = [], [(ram.CURRENT_MAP, map_code, ram.MAIN_RAM), (ram.BATTLE_STATE, battle, ram.MAIN_RAM)]
        for slot, (_, code) in chest_rewrites(records, chests).items():
            writes.append((slots[slot], code.to_bytes(4, "little"), ram.MAIN_RAM))
            guards.append((slots[slot], records[slot], ram.MAIN_RAM))
        for position, original, code in hidden_item_rewrites(map_code, spots):
            writes.append((ram.MAP_SCRIPT + position, [code], ram.MAIN_RAM))
            guards.append((ram.MAP_SCRIPT + position - 1, [ram.PUSH_BYTE, original], ram.MAIN_RAM))
        if writes:
            await bizhawk.guarded_write(ctx.bizhawk_ctx, writes, guards)

    async def name_generic_item(self, ctx: BizHawkClientContext) -> bool:
        """Give the generic item its name in the text tables of the game, if they have room for it."""
        if self.generic_name_failed:
            return False
        if self.generic_name is not None:
            address, name = self.generic_name
            current = (await bizhawk.read(ctx.bizhawk_ctx, [(address, len(name) + 1, ram.MAIN_RAM)]))[0]
            if current == name + b"\0":
                return True
            self.generic_name = None  # the game loaded its tables again: find them anew
        place = await self.find_generic_name_place(ctx)
        if place is None:
            self.generic_name_failed = True  # unknown tables or no room: chests keep their original item
            return False
        table, rows, name_offset, name, free = place
        # Name, then the description row points at the name's final zero: an empty description.
        if await bizhawk.guarded_write(
            ctx.bizhawk_ctx,
            [(table + name_offset, name + b"\0", ram.MAIN_RAM),
             (rows + (ram.GENERIC_ITEM_NAME_ROW + 1) * 4, (name_offset + len(name)).to_bytes(4, "little"),
              ram.MAIN_RAM)],
            [(table + name_offset, free, ram.MAIN_RAM)],
        ):
            self.generic_name = (table + name_offset, name)
            return True
        return False

    @staticmethod
    async def find_generic_name_place(ctx: BizHawkClientContext) -> tuple[int, int, int, bytes, bytes] | None:
        """(table address, rows address, offset of the generic item's name, its name, current bytes there) in the
        item texts of ram.TEXT_TABLES, or None if the tables are not as expected or the name has no room."""
        header = (await bizhawk.read(ctx.bizhawk_ctx, [(ram.TEXT_TABLES, 8, ram.MAIN_RAM)]))[0]
        count = int.from_bytes(header[:4], "little")
        if not 0 < count <= 64:
            return None
        starts_block = (await bizhawk.read(ctx.bizhawk_ctx, [(ram.TEXT_TABLES + 8, 4 * count, ram.MAIN_RAM)]))[0]
        starts = [int.from_bytes(starts_block[i:i + 4], "little") for i in range(0, 4 * count, 4)]
        if any(start >= 0x40000 for start in starts):
            return None
        heads = await bizhawk.read(ctx.bizhawk_ctx, [(ram.TEXT_TABLES + start, 0x40, ram.MAIN_RAM) for start in starts])
        index = find_text_table(heads, ram.ITEM_TEXT_TABLE)
        if index is None:
            return None
        table = ram.TEXT_TABLES + starts[index]
        rows = table + int.from_bytes(heads[index][0xA:0xC], "little")
        pointers = await bizhawk.read(ctx.bizhawk_ctx, [(rows, 4, ram.MAIN_RAM),
                                                       (rows + ram.GENERIC_ITEM_NAME_ROW * 4, 4, ram.MAIN_RAM)])
        first_name, name_offset = (int.from_bytes(pointer, "little") for pointer in pointers)
        if max(first_name, name_offset) >= 0x10000:
            return None
        first, free = await bizhawk.read(ctx.bizhawk_ctx, [(table + first_name, 16, ram.MAIN_RAM),
                                                           (table + name_offset, GENERIC_NAME_SPACE, ram.MAIN_RAM)])
        name = generic_item_name(first)
        if not (free == bytes(GENERIC_NAME_SPACE) or free.startswith(name + b"\0")):
            return None
        return table, rows, name_offset, name, free

    async def tell_found_items(self, ctx: BizHawkClientContext, location_ids: set[int]) -> None:
        """Say in BizHawk what each new check held and for whom: the game itself only shows an item name."""
        for location_id in sorted(location_ids):
            item = ctx.locations_info.get(location_id)
            if item is None:
                continue
            name = ctx.item_names.lookup_in_slot(item.item, item.player)
            if item.player == ctx.slot:
                await bizhawk.display_message(ctx.bizhawk_ctx, f"Found your {name}")
            else:
                await bizhawk.display_message(ctx.bizhawk_ctx, f"Sent {name} to {ctx.player_names[item.player]}")

    async def take_back_original_items(
        self, ctx: BizHawkClientContext, map_code: bytes, flags: bytes, inventory: bytes
    ) -> bytes:
        """Approach A of the design: a location still gives an item (its original one, or the one show_real_items put
        in it), the client removes it right after.

        Story steps are left out: they give no item of their own, but a scene may give a key item at that moment.
        """
        if self.previous_flags is None or self.previous_inventory is None or self.previous_map != map_code:
            self.recent_pickups = []
        else:
            pickups = picked_up_items(self.previous_inventory, inventory) + self.recent_pickups
            newly_opened = (opened_locations(flags, ORIGINAL_ITEM_LOCATION_IDS)
                            - opened_locations(self.previous_flags, ORIGINAL_ITEM_LOCATION_IDS))
            expected = []
            for location_id in sorted(newly_opened):
                flag = location_id - LOCATION_ID_BASE
                expected.append({ORIGINAL_ITEM_CODES[flag] - 1, self.shown_codes.get(flag, 0) - 1})
            chosen = items_to_take_back(expected, pickups)
            if len(chosen) < len(expected):
                logger.info("A chest was opened but the item it gave could not be identified; it was kept")
            restore: dict[int, int] = {}
            for offset in chosen:
                restore[offset] = restore.get(offset, inventory[offset]) - 1
            restore = {offset: quantity for offset, quantity in restore.items() if quantity >= 0}
            if restore and await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                [(ram.INVENTORY + offset, [quantity], ram.MAIN_RAM) for offset, quantity in restore.items()],
                [(ram.INVENTORY + offset, [inventory[offset]], ram.MAIN_RAM) for offset in restore]
                + [(ram.CURRENT_MAP, map_code, ram.MAIN_RAM)],
            ):
                updated = bytearray(inventory)
                for offset, quantity in restore.items():
                    updated[offset] = quantity
                inventory = bytes(updated)
                for offset in chosen:
                    pickups.remove(offset)
            self.recent_pickups = pickups[:RECENT_PICKUPS]
        self.previous_map, self.previous_flags, self.previous_inventory = map_code, flags, inventory
        return inventory

    async def multiply_experience(
        self, ctx: BizHawkClientContext, map_code: bytes, battle: bytes, sheets: bytes
    ) -> None:
        """After each battle, add the extra experience and AP of the experience_multiplier option."""
        multiplier = (ctx.slot_data or {}).get("experience_multiplier", 1)
        in_battle = battle == IN_BATTLE
        progress = read_progress(sheets)
        if multiplier > 1 and self.was_in_battle and not in_battle and self.progress_before_battle is not None:
            writes, guards = [], [(ram.CURRENT_MAP, map_code, ram.MAIN_RAM), (ram.BATTLE_STATE, battle, ram.MAIN_RAM)]
            reserve = list(self.experience_reserve)
            for character, (before, after) in enumerate(zip(self.progress_before_battle, progress)):
                experience, ap, reserve[character] = battle_bonus(before, after, multiplier, reserve[character])
                sheet = ram.CHARACTER_SHEETS + character * ram.CHARACTER_SHEET_SIZE
                for offset, old, new in ((ram.EXPERIENCE_OFFSET, after.experience, after.experience + experience),
                                         (ram.EXPERIENCE_TO_NEXT_OFFSET, after.to_next, after.to_next - experience),
                                         (ram.AP_OFFSET, after.ap, after.ap + ap)):
                    if new != old:
                        writes.append((sheet + offset, new.to_bytes(4, "little"), ram.MAIN_RAM))
                        guards.append((sheet + offset, old.to_bytes(4, "little"), ram.MAIN_RAM))
            if not writes or await bizhawk.guarded_write(ctx.bizhawk_ctx, writes, guards):
                self.experience_reserve = reserve
                if writes:
                    sheets = (await bizhawk.read(
                        ctx.bizhawk_ctx, [(ram.CHARACTER_SHEETS, ram.CHARACTER_SHEETS_SIZE, ram.MAIN_RAM)]
                    ))[0]
                    progress = read_progress(sheets)
        if not in_battle:
            self.progress_before_battle = progress
        self.was_in_battle = in_battle

    async def give_items(
        self, ctx: BizHawkClientContext, map_code: bytes, battle: bytes, inventory: bytes, counter: bytes
    ) -> None:
        """Add every item received since the last time, and store how many were given in the save (D20)."""
        already_given = int.from_bytes(counter, "little")
        received = [network_item.item for network_item in ctx.items_received]
        if already_given >= len(received):
            return
        quantities = items_to_give(inventory, received, already_given)
        written = await bizhawk.guarded_write(
            ctx.bizhawk_ctx,
            [(ram.INVENTORY + offset, [quantity], ram.MAIN_RAM) for offset, quantity in quantities.items()]
            + [(ram.RECEIVED_ITEMS_COUNTER, len(received).to_bytes(4, "little"), ram.MAIN_RAM)],
            [(ram.INVENTORY + offset, [inventory[offset]], ram.MAIN_RAM) for offset in quantities]
            + [
                (ram.RECEIVED_ITEMS_COUNTER, counter, ram.MAIN_RAM),
                (ram.CURRENT_MAP, map_code, ram.MAIN_RAM),
                (ram.BATTLE_STATE, battle, ram.MAIN_RAM),
            ],
        )
        if not written:
            return
        if self.previous_inventory is not None:
            updated = bytearray(self.previous_inventory)
            for offset, quantity in quantities.items():
                updated[offset] = quantity
            self.previous_inventory = bytes(updated)
        for ap_id in received[already_given:]:
            await bizhawk.display_message(ctx.bizhawk_ctx, f"Received {ITEM_NAMES.get(ap_id, ap_id)}")

    async def handle_death_link(
        self, ctx: BizHawkClientContext, map_code: bytes, battle: bytes, party: bytes
    ) -> None:
        """Watch the fighters for send_death_on_game_over; a received death sets their HP to 0 at the next battle."""
        if not (ctx.slot_data or {}).get("death_link"):
            return
        if "DeathLink" not in ctx.tags:
            await ctx.update_death_link(True)
            self.previous_death_link = ctx.last_death_link
        if self.previous_death_link != ctx.last_death_link:
            self.previous_death_link = ctx.last_death_link
            self.death_pending = True

        addresses = party_hp_addresses(party)
        hp = [int.from_bytes(value, "little") for value in await bizhawk.read(
            ctx.bizhawk_ctx, [(address, 4, ram.MAIN_RAM) for address in addresses]
        )] if addresses else []
        defeated = party_defeated(hp)
        self.party_was_defeated = defeated

        # The game only checks for a defeat during a battle, at the end of an action (research/decisions.md, C32);
        # with every fighter down it shows "Defeat" and restarts.
        if self.death_pending and battle == IN_BATTLE and not defeated and addresses:
            if await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                [(address, (0).to_bytes(4, "little"), ram.MAIN_RAM) for address in addresses],
                [(ram.CURRENT_MAP, map_code, ram.MAIN_RAM), (ram.BATTLE_STATE, battle, ram.MAIN_RAM),
                 (ram.PARTY, party, ram.MAIN_RAM)],
            ):
                self.death_pending = False
                self.ignore_next_defeat = True

    async def send_death_on_game_over(self, ctx: BizHawkClientContext) -> None:
        """Called when the game leaves the field: send a death if this is the restart that follows a defeat."""
        if game_over(self.party_was_defeated, still_in_game=False) and (ctx.slot_data or {}).get("death_link"):
            if self.ignore_next_defeat:
                self.ignore_next_defeat = False  # the defeat came from a received death
            else:
                await ctx.send_death(f"{ctx.player_names[ctx.slot]}'s party was defeated.")
                self.previous_death_link = ctx.last_death_link

    async def sync_key_items(self, ctx: BizHawkClientContext, map_code: bytes, battle: bytes) -> None:
        """Keep each shuffled key item at the quantity received from the server (option key_items)."""
        if not (ctx.slot_data or {}).get("key_items"):
            return
        inventory = (await bizhawk.read(ctx.bizhawk_ctx, [(ram.INVENTORY, ram.INVENTORY_SIZE, ram.MAIN_RAM)]))[0]
        corrections = key_item_corrections(inventory, [item.item for item in ctx.items_received])
        if corrections:
            await bizhawk.guarded_write(
                ctx.bizhawk_ctx,
                [(ram.INVENTORY + offset, [quantity], ram.MAIN_RAM) for offset, quantity in corrections.items()],
                [(ram.INVENTORY + offset, [inventory[offset]], ram.MAIN_RAM) for offset in corrections]
                + [(ram.CURRENT_MAP, map_code, ram.MAIN_RAM), (ram.BATTLE_STATE, battle, ram.MAIN_RAM)],
            )
