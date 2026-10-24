from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import Has, Rule

from .items import GAS_MASK, KI_BLAST_FRUIT
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


def set_all_rules(world: DbzAotsWorld) -> None:
    for chapter, rule in CHAPTER_REQUIREMENTS.items():
        if chapter > world.options.goal_chapter:
            continue
        world.set_rule(world.get_entrance(chapter_entrance(chapter)), rule)
    world.set_completion_rule(Has(VICTORY))
