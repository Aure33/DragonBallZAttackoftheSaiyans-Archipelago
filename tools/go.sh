#!/usr/bin/env bash
# go.sh "ordre" ... : envoie les ordres à la télécommande BizHawk, puis capture l'écran.
# Écran du haut agrandi dans $SHOT (par défaut /tmp/dbz_cur.png) ; both=1 : les deux écrans.
set -euo pipefail
SHOT="${SHOT:-/tmp/dbz_cur.png}"
REMOTE_DIR=/mnt/c/Users/Aurelien/Desktop/archipelago/dbz_research/remote
cd "$(dirname "$0")/.."
python3 research/scripts/remote.py "$@" "shot cur" | grep -v "shot cur ok" || true
python3 - "$REMOTE_DIR/cur.png" "$SHOT" "${both:-0}" <<'PY'
import sys
from PIL import Image
image = Image.open(sys.argv[1])
if sys.argv[3] == "1":
    image.resize((512, 768)).save(sys.argv[2])
else:
    image.crop((0, 0, 256, 192)).resize((512, 384)).save(sys.argv[2])
PY
