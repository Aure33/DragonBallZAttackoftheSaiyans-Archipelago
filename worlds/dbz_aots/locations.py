from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Location

from .items import GAME_NAME, DbzAotsItem
from .location_data import LOCATIONS, LocationData
from .ram import CHAPTER_START_FLAGS
from .regions import LAST_CHAPTER, chapter_region

if TYPE_CHECKING:
    from . import DbzAotsWorld

LOCATION_ID_BASE = 100_000
"""A location's Archipelago ID is LOCATION_ID_BASE + the game flag set when its item is taken."""

# Story steps: finishing a chapter sets the story flag of the next one. They hold no item in the original game.
# The last chapter ends with the goal instead.
STORY_LOCATIONS: dict[str, tuple[int, int]] = {
    f"{chapter_region(chapter)} Cleared": (chapter, CHAPTER_START_FLAGS[chapter]) for chapter in range(LAST_CHAPTER)
}

LOCATION_NAME_TO_ID: dict[str, int] = {
    **{data.name: LOCATION_ID_BASE + data.flag for data in LOCATIONS},
    **{name: LOCATION_ID_BASE + flag for name, (_, flag) in STORY_LOCATIONS.items()},
}
ORIGINAL_ITEM_LOCATION_IDS = frozenset(LOCATION_ID_BASE + data.flag for data in LOCATIONS)
"""Locations that give an item in the original game, which the client takes back (approach A)."""

GOAL_EVENT = "Defeat Vegeta"
VICTORY = "Victory"


class DbzAotsLocation(Location):
    game = GAME_NAME


def included_locations(world: DbzAotsWorld) -> list[LocationData]:
    return [data for data in LOCATIONS if not data.bonus or world.options.east_city_ruins]


def original_contents(world: DbzAotsWorld) -> list[str]:
    """Items found at the included locations in the original game: they make up the item pool."""
    return [data.item for data in included_locations(world)]


def create_all_locations(world: DbzAotsWorld) -> None:
    for data in included_locations(world):
        world.get_region(chapter_region(data.chapter)).add_locations(
            {data.name: LOCATION_NAME_TO_ID[data.name]}, DbzAotsLocation
        )
    for name, (chapter, _) in STORY_LOCATIONS.items():
        world.get_region(chapter_region(chapter)).add_locations({name: LOCATION_NAME_TO_ID[name]}, DbzAotsLocation)
    # The last battle (Vegeta, end of chapter 15); the client sees it through the story flag of the next scene.
    world.get_region(chapter_region(LAST_CHAPTER)).add_event(
        GOAL_EVENT, VICTORY, location_type=DbzAotsLocation, item_type=DbzAotsItem
    )
