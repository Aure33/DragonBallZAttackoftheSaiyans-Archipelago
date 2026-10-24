# Changelog

All notable changes to the world. Versions follow `world_version` in
[`worlds/dbz_aots/archipelago.json`](worlds/dbz_aots/archipelago.json).

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
