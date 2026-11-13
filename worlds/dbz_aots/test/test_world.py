from collections import Counter

from BaseClasses import LocationProgressType

from .bases import DbzAotsTestBase
from .. import ram
from ..items import (BUBBLES_THING, FILLER_ITEM, GAS_MASK, ITEM_NAME_TO_ID, ITEMS, KI_BLAST_FRUIT, SEWER_KEY,
                     SNOWFIELD_KEY, SUBMARINE)
from ..location_data import LOCATIONS
from ..locations import (GOAL_EVENT, KEY_ITEM_LOCATIONS, LOCATION_ID_BASE, LOCATION_NAME_TO_ID, MISSABLE_ZONES,
                         STORY_LOCATIONS)

BONUS_CHEST = "East City Ruins 7 - Invigorate Ring Chest"


def addresses_of(locations) -> list[str]:
    return [location.name for location in locations if location.address is not None]


class TestDefaultWorld(DbzAotsTestBase):
    def test_bonus_chests_are_left_out(self) -> None:
        names = addresses_of(self.multiworld.get_locations(self.player))
        self.assertEqual(len([data for data in LOCATIONS if not data.bonus]) + len(STORY_LOCATIONS)
                         + len(KEY_ITEM_LOCATIONS), len(names))
        self.assertNotIn(BONUS_CHEST, names)

    def test_pool_is_the_original_contents(self) -> None:
        pool = Counter(item.name for item in self.multiworld.itempool if item.player == self.player)
        expected = Counter(data.item for data in LOCATIONS if not data.bonus)
        expected[self.world.get_filler_item_name()] += len(STORY_LOCATIONS)  # story steps hold filler
        expected.update(item for _, _, item in KEY_ITEM_LOCATIONS.values())
        self.assertEqual(expected, pool)  # the Sewer Key comes from its 1000-carrot reward

    def test_client_watches_the_end_of_the_game(self) -> None:
        self.assertEqual(ram.GOAL_FLAG, self.world.fill_slot_data()["goal_flag"])

    def test_story_steps_follow_the_chapter_requirements(self) -> None:
        self.assertEqual(15, len(STORY_LOCATIONS))
        self.assertFalse(self.can_reach_location("Prologue Cleared"))
        self.collect_by_name(GAS_MASK)
        self.assertTrue(self.can_reach_location("Prologue Cleared"))
        self.assertTrue(self.can_reach_location("Chapter 7 Cleared"))
        self.assertFalse(self.can_reach_location("Chapter 8 Cleared"))

    def test_the_prologue_chests_need_nothing(self) -> None:
        # They are all before the poison mist of Training Island (seen in game: Bulma stops you at the mist).
        for data in LOCATIONS:
            if data.chapter == 0:
                with self.subTest(data.name):
                    self.assertTrue(self.can_reach_location(data.name))

    def test_everything_after_the_prologue_needs_the_gas_mask(self) -> None:
        for name in ("Spinach Wastes 1 - Large Bean Chest",
                     next(data.name for data in LOCATIONS if data.chapter == 1)):
            with self.subTest(name):
                self.assertFalse(self.can_reach_location(name))
        self.collect_by_name(GAS_MASK)
        for name in ("Spinach Wastes 1 - Large Bean Chest",
                     next(data.name for data in LOCATIONS if data.chapter == 1)):
            with self.subTest(name):
                self.assertTrue(self.can_reach_location(name))

    def test_gas_mask_is_placed_early_in_this_world_by_default(self) -> None:
        self.assertEqual(1, self.multiworld.local_early_items[self.player][GAS_MASK])

    def test_chapter_8_needs_one_ki_blast_fruit(self) -> None:
        self.collect_by_name([GAS_MASK, SNOWFIELD_KEY])
        self.assertFalse(self.can_reach_location("Mt. Paozu 3 - Sleep Knuckle Chest"))
        self.collect(self.get_item_by_name(KI_BLAST_FRUIT))
        self.assertTrue(self.can_reach_location("Mt. Paozu 3 - Sleep Knuckle Chest"))

    def test_chapter_13_and_the_goal_need_two_ki_blast_fruits(self) -> None:
        self.collect_by_name([GAS_MASK, SNOWFIELD_KEY, SUBMARINE, BUBBLES_THING])
        self.collect(self.get_item_by_name(KI_BLAST_FRUIT))
        for name in ("Yemma Forest 2 - Demon Seal Chest", GOAL_EVENT):
            with self.subTest(name):
                self.assertFalse(self.can_reach_location(name))
        self.collect_by_name(KI_BLAST_FRUIT)
        for name in ("Yemma Forest 2 - Demon Seal Chest", GOAL_EVENT):
            with self.subTest(name):
                self.assertTrue(self.can_reach_location(name))

    def test_missable_areas_and_carrot_rewards_hold_no_progression(self) -> None:
        for data in LOCATIONS:
            if data.bonus:
                continue
            location = self.multiworld.get_location(data.name, self.player)
            with self.subTest(data.name):
                expected = data.zone in MISSABLE_ZONES or data.carrots > 0
                self.assertEqual(expected, location.progress_type == LocationProgressType.EXCLUDED)
                if expected and location.item:
                    self.assertFalse(location.item.advancement)

    def test_the_four_ki_blast_fruits_are_in_the_pool(self) -> None:
        # Two from the story chests (chapters 7 and 12), one from Pilaf's Castle 5 (research/decisions.md, C50), one
        # from the sewers (C57).
        self.assertEqual(4, len(self.get_items_by_name(KI_BLAST_FRUIT)))


