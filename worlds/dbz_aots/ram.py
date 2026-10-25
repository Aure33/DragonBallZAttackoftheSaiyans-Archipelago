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

GAME_RUNNING = 0x0AF1E4
"""4 bytes: 1 while a game is loaded (field, battle, menus, scenes), 0 on the logos and the title screen. A defeat
makes the game restart from the logos, which sets it to 0 (research/decisions.md, C37)."""

PARTY = 0x0CC374
"""Party slots, 4 bytes each: 3 fighters then 5 reserve slots, each 0 or the DS address of a character sheet. Read by
the native AddBtlMember of the game code (research/decisions.md, C33)."""
PARTY_SLOT_COUNT = 8
SHEET_ADDRESS_TO_CURRENT_HP = 0xA0
"""A party slot points 0xA0 bytes before the current HP of the character (0x8 before its max HP)."""
DS_MAIN_RAM_START = 0x02000000
"""Party slots hold DS bus addresses; Main RAM addresses in this file are relative to this one."""

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

BROLY_DEFEATED_FLAG = 2672
"""Set by scene c1410_04, which only plays after Broly is beaten (a defeat restarts the game): seen in game, along with
Broly's Necklace (research/decisions.md, C47)."""

OBJECT_POOL = 0x0D23DC
"""Objects of the current field map, OBJECT_SIZE bytes each, kept after a map change until their slot is reused. A
chest made by the script call CreateBox keeps there what it gives: item code at +0x30, state at +0x34 (0 closed,
2 opened) and game flag at +0x3C, 4 bytes each. Writing the item code before the chest is opened changes the item
the game shows and gives (research/decisions.md, C55)."""
OBJECT_SIZE = 0xEC
OBJECT_SLOTS = 48
"""Slots read by the client: a map makes at most 21 chests, and slots past 31 were empty on every map looked at."""
CHEST_FIELDS_OFFSET = 0x30
CHEST_FIELDS_SIZE = 0x10

MAP_SCRIPT = 0x282000
"""Copy of the script of the current map (script/<language>/cf0/<area>/<map>.sb), the same bytes as the file but for
its header: a hidden item's code can be rewritten there before it is examined (research/decisions.md, C55)."""
PUSH_BYTE = 0x14
"""Script opcode that pushes the next byte (signed): hidden items use it for their item code."""
HIGHEST_HIDDEN_ITEM_CODE = 0x7F

TEXT_TABLES = 0x200000
"""Copy of btl/bdat/<language>/bdat.bin, loaded at boot: u32 table count, u32 size, then u32 table offsets; each
table starts with "BDAT", u16 name offset at +6 and u16 row offset at +0xA, rows of u32 text offsets."""
ITEM_TEXT_TABLE = b"use_item_mes"
"""Names and descriptions of the use items: rows 2n and 2n + 1 for text n."""
GENERIC_ITEM_CODE = 103
"""Use item 102 (table Use_Item), unused by the game: its name and description point to empty strings at the end of
use_item_mes, where the client writes "Archipelago Item" in the language of the game (research/decisions.md, C55)."""
GENERIC_ITEM_NAME_ROW = 208
"""Row of its name in use_item_mes (text 104, from the first field of its Use_Item row); the description follows."""

RECEIVED_ITEMS_COUNTER = 0x09FB44
"""4 bytes at the end of the flag block, never used by the game so far: provisional (research/decisions.md, D20)."""


def item_code(category: ItemCategory, index: int) -> int:
    """Code of an item in the game scripts (chests, GetItem): its inventory position plus 1."""
    return INVENTORY_OFFSET[category] + index + 1


def inventory_address(category: ItemCategory, index: int) -> int:
    """Address of the quantity byte of item `index` of `category`."""
    return INVENTORY + INVENTORY_OFFSET[category] + index


def flag_position(flag: int) -> tuple[int, int]:
    """Address of the byte holding `flag`, and the bit mask of the flag in that byte."""
    if not 0 <= flag < FLAGS_SIZE * 8:
        raise ValueError(f"Flag {flag} is outside the flag block")
    return FLAGS + flag // 8, 1 << (flag % 8)
