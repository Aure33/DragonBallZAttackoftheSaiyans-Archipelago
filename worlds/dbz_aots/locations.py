from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Location

from .chest_data import CHESTS, ChestData
from .items import GAME_NAME, DbzAotsItem
from .regions import LAST_CHAPTER, chapter_region

if TYPE_CHECKING:
    from . import DbzAotsWorld

LOCATION_ID_BASE = 100_000
"""A chest's Archipelago ID is LOCATION_ID_BASE + the game flag set when the chest is opened."""

LOCATION_NAME_TO_ID: dict[str, int] = {chest.name: LOCATION_ID_BASE + chest.flag for chest in CHESTS}

GOAL_EVENT = "Defeat Vegeta"
VICTORY = "Victory"


class DbzAotsLocation(Location):
    game = GAME_NAME


def included_chests(world: DbzAotsWorld) -> list[ChestData]:
    return [chest for chest in CHESTS if not chest.bonus or world.options.east_city_ruins]


def original_contents(world: DbzAotsWorld) -> list[str]:
    """Items found in the included chests in the original game: they make up the item pool."""
    return [chest.item for chest in included_chests(world)]


def create_all_locations(world: DbzAotsWorld) -> None:
    for chest in included_chests(world):
        world.get_region(chapter_region(chest.chapter)).add_locations(
            {chest.name: LOCATION_NAME_TO_ID[chest.name]}, DbzAotsLocation
        )
    # The last battle (Vegeta, end of chapter 15); the client sees it through the story flag of the next scene.
    world.get_region(chapter_region(LAST_CHAPTER)).add_event(
        GOAL_EVENT, VICTORY, location_type=DbzAotsLocation, item_type=DbzAotsItem
    )
