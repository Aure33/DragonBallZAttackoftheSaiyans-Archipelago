from dataclasses import dataclass

from Options import DeathLink, PerGameCommonOptions, Range, Toggle


class EastCityRuins(Toggle):
    """
    Include the 6 chests of East City Ruins.
    Getting there needs the 7 Dragon Balls and Shenron's wish "To Go Somewhere New", which takes a long time.
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
    east_city_ruins: EastCityRuins
    experience_multiplier: ExperienceMultiplier
    death_link: DeathLink
