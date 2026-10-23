from test.bases import WorldTestBase

from .. import DbzAotsWorld
from ..items import GAME_NAME


class DbzAotsTestBase(WorldTestBase):
    game = GAME_NAME
    world: DbzAotsWorld
