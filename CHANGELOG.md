# Changelog

All notable changes to the world. Versions follow `world_version` in
[`worlds/dbz_aots/archipelago.json`](worlds/dbz_aots/archipelago.json).

## 0.16.0 — every chest of the game, carrot rewards

### Added
- The last locations left aside, checked in game: Mutaito Training Grounds 5 (chest in the hollow), Princess Snake's
  House 3 (chest in the niche, and a trap chest that starts a battle), the back of the red car in West City, and the
  ghost of the Underworld. Every chest and hidden item of the game is now a location: 256 by default.
- Option `carrot_rewards` (default on): the rewards of the carrot man of West City for 1, 100, 500 and 1000 carrots
  are locations. They only ever hold filler. The 1000-carrot one is where the Sewer Key comes from.
- PopTracker pack: the real Gas Mask icon from the game; the Underworld in the Other World panel.

### Fixed
- The client took back the original item of a location that is not in your seed (an option turned off, or a location
  added by a later version): you now keep it.

## 0.15.0 — the Sewer, a world map in the tracker

### Added
- The optional Sewer under the Martial Arts Temple (with `key_items`): its two chests and its trap chest (a battle,
  then Kami's Cape) are locations. The **Sewer Key**, which the game gives for 1000 carrots, is shuffled in place of
  a filler item; the logic expects the Sewer in chapter 15, with the key. 247 locations by default.
- PopTracker pack: a "World" tab with every location on the world map of the game, grouped on its area (the Other
  World in a panel beside it); the Sewer Key in the item grid, and 4 Ki-Blast Fruits.

### Fixed
- The client also takes back an item given after its location's flag (the trap chest does so).
- `extract_tracker_assets.py` failed since 0.13.0.

## 0.14.0 — the Gas Mask is needed from the prologue

### Fixed
- The logic asked for the Gas Mask only from chapter 6, but Bulma lets nobody into the poison mist of Training
  Island until it is equipped, and the end of the prologue is behind it: a seed could put the Gas Mask where it could
  not be reached. The end of the prologue and every chapter now need it.

### Added
- Option `gas_mask_placement` (default `own_early`): the Gas Mask is in one of your own first locations (Kame House
  and Training Island). Also `any_early` (first locations of any world), `start` (starting inventory) and `anywhere`.
- BizHawk reminds you to equip the Gas Mask when you receive it.

## 0.13.0 — chests show what they hold, tracker follows you

### Added
- Chests and hidden items show and give the item they hold in the multiworld: your own item by its name, another
  player's as "Archipelago Item" (named in the language of the game). BizHawk also says who got it.
- The PopTracker pack opens the tab of the area you are in (button "Map" to turn it off). Needs PopTracker 0.25.4.

### Fixed
- Taking a hidden item also let you keep its original item: the game sets its flag only when its message closes,
  after giving the item, so the client did not recognise it.

## 0.12.0 — first release

Requires Archipelago 0.6.8 or newer, BizHawk 2.10 or newer, and the European ROM (`BRPP`, revision 0).

### Added
- Patch file `AP_..._<name>.apdbzaots` for each player: opening it starts BizHawk with your ROM and the connector
  script, like other BizHawk games. It does not modify the game; the ROM is checked by its header.
- 17 more locations, checked in game: chests hidden under breakable rocks and hidden items off the story path. They
  are in logic in chapter 15 (the Dragon Ball hunt before the final battle). 244 locations by default.
- Goal `broly`: defeat Broly, the secret boss.
- Story key items shuffled with `key_items`: Snowfield Key (chapter 8), Submarine (chapter 10), Bubbles' Thing
  (chapter 13).
- DeathLink, sent on a Game Over.
- Options: `goal`, `goal_chapter`, `hidden_items`, `chapter_checks`, `key_items`, `east_city_ruins`,
  `experience_multiplier`, `death_link`.
- PopTracker pack with the real maps of the game, built from the player's ROM.
- French setup guide.

## Development versions (0.1.0 – 0.11.0)

Not released. In order: Training Island only (0.1–0.2), every chest of the story (0.3), hidden items and chapter
ends (0.4), experience multiplier (0.5), DeathLink (0.6–0.7.1), YAML options (0.7), Snowfield Key (0.8), Submarine and
Bubbles' Thing (0.9), Broly goal (0.10), off-path locations (0.11). The reasons behind each choice are logged in
[research/decisions.md](research/decisions.md) (in French).
