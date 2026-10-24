from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import Has, Rule

from .items import GAS_MASK, KI_BLAST_FRUIT, SNOWFIELD_KEY
from .locations import VICTORY
from .regions import chapter_entrance

if TYPE_CHECKING:
    from . import DbzAotsWorld

# What the story needs before a chapter can be played (research/decisions.md, D28). A chapter keeps the
# requirements of the previous ones, since the regions form a single line.
CHAPTER_REQUIREMENTS: dict[int, Rule] = {
    # Spinach Wastes: the story path crosses a gas floor (DSR guide, chapter 6).
    6: Has(GAS_MASK),
    # East Mt. Paozu: the story path is blocked by a level 2 rock; the guide got level 2 from its first
    # Ki-Blast Fruit (chapter 7).
    8: Has(KI_BLAST_FRUIT),
    # Yemma Forest: the stumps to repair are behind level 3 doors; the guide got level 3 from its second
    # Ki-Blast Fruit (chapter 12).
    13: Has(KI_BLAST_FRUIT, 2),
}


# Holly Plain gate: the story of chapter 8 goes on behind it, and it only opens with the Snowfield Key in the
# inventory (research/decisions.md, C42). The logic asks for the key from the start of chapter 8, which is stricter
# than the game (the key is only needed after Lunch is found) and therefore safe.
KEY_ITEM_REQUIREMENTS: dict[int, Rule] = {8: Has(SNOWFIELD_KEY)}


def set_all_rules(world: DbzAotsWorld) -> None:
    for chapter in sorted(set(CHAPTER_REQUIREMENTS) | set(KEY_ITEM_REQUIREMENTS)):
        if chapter > world.options.goal_chapter:
            continue
        rule = CHAPTER_REQUIREMENTS.get(chapter)
        if world.options.key_items and chapter in KEY_ITEM_REQUIREMENTS:
            rule = KEY_ITEM_REQUIREMENTS[chapter] if rule is None else rule & KEY_ITEM_REQUIREMENTS[chapter]
        world.set_rule(world.get_entrance(chapter_entrance(chapter)), rule)
    world.set_completion_rule(Has(VICTORY))
