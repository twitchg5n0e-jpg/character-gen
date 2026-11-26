#!/usr/bin/env bash
# Laeuft auf der gemieteten GPU: ComfyUI starten -> Set fuer Set generieren und pushen -> GPU stoppen
set -euo pipefail

# ===== ANPASSEN =====
REPO="twitchg5n0e-jpg/character-gen"
LIMIT="${LIMIT:-0}"   # 0 = alle offenen Sets, sonst nur so viele
SET="${SET:-}"        # z. B. SET=Human/Female/Body1/Stage1 fuer genau ein Set
AUTO_STOP="${AUTO_STOP:-1}"   # 1 = GPU am Ende automatisch stoppen (RunPod), 0 = laufen lassen
BRANCH="${BRANCH:-}"   # z. B. BRANCH=claude/gifted-pasteur-7ee42l; leer = der ausgecheckte Branch
# ====================

# Alles mitschreiben: RunPod loescht die Logs eines gestoppten Pods, darum werden sie bei einem Fehler gepusht.
LOG="$(cd "$(dirname "$0")" && pwd)/run_pod.log"
exec > >(tee -a "$LOG") 2>&1

# Bei einem Fehler das Log (und comfyui.log) nach logs/ pushen, dann die GPU stoppen, damit sie kein Geld kostet.
stop_pod() {
  code=$?
  set +e +o pipefail   # beim Aufraeumen nicht an einem einzelnen Fehler abbrechen
  if [ "$code" != "0" ] && [ -n "${GITHUB_TOKEN:-}" ]; then
    cd "$(dirname "$LOG")"
    mkdir -p logs
    name="logs/fehler_$(date +%F_%H-%M)_${RUNPOD_POD_ID:-lokal}.txt"
    { echo "Exit-Code $code"; nvidia-smi 2>&1 | head -15; echo "===== run_pod.log"; tail -n 150 "$LOG";
      echo "===== comfyui.log"; tail -n 150 comfyui.log 2>/dev/null; } > "$name"
    git add -f "$name" && git commit -q -m "Fehler-Log $(basename "$name")" && \
      { git pull -q --rebase -X theirs; git push -q; } || echo "Fehler-Log konnte nicht gepusht werden"
  fi
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

# Auf dem gewuenschten Branch arbeiten (Prompts und Ergebnisse gehoeren auf denselben Branch).
if [ -n "$BRANCH" ] && [ "$(git rev-parse --abbrev-ref HEAD)" != "$BRANCH" ]; then
  git fetch -q origin "$BRANCH"
  git checkout -q -B "$BRANCH" "origin/$BRANCH"
fi
git branch --set-upstream-to="origin/$(git rev-parse --abbrev-ref HEAD)" >/dev/null 2>&1 || true

pip install -q -r requirements.txt

# Erst pruefen, ob PyTorch die GPU wirklich ansprechen kann, bevor 50 GB Modelle geladen werden. Manche gemieteten
# Rechner zeigen die GPU in nvidia-smi, aber CUDA laesst sich im Container nicht starten ("CUDA unknown error").
python - <<'PY'
import torch
torch.cuda.init()
x = torch.ones(1024, 1024, device="cuda")
print("GPU ok:", torch.cuda.get_device_name(0), "PyTorch", torch.__version__, "CUDA", torch.version.cuda, float((x @ x).sum()))
PY

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
