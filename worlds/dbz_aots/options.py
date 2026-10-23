from dataclasses import dataclass

from Options import PerGameCommonOptions


@dataclass
class DbzAotsOptions(PerGameCommonOptions):
    """No game-specific option yet (minimal world, Training Island only)."""
