"""Extrait les listes « Items: » du guide DSR et les affiche en tableau Markdown.

Source : Darkstar Ripclaw, FAQ/Walkthrough v1.1, copie GameRevolution
https://www.gamerevolution.com/guides/45075-dragon-ball-z-attack-of-the-saiyans-faqwalkthrough

Le guide n'est pas dans le dépôt : le télécharger d'abord, puis
    curl -sL -A "Mozilla/5.0" "<url ci-dessus>" -o dsr.html
    python3 research/scripts/extract_dsr_items.py dsr.html > items.md
"""
from __future__ import annotations

import html
import re
import sys
from dataclasses import dataclass

CHAPTERS: dict[str, str] = {
    "PROL": "Prologue",
    **{f"CHP{n}": f"Ch. {n}" for n in range(1, 10)},
    **{f"CH{n}": f"Ch. {n}" for n in range(10, 16)},
    "ODEN": "Fin de jeu",
}
# Mots qui indiquent qu'une parenthèse est un emplacement (« (Second Screen) ») et non une partie du nom.
PLACE_WORDS = ("Screen", "Floor", "Area", "Side", "Room", "Cave", "Basement", "Entrance", "Level", "House", "Spaceship")
QUANTITY = re.compile(r"^x(\d+)$")


@dataclass
class Item:
    chapter: str
    zone: str
    place: str
    name: str
    quantity: int


def guide_text(path: str) -> str:
    raw = open(path, encoding="utf-8", errors="ignore").read()
    raw = re.sub(r"<br\s*/?>", "\n", raw)
    return html.unescape(re.sub(r"<[^>]+>", "", raw)).replace("\r", "")


def parse_block(block: str) -> list[tuple[str, str, int]]:
    """« A, B (x2) (First Screen) C (Second Screen) » -> [(place, name, quantity), ...]."""
    entries: list[tuple[str, str, int]] = []
    pending: list[list] = []  # [nom, quantité] en attente de leur emplacement
    pos = 0
    for match in re.finditer(r"\(([^)]*)\)", block):
        for name in block[pos:match.start()].split(","):
            if name.strip():
                pending.append([name.strip(), 1])
        pos = match.end()
        label = match.group(1).strip()
        quantity = QUANTITY.match(label)
        if quantity and pending:
            pending[-1][1] = int(quantity.group(1))
        elif any(word in label for word in PLACE_WORDS):
            entries += [(label, name, qty) for name, qty in pending]
            pending = []
        elif pending:
            pending[-1][0] += f" ({label})"
    for name in block[pos:].split(","):
        if name.strip():
            pending.append([name.strip(), 1])
    entries += [("", name, qty) for name, qty in pending]
    return entries


def extract(text: str) -> list[Item]:
    lines = text.split("\n")
    chapter = "?"
    items: list[Item] = []
    for i, line in enumerate(lines):
        marker = re.fullmatch(r"\s*\[([A-Z0-9]{4})\]\s*", line)
        if marker and marker.group(1) in CHAPTERS:
            chapter = CHAPTERS[marker.group(1)]
        if not line.strip().startswith("Items:"):
            continue
        zone = lines[i - 2].strip()  # titre, puis ligne de soulignement, puis « Items: »
        block = [line.strip().removeprefix("Items:")]
        j = i + 1
        while j < len(lines) and lines[j].strip():
            block.append(lines[j].strip())
            j += 1
        for place, name, quantity in parse_block(" ".join(block)):
            items.append(Item(chapter, zone, place, name, quantity))
    return items


def main() -> None:
    items = extract(guide_text(sys.argv[1]))
    print("| N° | Chapitre | Zone | Emplacement (DSR) | Objet (EN) | Qté | Nom FR | Source | Statut |")
    print("|---|---|---|---|---|---|---|---|---|")
    for number, item in enumerate(items, 1):
        print(f"| {number} | {item.chapter} | {item.zone} | {item.place} | {item.name} | {item.quantity} | "
              f"| DSR {item.chapter} (en-tête Items) | 📖 |")
    print(f"{len(items)} lignes, {sum(item.quantity for item in items)} objets", file=sys.stderr)


if __name__ == "__main__":
    main()
