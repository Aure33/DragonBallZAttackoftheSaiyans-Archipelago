"""Build the PopTracker pack of the world from its own data, so the two never diverge (research/roadmap.md, bloc 5).

The pack shows the real screens of the game, one tab per area, with a pin on every chest and hidden item at its exact
place. Those images come from the player's own ROM: extract them first (they never go into the repository):
    research/.venv/bin/python research/scripts/extract_tracker_assets.py "<ROM>"
Then run with the Python of the Archipelago clone (it imports the world):
    ~/Coding/ArchipelagoRom/Archipelago/.venv/bin/python tools/build_poptracker.py [--deploy]
Output: build/poptracker/dbz_aots/ and build/poptracker/dbz_aots.zip; --deploy also copies the folder into the
packs of the Windows PopTracker.

Autotracking uses the Archipelago connection of PopTracker: received items and checked locations come from the
server, and slot_data hides what the slot does not shuffle (hidden items, chapter ends, key items, East City Ruins,
chapters after the goal).
"""
from __future__ import annotations

import json
import os
import shutil
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
ARCHIPELAGO = Path(os.environ.get("ARCHIPELAGO", Path.home() / "Coding/ArchipelagoRom/Archipelago"))
sys.path.insert(0, str(ARCHIPELAGO))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from worlds.dbz_aots.items import (BUBBLES_THING, GAS_MASK, ITEM_NAME_TO_ID, KI_BLAST_FRUIT, SNOWFIELD_KEY,  # noqa: E402
                                    SUBMARINE)
from worlds.dbz_aots.location_data import LOCATIONS  # noqa: E402
from worlds.dbz_aots.locations import KEY_ITEM_LOCATIONS, LOCATION_NAME_TO_ID, STORY_LOCATIONS  # noqa: E402
from worlds.dbz_aots.regions import LAST_CHAPTER, chapter_region  # noqa: E402

OUT = REPO / "build/poptracker/dbz_aots"
ASSETS = REPO / "build/tracker_assets"
WINDOWS_PACKS = Path("/mnt/c/Users/Aurelien/Desktop/archipelago/poptracker/packs")
VERSION = json.loads((REPO / "worlds/dbz_aots/archipelago.json").read_text())["world_version"]
FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Tracked items: PopTracker code, maximum count, colour of the generated icon, short label.
TRACKED = {GAS_MASK: ("gasmask", 1, (70, 140, 70), "GM"), KI_BLAST_FRUIT: ("kiblast", 3, (220, 120, 30), "KB"),
           SNOWFIELD_KEY: ("snowkey", 1, (90, 160, 220), "SK"), SUBMARINE: ("submarine", 1, (230, 190, 40), "SU"),
           BUBBLES_THING: ("bubbles", 1, (200, 90, 200), "BT")}
KEY_ITEM_CODES = ("snowkey", "submarine", "bubbles")
# Same requirements as rules.py (research/decisions.md, D28 and D47), as PopTracker rules. With key_items off, the
# pack marks the three key items as owned (the story gives them), so the same rules hold.
CHAPTER_RULES = {6: "gasmask", 8: "gasmask,kiblast:1,snowkey", 10: "gasmask,kiblast:1,snowkey,submarine",
                 13: "gasmask,kiblast:2,snowkey,submarine,bubbles"}
# Options read from slot_data (consumables used as switches, on by default when the pack is used by hand).
OPTIONS = {"opt_hidden": "hidden_items", "opt_chapters": "chapter_checks", "opt_keys": "key_items",
           "opt_ruins": "east_city_ruins"}
GROUPS = ((0, 4, "Prologue - Ch. 4"), (5, 8, "Ch. 5 - 8"), (9, 12, "Ch. 9 - 12"), (13, 15, "Ch. 13 - 15"))

ROW_WIDTH, LABEL, GAP = 1600, 34, 12
BOX_W, BOX_H, COLUMNS = 300, 120, 4


def font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT, size)
    except OSError:
        return ImageFont.load_default()


