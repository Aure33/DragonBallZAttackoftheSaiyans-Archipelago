#!/usr/bin/env bash
# Essai du client en conditions réelles, piloté depuis WSL (voir CLAUDE.md, « Essai du client en conditions réelles »).
#   live_test.sh server <fichier .archipelago>  serveur Archipelago (WSL), à lancer en arrière-plan
#   live_test.sh client                         BizHawk Client de l'installation Windows, en mode texte, en arrière-plan
#   live_test.sh to-server "/send Aure Gas Mask" commande tapée dans la console du serveur
#   live_test.sh to-client "Aure"               texte tapé dans le client (ex. nom du joueur demandé)
#   live_test.sh logs                           dernières lignes des deux journaux
# Prérequis : BizHawk ouvert avec la ROM et connector_bizhawk_generic.lua chargé, aucun autre BizHawk Client ouvert.
set -euo pipefail

ARCHIPELAGO="${ARCHIPELAGO:-$HOME/Coding/ArchipelagoRom/Archipelago}"
WINDOWS_ARCHIPELAGO="/mnt/c/ProgramData/Archipelago"
LIVE="${LIVE:-$HOME/.cache/dbz_aots_live}"
PORT=38281
mkdir -p "$LIVE"

open_pipe() {  # crée un tube nommé et le garde ouvert en écriture, pour que le lecteur ne voie jamais sa fin
    rm -f "$1"
    mkfifo "$1"
    (sleep infinity > "$1" &)
}

case "${1:-}" in
    server)
        open_pipe "$LIVE/server_in"
        cd "$ARCHIPELAGO"
        exec .venv/bin/python MultiServer.py "$2" --port "$PORT" < "$LIVE/server_in" > "$LIVE/server.log" 2>&1
        ;;
    client)
        open_pipe "$LIVE/client_in"
        cd "$WINDOWS_ARCHIPELAGO"
        exec ./ArchipelagoLauncherDebug.exe "BizHawk Client" -- --nogui --connect "localhost:$PORT" \
            < "$LIVE/client_in" > "$LIVE/client.log" 2>&1
        ;;
    to-server) echo "$2" > "$LIVE/server_in" ;;
    to-client) echo "$2" > "$LIVE/client_in" ;;
    logs)
        tail -n 15 "$LIVE/server.log" 2>/dev/null || true
        echo "---"
        tail -n 15 "$(ls -t "$WINDOWS_ARCHIPELAGO"/logs/BizHawkClient_* | head -1)"
        ;;
    *)
        sed -n '2,8p' "$0"
        exit 1
        ;;
esac
