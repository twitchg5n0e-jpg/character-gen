#!/usr/bin/env bash
# Laeuft auf der gemieteten GPU: generieren -> pushen -> GPU stoppen
set -euo pipefail

# ===== ANPASSEN =====
REPO="twitchg5n0e-jpg/character-gen"
GENERATE_CMD="python scripts/generate.py"
AUTO_STOP=1   # 1 = GPU am Ende automatisch stoppen (RunPod)
# ====================

: "${GITHUB_TOKEN:?GITHUB_TOKEN ist nicht gesetzt}"
cd "$(dirname "$0")"

git remote set-url origin "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git"
git config user.name "runpod"
git config user.email "runpod@users.noreply.github.com"
git lfs install

pip install -r requirements.txt
$GENERATE_CMD

git add output
git diff --cached --quiet || git commit -m "Neue Characters $(date +%F_%H-%M)"
git pull --rebase   # holt gespiegelte Ansichten von GitHub Actions
git push

if [ "$AUTO_STOP" = "1" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then
  runpodctl stop pod "$RUNPOD_POD_ID"
fi
