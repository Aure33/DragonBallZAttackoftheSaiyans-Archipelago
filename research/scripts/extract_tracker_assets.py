"""Extrait de la ROM ce qu'il faut au pack PopTracker : l'image de chaque écran qui contient un lieu, et la position
de chaque coffre et objet à examiner sur son écran.

    research/.venv/bin/python research/scripts/extract_tracker_assets.py <ROM> [dossier, par défaut build/tracker_assets]

Sortie (hors dépôt : ce sont des extraits de la ROM) : <dossier>/maps/<carte>.png et <dossier>/positions.json
({drapeau: [carte, x, y]}, en pixels de l'image). Sources :
- coffres : CreateBox(…, x, y, objet, drapeau, …) dans les fonctions TreasureSet_<carte> (extract_chests.py) ;
- objets à examiner : la zone Point(x, y) ou Line(x1, y1, x2, y2) qui appelle la fonction de l'objet (milieu du
  segment pour Line) ;
- images : fieldmap.py ;
- carte du monde : image `worldmap` et <dossier>/world.json ({carte d'arrivée: [x, y]}) = les zones cliquables, lues
  dans les appels SetClickPoint(n, x, y, nom, carte, ?, x d'arrivée, y d'arrivée, ?) de script/cf/worldmap.sb (les
  variables du script sont suivies ; les chaînes viennent de la section 2 : u32 8, u32 n, n décalages, textes).
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

import ndspy.rom

from extract_chests import PUSH, all_files, c_string, examine_spots, function_at, parse_script, push_value
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


# Faux coffre des égouts (build_world_data.py, EXTRA_LOCATIONS) : objet 1 de ges02_00, créé par CharaSet en (116, 207)
# dans ObjSet01 tant que le drapeau 2663 est éteint, relié à Trap01 par Id (ouvert en jeu, decisions.md C57).
# Même chose pour le faux coffre de Princesse Serpent (objet 1 de sna03_00, (191, 192)) et pour l'homme aux carottes
# (PNJ n° 6 de wst03_00, (443, 154)), dont les quatre récompenses sont posées côte à côte (decisions.md C59).
OBJECTS = {2663: ["ges02_00", 116, 207], 2582: ["sna03_00", 191, 192],
           2684: ["wst03_00", 422, 154], 2627: ["wst03_00", 436, 154], 2628: ["wst03_00", 450, 154],
           2629: ["wst03_00", 464, 154]}


def script_strings(data: bytes) -> list[str]:
    section = struct.unpack_from("<6I", data, 8)[2]
    count = struct.unpack_from("<I", data, section + 4)[0]
    base = section + 8 + 4 * count
    return [c_string(data, base + offset) for offset in struct.unpack_from(f"<{count}I", data, section + 8)]


def world_points(rom: ndspy.rom.NintendoDSRom) -> dict[str, list[int]]:
    """Carte d'arrivée -> position (x, y) de sa zone cliquable sur la carte du monde."""
    data = bytes(rom.getFileByName("script/cf/worldmap.sb"))
    natives, functions, code = parse_script(data)
    strings = script_strings(data)
    points: dict[str, list[int]] = {}
    for _, name in functions:
        ops = disassemble(natives, functions, code, name)
        variables: dict[str, int] = {}
        stack: list = []
        for i, op in enumerate(ops):
            if op.startswith("push "):
                stack.append(int(op.split()[1]))
            elif op == "op20.03" and i + 2 < len(ops) and ops[i + 2] == "3d" and stack:
                variables[ops[i + 1]] = stack.pop()  # push N | op20.03 | <variable> | 3d
            elif op.startswith("op29.03"):
                stack.append(("var", ops[i + 1]))
            elif op.startswith("op26."):
                stack.append(("str", int(op[5:], 16)))
            elif op == "CALL SetClickPoint" and len(stack) >= 10:
                args = stack[-10:-1]
                value = [variables.get(a[1]) if isinstance(a, tuple) and a[0] == "var" else a for a in args]
                if isinstance(value[4], tuple) and value[4][0] == "str" and None not in value[1:3]:
                    points.setdefault(strings[value[4][1]], [value[1], value[2]])
                stack = []
            elif op.startswith("CALL"):
                stack = []
    return points


def capsule_icon(data: bytes) -> "Image.Image":
    """Icône d'une capsule (menu/capsule/NN.img, « dIMG ») : u16 0, u8 largeur et u8 hauteur en unités de 4 pixels,
    palette de 256 couleurs BGR555, puis l'image en 4 bits par pixel, ligne par ligne (48 × 48, couleurs 0 à 15). La
    couleur 0 (vert) est la transparence (decisions.md C60)."""
    from PIL import Image
    palette = []
    for i in range(16):
        colour = int.from_bytes(data[8 + 2 * i:10 + 2 * i], "little")
        palette.append(((colour & 31) * 255 // 31, (colour >> 5 & 31) * 255 // 31, (colour >> 10 & 31) * 255 // 31,
                        0 if i == 0 else 255))
    image = Image.new("RGBA", (48, 48))
    pixels = image.load()
    for i, byte in enumerate(data[520:520 + 48 * 48 // 2]):
        for k, value in enumerate((byte & 15, byte >> 4)):
            pixels[(2 * i + k) % 48, (2 * i + k) // 48] = palette[value]
    return image


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parents[2] / "build/tracker_assets"
    positions: dict[int, list] = {}
    for path in sorted(n for n in all_files(rom.filenames) if n.startswith("script/cf0/") and n.endswith(".sb")):
        natives, functions, code = parse_script(bytes(rom.getFileByName(path)))
        positions.update(chest_positions(natives, functions, code))
        map_code = path.rsplit("/", 1)[1].removesuffix(".sb")
        for flag, _, function, _ in examine_spots(natives, functions, code):
            where = event_position(natives, functions, code, function)
            if where:
                positions[flag] = [map_code, *where]
    positions.update(OBJECTS)
    (out / "maps").mkdir(parents=True, exist_ok=True)
    for map_code in sorted({place for place, _, _ in positions.values()}):
        try:
            render(rom, map_code).save(out / "maps" / f"{map_code}.png")
        except ValueError:  # écran sans fichier de carte (ex. skr06) : ses lieux n'auront pas de point sur une image
            print("pas d'image pour", map_code)
    render(rom, "worldmap").save(out / "maps" / "worldmap.png")
    (out / "icons").mkdir(exist_ok=True)
    for name in all_files(rom.filenames):
        if name.startswith("menu/capsule/") and name.endswith(".img"):
            capsule_icon(bytes(rom.getFileByName(name))).save(out / "icons" / f"capsule_{name[-6:-4]}.png")
    (out / "world.json").write_text(json.dumps(world_points(rom), indent=1, sort_keys=True) + "\n", encoding="utf-8")
    (out / "positions.json").write_text(json.dumps(positions, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    print(f"{len(positions)} positions, {len({p for p, _, _ in positions.values()})} écrans -> {out}")


if __name__ == "__main__":
    main()
