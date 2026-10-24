"""Build the PopTracker pack of the world from its own data, so the two never diverge (research/roadmap.md, bloc 5).

Prototype without game maps: the "map" is a story board drawn here (one box per chapter, one pin per area of the
chapter), so the pack holds nothing taken from the ROM. Autotracking uses the Archipelago connection of PopTracker:
items and checked locations come from the server.

Run with the Python of the Archipelago clone (it imports the world):
    ~/Coding/ArchipelagoRom/Archipelago/.venv/bin/python tools/build_poptracker.py [--deploy]
Output: build/poptracker/dbz_aots/ and build/poptracker/dbz_aots.zip; --deploy also copies the folder into the
packs of the Windows PopTracker.
"""
from __future__ import annotations

import json
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARCHIPELAGO = Path.home() / "Coding/ArchipelagoRom/Archipelago"
sys.path.insert(0, str(ARCHIPELAGO))

from PIL import Image, ImageDraw  # noqa: E402

from worlds.dbz_aots.items import GAS_MASK, ITEM_NAME_TO_ID, KI_BLAST_FRUIT  # noqa: E402
from worlds.dbz_aots.location_data import LOCATIONS  # noqa: E402
from worlds.dbz_aots.locations import LOCATION_NAME_TO_ID, STORY_LOCATIONS  # noqa: E402
from worlds.dbz_aots.regions import LAST_CHAPTER, chapter_region  # noqa: E402

OUT = REPO / "build/poptracker/dbz_aots"
WINDOWS_PACKS = Path("/mnt/c/Users/Aurelien/Desktop/archipelago/poptracker/packs")
VERSION = json.loads((REPO / "worlds/dbz_aots/archipelago.json").read_text())["world_version"]

# Tracked items: PopTracker code, name, maximum count, colour of the generated icon.
TRACKED = {GAS_MASK: ("gasmask", 1, (70, 140, 70)), KI_BLAST_FRUIT: ("kiblast", 2, (220, 120, 30))}
# Same requirements as rules.py (research/decisions.md, D28), as PopTracker rules.
CHAPTER_RULES = {6: "gasmask", 8: "gasmask,kiblast:1", 13: "gasmask,kiblast:2"}

BOX_W, BOX_H, COLUMNS = 240, 150, 4


def chapter_rule(chapter: int) -> list[str]:
    applicable = [rule for start, rule in CHAPTER_RULES.items() if chapter >= start]
    return [applicable[-1]] if applicable else []


