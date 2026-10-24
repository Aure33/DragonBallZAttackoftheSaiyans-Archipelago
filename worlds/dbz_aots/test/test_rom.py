import unittest

from worlds.Files import AutoPatchRegister

from .. import ram
from ..rom import PATCH_FILE_ENDING, DbzAotsProcedurePatch, check_header


class TestRomCheck(unittest.TestCase):
    def header(self, revision: int = 0) -> bytearray:
        rom = bytearray(0x200)
        rom[:len(ram.EXPECTED_HEADER)] = ram.EXPECTED_HEADER
        rom[0x1E] = revision
        return rom

    def test_the_supported_release_passes(self) -> None:
        check_header(bytes(self.header()))

    def test_another_revision_is_refused(self) -> None:
        with self.assertRaises(ValueError):
            check_header(bytes(self.header(revision=1)))

    def test_another_game_is_refused(self) -> None:
        rom = self.header()
        rom[0x0C:0x10] = b"BRPE"
        with self.assertRaises(ValueError):
            check_header(bytes(rom))


class TestPatchFile(unittest.TestCase):
    def test_the_patch_file_opens_with_our_handler(self) -> None:
        self.assertIs(DbzAotsProcedurePatch, AutoPatchRegister.get_handler(f"AP_1_P1_Aure{PATCH_FILE_ENDING}"))

    def test_the_patch_changes_nothing(self) -> None:
        self.assertEqual([], DbzAotsProcedurePatch.procedure)
