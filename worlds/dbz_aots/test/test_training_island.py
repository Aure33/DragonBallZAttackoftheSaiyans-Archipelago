from collections import Counter

from .bases import DbzAotsTestBase
from .. import ram
from ..items import ITEM_NAME_TO_ID, ITEMS
from ..locations import GOAL_EVENT, LOCATION_ID_BASE, LOCATION_NAME_TO_ID, LOCATIONS, ORIGINAL_CONTENTS


class TestTrainingIsland(DbzAotsTestBase):
    def test_eight_chests(self) -> None:
        chests = [location for location in self.multiworld.get_locations(self.player) if location.address is not None]
        self.assertEqual(8, len(chests))

    def test_pool_is_the_original_contents(self) -> None:
        pool = Counter(item.name for item in self.multiworld.itempool if item.player == self.player)
        self.assertEqual(Counter(ORIGINAL_CONTENTS), pool)

    def test_every_chest_and_the_goal_reachable_from_the_start(self) -> None:
        for name in [*LOCATIONS, GOAL_EVENT]:
            with self.subTest(name):
                self.assertTrue(self.can_reach_location(name))


class TestIds(DbzAotsTestBase):
    run_default_tests = False

    def test_location_id_gives_the_game_flag(self) -> None:
        # Flag 1402 (Phoenix Feather chest) is bit 2 of 0x09F897 (research/ram_map.md, section 3).
        self.assertEqual(LOCATION_ID_BASE + 1402, LOCATION_NAME_TO_ID["Training Island Chest 3"])
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
