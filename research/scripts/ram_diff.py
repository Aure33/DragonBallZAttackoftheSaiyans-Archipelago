"""Compare des photos de la mémoire (« Main RAM ») prises avec dump_ram.lua.

Offsets affichés : offset dans le domaine Main RAM, et adresse DS (0x02000000 + offset).

Exemples (dossier des photos côté Windows) :
    D=/mnt/c/Users/Aurelien/Desktop/archipelago/dbz_research/dumps
    python3 research/scripts/ram_diff.py list $D
    python3 research/scripts/ram_diff.py find $D/01_test.bin "DB KAI RPG"
    python3 research/scripts/ram_diff.py find $D/01_test.bin 4253 --hex
    # Drapeaux : bits passés de 0 à 1 entre photo[i] et photo[i+1] et stables partout ailleurs
    python3 research/scripts/ram_diff.py flags $D/02_avant.bin $D/03_apres1.bin $D/04_apres2.bin
    # Octets changés entre A et B, sauf ceux qui changent aussi entre les photos de bruit
    python3 research/scripts/ram_diff.py diff $D/02_avant.bin $D/03_apres1.bin --noise $D/03_apres1.bin $D/03b_rien.bin
    # Valeur d'une adresse sur plusieurs photos
    python3 research/scripts/ram_diff.py value 0x1A2B3C 2 $D/*.bin
"""
from __future__ import annotations

import argparse
from pathlib import Path

DS_BASE = 0x02000000


def load(path: str) -> bytes:
    return Path(path).read_bytes()


def where(offset: int) -> str:
    return f"0x{offset:06X} (DS 0x{DS_BASE + offset:08X})"


def cmd_list(args: argparse.Namespace) -> None:
    index = Path(args.folder) / "index.txt"
    for line in index.read_text(encoding="latin-1").splitlines():
        number, label, frame, size = line.split(";")
        print(f"{number}  {label:30s} image {frame:>8s}  {size} octets")


def cmd_find(args: argparse.Namespace) -> None:
    data = load(args.dump)
    pattern = bytes.fromhex(args.pattern) if args.hex else args.pattern.encode("latin-1")
    start, hits = 0, 0
    while (position := data.find(pattern, start)) != -1 and hits < 50:
        print(where(position))
        start, hits = position + 1, hits + 1
    if hits == 0:
        print("Introuvable.")


def cmd_flags(args: argparse.Namespace) -> None:
    dumps = [load(path) for path in args.dumps]
    for step in range(len(dumps) - 1):
        found = []
        for offset in range(min(len(d) for d in dumps)):
            before, after = dumps[step][offset], dumps[step + 1][offset]
            raised = ~before & after & 0xFF
            if not raised:
                continue
            for bit in range(8):
                mask = 1 << bit
                if not raised & mask:
                    continue
                # Le bit doit valoir 0 sur toutes les photos d'avant et 1 sur toutes celles d'après.
                if all(not d[offset] & mask for d in dumps[:step + 1]) and all(d[offset] & mask for d in dumps[step + 1:]):
                    found.append((offset, bit))
        print(f"\n{Path(args.dumps[step]).name} -> {Path(args.dumps[step + 1]).name} : {len(found)} bit(s)")
        for offset, bit in found[:args.limit]:
            print(f"  {where(offset)} bit {bit}  (octet 0x{dumps[step][offset]:02X} -> 0x{dumps[step + 1][offset]:02X})")


def cmd_diff(args: argparse.Namespace) -> None:
    a, b = load(args.a), load(args.b)
    noise: set[int] = set()
    for first, second in zip(args.noise[::2], args.noise[1::2]):
        x, y = load(first), load(second)
        noise |= {offset for offset in range(min(len(x), len(y))) if x[offset] != y[offset]}
    changed = [offset for offset in range(min(len(a), len(b))) if a[offset] != b[offset] and offset not in noise]
    print(f"{len(changed)} octet(s) changé(s) hors bruit")
    for offset in changed[:args.limit]:
        print(f"  {where(offset)}  0x{a[offset]:02X} -> 0x{b[offset]:02X}")


def cmd_value(args: argparse.Namespace) -> None:
    offset = int(args.offset, 0)
    for path in args.dumps:
        raw = load(path)[offset:offset + args.size]
        print(f"{Path(path).name:35s} {raw.hex(' ')}  = {int.from_bytes(raw, 'little')}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(required=True)
    p = sub.add_parser("list", help="lister les photos d'un dossier")
    p.add_argument("folder")
    p.set_defaults(func=cmd_list)
    p = sub.add_parser("find", help="chercher un texte ou des octets")
    p.add_argument("dump")
    p.add_argument("pattern")
    p.add_argument("--hex", action="store_true", help="motif en hexadécimal")
    p.set_defaults(func=cmd_find)
    p = sub.add_parser("flags", help="bits 0 -> 1 stables, entre photos successives")
    p.add_argument("dumps", nargs="+")
    p.add_argument("--limit", type=int, default=40)
    p.set_defaults(func=cmd_flags)
    p = sub.add_parser("diff", help="octets changés entre deux photos, hors bruit")
    p.add_argument("a")
    p.add_argument("b")
    p.add_argument("--noise", nargs="*", default=[], help="paires de photos où rien n'a été fait")
    p.add_argument("--limit", type=int, default=60)
    p.set_defaults(func=cmd_diff)
    p = sub.add_parser("value", help="valeur d'une adresse sur plusieurs photos")
    p.add_argument("offset")
    p.add_argument("size", type=int)
    p.add_argument("dumps", nargs="+")
    p.set_defaults(func=cmd_value)
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
