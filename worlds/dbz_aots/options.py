from dataclasses import dataclass

from Options import PerGameCommonOptions, Toggle


class EastCityRuins(Toggle):
    """
    Include the 6 chests of East City Ruins.
    Getting there needs the 7 Dragon Balls and Shenron's wish "To Go Somewhere New", which takes a long time.
    """

    display_name = "East City Ruins"


@dataclass
class DbzAotsOptions(PerGameCommonOptions):
    east_city_ruins: EastCityRuins
