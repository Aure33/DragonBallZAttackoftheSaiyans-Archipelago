"""Memory map of Dragon Ball Z: Attack of the Saiyans, EU release (game code BRPP, revision 0).

Addresses are offsets in BizHawk's "Main RAM" domain (DS address minus 0x02000000).
Every value comes from research/ram_map.md, which records how and when it was found.
"""
from enum import IntEnum

MAIN_RAM = "Main RAM"

ROM_HEADER_COPY = 0x3FFE00
"""Copy of the cartridge header made by the DS at boot."""
EXPECTED_HEADER = b"DB KAI RPG\x00\x00BRPPAF"
"""Title, game code and maker code of the supported release (first 18 bytes of the header)."""

CURRENT_MAP = 0x0D226C
"""Map code of the current field map as 8 ASCII bytes (e.g. b"tut01_00"); all zero while no save is loaded."""
MAP_CODE_LENGTH = 8

BATTLE_STATE = 0x09B236
"""2 bytes: 0xFFFF during a battle (and before a save is loaded), 0x0000 on the field and in the menu."""

ZENI = 0x0CC370
"""Money, 4 bytes little-endian."""

INVENTORY = 0x0CC398
"""Owned quantity of every item, one byte each, grouped by category (see INVENTORY_OFFSET)."""


class ItemCategory(IntEnum):
    """Item categories, in the order of the game's data tables (and of the inventory)."""
    USE_ITEM = 0
    BATTLE_ACCESSORY = 1
    CAPSULE = 2
    KEY_ITEM = 3


INVENTORY_OFFSET: dict[ItemCategory, int] = {
    ItemCategory.USE_ITEM: 0x000,  # 128 entries, ROM table Use_Item
    ItemCategory.BATTLE_ACCESSORY: 0x080,  # 128 entries, ROM table Btl_Acc (offset deduced, not observed yet)
    ItemCategory.CAPSULE: 0x100,  # 48 entries, ROM table Pt_Eqp
    ItemCategory.KEY_ITEM: 0x130,  # 108 entries, ROM table Key_Item
}
INVENTORY_SIZE = 0x130 + 108

MAX_QUANTITY = 99
"""Highest quantity the client ever writes: a safety cap, the game's own limit has not been observed yet."""

CHARACTER_SHEETS = 0x0CD308
"""Max HP of Goku, start of the 6 character sheets (Goku, Gohan, Piccolo, Krillin, Tien, Yamcha): offsets below are
relative to a sheet's max HP (research/ram_map.md, section 2)."""
CHARACTER_SHEET_SIZE = 0x24C
CHARACTER_COUNT = 6
LEVEL_OFFSET = 0x60  # 1 byte
EXPERIENCE_OFFSET = 0x194  # 4 bytes, total experience (shown in the menu, not used to level up)
EXPERIENCE_TO_NEXT_OFFSET = 0x198  # 4 bytes; the game levels up when a battle brings it below 0
AP_OFFSET = 0x19C  # 4 bytes
CHARACTER_SHEETS_SIZE = (CHARACTER_COUNT - 1) * CHARACTER_SHEET_SIZE + AP_OFFSET + 4
MAX_AP = 999_999
"""Highest AP total the client ever writes: a safety cap, the game's own limit has not been observed yet."""

FLAGS = 0x09F7E8
"""Permanent event flags (chests, story...), one bit each; saved verbatim in the save file."""
FLAGS_SIZE = 0x360

CHAPTER_START_FLAGS = (55, 110, 165, 220, 275, 380, 435, 490, 595, 650, 755, 810, 865, 920, 1025)
"""Story flags set when chapters 1 to 15 start (first scenes c0100_00 to c1500_00): research/ram_map.md, section 4."""

GOAL_FLAG = 1050
"""Story flag set when scene c1505_00 starts, right after the last battle of the game (Vegeta, battle LAS_EB05 of
scene c1504_01): research/ram_map.md, section 4."""

RECEIVED_ITEMS_COUNTER = 0x09FB44
"""4 bytes at the end of the flag block, never used by the game so far: provisional (research/decisions.md, D20)."""


def inventory_address(category: ItemCategory, index: int) -> int:
    """Address of the quantity byte of item `index` of `category`."""
    return INVENTORY + INVENTORY_OFFSET[category] + index


def flag_position(flag: int) -> tuple[int, int]:
    """Address of the byte holding `flag`, and the bit mask of the flag in that byte."""
    if not 0 <= flag < FLAGS_SIZE * 8:
        raise ValueError(f"Flag {flag} is outside the flag block")
    return FLAGS + flag // 8, 1 << (flag % 8)
