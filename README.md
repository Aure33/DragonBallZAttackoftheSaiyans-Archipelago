# Dragon Ball Z: Attack of the Saiyans — Archipelago

An [Archipelago](https://archipelago.gg) world for **Dragon Ball Z: Attack of the Saiyans** (Nintendo DS, 2009),
played on [BizHawk](https://tasvideos.org/BizHawk) with Archipelago's BizHawk Client.

The chests and hidden items of the whole story are shuffled with the other games of your multiworld, and so are the
story key items that open the way (Snowfield Key, Submarine, Bubbles' Thing). The game itself is not modified: the
client reads and writes the game's memory while you play.

## Quick links

| | |
|---|---|
| **Download** | [Latest release](../../releases/latest): `dbz_aots.apworld` and a YAML template |
| **Setup guide** | [English](worlds/dbz_aots/docs/setup_en.md) · [Français](worlds/dbz_aots/docs/setup_fr.md) |
| **Game page** (what is randomized, options, goals) | [English](worlds/dbz_aots/docs/en_Dragon%20Ball%20Z%20-%20Attack%20of%20the%20Saiyans.md) |
| **YAML template** | [examples/](examples/) (or Archipelago Launcher > "Generate Template Options") |
| **Changelog** | [CHANGELOG.md](CHANGELOG.md) |
| **Report a bug** | [Issues](../../issues/new/choose) |

## Features

- **244 locations** by default: 209 chests, 17 hidden items, the end of each chapter, and the three story scenes
  that give a key item.
- **Story key items** shuffled (`key_items`): the Snowfield Key, the Submarine and Bubbles' Thing only appear in your
  inventory once you receive them from the multiworld.
- **Logic that follows the story**: Gas Mask, Ki-Blast Fruits and key items are required where the game needs them;
  a seed can never lock you out.
- **Goals**: the end of any chapter (`goal_chapter`, 1 to 15), or defeating **Broly**, the secret boss (`goal: broly`).
- **DeathLink**: a Game Over sends a death; a received death ends your next battle.
- **Experience multiplier** (1 to 10) to keep up with a multiworld.
- **Chests show what they really hold**: your item's name, or "Archipelago Item" for another player's.
- **PopTracker pack** with the real maps of the game, which follows you from area to area (built from your own ROM,
  see below).

## Requirements

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) **0.6.8** or newer.
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) **2.10** or newer (tested with 2.11.1, melonDS core).
- Your own ROM of the **European release** (game code `BRPP`, revision 0). Other releases are not supported.

## How to play (short version)

1. Install `dbz_aots.apworld` (Archipelago Launcher > "Install APWorld"). Whoever **generates** the multiworld needs
   it; the other players do not.
2. Fill in a YAML (template in the release) and generate the multiworld as usual. Custom worlds must be generated
   locally; the result can then be hosted on archipelago.gg or on your own computer.
3. Open your `AP_..._<name>.apdbzaots` file: BizHawk starts with your ROM and the connector script, and the BizHawk
   Client opens. Connect to the server and type your slot name.

The [setup guide](worlds/dbz_aots/docs/setup_en.md) has every step and the known limitations.

## PopTracker pack

A [PopTracker](https://github.com/black-sliver/PopTracker) pack shows every area of the game with a pin on each
chest, follows your items and checks through Archipelago, opens the tab of the area you are in, and hides what your
options do not shuffle. Its maps are
pictures of the game, so they are **not** distributed: you build the pack from your own ROM (Python 3.12 needed):

```bash
pip install ndspy pillow
python research/scripts/extract_tracker_assets.py "path/to/your/rom.nds"   # pictures + chest positions
ARCHIPELAGO=<Archipelago source checkout> <its Python> tools/build_poptracker.py    # pack in build/poptracker/
```

Details: [research/poptracker.md](research/poptracker.md) (in French).

## Building from source

The world lives in [`worlds/dbz_aots`](worlds/dbz_aots). With an Archipelago 0.6.8 source checkout:

```bash
ln -s "$PWD/worlds/dbz_aots" <Archipelago>/worlds/dbz_aots
cd <Archipelago>
AP_TEST_WORLDS=dbz_aots python -m pytest -q -n auto   # tests of this world
python Launcher.py "Build APWorlds" -- "Dragon Ball Z - Attack of the Saiyans" --skip_open_folder
```

Releases are built by GitHub Actions when a `v*` tag is pushed (the tag must match `world_version` in
[`archipelago.json`](worlds/dbz_aots/archipelago.json)).

### Repository layout

| Folder | Content |
|---|---|
| [`worlds/dbz_aots`](worlds/dbz_aots) | The world: items, locations, logic, options, BizHawk client, docs, tests |
| [`examples`](examples) | YAML template |
| [`tools`](tools) | Build and test scripts (apworld, PopTracker pack, mass seed generation, live tests) |
| [`research`](research) | Reverse engineering notes (in French): memory map, game data, decisions log, scripts |

Every memory address and game fact comes from the ROM or from tests in game; the sources are recorded in
[`research/ram_map.md`](research/ram_map.md), [`research/game_data.md`](research/game_data.md) and
[`research/decisions.md`](research/decisions.md). No ROM, save file or extracted game data is stored in this
repository.

## Credits

- World and client: Aure33.
- Game data cross-checked with Darkstar Ripclaw's
  [FAQ/Walkthrough](https://www.gamerevolution.com/guides/45075-dragon-ball-z-attack-of-the-saiyans-faqwalkthrough),
  the [jeuxmangas.com side quests guide](https://www.jeuxmangas.com/soluces-et-astuces/dragonball-z-attack-of-the-saiyans-ds-les-quetes-annexes)
  and the [Let's Play Archive](https://lparchive.org/Dragon-Ball-Z-Attack-Of-The-Saiyans/) (full list of sources in
  [research/game_data.md](research/game_data.md)).
- Archipelago, its BizHawk Client and connector script: the [Archipelago team](https://github.com/ArchipelagoMW/Archipelago).

## AI usage disclosure

This world was written with heavy help from an AI coding assistant (Claude, by Anthropic): code, reverse
engineering of the game's scripts and memory, and documentation. Every result was checked against the game itself
(in-game tests through BizHawk), and the world is covered by automated tests and mass seed generation.

Dragon Ball Z: Attack of the Saiyans was developed by Monolith Soft and published by Namco Bandai. Dragon Ball
belongs to its rights holders. This fan project is not affiliated with them.
