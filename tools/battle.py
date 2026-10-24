"""Combats pilotés par la télécommande BizHawk (remote.lua doit tourner).

    python3 tools/battle.py walk            marcher (haut/bas) jusqu'à un combat aléatoire
    python3 tools/battle.py fight [tours]   attaquer (A) jusqu'au retour sur le terrain ; répartit les points si le
                                            jeu attend une montée de niveau
    python3 tools/battle.py defend [tours]  se défendre jusqu'à la fin du combat (défaite pour DeathLink)
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "research/scripts"))
from remote import REMOTE_DIR, send  # noqa: E402
from PIL import Image  # noqa: E402

BATTLE_STATE = "09B236"  # FF FF en combat (pas toujours fiable, voir research/decisions.md C30)
LEVEL_UP = ["press Right 3", "wait 15", "press Right 3", "wait 15", "press A 3", "wait 30", "press Up 3", "wait 10",
            "press A 3", "wait 60"]


def values(reply: str) -> list[str]:
    return [line.split(": ", 1)[1] for line in reply.splitlines() if line.startswith("read ")]


def on_field(image: Image.Image) -> bool:
    """La jauge de Ki du terrain : boule orange à gauche et extrémité rouge, en bas ou en haut de l'écran du haut."""
    return any(image.getpixel((12, y)) == (251, 121, 8) and image.getpixel((135, y)) == (186, 0, 0) for y in (184, 12))


def screenshot() -> Image.Image:
    send(["shot battle"])
    return Image.open(REMOTE_DIR / "battle.png").convert("RGB")


def walk(steps: int = 80) -> bool:
    for step in range(steps):
        if values(send([f"press {'Up' if step % 2 else 'Down'} 40", f"read {BATTLE_STATE} 2"]))[0] == "FF FF":
            send(["wait 150"])
            print(f"combat après {step + 1} pas")
            return True
    print("pas de combat")
    return False


def fight(turns: int = 80) -> bool:
    last = None
    for turn in range(turns):
        send(["press A 3", "wait 40"])
        image = screenshot()
        if on_field(image):
            send(["wait 30"])
            if on_field(screenshot()):
                print(f"terrain après {turn + 1} tours")
                return True
        digest = hashlib.md5(image.tobytes()).hexdigest()
        if digest == last:
            send(LEVEL_UP)
        last = digest
    print("toujours pas sur le terrain")
    return False


def defend(turns: int = 30) -> None:
    for turn in range(turns):
        send(["press Down 3", "wait 10", "press A 3", "wait 120"])
        if on_field(screenshot()):
            print(f"terrain après {turn + 1} tours")
            return
    print(f"{turns} tours joués")


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else ""
    count = [int(sys.argv[2])] if len(sys.argv) > 2 else []
    {"walk": walk, "fight": fight, "defend": defend}.get(action, lambda *_: print(__doc__))(*count)
