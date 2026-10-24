import os
from typing import Any, ClassVar

from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld, World

from . import client as client  # importing the module registers the BizHawk client
from . import items, locations, regions, rules
from .options import DbzAotsOptions, Goal
from .rom import DbzAotsProcedurePatch, DbzAotsSettings


class DbzAotsWebWorld(WebWorld):
    game = items.GAME_NAME
    theme = "grass"
    tutorials = [
        Tutorial(
            "Multiworld Setup Guide",
            "A guide to setting up Dragon Ball Z - Attack of the Saiyans for Archipelago.",
            "English",
            "setup_en.md",
            "setup/en",
            ["Aure33"],
        )
    ]


class DbzAotsWorld(World):
    """
    Dragon Ball Z: Attack of the Saiyans is a turn-based RPG for the Nintendo DS that follows the Saiyan saga,
    from Goku's training to the battle against Vegeta.
    """

    game = items.GAME_NAME
    web = DbzAotsWebWorld()
    options_dataclass = DbzAotsOptions
    options: DbzAotsOptions
    settings_key = "dbz_aots_settings"
    settings: ClassVar[DbzAotsSettings]

    item_name_to_id = items.ITEM_NAME_TO_ID
    location_name_to_id = locations.LOCATION_NAME_TO_ID
    location_name_groups = locations.LOCATION_NAME_GROUPS

    def generate_early(self) -> None:
        # Broly is fought at the end of the story (chapter 15), so that goal needs every chapter.
        if self.options.goal == Goal.option_broly:
            self.options.goal_chapter.value = regions.LAST_CHAPTER

    def create_regions(self) -> None:
        regions.create_and_connect_regions(self)
        locations.create_all_locations(self)

    def set_rules(self) -> None:
        rules.set_all_rules(self)

    def create_items(self) -> None:
        items.create_all_items(self, locations.original_contents(self))

    def create_item(self, name: str) -> items.DbzAotsItem:
        return items.create_item(self, name)

    def get_filler_item_name(self) -> str:
        return items.FILLER_ITEM

    def generate_output(self, output_directory: str) -> None:
        # The patch holds no change to the game: opening it lets the BizHawk Client start BizHawk with the ROM.
        patch = DbzAotsProcedurePatch(player=self.player, player_name=self.player_name)
        patch.write(os.path.join(output_directory,
                                 f"{self.multiworld.get_out_file_name_base(self.player)}{patch.patch_file_ending}"))

    def fill_slot_data(self) -> dict[str, Any]:
        return {
            "experience_multiplier": self.options.experience_multiplier.value,
            "death_link": self.options.death_link.value,
            "goal_flag": locations.goal_flag(self.options.goal_chapter.value,
                                             self.options.goal == Goal.option_broly),
            "key_items": self.options.key_items.value,
            # Read by the PopTracker pack only, to show what this slot shuffles.
            "goal_chapter": self.options.goal_chapter.value,
            "hidden_items": self.options.hidden_items.value,
            "chapter_checks": self.options.chapter_checks.value,
            "east_city_ruins": self.options.east_city_ruins.value,
        }