def chapter_rule(chapter: int) -> list[str]:
    applicable = [rule for start, rule in CHAPTER_RULES.items() if chapter >= start]
    return [applicable[-1]] if applicable else []


def visibility(chapter: int, *switches: str) -> list[str]:
    conditions = list(switches) + ([f"goalch:{chapter}"] if chapter else [])
    return [",".join(conditions)] if conditions else []


def screen_label(zone: str, map_code: str) -> str:
    number, variant = int(map_code[3:5]), int(map_code[6:8])
    return f"{zone} {number}-{variant}" if variant else f"{zone} {number}"


def screen_image(code: str) -> Image.Image:
    """The screen from the ROM, or a grey box for a screen the game draws without a map file (skr06)."""
    path = ASSETS / "maps" / f"{code}.png"
    if path.exists():
        return Image.open(path).convert("RGB")
    image = Image.new("RGB", (256, 192), (60, 60, 70))
    ImageDraw.Draw(image).text((128, 30), "(no map image)", font=font(18), fill=(200, 200, 200), anchor="mm")
    return image


def area_map(zone: str, screens: list[str]) -> tuple[Image.Image, dict[str, tuple[int, int]]]:
    """All screens of an area on one image, in rows, each with its name above it."""
    images = {code: screen_image(code) for code in screens}
    rows: list[list[str]] = [[]]
    width = 0
    for code in screens:
        if rows[-1] and width + images[code].width > ROW_WIDTH:
            rows.append([])
            width = 0
        rows[-1].append(code)
        width += images[code].width + GAP
    total_w = max(sum(images[c].width + GAP for c in row) for row in rows) + GAP
    total_h = sum(max(images[c].height for c in row) + LABEL + GAP for row in rows) + GAP
    canvas = Image.new("RGB", (total_w, total_h), (24, 24, 30))
    draw = ImageDraw.Draw(canvas)
    origins, y = {}, GAP
    for row in rows:
        x = GAP
        for code in row:
            draw.text((x + 4, y + 4), screen_label(zone, code), font=font(22), fill=(245, 215, 120))
            canvas.paste(images[code], (x, y + LABEL))
            origins[code] = (x, y + LABEL)
            x += images[code].width + GAP
        y += max(images[c].height for c in row) + LABEL + GAP
    return canvas, origins


