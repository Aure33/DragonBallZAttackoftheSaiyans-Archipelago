import struct
import unittest

from NetUtils import NetworkItem

from .. import ram
from ..client import (ORIGINAL_ITEM_CODES, Progress, battle_bonus, chest_rewrites, find_text_table, flag_is_set,
                      game_over, generic_item_name, hidden_item_rewrites, in_game, items_to_give, key_item_corrections,
                      items_to_take_back, map_key, opened_locations, party_defeated, party_hp_addresses,
                      picked_up_items, read_progress, shown_item_code)
from ..items import ITEM_NAME_TO_ID
from ..locations import LOCATION_NAME_TO_ID, ORIGINAL_ITEM_LOCATION_IDS


class TestClientLogic(unittest.TestCase):
    def test_in_game_needs_a_map_code_and_a_running_game(self) -> None:
        running, title = (1).to_bytes(4, "little"), bytes(4)
        self.assertTrue(in_game(b"tut01_00", running))
        self.assertFalse(in_game(bytes(8), title))  # logos and title screen after power on
        self.assertFalse(in_game(b"tut02_00", title))  # title screen after a defeat: the map code stays

    def test_map_key_matches_the_poptracker_pack(self) -> None:
        self.assertEqual(map_key(0, 2), "dbz_aots_map_0_2")  # tools/build_poptracker.py: MAP_KEY_PREFIX

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

    def test_picked_up_item(self) -> None:
        before = bytes(ram.INVENTORY_SIZE)
        after = bytearray(before)
        after[29] = 1  # the Phoenix Feather chest was opened
        self.assertEqual([29], picked_up_items(before, bytes(after)))

    def test_ambiguous_changes_are_no_pickup(self) -> None:
        before = bytes(ram.INVENTORY_SIZE)
        plus_two = bytearray(before)
        plus_two[0] = 2
        self.assertEqual([], picked_up_items(before, bytes(plus_two)))
        minus_one = bytearray(before)
        minus_one[29], minus_one[0] = 1, 0xFF  # a state was loaded
        self.assertEqual([], picked_up_items(before, bytes(minus_one)))

    def test_item_taken_back_is_the_one_the_location_gave(self) -> None:
        self.assertEqual([29], items_to_take_back([{29}], [0, 29]))  # two pick-ups, one chest
        self.assertEqual([], items_to_take_back([{29}], [0]))  # not the expected item: kept
        self.assertEqual([2, 29], items_to_take_back([{2, 102}, {29}], [29, 2, 2]))
        self.assertEqual([2, 2], items_to_take_back([{2}, {2}], [2, 2]))  # two chests with the same item

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



class TestDeathLink(unittest.TestCase):
    # Party slots read in game (research/decisions.md, C33): Krillin, Tien and Yamcha on Training Island, then
    # Krillin alone in the middle slot in East City.
    TRIO = bytes.fromhex("44D90C02" "90DB0C02" "DCDD0C02") + bytes(20)
    KRILLIN_ALONE = bytes(4) + bytes.fromhex("44D90C02") + bytes(24)

    def test_slots_give_the_current_hp_of_each_member(self) -> None:
        self.assertEqual([0x0CD9E4, 0x0CDC30, 0x0CDE7C], party_hp_addresses(self.TRIO))

    def test_empty_slots_are_skipped(self) -> None:
        self.assertEqual([0x0CD9E4], party_hp_addresses(self.KRILLIN_ALONE))
        self.assertEqual([], party_hp_addresses(bytes(ram.PARTY_SLOT_COUNT * 4)))

    def test_defeat_when_every_member_is_down(self) -> None:
        self.assertTrue(party_defeated([0, 0, 0]))
        self.assertTrue(party_defeated([0]))

    def test_no_defeat_while_one_member_stands(self) -> None:
        self.assertFalse(party_defeated([0, 1, 0]))

    def test_game_over_is_a_restart_after_a_defeat(self) -> None:
        self.assertTrue(game_over(party_was_defeated=True, still_in_game=False))

    def test_story_battle_lost_on_purpose_is_no_death(self) -> None:
        # The story goes on: the game never restarts.
        self.assertFalse(game_over(party_was_defeated=True, still_in_game=True))

    def test_soft_reset_is_no_death(self) -> None:
        self.assertFalse(game_over(party_was_defeated=False, still_in_game=False))
        self.assertFalse(game_over(party_was_defeated=None, still_in_game=False))

    def test_no_defeat_without_a_party(self) -> None:
        self.assertFalse(party_defeated([]))