class TestEastCityRuins(DbzAotsTestBase):
    options = {"east_city_ruins": True}

    def test_bonus_chests_are_included(self) -> None:
        self.assertEqual(len(LOCATIONS) + len(STORY_LOCATIONS) + len(KEY_ITEM_LOCATIONS),
                         len(addresses_of(self.multiworld.get_locations(self.player))))
        self.assertTrue(self.multiworld.get_location(BONUS_CHEST, self.player).address)


class TestShortGoal(DbzAotsTestBase):
    options = {"goal_chapter": 1}

    def test_only_locations_up_to_the_goal(self) -> None:
        names = set(addresses_of(self.multiworld.get_locations(self.player)))
        expected = {data.name for data in LOCATIONS if data.chapter <= 1} | {"Prologue Cleared"}
        self.assertEqual(expected, names)

    def test_goal_needs_only_the_gas_mask(self) -> None:
        self.assertFalse(self.can_reach_location(GOAL_EVENT))
        self.collect_by_name(GAS_MASK)
        self.assertTrue(self.can_reach_location(GOAL_EVENT))

    def test_client_watches_the_start_of_chapter_2(self) -> None:
        self.assertEqual(ram.CHAPTER_START_FLAGS[1], self.world.fill_slot_data()["goal_flag"])


class TestBrolyGoal(DbzAotsTestBase):
    options = {"goal": "broly", "goal_chapter": 3}

    def test_whole_story_is_included(self) -> None:
        self.assertEqual(15, self.world.options.goal_chapter.value)
        self.assertIn("Chapter 14 Cleared", addresses_of(self.multiworld.get_locations(self.player)))

    def test_client_watches_the_broly_flag(self) -> None:
        self.assertEqual(ram.BROLY_DEFEATED_FLAG, self.world.fill_slot_data()["goal_flag"])

    def test_goal_needs_the_whole_story(self) -> None:
        self.assertFalse(self.can_reach_location(GOAL_EVENT))
        self.collect_all_but(BUBBLES_THING)
        self.assertFalse(self.can_reach_location(GOAL_EVENT))
        self.collect_by_name(BUBBLES_THING)
        self.assertTrue(self.can_reach_location(GOAL_EVENT))


