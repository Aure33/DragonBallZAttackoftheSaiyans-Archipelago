"""Construit les données des lieux du world à partir de la ROM (coffres, objets à examiner) et du guide DSR.

Usage (après extract_chests.py, qui écrit research/extracted/chests.json) :
    python3 research/scripts/build_world_data.py

Écrit :
- research/chests.md : tous les lieux trouvés dans la ROM, avec le chapitre, la source et ceux mis de côté ;
- worlds/dbz_aots/location_data.py : les lieux retenus pour le world (fichier généré, ne pas modifier à la main).

Règle d'association : un lieu de la ROM (carte → zone) est relié à la ligne du guide DSR
(research/game_data.md, « Tous les objets ramassables ») de la même zone et du même objet. Le chapitre du coffre
est celui de cette ligne : c'est le moment où l'auteur du guide l'a réellement ouvert, donc une condition
suffisante (histoire + niveau de Ki Blast de ce moment-là). « Fin de jeu » = chapitre 15, avant le combat final.
Un lieu sans ligne DSR est mis de côté (pas de lieu Archipelago) jusqu'à vérification.
"""
from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
CHESTS_JSON = ROOT / "research" / "extracted" / "chests.json"
GAME_DATA = ROOT / "research" / "game_data.md"
CHESTS_MD = ROOT / "research" / "chests.md"
WORLD_DATA = ROOT / "worlds" / "dbz_aots" / "location_data.py"

# Préfixe de carte → (nom de zone du world (EN, ROM EU), zones correspondantes dans le guide DSR).
ZONES: dict[str, tuple[str, tuple[str, ...]]] = {
    "tut": ("Training Island", ("Training Island",)),
    "bam": ("Bamboo Forest", ("Bamboo Forest",)),
    "pao": ("Mt. Paozu", ("Mt. Paozu", "East Mt. Paozu")),
    "krd": ("Divine Crossing", ("Divine Crossing",)),
    "gog": ("Mt. Five Element", ("Mount Five Element",)),
    "kiu": ("Kiwi Volcano", ("Kiwi Volcano",)),
    "fur": ("Mt. Frappe", ("Mt. Frappe",)),
    "spi": ("Spinach Wastes", ("Spinach Wastes",)),
    "kou": ("Break Wasteland", ("Break Wasteland",)),
    "wst": ("West City", ("West City",)),
    "jin": ("Jingle Village", ("Jingle Village",)),
    "hii": ("Holly Plain", ("Holly Plain",)),
    "skr": ("Sacred Land of Korin", ("Sacred Land of Korin",)),
    "sen": ("Hermit Spring", ("Hermit Spring",)),
    "enm": ("King Yemma's Mansion", ("King Yemma's Mansion",)),
    "sna": ("Princess Snake's House", ("Princess Snake's Mansion",)),
    "kos": ("King Kai's Planet", ("King Kai's Planet",)),
    "for": ("Yemma Forest", ("Yemma Forest",)),
    "kai": ("Pirate Cave", ("Pirate Cave",)),
    "snd": ("Desert", ("Desert",)),
    "mas": ("Muscle Tower", ("Muscle Tower",)),
    "yun": ("Yunzabit Heights", ("Yunzabit Heights",)),
    "ben": ("Devil's Toilet", ("Devil's Toilet",)),
    "pir": ("Pilaf's Castle", ("Pilaf Castle",)),
    "nem": ("Nemuria Ruins", ("Nemuria Ruins",)),
    "mut": ("Mutaito Training Grounds", ("Mutaito's Grounds",)),
    "nap": ("Paprika Wasteland", ("Paprika Wasteland",)),
    "las": ("Gizard Wasteland", ("Gizard Wasteland",)),
    "est": ("East City", ("East City",)),
    "ges": ("Sewer", ()),
    "kam": ("Kame House", ("Kame House",)),
    "bud": ("Martial Arts Temple", ("Martial Arts Temple",)),
    "ura": ("Baba's Palace", ("Baba's Palace",)),
    "gok": ("Goku's House", ("East Mt. Paozu",)),
    "kar": ("Korin Tower", ("Korin Tower",)),
    "hel": ("Underworld", ("Underworld",)),
}
# East City est détruite au chapitre 10 : ses écrans 7 à 9 sont les Ruines, qui n'ouvrent qu'avec les Dragon Balls.
EAST_CITY_RUINS = ("East City Ruins", ("East City Ruins",))
BONUS_ZONES = {"East City Ruins"}  # 7 Dragon Balls + vœu « To Go Somewhere New » (DSR Odds-and-Ends)
# Coffres connus sans ligne DSR (l'en-tête « Items » du prologue les oublie ; vus en jeu le 2026-10-23).
KNOWN_WITHOUT_DSR = {1583: "Prologue", 1584: "Prologue"}
# Fautes ou variantes d'écriture du guide.
DSR_SPELLING = {"recovery capsule": "recover capsule", "invigoration": "invigorate", "judgement": "judgment",
                "ninja boots": "ninja sandals", "max bean": "max bean"}


