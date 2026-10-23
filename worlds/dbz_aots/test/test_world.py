from collections import Counter

from .bases import DbzAotsTestBase
from .. import ram
from ..chest_data import CHESTS
from ..items import GAS_MASK, ITEM_NAME_TO_ID, ITEMS, KI_BLAST_FRUIT
from ..locations import GOAL_EVENT, LOCATION_ID_BASE, LOCATION_NAME_TO_ID

BONUS_CHEST = "East City Ruins 7 - Invigorate Ring Chest"


def chests_of(locations) -> list[str]:
    return [location.name for location in locations if location.address is not None]


class TestDefaultWorld(DbzAotsTestBase):
    def test_bonus_chests_are_left_out(self) -> None:
        chests = chests_of(self.multiworld.get_locations(self.player))
        self.assertEqual(len([chest for chest in CHESTS if not chest.bonus]), len(chests))
        self.assertNotIn(BONUS_CHEST, chests)

    def test_pool_is_the_original_contents(self) -> None:
        pool = Counter(item.name for item in self.multiworld.itempool if item.player == self.player)
        self.assertEqual(Counter(chest.item for chest in CHESTS if not chest.bonus), pool)

    def test_chapters_before_spinach_wastes_need_nothing(self) -> None:
        for chest in CHESTS:
            if chest.chapter < 6:
                with self.subTest(chest.name):
                    self.assertTrue(self.can_reach_location(chest.name))

    def test_chapter_6_needs_the_gas_mask(self) -> None:
        self.assertFalse(self.can_reach_location("Spinach Wastes 1 - Large Bean Chest"))
        self.collect_by_name(GAS_MASK)
        self.assertTrue(self.can_reach_location("Spinach Wastes 1 - Large Bean Chest"))

    def test_chapter_8_needs_one_ki_blast_fruit(self) -> None:
        self.collect_by_name(GAS_MASK)
        self.assertFalse(self.can_reach_location("Mt. Paozu 3 - Sleep Knuckle Chest"))
        self.collect(self.get_item_by_name(KI_BLAST_FRUIT))
        self.assertTrue(self.can_reach_location("Mt. Paozu 3 - Sleep Knuckle Chest"))

    def test_chapter_13_and_the_goal_need_two_ki_blast_fruits(self) -> None:
        self.collect_by_name(GAS_MASK)
        self.collect(self.get_item_by_name(KI_BLAST_FRUIT))
        for name in ("Yemma Forest 2 - Demon Seal Chest", GOAL_EVENT):
            with self.subTest(name):
                self.assertFalse(self.can_reach_location(name))
        self.collect_by_name(KI_BLAST_FRUIT)
        for name in ("Yemma Forest 2 - Demon Seal Chest", GOAL_EVENT):
            with self.subTest(name):
                self.assertTrue(self.can_reach_location(name))

    def test_both_ki_blast_fruits_are_in_the_pool(self) -> None:
        self.assertEqual(2, len(self.get_items_by_name(KI_BLAST_FRUIT)))


class TestEastCityRuins(DbzAotsTestBase):
    options = {"east_city_ruins": True}

    def test_bonus_chests_are_included(self) -> None:
        self.assertEqual(len(CHESTS), len(chests_of(self.multiworld.get_locations(self.player))))
        self.assertTrue(self.multiworld.get_location(BONUS_CHEST, self.player).address)


class TestIds(DbzAotsTestBase):
    run_default_tests = False

    def test_location_id_gives_the_game_flag(self) -> None:
        # Flag 1402 (Phoenix Feather chest) is bit 2 of 0x09F897 (research/ram_map.md, section 3).
        self.assertEqual(LOCATION_ID_BASE + 1402, LOCATION_NAME_TO_ID["Training Island 1 - Phoenix Feather Chest"])
        self.assertEqual((0x09F897, 1 << 2), ram.flag_position(1402))

    def test_item_id_gives_the_inventory_slot(self) -> None:
        # Seen in game: Phoenix Feather at 0x0CC3B5, Gas Mask at 0x0CC4B6 (research/ram_map.md, section 2).
        for name, address in (("Phoenix Feather", 0x0CC3B5), ("Gas Mask", 0x0CC4B6), ("Small Bean", 0x0CC398)):
            with self.subTest(name):
                data = ITEMS[name]
                self.assertEqual(address, ram.inventory_address(data.category, data.index))
                self.assertEqual(1000 * (data.category + 1) + data.index, ITEM_NAME_TO_ID[name])

    def test_ids_are_unique(self) -> None:
        self.assertEqual(len(ITEM_NAME_TO_ID), len(set(ITEM_NAME_TO_ID.values())))
        self.assertEqual(len(LOCATION_NAME_TO_ID), len(set(LOCATION_NAME_TO_ID.values())))

    def test_flags_fit_in_the_flag_block(self) -> None:
        for chest in CHESTS:
            with self.subTest(chest.name):
                ram.flag_position(chest.flag)
        ram.flag_position(ram.GOAL_FLAG)
