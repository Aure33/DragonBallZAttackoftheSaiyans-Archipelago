from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Location, LocationProgressType

from .items import GAME_NAME, DbzAotsItem
from .location_data import LOCATIONS, LocationData
from .ram import CHAPTER_START_FLAGS, GOAL_FLAG
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
# Areas the story may close for a while (the Other World between chapters 9 and 13) or for good (Nemuria Ruins: no
# known way back). A chest left there must never block anyone, so their locations never hold progression items
# (research/decisions.md, D36).
MISSABLE_ZONES = frozenset({"King Yemma's Mansion", "Princess Snake's House", "King Kai's Planet", "Yemma Forest",
                            "Nemuria Ruins"})

LOCATION_NAME_GROUPS: dict[str, set[str]] = {}
for _data in LOCATIONS:
    LOCATION_NAME_GROUPS.setdefault(_data.zone, set()).add(_data.name)
LOCATION_NAME_GROUPS["Story"] = set(STORY_LOCATIONS)

ORIGINAL_ITEM_LOCATION_IDS = frozenset(LOCATION_ID_BASE + data.flag for data in LOCATIONS)
"""Locations that give an item in the original game, which the client takes back (approach A)."""

GOAL_EVENT = "Goal"
VICTORY = "Victory"


class DbzAotsLocation(Location):
    game = GAME_NAME


def included_locations(world: DbzAotsWorld) -> list[LocationData]:
    options = world.options
    return [data for data in LOCATIONS
            if data.chapter <= options.goal_chapter
            and (not data.bonus or options.east_city_ruins)
            and (not data.hidden or options.hidden_items)]


def included_story_locations(world: DbzAotsWorld) -> dict[str, tuple[int, int]]:
    """Ends of chapter before the goal (the end of the goal chapter is the goal itself)."""
    if not world.options.chapter_checks:
        return {}
    return {name: step for name, step in STORY_LOCATIONS.items() if step[0] < world.options.goal_chapter}


def goal_flag(goal_chapter: int) -> int:
    """Game flag that tells the client the goal is reached: the start of the next chapter, or the end of the game."""
    return GOAL_FLAG if goal_chapter == LAST_CHAPTER else CHAPTER_START_FLAGS[goal_chapter]


def original_contents(world: DbzAotsWorld) -> list[str]:
    """Items found at the included locations in the original game: they make up the item pool."""
    return [data.item for data in included_locations(world)]


def create_all_locations(world: DbzAotsWorld) -> None:
    for data in included_locations(world):
        region = world.get_region(chapter_region(data.chapter))
        location = DbzAotsLocation(world.player, data.name, LOCATION_NAME_TO_ID[data.name], region)
        if data.zone in MISSABLE_ZONES:
            location.progress_type = LocationProgressType.EXCLUDED
        region.locations.append(location)
    for name, (chapter, _) in included_story_locations(world).items():
        world.get_region(chapter_region(chapter)).add_locations({name: LOCATION_NAME_TO_ID[name]}, DbzAotsLocation)
    # The end of the goal chapter (for chapter 15, the last battle against Vegeta); the client sees it through the
    # story flag of the next scene.
    world.get_region(chapter_region(world.options.goal_chapter.value)).add_event(
        GOAL_EVENT, VICTORY, location_type=DbzAotsLocation, item_type=DbzAotsItem
    )
