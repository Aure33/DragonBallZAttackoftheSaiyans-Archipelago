# Dragon Ball Z - Attack of the Saiyans Setup Guide

This world randomizes the chests of the whole story (see the game page for what is covered).

## Required software

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.8 or newer
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.10 or newer (tested with 2.11.1)
- Your own dump of the European release of Dragon Ball Z: Attack of the Saiyans (game code `BRPP`)

## Installation

1. Put `dbz_aots.apworld` in the `custom_worlds` folder of your Archipelago installation.
2. Generate a game with a YAML file for "Dragon Ball Z - Attack of the Saiyans".

## Connecting

1. Open your ROM in BizHawk (melonDS core) and load or start a save file.
2. In BizHawk, open `Tools > Lua Console` and load `data/lua/connector_bizhawk_generic.lua` from your Archipelago
   installation.
3. Open the Archipelago Launcher, start the BizHawk Client and connect to the server.
4. The client asks for your slot name (the `name` of your YAML): type it in the client.

Only one BizHawk Client can talk to BizHawk at a time: close any other BizHawk Client window first.

## Known limitations

- Chests still show their original item when opened; the client removes it from your inventory right away.
  If a chest is opened while the client is not connected, you keep that original item.
- Received items are added while you are on the field; during a battle they wait until it ends.
- Received items are only added to your inventory: use the Ki-Blast Fruits and equip the Gas Mask yourself.
