"""Extrait les coffres et les objets à examiner du jeu depuis les scripts de la ROM.

Usage (environnement de recherche, qui contient ndspy) :
    research/.venv/bin/python research/scripts/extract_chests.py "<chemin de la ROM .nds>"

Écrit research/extracted/chests.json (ignoré par Git), lu par build_world_data.py, et affiche le nombre de lieux.

Format des scripts .sb observé (2026-10-24, ROM EU BRPP rév. 0), en little-endian sauf mention :
- en-tête : « SB  », u16, u16, puis 6 u32 = début des sections 0 à 5 ;
- section 0 : u32 taille de son en-tête, puis le code (machine à pile) ;
- section 3 : u32 8, u32 n, puis n couples (u32 décalage du nom depuis le début des couples, u32 position dans
  le code) = fonctions et étiquettes du script (ex. TreasureSet_tut01_00) ;
- section 4 : u32 8, u32 n, puis n couples (u16 décalage du nom, u16 module) = fonctions du jeu appelables ;
- instructions vues : 0x13 + 4 octets, 0x14 + 1 octet, 0x15 + 2 octets (gros-boutiste) = empiler une valeur ;
  0x16 à 0x1f = empiler -1 à 8 ; 0x4a + 1 octet = appeler la fonction du jeu n° x.
Un coffre = 8 valeurs empilées puis l'appel de CreateBox : (unité, ?, ?, x, y, objet, drapeau, 7).
Objet à examiner (tiroir, étal, porte…) = dans une fonction du script : GetFlag(drapeau, 1), puis
GetItem(objet, quantité, 2) et SetFlag(drapeau, 1, 2), avec un seul drapeau. Les dons à plusieurs drapeaux
(échanges, captures) et les objets clés d'histoire (scènes cf1, sans drapeau propre) ne sont pas relevés ici.
Objet : code - 1 = position dans l'inventaire en mémoire (ram_map.md §2) : objets à +0x000, accessoires à +0x080,
capsules à +0x100, objets clés à +0x130.
Les fichiers de cf2/_kz (cartes de test, contenus parfois différents) sont ignorés.
"""
from __future__ import annotations

import json
import re
import struct
import sys
from collections import defaultdict
from pathlib import Path

import ndspy.fnt
import ndspy.rom

from extract_rom_names import names, read_tables

OUTPUT = Path(__file__).resolve().parent.parent / "extracted" / "chests.json"
SCRIPT_FOLDERS = ("script/cf0/", "script/cf1/")
PUSH = rb"(?:\x13....|\x14.|\x15..|[\x16-\x1f])"
CATEGORIES = (("Use_Item", "use_item_mes"), ("Btl_Acc", "btl_acc_mes"),
              ("Pt_Eqp", "pt_eqp_mes"), ("Key_Item", "key_item_mes"))
INVENTORY_OFFSETS = (0x000, 0x080, 0x100, 0x130)


def all_files(folder: ndspy.fnt.Folder, prefix: str = "") -> list[str]:
    paths = [prefix + name for name in folder.files]
    for name, subfolder in folder.folders:
        paths += all_files(subfolder, prefix + name + "/")
    return paths


def c_string(data: bytes, offset: int) -> str:
    return data[offset:data.index(b"\0", offset)].decode("latin-1")


def parse_script(data: bytes) -> tuple[list[str], list[tuple[int, str]], bytes]:
    """Retourne (fonctions du jeu appelables, fonctions du script triées par position, code)."""
    sections = struct.unpack_from("<6I", data, 8)
    count = struct.unpack_from("<I", data, sections[4] + 4)[0]
    base = sections[4] + 8 + 4 * count
    natives = [c_string(data, base + struct.unpack_from("<H", data, sections[4] + 8 + 4 * i)[0]) for i in range(count)]
    count = struct.unpack_from("<I", data, sections[3] + 4)[0]
    pairs = [struct.unpack_from("<II", data, sections[3] + 8 + 8 * i) for i in range(count)]
    functions = sorted((position, c_string(data, sections[3] + 8 + name)) for name, position in pairs)
    code = data[sections[0] + struct.unpack_from("<I", data, sections[0])[0]:sections[1]]
    return natives, functions, code


def push_value(instruction: bytes) -> int:
    opcode = instruction[0]
    if opcode == 0x13:
        return struct.unpack(">i", instruction[1:5])[0]
    if opcode == 0x14:
        return struct.unpack("b", instruction[1:2])[0]
    if opcode == 0x15:
        return struct.unpack(">h", instruction[1:3])[0]
    return opcode - 0x17


