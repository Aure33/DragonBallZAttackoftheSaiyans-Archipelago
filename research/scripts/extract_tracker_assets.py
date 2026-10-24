"""Extrait de la ROM ce qu'il faut au pack PopTracker : l'image de chaque écran qui contient un lieu, et la position
de chaque coffre et objet à examiner sur son écran.

    research/.venv/bin/python research/scripts/extract_tracker_assets.py <ROM> [dossier, par défaut build/tracker_assets]

Sortie (hors dépôt : ce sont des extraits de la ROM) : <dossier>/maps/<carte>.png et <dossier>/positions.json
({drapeau: [carte, x, y]}, en pixels de l'image). Sources :
- coffres : CreateBox(…, x, y, objet, drapeau, …) dans les fonctions TreasureSet_<carte> (extract_chests.py) ;
- objets à examiner : la zone Point(x, y) ou Line(x1, y1, x2, y2) qui appelle la fonction de l'objet (milieu du
  segment pour Line) ;
- images : fieldmap.py.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import ndspy.rom

from extract_chests import PUSH, all_files, examine_spots, function_at, parse_script, push_value
from fieldmap import render
from sbdis import disassemble


def chest_positions(natives: list[str], functions: list[tuple[int, str]], code: bytes) -> dict[int, list]:
    if "CreateBox" not in natives:
        return {}
    call = re.escape(bytes([0x4A, natives.index("CreateBox")]))
    found = {}
    for match in re.finditer(rb"((?:" + PUSH + rb"){8})" + call, code, re.S):
        _, _, _, x, y, _, flag, _ = (push_value(i) for i in re.findall(PUSH, match.group(1), re.S))
        found[flag] = [function_at(functions, match.start()).removeprefix("TreasureSet_"), x, y]
    return found


def event_position(natives: list[str], functions: list[tuple[int, str]], code: bytes, target: str) -> list | None:
    """Milieu de la zone (Point ou Line) qui déclenche la fonction `target` du script."""
    reference = f"{[name for _, name in functions].index(target):02x}"
    for _, name in functions:
        ops = disassemble(natives, functions, code, name)
        for i in range(2, len(ops)):
            # sbdis lit « 23 24 17 » comme « 23 | op24.17 » quand le numéro de fonction est aussi un code à argument.
            if (ops[i] == reference or ops[i].startswith(f"op{reference}.")) and ops[i - 1] == "23" \
                    and ops[i - 2] == "push 1200":
                start = max([k for k in range(i) if ops[k].startswith("CALL ")] + [0])
                coords = [int(ops[k - 1].split()[1]) for k in range(start, i)
                          if ops[k] == "op20.03" and ops[k - 1].startswith("push ")]
                if len(coords) == 2:
                    return coords
                if len(coords) == 4:
                    return [(coords[0] + coords[2]) // 2, (coords[1] + coords[3]) // 2]
    return None


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[2] / "build/tracker_assets"
    positions: dict[int, list] = {}
    for path in sorted(n for n in all_files(rom.filenames) if n.startswith("script/cf0/") and n.endswith(".sb")):
        natives, functions, code = parse_script(bytes(rom.getFileByName(path)))
        positions.update(chest_positions(natives, functions, code))
        map_code = path.rsplit("/", 1)[1].removesuffix(".sb")
        for flag, _, function in examine_spots(natives, functions, code):
            where = event_position(natives, functions, code, function)
            if where:
                positions[flag] = [map_code, *where]
    (out / "maps").mkdir(parents=True, exist_ok=True)
    for map_code in sorted({place for place, _, _ in positions.values()}):
        try:
            render(rom, map_code).save(out / "maps" / f"{map_code}.png")
        except ValueError:  # écran sans fichier de carte (ex. skr06) : ses lieux n'auront pas de point sur une image
            print("pas d'image pour", map_code)
    (out / "positions.json").write_text(json.dumps(positions, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(positions)} positions, {len({p for p, _, _ in positions.values()})} écrans -> {out}")


if __name__ == "__main__":
    main()
