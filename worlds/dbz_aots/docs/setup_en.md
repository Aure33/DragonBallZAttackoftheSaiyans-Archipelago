# Dragon Ball Z - Attack of the Saiyans Setup Guide

This world is not playable yet: the BizHawk client is still being written. This guide describes the intended setup.

## Required software

- [Archipelago](https://github.com/ArchipelagoMW/Archipelago/releases) 0.6.8 or newer
- [BizHawk](https://tasvideos.org/BizHawk/ReleaseHistory) 2.10 or newer (tested with 2.11.1)
- Your own dump of the European release of Dragon Ball Z: Attack of the Saiyans (game code `BRPP`)

## Installation

1. Put `dbz_aots.apworld` in the `custom_worlds` folder of your Archipelago installation.
2. Generate a game with a YAML file for "Dragon Ball Z - Attack of the Saiyans".

## Connecting

1. Open your ROM in BizHawk (melonDS core).
2. In BizHawk, open `Tools > Lua Console` and load `data/lua/connector_bizhawk_generic.lua` from your Archipelago
   installation.
3. Open the Archipelago Launcher, start the BizHawk Client and connect to the server.
