#!/usr/bin/env bash
# Laeuft auf der gemieteten GPU: ComfyUI starten -> Set fuer Set generieren und pushen -> GPU stoppen
set -euo pipefail

# ===== ANPASSEN =====
REPO="twitchg5n0e-jpg/character-gen"
LIMIT="${LIMIT:-0}"   # 0 = alle offenen Sets, sonst nur so viele
SET="${SET:-}"        # z. B. SET=Human/Female/Body1/Stage1 fuer genau ein Set
AUTO_STOP=1           # 1 = GPU am Ende automatisch stoppen (RunPod)
# ====================

# GPU auch bei einem Fehler stoppen, damit sie nicht weiter Geld kostet.
stop_pod() {
  if [ "$AUTO_STOP" = "1" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then
    runpodctl stop pod "$RUNPOD_POD_ID" || runpodctl pod stop "$RUNPOD_POD_ID"   # alte und neue runpodctl-Syntax
  fi
}
trap stop_pod EXIT

: "${GITHUB_TOKEN:?GITHUB_TOKEN ist nicht gesetzt}"
cd "$(dirname "$0")"

# git-lfs fuer die Bilder, libgl1 + libglib2.0-0 fuer OpenCV (Pose-Pruefung der Seitenansicht)
apt-get update -qq && apt-get install -y -qq git-lfs libgl1 libglib2.0-0
git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git"
git config user.name "runpod"
git config user.email "runpod@users.noreply.github.com"
git lfs install

pip install -q -r requirements.txt
bash scripts/setup_comfyui.sh

push() {
  git add output
  git diff --cached --quiet || git commit -q -m "Neue Characters $(date +%F_%H-%M)"
  for i in 1 2 3 4; do
    git pull -q --rebase -X theirs && git push -q && return 0   # holt gespiegelte Ansichten von GitHub Actions
    sleep $((2 ** i))
  done
  echo "Push fehlgeschlagen; der naechste Durchlauf versucht es wieder"
}

# Nach jedem fertigen Set pushen, damit bei einem Abbruch nichts verloren geht.
if [ -n "$SET" ]; then
  python scripts/generate.py --set "$SET"
  push
else
  done_sets=0
  while [ "$LIMIT" = "0" ] || [ "$done_sets" -lt "$LIMIT" ]; do
    out=$(python scripts/generate.py --limit 1 | tee /dev/stderr)
    echo "$out" | grep -q "^0 open set" && break
    push
    done_sets=$((done_sets + 1))
  done
fi
push