def story_board() -> Image.Image:
    rows = (LAST_CHAPTER + COLUMNS) // COLUMNS
    image = Image.new("RGB", (COLUMNS * BOX_W, rows * BOX_H), (24, 24, 30))
    draw = ImageDraw.Draw(image)
    for chapter in range(LAST_CHAPTER + 1):
        x, y = (chapter % COLUMNS) * BOX_W, (chapter // COLUMNS) * BOX_H
        draw.rounded_rectangle((x + 6, y + 6, x + BOX_W - 6, y + BOX_H - 6), radius=10, outline=(200, 160, 60), width=3)
        draw.text((x + 18, y + 14), chapter_region(chapter), font=font(22), fill=(245, 215, 120))
    return image


def item_icon(colour: tuple[int, int, int], label: str) -> Image.Image:
    image = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((3, 3, 61, 61), radius=12, fill=colour, outline=(255, 255, 255), width=3)
    draw.text((32, 33), label, font=font(26), fill=(255, 255, 255), anchor="mm")
    return image


def build() -> None:
    if not (ASSETS / "positions.json").exists():
        sys.exit(f"{ASSETS} is missing: run research/scripts/extract_tracker_assets.py with your ROM first.")
    positions = {int(flag): place for flag, place in json.loads((ASSETS / "positions.json").read_text()).items()}
    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "images/maps").mkdir(parents=True)
    (OUT / "images/items").mkdir(parents=True)

    # Area tabs: every screen of an area that holds a location, with a pin per location.
    by_zone: dict[str, list] = defaultdict(list)
    for data in LOCATIONS:
        by_zone[data.zone].append(data)
    maps, locations, mapping, zone_chapter, unplaced = [], [], {}, {}, []
    for zone, entries in by_zone.items():
        zone_chapter[zone] = min(data.chapter for data in entries)
        screens = sorted({positions[d.flag][0] for d in entries if d.flag in positions})
        map_id = "zone_" + "".join(c if c.isalnum() else "_" for c in zone.lower())
        origins = {}
        if screens:
            canvas, origins = area_map(zone, screens)
            canvas.save(OUT / f"images/maps/{map_id}.png")
            maps.append({"name": map_id, "location_size": 22, "location_border_thickness": 3,
                         "img": f"images/maps/{map_id}.png"})
        for data in entries:
            switches = (["opt_hidden"] if data.hidden else []) + (["opt_ruins"] if data.bonus else [])
            location = {"name": data.name, "access_rules": chapter_rule(data.chapter),
                        "visibility_rules": visibility(data.chapter, *switches),
                        "sections": [{"name": "Item", "item_count": 1}]}
            place = positions.get(data.flag)
            if place and place[0] in origins:
                x0, y0 = origins[place[0]]
                location["map_locations"] = [{"map": map_id, "x": x0 + place[1], "y": y0 + place[2]}]
            else:
                unplaced.append(data.name)
            locations.append(location)
            mapping[LOCATION_NAME_TO_ID[data.name]] = f"@{data.name}/Item"

    # Story tab: chapter ends and the scenes that give a key item, in their chapter box.
    story_board().save(OUT / "images/maps/story.png")
    maps.append({"name": "story", "location_size": 30, "location_border_thickness": 3, "img": "images/maps/story.png"})
    slots: dict[int, int] = defaultdict(int)
    story = [(chapter, name, visibility(chapter + 1, "opt_chapters")) for name, (chapter, _) in STORY_LOCATIONS.items()]
    story += [(chapter, name, visibility(chapter, "opt_keys")) for name, (chapter, _, _) in KEY_ITEM_LOCATIONS.items()]
    for chapter, name, shown in story:
        x = (chapter % COLUMNS) * BOX_W + 40 + slots[chapter] * 50
        y = (chapter // COLUMNS) * BOX_H + 75
        slots[chapter] += 1
        locations.append({"name": name, "access_rules": chapter_rule(chapter), "visibility_rules": shown,
                          "sections": [{"name": "Item", "item_count": 1}],
                          "map_locations": [{"map": "story", "x": x, "y": y}]})
        mapping[LOCATION_NAME_TO_ID[name]] = f"@{name}/Item"

    for name, (code, _, colour, label) in TRACKED.items():
        item_icon(colour, label).save(OUT / f"images/items/{code}.png")
    switch = Image.new("RGBA", (8, 8), (0, 0, 0, 0))
    switch.save(OUT / "images/items/switch.png")
    items = [{"name": name, "type": "consumable" if count > 1 else "toggle", "codes": code,
              "img": f"images/items/{code}.png", **({"max_quantity": count} if count > 1 else {})}
             for name, (code, count, _, _) in TRACKED.items()]
    items += [{"name": code, "type": "consumable", "codes": code, "img": "images/items/switch.png",
               "max_quantity": 1, "initial_quantity": 1} for code in OPTIONS]
    items.append({"name": "Goal chapter", "type": "consumable", "codes": "goalch", "img": "images/items/switch.png",
                  "max_quantity": LAST_CHAPTER, "initial_quantity": LAST_CHAPTER})

    tabs = [{"title": "Story", "content": {"type": "map", "maps": ["story"]}}]
    for first, last, title in GROUPS:
        zones = sorted((z for z in by_zone if first <= zone_chapter[z] <= last and any(
            m["name"] == "zone_" + "".join(c if c.isalnum() else "_" for c in z.lower()) for m in maps)),
            key=lambda z: (zone_chapter[z], z))
        tabs.append({"title": title, "content": {"type": "tabbed", "tabs": [
            {"title": zone, "content": {"type": "map", "maps": [
                "zone_" + "".join(c if c.isalnum() else "_" for c in zone.lower())]}} for zone in zones]}})
    grid = [[code for code, _, _, _ in TRACKED.values()]]
    files = {
        "manifest.json": {
            "name": "Dragon Ball Z - Attack of the Saiyans Archipelago",
            "game_name": "Dragon Ball Z - Attack of the Saiyans",
            "package_uid": "ap_dbz_aots",
            "package_version": VERSION,
            "platform": "nds",
            "author": "Aure33",
            "min_poptracker_version": "0.25.2",
            "variants": {"standard": {"display_name": "Maps", "flags": ["ap"]}},
        },
        "items/items.json": items,
        "maps/maps.json": maps,
        "locations/locations.json": locations,
        "layouts/tracker.json": {
            "tracker_default": {"type": "dock", "content": [
                {"type": "itemgrid", "dock": "top", "item_size": 48, "rows": grid},
                {"type": "tabbed", "tabs": tabs},
            ]},
            "tracker_broadcast": {"type": "itemgrid", "item_size": 48, "rows": grid},
        },
    }
    for path, content in files.items():
        (OUT / path).parent.mkdir(parents=True, exist_ok=True)
        (OUT / path).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")

    item_lines = [f"    [{ITEM_NAME_TO_ID[name]}] = \"{code}\"," for name, (code, _, _, _) in TRACKED.items()]
    location_lines = [f"    [{ap_id}] = {json.dumps(path)}," for ap_id, path in sorted(mapping.items())]
    option_lines = [f"    {code} = \"{key}\"," for code, key in OPTIONS.items()]
    scripts = {
        "scripts/init.lua": """Tracker:AddItems("items/items.json")
Tracker:AddMaps("maps/maps.json")
Tracker:AddLocations("locations/locations.json")
Tracker:AddLayouts("layouts/tracker.json")
ScriptHost:LoadScript("scripts/autotracking.lua")
""",
        "scripts/mapping.lua": "-- Generated by tools/build_poptracker.py: do not edit by hand.\nITEM_MAPPING = {\n"
                              + "\n".join(item_lines) + "\n}\nLOCATION_MAPPING = {\n" + "\n".join(location_lines)
                              + "\n}\nOPTION_MAPPING = {\n" + "\n".join(option_lines) + "\n}\nKEY_ITEM_CODES = {"
                              + ", ".join(f'"{code}"' for code in KEY_ITEM_CODES) + "}\n",
        "scripts/autotracking.lua": """ScriptHost:LoadScript("scripts/mapping.lua")

local function set_count(code, count)
    local item = Tracker:FindObjectForCode(code)
    if item then item.AcquiredCount = count end
end

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
    -- What this slot shuffles: hide the rest.
    for code, key in pairs(OPTION_MAPPING) do
        if slot_data[key] ~= nil then set_count(code, slot_data[key] ~= 0 and 1 or 0) end
    end
    if slot_data["goal_chapter"] ~= nil then set_count("goalch", slot_data["goal_chapter"]) end
    -- Key items left in place: the story gives them, so the rules that need them hold.
    if slot_data["key_items"] == 0 then
        for _, code in ipairs(KEY_ITEM_CODES) do
            local item = Tracker:FindObjectForCode(code)
            if item then item.Active = true end
        end
    end
end

function onItem(index, item_id, item_name, player_number)
    local code = ITEM_MAPPING[item_id]
    if not code then return end
    local item = Tracker:FindObjectForCode(code)
    if not item then return end
    if item.Type == "consumable" then
        item.AcquiredCount = item.AcquiredCount + item.Increment
    else
        item.Active = true
    end
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
    print(f"Pack : {OUT} ({len(maps) - 1} zones avec cartes, {len(mapping)} lieux, {len(unplaced)} sans point : "
          f"{unplaced}) ; archive : {archive}")


if __name__ == "__main__":
    build()
    if "--deploy" in sys.argv[1:]:
        target = WINDOWS_PACKS / "dbz_aots"
        if target.exists():
            shutil.rmtree(target)
        shutil.copytree(OUT, target)
        print(f"Copié dans : {target}")
