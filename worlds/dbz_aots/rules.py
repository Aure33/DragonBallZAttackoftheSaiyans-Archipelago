from __future__ import annotations

from typing import TYPE_CHECKING

from rule_builder.rules import Has

from .locations import VICTORY

if TYPE_CHECKING:
    from . import DbzAotsWorld


def set_all_rules(world: DbzAotsWorld) -> None:
    # Every Training Island chest is reachable from the start: the Ki blast that breaks the glowing rocks
    # is taught on the island itself, and the last two chests only need story progress.
    world.set_completion_rule(Has(VICTORY))
