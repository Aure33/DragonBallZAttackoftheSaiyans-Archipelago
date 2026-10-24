"""Décode les cartes de terrain (fld/map/<zone>/<carte>.map) en images, depuis la ROM.

    research/.venv/bin/python research/scripts/fieldmap.py <ROM> <carte> [<carte>...] [--out <dossier>]

Format observé (2026-10-24, ROM EU BRPP rév. 0, code ARM de la fonction 0x02043D04 qui charge la carte à 0x02360000) :
- en-tête de 16 octets : « dMAP », u16 0, u8 largeur et u8 hauteur en carreaux de 8 pixels, u32 position (dans le
  fichier) du calque 2, u32 taille d'une section d'enregistrements qui suit l'en-tête ;
- puis la palette (256 couleurs BGR555), puis le calque 1 compressé ; le calque 2 compressé à la position indiquée.
- Décompression : fonction 0x0200A6C0 (destination, source, largeur, hauteur en pixels), réécrite ici. Image en
  8 bits par pixel, ligne par ligne. Les tables de décalages viennent de l'ARM9 (0x0209B14C, 0x0209B16C, 0x0209B18C,
  0x0209B196).
Les images restent hors du dépôt (ce sont des extraits de la ROM).
"""
from __future__ import annotations

import sys
from pathlib import Path

import ndspy.rom
from PIL import Image

NEAR = 0x0209B14C  # 32 décalages courts (octets signés)
COLUMN = 0x0209B16C  # 32 décalages horizontaux
ROW = 0x0209B18C  # 8 décalages verticaux (multipliés par la largeur)
SWAPS = 0x0209B196  # 14 échanges dans la table


def signed(byte: int) -> int:
    return byte - 256 if byte >= 128 else byte


def offset_table(arm9: bytes, base: int, width: int) -> list[int]:
    at = lambda address, n: arm9[address - base:address - base + n]  # noqa: E731
    table = [signed(b) for b in at(NEAR, 32)]
    column, row = at(COLUMN, 32), at(ROW, 8)
    table += [signed(column[i & 31]) + signed(row[i >> 5]) * width for i in range(32, 256)]
    for i, other in enumerate(at(SWAPS, 14), start=2):
        table[i], table[other] = table[other], table[i]
    return table


def decompress(data: bytes, start: int, width: int, height: int, table: list[int]) -> bytearray:
    out = bytearray()
    end = width * height
    src = start
    out.append(data[src]); src += 1
    while len(out) < end:
        code = data[src]; src += 1
        if code < 0x10:  # code + 1 octets tels quels
            out += data[src:src + code + 1]; src += code + 1
        elif code == 0x10:  # répéter le dernier octet n + 3 fois
            out += bytes([out[-1]]) * (data[src] + 3); src += 1
        elif code < 0x20:
            continue
        else:
            if code < 0x80:
                distance, length, literals = table[code & 0xF], (code >> 4) + 1, 0
            else:
                distance, length, literals = table[data[src]], (code & 0xF) + 3, (code >> 4) & 7
                src += 1
            for _ in range(length):
                out.append(out[len(out) + distance])
            out += data[src:src + literals]; src += literals
    return out[:end]


def render(rom: ndspy.rom.NintendoDSRom, name: str) -> Image.Image:
    try:
        data = bytes(rom.getFileByName(f"fld/map/{name[:3]}/{name}.map"))
    except ValueError:  # une variante d'écran (ex. bud03_01) sans fichier propre reprend l'image de l'écran _00
        data = bytes(rom.getFileByName(f"fld/map/{name[:3]}/{name[:6]}00.map"))
    assert data[:4] == b"dMAP", name
    width, height = data[6] * 8, data[7] * 8
    records = int.from_bytes(data[12:16], "little")
    palette_at = 0x10 + records
    palette: list[int] = []
    for i in range(256):
        colour = int.from_bytes(data[palette_at + 2 * i:palette_at + 2 * i + 2], "little")
        palette += [(colour & 31) * 255 // 31, (colour >> 5 & 31) * 255 // 31, (colour >> 10 & 31) * 255 // 31]
    table = offset_table(rom.arm9, rom.arm9RamAddress, width)
    image = Image.frombytes("P", (width, height), bytes(decompress(data, palette_at + 0x200, width, height, table)))
    image.putpalette(palette)
    # Le calque 2 n'est pas un décor (formes grises : ombres ou priorité d'affichage) : il n'est pas dessiné.
    result = image.convert("RGB")
    return result


if __name__ == "__main__":
    args = sys.argv[1:]
    out = Path(args[args.index("--out") + 1]) if "--out" in args else Path(".")
    names = [a for a in args[1:] if a != "--out" and a != str(out)]
    rom = ndspy.rom.NintendoDSRom.fromFile(args[0])
    out.mkdir(parents=True, exist_ok=True)
    for name in names:
        render(rom, name).save(out / f"{name}.png")
        print(name, "ok")
