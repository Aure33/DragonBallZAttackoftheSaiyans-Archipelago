from dataclasses import dataclass

from Options import DeathLink, DefaultOnToggle, PerGameCommonOptions, Range, Toggle


class GoalChapter(Range):
    """
    The chapter whose end wins the game. 15 is the whole story: defeat Vegeta in the last battle.
    A lower chapter makes a shorter game: only the locations up to that chapter are included.
    """

    display_name = "Goal Chapter"
    range_start = 1
    range_end = 15
    default = 15


class HiddenItems(DefaultOnToggle):
    """Include the 14 items found by examining a drawer, a stall, a door... and not in a chest."""

    display_name = "Hidden Items"


class ChapterChecks(DefaultOnToggle):
    """The end of the prologue and of each chapter before the goal sends a check."""

    display_name = "Chapter Checks"


class EastCityRuins(Toggle):
    """
    Include the 6 chests of East City Ruins.
    Getting there needs the 7 Dragon Balls and Shenron's wish "To Go Somewhere New", which takes a long time.
    Only used when the goal is chapter 15.
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
    goal_chapter: GoalChapter
    hidden_items: HiddenItems
    chapter_checks: ChapterChecks
    east_city_ruins: EastCityRuins
    experience_multiplier: ExperienceMultiplier
    death_link: DeathLink