def box_origin(chapter: int) -> tuple[int, int]:
    return (chapter % COLUMNS) * BOX_W, (chapter // COLUMNS) * BOX_H


def draw_story_board() -> None:
    rows = (LAST_CHAPTER + COLUMNS) // COLUMNS
    image = Image.new("RGB", (COLUMNS * BOX_W, rows * BOX_H), (30, 30, 36))
    draw = ImageDraw.Draw(image)
    for chapter in range(LAST_CHAPTER + 1):
        x, y = box_origin(chapter)
        draw.rectangle((x + 4, y + 4, x + BOX_W - 4, y + BOX_H - 4), outline=(200, 160, 60), width=2)
        draw.text((x + 12, y + 10), chapter_region(chapter), fill=(240, 220, 180))
    (OUT / "images/maps").mkdir(parents=True)
    image.save(OUT / "images/maps/story.png")


def draw_item_icons() -> None:
    (OUT / "images/items").mkdir(parents=True)
    for name, (code, _, colour) in TRACKED.items():
        image = Image.new("RGBA", (32, 32), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        draw.ellipse((2, 2, 30, 30), fill=colour, outline=(255, 255, 255), width=2)
        draw.text((9, 10), "".join(word[0] for word in name.replace("-", " ").split())[:2], fill=(255, 255, 255))
        image.save(OUT / f"images/items/{code}.png")


def build() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    draw_story_board()
    draw_item_icons()

    # Areas: one per (chapter, zone), plus the chapter ends; sections are the locations.
    areas: dict[tuple[int, str], list[str]] = defaultdict(list)
    for data in LOCATIONS:
        areas[(data.chapter, data.zone)].append(data.name)
    for name, (chapter, _) in STORY_LOCATIONS.items():
        areas[(chapter, "Story")].append(name)

    per_chapter: dict[int, list[str]] = defaultdict(list)
    locations, mapping = [], {}
    for (chapter, zone), names in sorted(areas.items()):
        per_chapter[chapter].append(zone)
        slot = len(per_chapter[chapter]) - 1
        x, y = box_origin(chapter)
        area = f"{chapter_region(chapter)}: {zone}"
        locations.append({
            "name": area,
            "access_rules": chapter_rule(chapter),
            "map_locations": [{"map": "story", "x": x + 30 + (slot % 6) * 36, "y": y + 50 + (slot // 6) * 36}],
            "sections": [{"name": name, "item_count": 1} for name in names],
        })
        for name in names:
            mapping[LOCATION_NAME_TO_ID[name]] = f"@{area}/{name}"

    files = {
        "manifest.json": {
            "name": "Dragon Ball Z - Attack of the Saiyans Archipelago (prototype)",
            "game_name": "Dragon Ball Z - Attack of the Saiyans",
            "package_uid": "ap_dbz_aots",
            "package_version": VERSION,
            "platform": "nds",
            "author": "Aure33",
            "min_poptracker_version": "0.25.2",
            "variants": {"standard": {"display_name": "Story board", "flags": ["ap"]}},
        },
        "items/items.json": [
            {"name": name, "type": "consumable" if count > 1 else "toggle", "codes": code,
             "img": f"images/items/{code}.png", **({"max_quantity": count} if count > 1 else {})}
            for name, (code, count, _) in TRACKED.items()
        ],
        "maps/maps.json": [{"name": "story", "location_size": 28, "location_border_thickness": 2,
                            "img": "images/maps/story.png"}],
        "locations/locations.json": locations,
        "layouts/tracker.json": {
            "tracker_default": {"type": "dock", "content": [
                {"type": "itemgrid", "dock": "top", "item_size": 40, "rows": [list(c for c, _, _ in TRACKED.values())]},
                {"type": "map", "maps": ["story"]},
            ]},
            "tracker_broadcast": {"type": "itemgrid", "item_size": 40,
                                  "rows": [list(c for c, _, _ in TRACKED.values())]},
        },
    }
    for path, content in files.items():
        (OUT / path).parent.mkdir(parents=True, exist_ok=True)
        (OUT / path).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")

    item_lines = [f"    [{ITEM_NAME_TO_ID[name]}] = \"{code}\"," for name, (code, _, _) in TRACKED.items()]
    location_lines = [f"    [{ap_id}] = {json.dumps(path)}," for ap_id, path in sorted(mapping.items())]
    scripts = {
        "scripts/init.lua": """Tracker:AddItems("items/items.json")
Tracker:AddMaps("maps/maps.json")
Tracker:AddLocations("locations/locations.json")
Tracker:AddLayouts("layouts/tracker.json")
ScriptHost:LoadScript("scripts/autotracking.lua")
""",
        "scripts/mapping.lua": "-- Generated by tools/build_poptracker.py: do not edit by hand.\nITEM_MAPPING = {\n"
                              + "\n".join(item_lines) + "\n}\nLOCATION_MAPPING = {\n" + "\n".join(location_lines)
                              + "\n}\n",
        "scripts/autotracking.lua": """ScriptHost:LoadScript("scripts/mapping.lua")

function onClear(slot_data)
    for _, code in pairs(ITEM_MAPPING) do
        local item = Tracker:FindObjectForCode(code)
        if item then
            if item.Type == "consumable" then item.AcquiredCount = 0 else item.Active = false end
        end
    end
    for _, path in pairs(LOCATION_MAPPING) do
        local section = Tracker:FindObjectForCode(path)
        if section then section.AvailableChestCount = section.ChestCount end
    end
end

function onItem(index, item_id, item_name, player_number)
    local code = ITEM_MAPPING[item_id]
    if not code then return end
    local item = Tracker:FindObjectForCode(code)
    if not item then return end
    if item.Type == "consumable" then item.AcquiredCount = item.AcquiredCount + item.Increment else item.Active = true end
end

function onLocation(location_id, location_name)
    local path = LOCATION_MAPPING[location_id]
    if not path then return end
    local section = Tracker:FindObjectForCode(path)
    if section then section.AvailableChestCount = section.AvailableChestCount - 1 end
end

Archipelago:AddClearHandler("clear handler", onClear)
Archipelago:AddItemHandler("item handler", onItem)
Archipelago:AddLocationHandler("location handler", onLocation)
""",
    }
    (OUT / "scripts").mkdir()
    for path, content in scripts.items():
        (OUT / path).write_text(content, encoding="utf-8")

    archive = shutil.make_archive(str(OUT), "zip", OUT)
    print(f"Pack : {OUT} ({len(locations)} zones, {len(mapping)} lieux) ; archive : {archive}")


if __name__ == "__main__":
    build()
    if "--deploy" in sys.argv[1:]:
        target = WINDOWS_PACKS / "dbz_aots"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(OUT, target)
        print(f"Copié dans : {target}")
