"""Extrait tous les coffres du jeu depuis les scripts de carte de la ROM (appels à la fonction CreateBox).

Usage (environnement de recherche, qui contient ndspy) :
    research/.venv/bin/python research/scripts/extract_chests.py "<chemin de la ROM .nds>"

Écrit research/extracted/chests.json (ignoré par Git) et affiche sur la sortie standard le tableau Markdown
des coffres à copier dans research/chests.md.

Format des scripts .sb observé (2026-10-24, ROM EU BRPP rév. 0), en little-endian sauf mention :
- en-tête : « SB  », u16, u16, puis 6 u32 = début des sections 0 à 5 ;
- section 0 : u32 taille de son en-tête, puis le code (machine à pile) ;
- section 3 : u32 8, u32 n, puis n couples (u32 décalage du nom depuis le début des couples, u32 position dans
  le code) = fonctions et étiquettes du script (ex. TreasureSet_tut01_00) ;
- section 4 : u32 8, u32 n, puis n couples (u16 décalage du nom, u16 module) = fonctions du jeu appelables ;
- instructions vues : 0x13 + 4 octets, 0x14 + 1 octet, 0x15 + 2 octets (gros-boutiste) = empiler une valeur ;
  0x16 à 0x1f = empiler -1 à 8 ; 0x4a + 1 octet = appeler la fonction du jeu n° x.
Un coffre = 8 valeurs empilées puis l'appel de CreateBox : (unité, ?, ?, x, y, objet, drapeau, 7).
Objet : code - 1 = 128 × catégorie + numéro interne (catégories : 0 objets, 1 accessoires, 2 capsules,
3 objets clés), comme l'ordre des tables d'inventaire en mémoire (ram_map.md §2).
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
CATEGORY_SIZE = 128


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
            items[CATEGORY_SIZE * category + index + 1] = {
                "category": category, "index": index, "text": text,
                **{lang: labels[lang][text] if text < len(labels[lang]) else "" for lang in labels}}
    return items


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    items = item_names(rom)
    chests: dict[int, dict[str, object]] = {}
    files: dict[int, set[str]] = defaultdict(set)
    for path, data in sorted((name, bytes(rom.getFileByName(name))) for name in all_files(rom.filenames)
                             if name.startswith(SCRIPT_FOLDERS) and name.endswith(".sb")):
        natives, functions, code = parse_script(data)
        if "CreateBox" not in natives:
            continue
        call = re.escape(bytes([0x4A, natives.index("CreateBox")]))
        for match in re.finditer(rb"((?:" + PUSH + rb"){8})" + call, code, re.S):
            unit, _, _, x, y, item, flag, _ = (push_value(i) for i in re.findall(PUSH, match.group(1), re.S))
            entry = {"flag": flag, "function": function_at(functions, match.start()), "x": x, "y": y,
                     "item_code": item, **items.get(item, {"EN": f"? code {item}"})}
            known = chests.setdefault(flag, entry)
            if (known["function"], known["item_code"], known["x"], known["y"]) != (entry["function"], item, x, y):
                print(f"Attention : drapeau {flag} différent dans {path}", file=sys.stderr)
            files[flag].add(path)
    for flag, entry in chests.items():
        entry["files"] = sorted(files[flag])
    OUTPUT.write_text(json.dumps(sorted(chests.values(), key=lambda e: e["flag"]), ensure_ascii=False, indent=1),
                      encoding="utf-8")

    print(f"| Drapeau | Carte | Objet EN (EU) | Objet FR | Catégorie, n° interne | x, y |")
    print("|---|---|---|---|---|---|")
    for entry in sorted(chests.values(), key=lambda e: (e["function"], e["flag"])):
        carte = str(entry["function"]).removeprefix("TreasureSet_")
        print(f"| {entry['flag']} | `{carte}` | {entry['EN']} | {entry.get('FR', '')} | "
              f"{entry.get('category', '?')}, {entry.get('index', '?')} | {entry['x']}, {entry['y']} |")
    print(f"\n{len(chests)} coffres. Détail : {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
