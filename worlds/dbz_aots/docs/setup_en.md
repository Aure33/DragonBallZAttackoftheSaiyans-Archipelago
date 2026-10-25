# Dragon Ball Z - Attack of the Saiyans Setup Guide

This world randomizes the chests of the whole story (see the game page for what is covered).

## Required software

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.8 or newer
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.10 or newer (tested with 2.11.1)
- Your own dump of the European release of Dragon Ball Z: Attack of the Saiyans (game code `BRPP`)

## Installation

1. Install `dbz_aots.apworld`: Archipelago Launcher > "Install APWorld" (or put it in the `custom_worlds`
   folder of your Archipelago installation).
2. Generate a game with a YAML file for "Dragon Ball Z - Attack of the Saiyans". To get a template with every
   option and its description, open the Archipelago Launcher and click "Generate Template Options" (after step 1).
   Every player of the multiworld who generates the game needs the `.apworld`; the others do not.

## Connecting

The game generates a patch file for you, `AP_..._<your name>.apdbzaots` (in the output zip, or sent by the host).
It does not change the game: it only lets the BizHawk Client start everything for you.

1. Double-click the `.apdbzaots` file (if Windows asks which program to use, pick the Archipelago Launcher), or open
   the Archipelago Launcher, click "Open Patch" and select it.
2. The first time, select your ROM when asked (and `EmuHawk.exe` if it is not set yet). The ROM is checked: it must be
   the European release (game code `BRPP`, revision 0).
3. BizHawk starts with the ROM and the connector script, and the BizHawk Client opens. Type the server address
   (`address:port`) at the top and connect, then type your slot name (the `name` of your YAML).

Without the patch file: open the ROM in BizHawk (melonDS core), load `data/lua/connector_bizhawk_generic.lua` from your
Archipelago installation in `Tools > Lua Console`, then open the BizHawk Client from the Launcher and connect.

Only one BizHawk Client can talk to BizHawk at a time: close any other BizHawk Client window first.

## Your save file

The ROM made from the patch file (`AP_..._<your name>.nds`, next to the patch file) has its own save in BizHawk, so
your other saves of the game are not touched. Start a new game in it, and open the same patch file every time you
play this multiworld.

Loading your last save (after a Game Over, for example) is safe: chests you open again are not sent twice, and the
client gives you back the items received since that save.

## What a chest shows

While the client is connected, each chest and hidden item gives what it really holds:

- your own item: the game shows its name ("Obtained: Absorb Bracelet!"); the client swaps it for the one the server
  sends you, so you get it once;
- another player's item: the game shows "Archipelago Item" (in the language of your game), which the client removes
  right away. BizHawk shows who got it ("Sent Sword to Ami").

Hidden items can only show use items (beans, fruits...): another kind of item of yours shows as "Archipelago Item"
there.

## Tracker

A PopTracker pack with the maps of the game can be built from your own ROM: see the README of the world's
repository. Once connected, it opens the tab of the area you are in (button "Map" to turn this off).

## Known limitations

- A chest or hidden item taken while the client is not connected gives its original item, which you keep.
- Received items are added while you are on the field; during a battle they wait until it ends.
- Received items are only added to your inventory: use the Ki-Blast Fruits and equip the Gas Mask yourself.
- With `key_items`, the client keeps the Snowfield Key, the Submarine and Bubbles' Thing in your inventory only once
  they are received: the story scenes that give them in the original game no longer do.
- Never load an older save or savestate to undo a defeat while DeathLink is on: the client only sends a death when
  the game restarts after a Game Over.
