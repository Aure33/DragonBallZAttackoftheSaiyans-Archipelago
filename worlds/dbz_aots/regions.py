from __future__ import annotations

from typing import TYPE_CHECKING

from BaseClasses import Region

if TYPE_CHECKING:
    from . import DbzAotsWorld

MENU = "Menu"
TRAINING_ISLAND = "Training Island"


def create_and_connect_regions(world: DbzAotsWorld) -> None:
    menu = Region(MENU, world.player, world.multiworld)
    training_island = Region(TRAINING_ISLAND, world.player, world.multiworld)
    world.multiworld.regions += [menu, training_island]
    # The prologue is linear: the island is reached by talking to Master Roshi, no item needed.
    menu.connect(training_island, f"{MENU} to {TRAINING_ISLAND}")
