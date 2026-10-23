"""Extrait les textes des tables BDAT de la ROM (une copie par langue dans btl/bdat/<LANG>/bdat.bin).

Usage (environnement de recherche, qui contient ndspy) :
    research/.venv/bin/python research/scripts/extract_rom_names.py "<chemin de la ROM .nds>"

Écrit research/extracted/rom_texts.json (toutes les lignes, toutes les langues, descriptions comprises ;
ignoré par Git) et affiche sur la sortie standard un tableau Markdown des noms (EN, US, FR) à copier dans
research/rom_names.md.

Format BDAT observé (2026-10-23, ROM EU BRPP rév. 0), en little-endian :
- fichier : u32 nombre de tables, u32 taille, puis u32 décalage de chaque table ;
- table : « BDAT », u16 drapeaux, u16 décalage du nom, u16 longueur d'une ligne, u16 décalage des lignes,
  u16 nombre de lignes ;
- tables de texte (*_mes, character_name) : chaque champ de 4 octets d'une ligne est le décalage d'une
  chaîne terminée par 0, compté depuis le début de la table. Les accents sont écrits « \\351 » (octal, Latin-1).
"""
from __future__ import annotations

import json
import re
import struct
import sys
from pathlib import Path

import ndspy.rom

LANGUAGES = ("EN", "US", "FR", "GR", "IT", "SP", "JP")
# Tables où chaque objet occupe 2 lignes : nom puis description.
NAME_DESCRIPTION_TABLES = ("use_item_mes", "btl_acc_mes", "pt_eqp_mes", "key_item_mes")
# Tables où les noms occupent la première moitié et les descriptions la seconde.
FIRST_HALF_TABLES = ("cf_mes_COMBO",)
# Tables d'un nom par ligne. cf_mes_QUEST (objectifs de l'histoire, phrases complètes) reste dans le JSON.
NAME_TABLES = ("cf_mes_LOC", "character_name")
# Tables où noms, descriptions et cris sont mélangés sans ordre régulier : on ne garde que les textes courts.
SHORT_TEXT_TABLES = ("btl_mes_BLAST",)
OUTPUT = Path(__file__).resolve().parent.parent / "extracted" / "rom_texts.json"


def decode(raw: bytes) -> str:
    text = raw.decode("latin-1")
    text = re.sub(r"\\([0-7]{3})", lambda match: chr(int(match.group(1), 8)), text)
    return text.replace("\xa0", " ")


def read_tables(data: bytes) -> dict[str, list[list[str | int]]]:
    """Retourne {nom de table: lignes}. Un champ qui n'est pas une chaîne valide reste un entier."""
    count = struct.unpack_from("<I", data, 0)[0]
    starts = list(struct.unpack_from(f"<{count}I", data, 8))
    ends = starts[1:] + [len(data)]
    tables: dict[str, list[list[str | int]]] = {}
    for start, end in zip(starts, ends):
        assert data[start:start + 4] == b"BDAT", hex(start)
        name_offset, row_length, rows_offset, row_count = struct.unpack_from("<4H", data, start + 6)
        name = data[start + name_offset:data.index(b"\0", start + name_offset)].decode("latin-1")
        rows: list[list[str | int]] = []
        for row in range(row_count):
            fields: list[str | int] = []
            for column in range(row_length // 4):
                value = struct.unpack_from("<I", data, start + rows_offset + row * row_length + column * 4)[0]
                is_string = rows_offset + row_count * row_length <= value < end - start
                fields.append(decode(data[start + value:data.index(b"\0", start + value)]) if is_string else value)
            rows.append(fields)
        tables[name] = rows
    return tables


def names(tables: dict[str, list[list[str | int]]], table: str) -> list[str]:
    rows = tables[table]
    if table in NAME_DESCRIPTION_TABLES:
        rows = rows[::2]
    elif table in FIRST_HALF_TABLES:
        rows = rows[:len(rows) // 2]
    texts = [next((field for field in row if isinstance(field, str)), "") for row in rows]
    if table in SHORT_TEXT_TABLES:
        texts = [text if len(text) <= 32 and "<n>" not in text and not text.endswith((".", "!")) else ""
                 for text in texts]
    return texts


def world_map_zones(script: bytes) -> list[tuple[str, str]]:
    """Zones de la carte du monde : dans worldmap.sb, chaque nom de zone précède son code de carte (« kam01_00 »)."""
    map_code = re.compile(r"[a-z]{3}\d\d_\d\d")
    strings = [raw.decode("latin-1") for raw in re.findall(rb"[\x20-\x7e\xa0-\xff]{3,}", script)]
    return [(code, previous) for previous, code in zip(strings, strings[1:])
            if map_code.fullmatch(code) and not map_code.fullmatch(previous) and not previous.startswith("Wobj")]


def main() -> None:
    rom = ndspy.rom.NintendoDSRom.fromFile(sys.argv[1])
    texts = {lang: read_tables(bytes(rom.getFileByName(f"btl/bdat/{lang}/bdat.bin"))) for lang in LANGUAGES}
    zones = {lang: world_map_zones(bytes(rom.getFileByName(f"script/{lang}/cf/worldmap.sb"))) for lang in ("EN", "US", "FR")}
    OUTPUT.write_text(json.dumps({"bdat": texts, "world_map": zones}, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"\n### Zones de la carte du monde (`script/<LANG>/cf/worldmap.sb`, {len(zones['EN'])} entrées)\n")
    print("| Code de carte | EN (EU) | US | FR |")
    print("|---|---|---|---|")
    for (code, name_en), (_, name_us), (_, name_fr) in zip(zones["EN"], zones["US"], zones["FR"]):
        print(f"| `{code}` | {name_en} | {'=' if name_us == name_en else name_us} | {name_fr} |")

    for table in NAME_DESCRIPTION_TABLES + FIRST_HALF_TABLES + NAME_TABLES + SHORT_TEXT_TABLES:
        en, us, fr = (names(texts[lang], table) for lang in ("EN", "US", "FR"))
        if table in SHORT_TEXT_TABLES:
            fr = [name_fr if name_en else "" for name_en, name_fr in zip(en, fr)]
        print(f"\n### `{table}` ({len(en)} entrées)\n")
        print("| Index | EN (EU) | US | FR |")
        print("|---|---|---|---|")
        for index, (name_en, name_us, name_fr) in enumerate(zip(en, us, fr)):
            if name_en or name_fr:
                print(f"| {index} | {name_en} | {'=' if name_us == name_en else name_us} | {name_fr} |")
    print(f"\nTextes complets : {OUTPUT}", file=sys.stderr)


if __name__ == "__main__":
    main()
