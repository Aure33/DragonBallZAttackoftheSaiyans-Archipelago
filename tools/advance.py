"""Fait défiler une scène (A en boucle) jusqu'au retour sur le terrain (jauge de Ki visible). En combat, A attaque.
L'octet de combat 0x09B236 vaut aussi FF FF pendant certaines scènes : il ne sert pas ici.

    python3 tools/advance.py [appuis max]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from battle import on_field, screenshot, send, values  # noqa: E402

limit = int(sys.argv[1]) if len(sys.argv) > 1 else 60
for press in range(limit):
    found = values(send(["press A 3", "wait 40", "read 0D226C 8"]))
    if press % 3 == 2 and on_field(screenshot()):
        print(f"terrain après {press + 1} appuis, carte", bytes.fromhex(found[0].replace(" ", "")).decode(errors="replace"))
        break
else:
    print(f"{limit} appuis sans retour au terrain")
