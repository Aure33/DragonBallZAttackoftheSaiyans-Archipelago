from dataclasses import dataclass

from Options import Choice, DeathLink, DefaultOnToggle, PerGameCommonOptions, Range, Toggle


class Goal(Choice):
    """
    chapter: the end of the chapter chosen in Goal Chapter wins the game.
    broly: defeat Broly, the secret boss. He can be fought after Nappa and before the last battle against Vegeta:
    collect the Dragon Balls that Mr. Popo makes again, then pick Shenron's wish "To fight the ultimate enemy" and
    enter the portal on East Mt. Paozu. The whole story is included (Goal Chapter is not used).
    """

    display_name = "Goal"
    option_chapter = 0
    option_broly = 1
    default = 0


class GoalChapter(Range):
    """
    The chapter whose end wins the game, when Goal is "chapter". 15 is the whole story: defeat Vegeta in the last
    battle.
    A lower chapter makes a shorter game: only the locations up to that chapter are included.
    """

    display_name = "Goal Chapter"
    range_start = 1
    range_end = 15
    default = 15


class HiddenItems(DefaultOnToggle):
    """Include the 17 items found by examining a drawer, a stall, a door... and not in a chest."""

    display_name = "Hidden Items"


class ChapterChecks(DefaultOnToggle):
    """The end of the prologue and of each chapter before the goal sends a check."""

    display_name = "Chapter Checks"


class KeyItems(DefaultOnToggle):
    """
    Shuffle the story key items that the game checks in the inventory: the Snowfield Key (chapter 8), the Submarine
    (chapter 10) and Bubbles' Thing (chapter 13). The scenes that give them become locations, and the way they open
    stays closed until the item is received.
    """

    display_name = "Key Items"


class EastCityRuins(Toggle):
    """
    Include the 6 chests of East City Ruins.
    Getting there needs the 7 Dragon Balls and Shenron's wish "To Go Somewhere New", which takes a long time.
    Only used when the whole story is included (goal chapter 15 or Broly).
    """

    display_name = "East City Ruins"


class ExperienceMultiplier(Range):
    """
    Multiply the experience and AP earned in battle, to keep up with a multiworld.
    The extra experience never skips a level at once: what is left is added after the next battles.
    """

    display_name = "Experience Multiplier"
    range_start = 1
    range_end = 10
    default = 1


@dataclass
class DbzAotsOptions(PerGameCommonOptions):
    goal: Goal
    goal_chapter: GoalChapter
    hidden_items: HiddenItems
    chapter_checks: ChapterChecks
    key_items: KeyItems
    east_city_ruins: EastCityRuins
    experience_multiplier: ExperienceMultiplier
    death_link: DeathLink