class TestGoalAfterTheGasMask(DbzAotsTestBase):
    options = {"goal_chapter": 6}

    def test_goal_needs_the_gas_mask_only(self) -> None:
        self.assertFalse(self.can_reach_location(GOAL_EVENT))
        self.collect_by_name(GAS_MASK)
        self.assertTrue(self.can_reach_location(GOAL_EVENT))


class TestGasMaskInStartingInventory(DbzAotsTestBase):
    options = {"gas_mask_placement": "start"}

    def test_gas_mask_is_given_and_not_in_the_pool(self) -> None:
        self.assertIn(GAS_MASK, [item.name for item in self.multiworld.precollected_items[self.player]])
        self.assertNotIn(GAS_MASK, [item.name for item in self.multiworld.itempool if item.player == self.player])
        self.assertEqual(len(self.multiworld.get_unfilled_locations(self.player)),
                         len([item for item in self.multiworld.itempool if item.player == self.player]))


class TestGasMaskEarlyInAnyWorld(DbzAotsTestBase):
    options = {"gas_mask_placement": "any_early"}

    def test_gas_mask_is_early(self) -> None:
        self.assertEqual(1, self.multiworld.early_items[self.player][GAS_MASK])
        self.assertNotIn(GAS_MASK, self.multiworld.local_early_items[self.player])


class TestWithoutHiddenItemsAndChapterChecks(DbzAotsTestBase):
    options = {"hidden_items": False, "chapter_checks": False}

    def test_only_chests_remain(self) -> None:
        names = set(addresses_of(self.multiworld.get_locations(self.player)))
        chests = {data.name for data in LOCATIONS if not data.bonus and not data.hidden}
        self.assertEqual(chests | set(KEY_ITEM_LOCATIONS), names)


class TestSnowfieldKey(DbzAotsTestBase):
    def test_chapter_8_needs_the_snowfield_key(self) -> None:
        self.collect_by_name([GAS_MASK, KI_BLAST_FRUIT])
        self.assertFalse(self.can_reach_location("Chapter 8 Cleared"))
        self.collect_by_name(SNOWFIELD_KEY)
        self.assertTrue(self.can_reach_location("Chapter 8 Cleared"))

    def test_lunch_location_is_flag_511(self) -> None:
        self.assertEqual(LOCATION_ID_BASE + 511, LOCATION_NAME_TO_ID["Holly Plain - Snowfield Key from Lunch"])


class TestSubmarineAndBubblesThing(DbzAotsTestBase):
    def test_chapter_10_needs_the_submarine(self) -> None:
        self.collect_by_name([GAS_MASK, KI_BLAST_FRUIT, SNOWFIELD_KEY])
        self.assertTrue(self.can_reach_location("Chapter 9 Cleared"))
        self.assertFalse(self.can_reach_location("Chapter 10 Cleared"))
        self.collect_by_name(SUBMARINE)
        self.assertTrue(self.can_reach_location("Chapter 10 Cleared"))

    def test_chapter_13_needs_bubbles_thing(self) -> None:
        self.collect_by_name([GAS_MASK, KI_BLAST_FRUIT, SNOWFIELD_KEY, SUBMARINE])
        self.assertFalse(self.can_reach_location("Chapter 13 Cleared"))
        self.collect_by_name(BUBBLES_THING)
        self.assertTrue(self.can_reach_location("Chapter 13 Cleared"))

    def test_scene_locations_are_their_story_flags(self) -> None:
        self.assertEqual(LOCATION_ID_BASE + 681, LOCATION_NAME_TO_ID["West City - Submarine"])
        self.assertEqual(LOCATION_ID_BASE + 870, LOCATION_NAME_TO_ID["King Kai's Planet - Bubbles' Thing"])

    def test_items_are_key_items_9_and_22(self) -> None:
        self.assertEqual(4009, ITEM_NAME_TO_ID[SUBMARINE])
        self.assertEqual(4022, ITEM_NAME_TO_ID[BUBBLES_THING])