def normalize(name: str) -> str:
    name = name.lower()
    for wrong, right in DSR_SPELLING.items():
        name = name.replace(wrong, right)
    return re.sub(r"[^a-z0-9]", "", name)


def dsr_rows() -> list[dict[str, str | int]]:
    rows = []
    for line in GAME_DATA.read_text(encoding="utf-8").splitlines():
        if re.match(r"^\| \d+ \| ", line):
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            rows.append({"n": int(cells[0]), "chapter": cells[1], "zone": cells[2], "where": cells[3],
                         "item": cells[4], "qty": int(cells[5]) if cells[5].isdigit() else 1})
    return rows


def chapter_number(label: str) -> int:
    if label == "Prologue":
        return 0
    if label == "Fin de jeu":
        return 15
    return int(label.removeprefix("Ch. "))


def match(chests: list[dict], rows: list[dict]) -> dict[int, dict | None]:
    left = {row["n"]: row["qty"] for row in rows}
    found: dict[int, dict | None] = {}
    for chest in sorted(chests, key=lambda c: c["flag"]):
        zones = zone_of(chest["map"])[1]
        candidates = [row for row in rows if row["zone"] in zones and left[row["n"]] > 0]
        exact = [row for row in candidates if normalize(row["item"]) == normalize(chest["EN"])]
        # Le guide colle parfois deux objets (« Large Beam Ki Drink Z ») ou abrège (« HP Capsule », « Bushido »).
        loose = [row for row in candidates
                 if normalize(chest["EN"]) in normalize(row["item"]) or normalize(row["item"]) in normalize(chest["EN"])]
        row = (exact or loose or [None])[0]
        if row is not None:
            left[row["n"]] -= 1
        found[chest["flag"]] = row
    return found


def zone_of(map_code: str) -> tuple[str, tuple[str, ...]]:
    if map_code[:3] == "est" and int(map_code[3:5]) >= 7:
        return EAST_CITY_RUINS
    return ZONES[map_code[:3]]


def screen(map_code: str) -> str:
    number, variant = int(map_code[3:5]), int(map_code[6:8])
    return f"{number}-{variant}" if variant else str(number)


