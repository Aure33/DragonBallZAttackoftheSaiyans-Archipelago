"""Raccourcis de test par la télécommande BizHawk : téléportation, saut de scène, histoire avancée à la main.
À n'utiliser que sur les états de sauvegarde de Claude (7, 8, 9) : la partie du joueur n'est jamais modifiée.

    python3 tools/warp.py map <carte> [x y]   aller sur une carte (ex. hii03_00 532 170) ; sans x y : (128, 128)
    python3 tools/warp.py scene <scène>       jouer une scène d'histoire (ex. c0602_00) : le jeu la joue lui-même
    python3 tools/warp.py story <drapeau>     allumer tous les drapeaux d'histoire de 0 à <drapeau> (inclus) et
                                              éteindre les suivants jusqu'à 1199 (le jeu prend le plus haut allumé)
    python3 tools/warp.py where               carte courante et plus haut drapeau d'histoire

Fonctionnement (research/decisions.md, C39) : la fonction MapJump du jeu écrit la destination (nom sur 8 octets,
x, y en 16 bits, direction) à 0x09F7B4, puis lève une demande de changement à 0x0D1D28 (01 00 00 01). Une scène
cXXYY_ZZ se rejoint comme une carte.
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research/scripts"))
from remote import send  # noqa: E402

DESTINATION = 0x09F7B4
JUMP_REQUEST = 0x0D1D28
FLAGS = 0x09F7E8
STORY_FLAG_COUNT = 1200  # GetMaxFlag(0, 1199) dans les scripts


def hexbytes(data: bytes) -> str:
    return " ".join(f"{b:02X}" for b in data)


def jump(name: str, x: int = 128, y: int = 128) -> None:
    target = name.encode().ljust(8, b"\0")[:8] + x.to_bytes(2, "little") + y.to_bytes(2, "little") + bytes(2)
    print(send([f"write {DESTINATION:06X} {hexbytes(target)}", f"write {JUMP_REQUEST:06X} 01 00 00 01", "wait 200"]))


def story(last: int) -> None:
    bits = bytearray(STORY_FLAG_COUNT // 8)
    for flag in range(last + 1):
        bits[flag // 8] |= 1 << (flag % 8)
    print(send([f"write {FLAGS:06X} {hexbytes(bytes(bits))}"]))


def where() -> None:
    reply = send([f"read {DESTINATION:06X} 8", f"read {FLAGS:06X} {STORY_FLAG_COUNT // 8}"])
    lines = [line.split(": ", 1)[1] for line in reply.splitlines() if line.startswith("read ")]
    flags = bytes.fromhex(lines[1].replace(" ", ""))
    highest = max((i * 8 + b for i, v in enumerate(flags) for b in range(8) if v >> b & 1), default=-1)
    print("carte", bytes.fromhex(lines[0].replace(" ", "")).decode(errors="replace"), "| histoire", highest)


if __name__ == "__main__":
    action, args = (sys.argv[1] if len(sys.argv) > 1 else ""), sys.argv[2:]
    if action == "map":
        jump(args[0], *(int(v) for v in args[1:3]))
    elif action == "scene":
        jump(args[0])
    elif action == "story":
        story(int(args[0]))
    elif action == "where":
        where()
    else:
        print(__doc__)