class TestSewers(DbzAotsTestBase):
    SEWERS = ("Sewer 1 - Ki-Blast Fruit Chest", "Sewer 2 - Shenron's Nail Chest", "Sewer 2 - Kami's Cape Trap Chest")

    def test_sewer_locations_need_the_sewer_key(self) -> None:
        self.collect_all_but(SEWER_KEY)
        for name in self.SEWERS:
            self.assertFalse(self.can_reach_location(name), name)
        self.collect_by_name(SEWER_KEY)
        for name in self.SEWERS:
            self.assertTrue(self.can_reach_location(name), name)

    def test_sewer_key_is_shuffled_once_and_told_to_the_client(self) -> None:
        self.assertEqual(1, len(self.get_items_by_name(SEWER_KEY)))
        self.assertEqual(4026, ITEM_NAME_TO_ID[SEWER_KEY])
        self.assertEqual(1, self.world.fill_slot_data()["sewer_key"])

    def test_sewer_locations_are_their_flags(self) -> None:
        self.assertEqual([LOCATION_ID_BASE + flag for flag in (1449, 1450, 2663)],
                         [LOCATION_NAME_TO_ID[name] for name in self.SEWERS])


class TestCarrotRewards(DbzAotsTestBase):
    REWARDS = {2684: "West City 3 - Medium Bean for 1 Carrot", 2627: "West City 3 - Escape Path for 100 Carrots",
               2628: "West City 3 - Zeni Rush for 500 Carrots", 2629: "West City 3 - Sewer Key for 1000 Carrots"}

    def test_rewards_are_their_flags_and_hold_filler(self) -> None:
        for flag, name in self.REWARDS.items():
            self.assertEqual(LOCATION_ID_BASE + flag, LOCATION_NAME_TO_ID[name])
            location = self.multiworld.get_location(name, self.player)
            self.assertEqual(LocationProgressType.EXCLUDED, location.progress_type)
        self.assertEqual(1, self.world.fill_slot_data()["carrot_rewards"])


class TestCarrotRewardsOff(DbzAotsTestBase):
    options = {"carrot_rewards": False}

    def test_no_reward_and_the_sewer_key_replaces_a_filler(self) -> None:
        names = addresses_of(self.multiworld.get_locations(self.player))
        self.assertFalse([name for name in names if "Carrot" in name])
        self.assertEqual(1, len(self.get_items_by_name(SEWER_KEY)))
        pool = Counter(item.name for item in self.multiworld.itempool if item.player == self.player)
        self.assertEqual(len(names), sum(pool.values()))  # one item per location


class TestSewersWithShortGoal(DbzAotsTestBase):
    options = {"goal_chapter": 14}

    def test_no_sewers_nor_sewer_key(self) -> None:
        names = addresses_of(self.multiworld.get_locations(self.player))
        self.assertFalse([name for name in names if name.startswith("Sewer")])
        self.assertEqual([], self.get_items_by_name(SEWER_KEY))
        self.assertNotIn("West City 3 - Sewer Key for 1000 Carrots", names)
        self.assertIn("West City 3 - Zeni Rush for 500 Carrots", names)
        self.assertEqual(0, self.world.fill_slot_data()["sewer_key"])


class TestKeyItemsOff(DbzAotsTestBase):
    options = {"key_items": False}

    def test_no_key_item_location_nor_item(self) -> None:
        names = addresses_of(self.multiworld.get_locations(self.player))
        self.assertNotIn("Holly Plain - Snowfield Key from Lunch", names)
        self.assertFalse([name for name in names if name.startswith("Sewer")])
        self.assertEqual([], self.get_items_by_name(SNOWFIELD_KEY))
        self.assertEqual([], self.get_items_by_name(SUBMARINE))
        self.assertEqual([], self.get_items_by_name(BUBBLES_THING))
        self.assertEqual([], self.get_items_by_name(SEWER_KEY))


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
        for data in LOCATIONS:
            with self.subTest(data.name):
                ram.flag_position(data.flag)
        for flag in (*ram.CHAPTER_START_FLAGS, ram.GOAL_FLAG):
            ram.flag_position(flag)
