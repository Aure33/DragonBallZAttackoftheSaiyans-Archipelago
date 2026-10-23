"""Extrait le drapeau d'avancement de chaque scène d'histoire (appels SetScenarioCnt des scripts cf1).

Usage (environnement de recherche, qui contient ndspy) :
    research/.venv/bin/python research/scripts/extract_story_flags.py "<chemin de la ROM .nds>"

Affiche un tableau Markdown « scène → drapeau » à copier dans research/ram_map.md.

Observé (2026-10-24, ROM EU BRPP rév. 0) : chaque script contient la fonction SetScenarioCnt(n), dont le corps est
SetFlag(n, 1, 2). Une scène cXXYY_ZZ l'appelle au début avec une valeur fixe : 0x15 nn nn (empiler n) puis
0x46 + n° de SetScenarioCnt dans la table des fonctions du script (section 3) = appel d'une fonction du script.
Vérifié sur le prologue : les valeurs extraites (0, 5, 10, 11, 12, 15, 20, puis 55, 60) sont exactement les
drapeaux d'histoire allumés en mémoire (ram_map.md §4).
"""
from __future__ import annotations

import re
import struct
import sys

import ndspy.rom

from extract_chests import PUSH, all_files, c_string, parse_script, push_value


def script_function_names(data: bytes) -> list[str]:
    """Noms des fonctions du script dans l'ordre de leur table (l'ordre utilisé par l'instruction 0x46)."""
    section = struct.unpack_from("<6I", data, 8)[3]
    count = struct.unpack_from("<I", data, section + 4)[0]
    return [c_string(data, section + 8 + struct.unpack_from("<I", data, section + 8 + 8 * i)[0]) for i in range(count)]


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    print("| Scène | Drapeau |")
    print("|---|---|")
    for path in sorted(name for name in all_files(rom.filenames) if name.startswith("script/cf1/")):
        data = bytes(rom.getFileByName(path))
        names = script_function_names(data)
        if "SetScenarioCnt" not in names:
            continue
        _, _, code = parse_script(data)
        call = re.escape(bytes([0x46, names.index("SetScenarioCnt")]))
        flags = [push_value(match.group(1)) for match in re.finditer(rb"(" + PUSH + rb")" + call, code, re.S)]
        if flags:
            scene = path.rsplit("/", 1)[1].removesuffix(".sb")
            print(f"| `{scene}` | {', '.join(map(str, flags))} |")


if __name__ == "__main__":
    main()
