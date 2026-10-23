from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import Item, ItemClassification

from .chest_data import ITEM_SLOTS
from .ram import ItemCategory

if TYPE_CHECKING:
    from . import DbzAotsWorld

GAME_NAME = "Dragon Ball Z - Attack of the Saiyans"

KI_BLAST_FRUIT = "Ki-Blast Fruit"
"""Raises the size of the Ki-blast meter on the field (ROM description): one per level of breakable rocks."""
GAS_MASK = "Gas Mask"
"""Makes gas floors safe (ROM description); Spinach Wastes (chapter 6) and later story paths cross them."""


class ItemData(NamedTuple):
    category: ItemCategory
    index: int
    """Item number in the game's data table, which is also its slot in the inventory."""
    classification: ItemClassification


def item_id(category: ItemCategory, index: int) -> int:
    """Archipelago ID of a game item: 1000 * (category + 1) + its number in the game's data table."""
    return 1000 * (category + 1) + index


def item_slot(ap_id: int) -> tuple[ItemCategory, int]:
    """Inverse of item_id: the category and number of the game item behind an Archipelago ID."""
    return ItemCategory(ap_id // 1000 - 1), ap_id % 1000


PROGRESSION = {KI_BLAST_FRUIT, GAS_MASK}
# Consumables worth more than a heal: permanent stat boosts, the EXP booster and the reusable Dragon Stone.
USEFUL_USE_ITEMS = {"HP Fruit", "Ki Fruit", "Power Fruit", "Defense Fruit", "Speed Fruit", "Luck Fruit",
                    "Skill Fruit", "Recovery Fruit", "EXP Boost", "Dragon Stone", "Super Senzu Bean"}


def classification(name: str, category: ItemCategory) -> ItemClassification:
    if name in PROGRESSION:
        return ItemClassification.progression
    if category in (ItemCategory.BATTLE_ACCESSORY, ItemCategory.CAPSULE) or name in USEFUL_USE_ITEMS:
        return ItemClassification.useful
    return ItemClassification.filler


# Every item found in a chest. Names are the English text of the EU ROM and slots come from its data tables
# (research/chests.md); the inventory layout was checked in game (research/ram_map.md, section 2).
ITEMS: dict[str, ItemData] = {
    name: ItemData(ItemCategory(category), index, classification(name, ItemCategory(category)))
    for name, (category, index) in ITEM_SLOTS.items()
}

ITEM_NAME_TO_ID: dict[str, int] = {name: item_id(data.category, data.index) for name, data in ITEMS.items()}

FILLER_ITEM = "Small Bean"


class DbzAotsItem(Item):
    game = GAME_NAME


def create_item(world: DbzAotsWorld, name: str) -> DbzAotsItem:
    return DbzAotsItem(name, ITEMS[name].classification, ITEM_NAME_TO_ID[name], world.player)


def create_all_items(world: DbzAotsWorld, original_contents: list[str]) -> None:
    """Put the original contents of the locations in the pool, topped up with filler if needed."""
    itempool = [world.create_item(name) for name in original_contents]
    missing = len(world.multiworld.get_unfilled_locations(world.player)) - len(itempool)
    itempool += [world.create_filler() for _ in range(missing)]
    world.multiworld.itempool += itempool
