from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import Has, Rule

from .items import BUBBLES_THING, GAS_MASK, KI_BLAST_FRUIT, SNOWFIELD_KEY, SUBMARINE
from .locations import PROLOGUE_END, VICTORY
from .regions import chapter_entrance, chapter_region

if TYPE_CHECKING:
    from . import DbzAotsWorld

# What the story needs before a chapter can be played (research/decisions.md, D28). A chapter keeps the
# requirements of the previous ones, since the regions form a single line.
CHAPTER_REQUIREMENTS: dict[int, Rule] = {
    # Training Island, end of the prologue: Bulma lets nobody into the poison mist before the crystal ball until the
    # Gas Mask is equipped (script tut02_00, PoisonLock: EquipPartyAcc(287)); the crystal ball starts the last battle
    # of the prologue (research/decisions.md, C56). The Spinach Wastes (chapter 6) cross a gas floor too.
    1: Has(GAS_MASK),
    # East Mt. Paozu: the story path is blocked by a level 2 rock; the guide got level 2 from its first
    # Ki-Blast Fruit (chapter 7).
    8: Has(KI_BLAST_FRUIT),
    # Yemma Forest: the stumps to repair are behind level 3 doors; the guide got level 3 from its second
    # Ki-Blast Fruit (chapter 12).
    13: Has(KI_BLAST_FRUIT, 2),
}


# Story key items, checked in the inventory on the story path (research/decisions.md, C42 and C46). The logic asks for
# each one from the start of its chapter, which is stricter than the game (it is only needed after the scene that
# gives it) and therefore safe.
KEY_ITEM_REQUIREMENTS: dict[int, Rule] = {
    # Holly Plain gate: the story of chapter 8 goes on behind it.
    8: Has(SNOWFIELD_KEY),
    # Pirate Cave: "We can't get across without a submarine" (chapter 10).
    10: Has(SUBMARINE),
    # Yemma Forest: the five stumps to repair before the story goes on (chapter 13).
    13: Has(BUBBLES_THING),
}


def set_all_rules(world: DbzAotsWorld) -> None:
    for chapter in sorted(set(CHAPTER_REQUIREMENTS) | set(KEY_ITEM_REQUIREMENTS)):
        if chapter > world.options.goal_chapter:
            continue
        rule = CHAPTER_REQUIREMENTS.get(chapter)
        if world.options.key_items and chapter in KEY_ITEM_REQUIREMENTS:
            rule = KEY_ITEM_REQUIREMENTS[chapter] if rule is None else rule & KEY_ITEM_REQUIREMENTS[chapter]
        if rule is None:
            continue
        world.set_rule(world.get_entrance(chapter_entrance(chapter)), rule)
    if PROLOGUE_END in {location.name for location in world.get_region(chapter_region(0)).locations}:
        world.set_rule(world.get_location(PROLOGUE_END), CHAPTER_REQUIREMENTS[1])
    world.set_completion_rule(Has(VICTORY))
