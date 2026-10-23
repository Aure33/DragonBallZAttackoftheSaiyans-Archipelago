from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

if TYPE_CHECKING:
    from . import DbzAotsWorld

MENU = "Menu"
LAST_CHAPTER = 15


def chapter_region(chapter: int) -> str:
    return "Prologue" if chapter == 0 else f"Chapter {chapter}"


def chapter_entrance(chapter: int) -> str:
    """Name of the story step leading into `chapter` (rules.py puts the item requirements on it)."""
    return f"{chapter_region(chapter - 1)} -> {chapter_region(chapter)}"


def create_and_connect_regions(world: DbzAotsWorld) -> None:
    # The story is a straight line of chapters. Areas seen in a chapter stay reachable from the world map later,
    # so each chapter region also holds the chests of earlier areas that were only opened then.
    menu = Region(MENU, world.player, world.multiworld)
    chapters = [Region(chapter_region(chapter), world.player, world.multiworld) for chapter in range(LAST_CHAPTER + 1)]
    world.multiworld.regions += [menu, *chapters]
    menu.connect(chapters[0])
    for chapter in range(1, LAST_CHAPTER + 1):
        chapters[chapter - 1].connect(chapters[chapter], chapter_entrance(chapter))
