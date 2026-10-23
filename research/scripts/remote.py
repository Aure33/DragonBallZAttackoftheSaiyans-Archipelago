"""Envoie des ordres à la télécommande BizHawk (remote.lua) et affiche le compte rendu.

Exemples :
    python3 research/scripts/remote.py "load 2" "wait 30" "shot ecran"
    python3 research/scripts/remote.py "press A 5" "wait 60" "dump apres_A"
Les captures arrivent dans REMOTE_DIR/<nom>.png, les photos mémoire dans DUMP_DIR/<nom>.bin.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

REMOTE_DIR = Path("/mnt/c/Users/Aurelien/Desktop/archipelago/dbz_research/remote")
TIMEOUT_S = 180


def send(orders: list[str]) -> str:
    REMOTE_DIR.mkdir(parents=True, exist_ok=True)
    command_id = str(time.time_ns())
    temporary = REMOTE_DIR / "cmd.tmp"
    temporary.write_text("id " + command_id + "\n" + "\n".join(orders) + "\n", encoding="utf-8")
    temporary.replace(REMOTE_DIR / "cmd.txt")
    done = REMOTE_DIR / "done.txt"
    deadline = time.monotonic() + TIMEOUT_S
    while time.monotonic() < deadline:
        if done.exists():
            text = done.read_text(encoding="utf-8", errors="replace")
            if text.startswith("id " + command_id + "\n"):
                (REMOTE_DIR / "cmd.txt").unlink(missing_ok=True)
                return text.split("\n", 1)[1]
        time.sleep(0.2)
    raise TimeoutError("Pas de réponse de BizHawk : le script remote.lua tourne-t-il, émulation non en pause ?")


if __name__ == "__main__":
    print(send(sys.argv[1:]), end="")
