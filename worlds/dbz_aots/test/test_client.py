import unittest

from .. import ram
from ..client import flag_is_set, in_game, items_to_give, opened_locations, original_items_to_take_back
from ..items import ITEM_NAME_TO_ID
from ..locations import LOCATION_NAME_TO_ID


class TestClientLogic(unittest.TestCase):
    def test_in_game_needs_a_map_code(self) -> None:
        self.assertTrue(in_game(b"tut01_00"))
        self.assertFalse(in_game(bytes(8)))  # logos and title screen

    def test_opened_chest_is_found_from_its_flag(self) -> None:
        flags = bytearray(ram.FLAGS_SIZE)
        flags[1402 // 8] |= 1 << (1402 % 8)
        chest = LOCATION_NAME_TO_ID["Training Island 1 - Phoenix Feather Chest"]
        self.assertEqual({chest}, opened_locations(bytes(flags), LOCATION_NAME_TO_ID.values()))

    def test_goal_flag(self) -> None:
        flags = bytearray(ram.FLAGS_SIZE)
        self.assertFalse(flag_is_set(bytes(flags), ram.GOAL_FLAG))
        flags[ram.GOAL_FLAG // 8] |= 1 << (ram.GOAL_FLAG % 8)
        self.assertTrue(flag_is_set(bytes(flags), ram.GOAL_FLAG))

    def test_original_item_is_taken_back(self) -> None:
        before = bytes(ram.INVENTORY_SIZE)
        after = bytearray(before)
        after[29] = 1  # the Phoenix Feather chest was opened
        self.assertEqual({29: 0}, original_items_to_take_back(before, bytes(after), 1))

    def test_ambiguous_changes_are_left_alone(self) -> None:
        before = bytes(ram.INVENTORY_SIZE)
        two_items = bytearray(before)
        two_items[0] = two_items[29] = 1
        self.assertEqual({}, original_items_to_take_back(before, bytes(two_items), 1))
        plus_two = bytearray(before)
        plus_two[0] = 2
        self.assertEqual({}, original_items_to_take_back(before, bytes(plus_two), 1))
        self.assertEqual({}, original_items_to_take_back(before, bytes(plus_two), 0))

    def test_only_new_items_are_given(self) -> None:
        inventory = bytearray(ram.INVENTORY_SIZE)
        inventory[0] = 5
        received = [ITEM_NAME_TO_ID["Small Bean"], ITEM_NAME_TO_ID["Gas Mask"], ITEM_NAME_TO_ID["Small Bean"]]
        self.assertEqual({0: 6, 0x100 + 30: 1}, items_to_give(bytes(inventory), received, 1))
        self.assertEqual({}, items_to_give(bytes(inventory), received, 3))

    def test_quantity_is_capped(self) -> None:
        inventory = bytearray(ram.INVENTORY_SIZE)
        inventory[0] = ram.MAX_QUANTITY
        self.assertEqual({0: ram.MAX_QUANTITY}, items_to_give(bytes(inventory), [ITEM_NAME_TO_ID["Small Bean"]], 0))

    def test_unknown_item_is_skipped(self) -> None:
        self.assertEqual({}, items_to_give(bytes(ram.INVENTORY_SIZE), [99_999], 0))