class TestKeyItems(unittest.TestCase):
    KEY_OFFSET = ram.INVENTORY_OFFSET[ram.ItemCategory.KEY_ITEM] + 6  # Snowfield Key

    def test_key_given_by_the_scene_is_taken_back(self) -> None:
        inventory = bytearray(ram.INVENTORY_SIZE)
        inventory[self.KEY_OFFSET] = 1
        self.assertEqual({self.KEY_OFFSET: 0}, key_item_corrections(bytes(inventory), []))

    def test_received_key_is_given(self) -> None:
        received = [ITEM_NAME_TO_ID["Snowfield Key"]]
        self.assertEqual({self.KEY_OFFSET: 1}, key_item_corrections(bytes(ram.INVENTORY_SIZE), received))

    def test_nothing_to_do_when_the_quantity_matches(self) -> None:
        inventory = bytearray(ram.INVENTORY_SIZE)
        inventory[self.KEY_OFFSET] = 1
        self.assertEqual({}, key_item_corrections(bytes(inventory), [ITEM_NAME_TO_ID["Snowfield Key"]]))

    def test_each_key_item_follows_its_own_count(self) -> None:
        submarine = ram.INVENTORY_OFFSET[ram.ItemCategory.KEY_ITEM] + 9
        bubbles_thing = ram.INVENTORY_OFFSET[ram.ItemCategory.KEY_ITEM] + 22
        inventory = bytearray(ram.INVENTORY_SIZE)
        inventory[submarine] = 1
        received = [ITEM_NAME_TO_ID["Bubbles' Thing"]]
        self.assertEqual({submarine: 0, bubbles_thing: 1}, key_item_corrections(bytes(inventory), received))


class TestRealItems(unittest.TestCase):
    OWN_SLOT, OTHER_SLOT = 1, 2

    @staticmethod
    def chest(item: int, state: int, flag: int) -> bytes:
        return struct.pack("<4I", item, state, 0, flag)

    def test_original_codes_come_from_the_rom_data(self) -> None:
        self.assertEqual(1, ORIGINAL_ITEM_CODES[1405])  # Small Bean (research/chests.md)
        self.assertEqual(30, ORIGINAL_ITEM_CODES[1402])  # Phoenix Feather
        self.assertEqual(83, ORIGINAL_ITEM_CODES[3201])  # hidden item of East City

    def test_own_item_is_shown_and_others_are_generic(self) -> None:
        own = NetworkItem(ITEM_NAME_TO_ID["Phoenix Feather"], 0, self.OWN_SLOT, 0)
        other = NetworkItem(ITEM_NAME_TO_ID["Phoenix Feather"], 0, self.OTHER_SLOT, 0)
        self.assertEqual(30, shown_item_code(own, self.OWN_SLOT, ram.GENERIC_ITEM_CODE))
        self.assertEqual(ram.GENERIC_ITEM_CODE, shown_item_code(other, self.OWN_SLOT, ram.GENERIC_ITEM_CODE))
        self.assertIsNone(shown_item_code(other, self.OWN_SLOT, None))

    def test_code_too_big_for_a_hidden_item_is_generic(self) -> None:
        gas_mask = NetworkItem(ITEM_NAME_TO_ID["Gas Mask"], 0, self.OWN_SLOT, 0)
        self.assertEqual(ram.GENERIC_ITEM_CODE, shown_item_code(
            gas_mask, self.OWN_SLOT, ram.GENERIC_ITEM_CODE, ram.HIGHEST_HIDDEN_ITEM_CODE))
        self.assertGreater(shown_item_code(gas_mask, self.OWN_SLOT, ram.GENERIC_ITEM_CODE), 0x7F)

    def test_only_closed_chests_with_their_original_item_are_rewritten(self) -> None:
        records = [self.chest(1, 0, 1405),  # closed, original item: rewritten
                   self.chest(2, 2, 1404),  # already opened
                   self.chest(ram.GENERIC_ITEM_CODE, 0, 1406),  # already rewritten
                   self.chest(1, 0, 1583),  # not in the wanted list
                   bytes(16)]
        wanted = {1405: 30, 1404: 30, 1406: ram.GENERIC_ITEM_CODE}
        self.assertEqual({0: (1, 30)}, chest_rewrites(records, wanted))

    def test_hidden_items_of_the_current_map_only(self) -> None:
        self.assertEqual([(4275, 83, ram.GENERIC_ITEM_CODE)],
                         hidden_item_rewrites(b"est01_00", {3201: ram.GENERIC_ITEM_CODE, 3202: 1}))
        self.assertEqual([], hidden_item_rewrites(b"est01_00", {3201: 83}))  # same item: nothing to do
        self.assertEqual(2, len(hidden_item_rewrites(b"pao04_00", {3203: 1})))  # two GetItem calls in its script

    def test_text_table_is_found_by_name(self) -> None:
        head = b"BDAT" + bytes(2) + (0x24).to_bytes(2, "little") + bytes(0x1C) + b"use_item_mes\0"
        other = b"BDAT" + bytes(2) + (0x24).to_bytes(2, "little") + bytes(0x1C) + b"btl_acc_mes\0"
        self.assertEqual(1, find_text_table([other.ljust(0x40, b"\0"), head.ljust(0x40, b"\0")], b"use_item_mes"))
        self.assertIsNone(find_text_table([other.ljust(0x40, b"\0")], b"use_item_mes"))

    def test_generic_name_follows_the_language(self) -> None:
        self.assertEqual(b"Objet Archipelago", generic_item_name(b"Petit haricot\0Redonne"))
        self.assertEqual(b"Archipelago Item", generic_item_name(b"Small Bean\0"))
