#!/usr/bin/env bash
# Construit dbz_aots.apworld depuis les sources d'Archipelago (WSL) et, avec --deploy, le copie dans
# l'installation Windows d'Archipelago (custom_worlds) pour l'essayer avec le BizHawk Client.
set -euo pipefail

ARCHIPELAGO="${ARCHIPELAGO:-$HOME/Coding/ArchipelagoRom/Archipelago}"
WINDOWS_CUSTOM_WORLDS="/mnt/c/ProgramData/Archipelago/custom_worlds"
GAME="Dragon Ball Z - Attack of the Saiyans"

cd "$ARCHIPELAGO"
.venv/bin/python Launcher.py "Build APWorlds" -- "$GAME" > /dev/null
echo "Construit : $ARCHIPELAGO/build/apworlds/dbz_aots.apworld"

if [[ "${1:-}" == "--deploy" ]]; then
    cp build/apworlds/dbz_aots.apworld "$WINDOWS_CUSTOM_WORLDS/"
    echo "Copié dans : $WINDOWS_CUSTOM_WORLDS (relancer le BizHawk Client pour le prendre en compte)"
fi