def main() -> None:
    chests = json.loads(CHESTS_JSON.read_text(encoding="utf-8"))
    rows = dsr_rows()
    matches = match(chests, rows)
    kept, set_aside = [], []
    for chest in sorted(chests, key=lambda c: c["flag"]):
        map_code = chest["map"]
        zone = zone_of(map_code)[0]
        row = matches[chest["flag"]]
        if row is None and chest["flag"] not in KNOWN_WITHOUT_DSR:
            set_aside.append((chest, map_code, zone))
            continue
        chapter = chapter_number(row["chapter"] if row else KNOWN_WITHOUT_DSR[chest["flag"]])
        source = f"DSR n° {row['n']} ({row['chapter']}, {row['zone']})" if row else "OBS 2026-10-23 (DSR Prologue, texte)"
        kept.append({"kind": chest["kind"], "flag": chest["flag"], "map": map_code, "zone": zone, "item": chest["EN"], "fr": chest["FR"],
                     "category": chest["category"], "index": chest["index"], "chapter": chapter,
                     "bonus": zone in BONUS_ZONES, "source": source})

    # Noms de lieux : « <zone> <écran> - <objet d'origine> Chest » (coffre) ou « … - Hidden <objet> » (objet à
    # examiner), numérotés si répétés sur le même écran.
    seen: Counter[str] = Counter()
    for chest in kept:
        what = f"{chest['item']} Chest" if chest["kind"] == "chest" else f"Hidden {chest['item']}"
        base = f"{chest['zone']} {screen(chest['map'])} - {what}"
        seen[base] += 1
        chest["name"] = base if seen[base] == 1 else f"{base} {seen[base]}"
    names = [chest["name"] for chest in kept]
    assert len(set(names)) == len(names), "noms de lieux en double"
    slots = {(c["category"], c["index"]): c["item"] for c in kept}
    assert len(set(slots.values())) == len(slots), "deux objets différents portent le même nom"

    lines = ['"""Locations of the game, generated by research/scripts/build_world_data.py: do not edit by hand.',
             "",
             "Chests come from CreateBox calls in the ROM map scripts, hidden items from flagged GetItem calls",
             "(research/chests.md). The chapter is the one where the DSR guide got the item (story progress and Ki",
             "Blast level known to be enough).",
             '"""',
             "from typing import NamedTuple",
             "",
             "",
             "class LocationData(NamedTuple):",
             "    name: str",
             "    zone: str",
             "    flag: int",
             '    """Game flag set when the item is taken (research/ram_map.md, section 3)."""',
             "    item: str",
             '    """Original contents, put in the item pool."""',
             "    chapter: int",
             '    """0 = prologue, 1-15 = story chapters (15 includes the tour made before the final battle)."""',
             "    bonus: bool",
             '    """Needs the 7 Dragon Balls (East City Ruins), only included by an option."""',
             "",
             "",
             "LOCATIONS: tuple[LocationData, ...] = ("]
    for c in kept:
        lines.append(f"    LocationData({c['name']!r}, {c['zone']!r}, {c['flag']}, {c['item']!r}, {c['chapter']}, "
                     f"{c['bonus']}),")
    lines += [")", "", "# Inventory slot of each item found at a location: (category, number in the game's data table).",
              "ITEM_SLOTS: dict[str, tuple[int, int]] = {"]
    for (category, index), item in sorted(slots.items()):
        lines.append(f"    {item!r}: ({category}, {index}),")
    lines.append("}")
    WORLD_DATA.write_text("\n".join(lines) + "\n", encoding="utf-8")

    out = ["# Coffres et objets à examiner du jeu (extraits de la ROM)", "",
           "Généré par [scripts/build_world_data.py](scripts/build_world_data.py) à partir de",
           "[scripts/extract_chests.py](scripts/extract_chests.py) (appels `CreateBox` et `GetItem` des scripts) et des",
           "lignes du guide DSR de [game_data.md](game_data.md). Ne pas modifier à la main.", "",
           f"**{sum(c['kind'] == 'chest' for c in chests)} coffres et {sum(c['kind'] == 'examine' for c in chests)} "
           f"objets à examiner** dans la ROM : {len(kept)} retenus pour le world "
           f"(dont {sum(c['bonus'] for c in kept)} en option « bonus »), {len(set_aside)} mis de côté.", "",
           "## Lieux retenus", "",
           "| Drapeau | Carte | Lieu (world) | Objet FR | Chapitre | Bonus | Source |",
           "|---|---|---|---|---|---|---|"]
    for c in kept:
        out.append(f"| {c['flag']} | `{c['map']}` | {c['name']} | {c['fr']} | {c['chapter']} | "
                   f"{'oui' if c['bonus'] else ''} | {c['source']} |")
    out += ["", "## Lieux mis de côté (pas de ligne DSR : accès et chapitre inconnus, à vérifier en jeu)", "",
            "| Drapeau | Type | Carte | Zone | Objet EN | Objet FR |", "|---|---|---|---|---|---|"]
    for chest, map_code, zone in set_aside:
        kind = "coffre" if chest["kind"] == "chest" else "à examiner"
        out.append(f"| {chest['flag']} | {kind} | `{map_code}` | {zone} | {chest['EN']} | {chest.get('FR', '')} |")
    CHESTS_MD.write_text("\n".join(out) + "\n", encoding="utf-8")
    print(f"{len(kept)} lieux retenus, {len(set_aside)} mis de côté")


if __name__ == "__main__":
    main()
