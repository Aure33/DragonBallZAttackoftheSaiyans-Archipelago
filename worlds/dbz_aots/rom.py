"""The patch file of a slot (.apdbzaots) and the setting that points to the player's ROM.

The world does not change the game: the patch only copies the player's own ROM (after checking it is the supported
release) so that opening the patch file with the BizHawk Client starts BizHawk with that ROM and the connector Lua
script, like the other BizHawk games (worlds/_bizhawk/context.py, _run_game).
"""
from __future__ import annotations

import settings
from worlds.Files import APProcedurePatch

from . import ram
from .items import GAME_NAME

PATCH_FILE_ENDING = ".apdbzaots"


def check_header(rom: bytes) -> None:
    """Raise if `rom` is not the supported release: EU, game code BRPP, revision 0 (header byte 0x1E)."""
    if rom[:len(ram.EXPECTED_HEADER)] != ram.EXPECTED_HEADER or rom[0x1E] != 0:
        raise ValueError("This is not the European release of Dragon Ball Z: Attack of the Saiyans "
                         "(game code BRPP, revision 0).")


class DbzAotsSettings(settings.Group):
    class RomFile(settings.UserFilePath):
        """File name of your Dragon Ball Z: Attack of the Saiyans ROM (European release, game code BRPP)"""
        description = "Dragon Ball Z - Attack of the Saiyans ROM File"
        copy_to = "Dragon Ball Z - Attack of the Saiyans (Europe).nds"

        @classmethod
        def validate(cls, path: str) -> None:
            with open(path, "rb") as file:
                check_header(file.read(0x20))

    rom_file: RomFile = RomFile(RomFile.copy_to)


class DbzAotsProcedurePatch(APProcedurePatch):
    game = GAME_NAME
    hash = "45ba1dcbca2f3646fa01a52de82b6f73"  # MD5 of the dump used to build the world (informative only)
    patch_file_ending = PATCH_FILE_ENDING
    result_file_ending = ".nds"
    procedure = []  # nothing to change: the result is the player's ROM, checked by its header

    @classmethod
    def get_source_data(cls) -> bytes:
        with open(settings.get_settings().dbz_aots_settings.rom_file, "rb") as file:
            rom = file.read()
        check_header(rom)
        return rom
