from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import Location

from .items import GAME_NAME, DbzAotsItem
from .regions import TRAINING_ISLAND

if TYPE_CHECKING:
    from . import DbzAotsWorld

LOCATION_ID_BASE = 100_000
"""A chest's Archipelago ID is LOCATION_ID_BASE + the game flag set when the chest is opened."""


class LocationData(NamedTuple):
    region: str
    flag: int


# Flags from research/ram_map.md, section 3. Flags 1400-1405 are the six chests of Training Island screens 1-2
# (1401: a Small Bean, 1402: the Phoenix Feather); 1583-1584 are the two chests found after Bulma's call.
# Which chest holds which flag is not fully known yet, so the names are numbered for now.
LOCATIONS: dict[str, LocationData] = {
    "Training Island Chest 1": LocationData(TRAINING_ISLAND, 1400),
    "Training Island Chest 2": LocationData(TRAINING_ISLAND, 1401),
    "Training Island Chest 3": LocationData(TRAINING_ISLAND, 1402),
    "Training Island Chest 4": LocationData(TRAINING_ISLAND, 1403),
    "Training Island Chest 5": LocationData(TRAINING_ISLAND, 1404),
    "Training Island Chest 6": LocationData(TRAINING_ISLAND, 1405),
    "Training Island Chest 7": LocationData(TRAINING_ISLAND, 1583),
    "Training Island Chest 8": LocationData(TRAINING_ISLAND, 1584),
}

# Original contents of the eight chests, checked in game (research/game_data.md, prologue): they go into the pool.
ORIGINAL_CONTENTS: list[str] = [
    "HP Capsule 50", "Small Bean", "Small Bean", "Small Bean",
    "Phoenix Feather", "Medium Bean", "Gas Mask", "Darkness Card",
]

LOCATION_NAME_TO_ID: dict[str, int] = {name: LOCATION_ID_BASE + data.flag for name, data in LOCATIONS.items()}

GOAL_EVENT = "Defeat Jackie Chun"
VICTORY = "Victory"


class DbzAotsLocation(Location):
    game = GAME_NAME


def create_all_locations(world: DbzAotsWorld) -> None:
    for name, data in LOCATIONS.items():
        world.get_region(data.region).add_locations({name: LOCATION_NAME_TO_ID[name]}, DbzAotsLocation)
    world.get_region(TRAINING_ISLAND).add_event(
        GOAL_EVENT, VICTORY, location_type=DbzAotsLocation, item_type=DbzAotsItem
    )
