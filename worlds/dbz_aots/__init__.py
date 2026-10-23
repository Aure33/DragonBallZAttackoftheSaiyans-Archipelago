from BaseClasses import Tutorial
from worlds.AutoWorld import WebWorld, World

from . import client as client  # importing the module registers the BizHawk client
from . import items, locations, regions, rules
from .options import DbzAotsOptions


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

    item_name_to_id = items.ITEM_NAME_TO_ID
    location_name_to_id = locations.LOCATION_NAME_TO_ID

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
