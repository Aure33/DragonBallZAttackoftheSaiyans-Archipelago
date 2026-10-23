from __future__ import annotations

import logging
import re
from collections.abc import Collection
from typing import TYPE_CHECKING

from NetUtils import ClientStatus
import worlds._bizhawk as bizhawk
from worlds._bizhawk.client import BizHawkClient

from . import ram
from .items import GAME_NAME, ITEM_NAME_TO_ID, item_slot
from .locations import LOCATION_ID_BASE, LOCATION_NAME_TO_ID

if TYPE_CHECKING:
    from worlds._bizhawk.context import BizHawkClientContext

logger = logging.getLogger("Client")

MAP_CODE = re.compile(rb"[a-z]{3}\d\d_\d\d")
IN_BATTLE = b"\xff\xff"
GOAL_MAP_PREFIX = b"est"
"""Chapter 1 opens in East City right after Jackie Chun is beaten: provisional goal check (decisions.md, D25)."""
CHEST_IDS = frozenset(LOCATION_NAME_TO_ID.values())
ITEM_NAMES = {ap_id: name for name, ap_id in ITEM_NAME_TO_ID.items()}


def in_game(map_code: bytes) -> bool:
    """A save is loaded and the player is on a map (the map code is empty on the logos and the title screen)."""
    return MAP_CODE.fullmatch(map_code) is not None


def opened_locations(flags: bytes, location_ids: Collection[int]) -> set[int]:
    """Locations among `location_ids` whose game flag is set in the flag block `flags`."""
    opened: set[int] = set()
    for location_id in location_ids:
        flag = location_id - LOCATION_ID_BASE
        if 0 <= flag < len(flags) * 8 and flags[flag // 8] >> (flag % 8) & 1:
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


class DbzAotsClient(BizHawkClient):
    game = GAME_NAME
    system = "NDS"

    def __init__(self) -> None:
        super().__init__()
        self.previous_map: bytes | None = None
        self.previous_flags: bytes | None = None
        self.previous_inventory: bytes | None = None

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
        ctx.want_slot_data = False
        ctx.watcher_timeout = 0.5
        return True

    async def game_watcher(self, ctx: BizHawkClientContext) -> None:
        if ctx.server is None or ctx.server.socket.closed or ctx.slot is None:
            return
        try:
            map_code, battle, flags, inventory, counter = await bizhawk.read(ctx.bizhawk_ctx, [
                (ram.CURRENT_MAP, ram.MAP_CODE_LENGTH, ram.MAIN_RAM),
                (ram.BATTLE_STATE, len(IN_BATTLE), ram.MAIN_RAM),
                (ram.FLAGS, ram.FLAGS_SIZE, ram.MAIN_RAM),
                (ram.INVENTORY, ram.INVENTORY_SIZE, ram.MAIN_RAM),
                (ram.RECEIVED_ITEMS_COUNTER, 4, ram.MAIN_RAM),
            ])
            if not in_game(map_code):
                self.previous_map = self.previous_flags = self.previous_inventory = None
                return

            opened = opened_locations(flags, ctx.server_locations)
            new_checks = opened - ctx.locations_checked
            if new_checks:
                ctx.locations_checked |= new_checks
                await ctx.check_locations(new_checks)

            inventory = await self.take_back_original_items(ctx, map_code, flags, inventory)

            if not ctx.finished_game and map_code.startswith(GOAL_MAP_PREFIX):
                await ctx.send_msgs([{"cmd": "StatusUpdate", "status": ClientStatus.CLIENT_GOAL}])
                ctx.finished_game = True

            if battle != IN_BATTLE:
                await self.give_items(ctx, map_code, battle, inventory, counter)
        except bizhawk.RequestFailedError:
            pass

    async def take_back_original_items(
        self, ctx: BizHawkClientContext, map_code: bytes, flags: bytes, inventory: bytes
    ) -> bytes:
        """Approach A of the design: a chest still gives its original item, the client removes it right after."""
        if self.previous_flags is not None and self.previous_inventory is not None and self.previous_map == map_code:
            newly_opened = opened_locations(flags, CHEST_IDS) - opened_locations(self.previous_flags, CHEST_IDS)
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
