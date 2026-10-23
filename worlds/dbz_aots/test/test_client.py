import unittest

from .. import ram
from ..client import (Progress, battle_bonus, flag_is_set, in_game, items_to_give, opened_locations,
                      original_items_to_take_back, read_progress)
from ..items import ITEM_NAME_TO_ID
from ..locations import LOCATION_NAME_TO_ID, ORIGINAL_ITEM_LOCATION_IDS


class TestClientLogic(unittest.TestCase):
    def test_in_game_needs_a_map_code(self) -> None:
        self.assertTrue(in_game(b"tut01_00"))
        self.assertFalse(in_game(bytes(8)))  # logos and title screen

    def test_opened_chest_is_found_from_its_flag(self) -> None:
        flags = bytearray(ram.FLAGS_SIZE)
        flags[1402 // 8] |= 1 << (1402 % 8)
        chest = LOCATION_NAME_TO_ID["Training Island 1 - Phoenix Feather Chest"]
        self.assertEqual({chest}, opened_locations(bytes(flags), LOCATION_NAME_TO_ID.values()))

    def test_story_steps_are_not_taken_back(self) -> None:
        self.assertNotIn(LOCATION_NAME_TO_ID["Prologue Cleared"], ORIGINAL_ITEM_LOCATION_IDS)
        self.assertIn(LOCATION_NAME_TO_ID["Training Island 1 - Phoenix Feather Chest"], ORIGINAL_ITEM_LOCATION_IDS)

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


class TestExperienceMultiplier(unittest.TestCase):
    # Seen in game (research/decisions.md, C26): Tien won 72 experience and 12 AP in one battle.
    BEFORE = Progress(level=4, experience=597, to_next=294, ap=98)
    AFTER = Progress(level=4, experience=669, to_next=222, ap=110)

    def test_extra_gain(self) -> None:
        self.assertEqual((144, 24, 0), battle_bonus(self.BEFORE, self.AFTER, 3, 0))

    def test_multiplier_one_adds_nothing(self) -> None:
        self.assertEqual((0, 0, 0), battle_bonus(self.BEFORE, self.AFTER, 1, 0))

    def test_never_reaches_the_next_level(self) -> None:
        # 72 * 9 = 648 wanted, but only 221 fit before the next level: the rest waits in reserve.
        self.assertEqual((221, 108, 427), battle_bonus(self.BEFORE, self.AFTER, 10, 0))

    def test_reserve_is_spent_after_the_next_battle(self) -> None:
        self.assertEqual((144 + 50, 24, 0), battle_bonus(self.BEFORE, self.AFTER, 3, 50))

    def test_level_up_counts_as_a_battle(self) -> None:
        # Krillin, level 1 -> 2: the counter was reset by the level up.
        before = Progress(level=1, experience=48, to_next=22, ap=8)
        after = Progress(level=2, experience=120, to_next=100, ap=20)
        self.assertEqual((72, 12, 0), battle_bonus(before, after, 2, 0))

    def test_unrelated_changes_are_ignored(self) -> None:
        loaded_state = Progress(level=4, experience=900, to_next=100, ap=98)
        self.assertEqual((0, 0, 7), battle_bonus(self.BEFORE, loaded_state, 3, 7))
        self.assertEqual((0, 0, 0), battle_bonus(self.AFTER, self.BEFORE, 3, 0))  # experience went down

    def test_read_progress(self) -> None:
        sheets = bytearray(ram.CHARACTER_SHEETS_SIZE)
        tien = 4 * ram.CHARACTER_SHEET_SIZE
        sheets[tien + ram.LEVEL_OFFSET] = 4
        sheets[tien + ram.EXPERIENCE_OFFSET:tien + ram.EXPERIENCE_OFFSET + 12] = bytes.fromhex("55020000 26010000 62000000")
        self.assertEqual(Progress(4, 597, 294, 98), read_progress(bytes(sheets))[4])