def function_at(functions: list[tuple[int, str]], position: int) -> str:
    return max((entry for entry in functions if entry[0] <= position), default=(0, ""))[1]


def item_names(rom: ndspy.rom.NintendoDSRom) -> dict[int, dict[str, str | int]]:
    """{code d'objet des coffres: catégorie, numéro interne, noms EN/US/FR}."""
    data = read_tables(bytes(rom.getFileByName("btl/bdat/EN/bdat.bin")))
    texts = {lang: read_tables(bytes(rom.getFileByName(f"btl/bdat/{lang}/bdat.bin"))) for lang in ("EN", "US", "FR")}
    items: dict[int, dict[str, str | int]] = {}
    for category, (data_table, text_table) in enumerate(CATEGORIES):
        labels = {lang: names(texts[lang], text_table) for lang in texts}
        for index, row in enumerate(data[data_table]):
            text = ((row[0] & 0xFFFF) - 1) // 2
            items[INVENTORY_OFFSETS[category] + index + 1] = {
                "category": category, "index": index, "text": text,
                **{lang: labels[lang][text] if text < len(labels[lang]) else "" for lang in labels}}
    return items


def examine_spots(natives: list[str], functions: list[tuple[int, str]], code: bytes) -> list[tuple[int, int, str]]:
    """(drapeau, code d'objet, fonction) des objets à examiner d'un script."""
    if not {"GetItem", "GetFlag", "SetFlag"} <= set(natives):
        return []
    get_item, get_flag, set_flag = (natives.index(name) for name in ("GetItem", "GetFlag", "SetFlag"))
    spots = []
    for match in re.finditer(rb"(" + PUSH + rb")(" + PUSH + rb")\x19" + re.escape(bytes([0x4A, get_item])), code, re.S):
        start = function_at_start(functions, match.start())
        end = min([position for position, _ in functions if position > match.start()] + [len(code)])
        body = code[start:end]
        set_flags = {push_value(m.group(1))
                     for m in re.finditer(rb"(\x15..)\x18\x19" + re.escape(bytes([0x4A, set_flag])), body, re.S)}
        get_flags = {push_value(m.group(1))
                     for m in re.finditer(rb"(\x15..)\x18" + re.escape(bytes([0x4A, get_flag])), body, re.S)}
        if len(set_flags) == 1 and set_flags == get_flags:
            spots.append((set_flags.pop(), push_value(match.group(1)), function_at(functions, match.start())))
    return spots


def function_at_start(functions: list[tuple[int, str]], position: int) -> int:
    return max((entry for entry in functions if entry[0] <= position), default=(0, ""))[0]


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    items = item_names(rom)
    locations: dict[int, dict[str, object]] = {}
    files: dict[int, set[str]] = defaultdict(set)
    for path, data in sorted((name, bytes(rom.getFileByName(name))) for name in all_files(rom.filenames)
                             if name.startswith(SCRIPT_FOLDERS) and name.endswith(".sb")):
        natives, functions, code = parse_script(data)
        found = []
        if "CreateBox" in natives:
            call = re.escape(bytes([0x4A, natives.index("CreateBox")]))
            for match in re.finditer(rb"((?:" + PUSH + rb"){8})" + call, code, re.S):
                unit, _, _, x, y, item, flag, _ = (push_value(i) for i in re.findall(PUSH, match.group(1), re.S))
                found.append({"kind": "chest", "flag": flag, "item_code": item,
                              "map": function_at(functions, match.start()).removeprefix("TreasureSet_")})
        map_code = path.rsplit("/", 1)[1].removesuffix(".sb")
        for flag, item, function in examine_spots(natives, functions, code):
            found.append({"kind": "examine", "flag": flag, "item_code": item, "map": map_code, "function": function})
        for entry in found:
            entry.update(items.get(entry["item_code"], {"EN": f"? code {entry['item_code']}"}))
            known = locations.setdefault(entry["flag"], entry)
            if (known["kind"], known["map"], known["item_code"]) != (entry["kind"], entry["map"], entry["item_code"]):
                print(f"Attention : drapeau {entry['flag']} différent dans {path}", file=sys.stderr)
            files[entry["flag"]].add(path)
    for flag, entry in locations.items():
        entry["files"] = sorted(files[flag])
    OUTPUT.write_text(json.dumps(sorted(locations.values(), key=lambda e: e["flag"]), ensure_ascii=False, indent=1),
                      encoding="utf-8")
    kinds = defaultdict(int)
    for entry in locations.values():
        kinds[entry["kind"]] += 1
    print(f"{dict(kinds)} -> {OUTPUT}")


if __name__ == "__main__":
    main()
