from __future__ import annotations

import logging
import re
from collections.abc import Collection
from typing import TYPE_CHECKING, NamedTuple

from NetUtils import ClientStatus
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from . import ram
from .items import GAME_NAME, ITEM_NAME_TO_ID, KEY_ITEMS, item_slot
from .locations import LOCATION_ID_BASE, ORIGINAL_ITEM_LOCATION_IDS
from .rom import PATCH_FILE_ENDING

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

MAP_CODE = re.compile(rb"[a-z]{3}\d\d_\d\d")
IN_BATTLE = b"\xff\xff"
ITEM_NAMES = {ap_id: name for name, ap_id in ITEM_NAME_TO_ID.items()}


def in_game(map_code: bytes, running: bytes) -> bool:
    """A save is loaded and the player is on a map. After a defeat the game restarts from the logos: the map code
    stays in memory, only ram.GAME_RUNNING tells the title screen apart."""
    return int.from_bytes(running, "little") == 1 and MAP_CODE.fullmatch(map_code) is not None


def flag_is_set(flags: bytes, flag: int) -> bool:
    return 0 <= flag < len(flags) * 8 and flags[flag // 8] >> (flag % 8) & 1 == 1


def opened_locations(flags: bytes, location_ids: Collection[int]) -> set[int]:
    """Locations among `location_ids` whose game flag is set in the flag block `flags`."""
    opened: set[int] = set()
    for location_id in location_ids:
        if flag_is_set(flags, location_id - LOCATION_ID_BASE):
            opened.add(location_id)
    return opened


def original_items_to_take_back(before: bytes, after: bytes, chests_opened: int) -> dict[int, int]:
    """Inventory offset -> quantity to restore, after `chests_opened` chests gave their original item.

    Only acts when exactly one item went up by exactly 1 per opened chest. Anything else (a state was loaded, a
    battle ended at the same moment...) is left alone rather than guessed.
    """
    changed = [offset for offset in range(len(after)) if after[offset] != before[offset]]
    if chests_opened == 0 or len(changed) != chests_opened:
        return {}
    if any(after[offset] != before[offset] + 1 for offset in changed):
        return {}
    return {offset: before[offset] for offset in changed}


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
        self.was_in_battle = False
        self.progress_before_battle: list[Progress] | None = None
        self.experience_reserve = [0] * ram.CHARACTER_COUNT
        self.party_was_defeated: bool | None = None
        self.previous_death_link = 0.0
        self.death_pending = False
        self.ignore_next_defeat = False

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

            opened = opened_locations(flags, ctx.server_locations)
            new_checks = opened - ctx.locations_checked
            if new_checks:
                ctx.locations_checked |= new_checks
                await ctx.check_locations(new_checks)

            inventory = await self.take_back_original_items(ctx, map_code, flags, inventory)

            goal_flag = (ctx.slot_data or {}).get("goal_flag", ram.GOAL_FLAG)
            if not ctx.finished_game and flag_is_set(flags, goal_flag):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True

            if battle != IN_BATTLE:
                await self.give_items(ctx, map_code, battle, inventory, counter)
                await self.sync_key_items(ctx, map_code, battle)
            await self.multiply_experience(ctx, map_code, battle, sheets)
            await self.handle_death_link(ctx, map_code, battle, party)
        except bizhawk.RequestFailedError:
            pass

    async def take_back_original_items(
        self, ctx: BizHawkClientContext, map_code: bytes, flags: bytes, inventory: bytes
    ) -> bytes:
        """Approach A of the design: a location still gives its original item, the client removes it right after.

        Story steps are left out: they give no item of their own, but a scene may give a key item at that moment.
        """
        if self.previous_flags is not None and self.previous_inventory is not None and self.previous_map == map_code:
            newly_opened = (opened_locations(flags, ORIGINAL_ITEM_LOCATION_IDS)
                            - opened_locations(self.previous_flags, ORIGINAL_ITEM_LOCATION_IDS))
            restore = original_items_to_take_back(self.previous_inventory, inventory, len(newly_opened))
            if newly_opened and not restore:
                logger.info("A chest was opened but its original item could not be identified; it was kept")
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
