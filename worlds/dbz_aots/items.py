from __future__ import annotations

from typing import TYPE_CHECKING, NamedTuple

from BaseClasses import Item, ItemClassification

from .ram import ItemCategory

if TYPE_CHECKING:
    from . import DbzAotsWorld

GAME_NAME = "Dragon Ball Z - Attack of the Saiyans"


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


# Names are the English text of the EU ROM (research/rom_names.md); indexes were checked in the inventory
# (research/ram_map.md, section 2). Only the contents of the Training Island chests for now.
ITEMS: dict[str, ItemData] = {
    "Small Bean": ItemData(ItemCategory.USE_ITEM, 0, ItemClassification.filler),
    "Medium Bean": ItemData(ItemCategory.USE_ITEM, 1, ItemClassification.filler),
    "HP Capsule 50": ItemData(ItemCategory.USE_ITEM, 7, ItemClassification.filler),
    "Phoenix Feather": ItemData(ItemCategory.USE_ITEM, 29, ItemClassification.filler),
    # Needed later to cross the poison mist of Spinach Wastes (chapter 6).
    "Gas Mask": ItemData(ItemCategory.CAPSULE, 30, ItemClassification.progression),
    "Darkness Card": ItemData(ItemCategory.CAPSULE, 37, ItemClassification.useful),
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
