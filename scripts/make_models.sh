#!/usr/bin/env bash
# Laeuft auf einer gemieteten GPU: 3D-Modelle aller fertigen Sets mit Hunyuan3D-2mv (scripts/make_models.py),
# nach jedem Modell nach models/<Set>/ pushen, am Ende die GPU stoppen.
#   BRANCH=claude/gifted-pasteur-7ee42l bash scripts/make_models.sh
#   LIMIT=1 ... nur ein Modell (Test)
set -uo pipefail

# Nutzerentscheidung 11.11.2026: keine 3D-Modelle aus der öffentlichen KI (Qualität reicht nicht).
# Nur mit MAKE_MODELS=1 laufen die Modelle; sonst endet das Skript sofort, und der Pod-Startbefehl stoppt den Pod.
if [ "${MAKE_MODELS:-0}" != "1" ]; then
  echo "3D-Modelle abgeschaltet (MAKE_MODELS=1 schaltet sie ein)"
  echo "MODELLE_FERTIG"
  exit 0
fi

REPO="twitchg5n0e-jpg/character-gen"
BRANCH="${BRANCH:-main}"
LIMIT="${LIMIT:-0}"
AUTO_STOP="${AUTO_STOP:-1}"

stop_pod() {
  if [ "$AUTO_STOP" = "1" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then
    runpodctl stop pod "$RUNPOD_POD_ID" || runpodctl pod stop "$RUNPOD_POD_ID"
  fi
}
trap stop_pod EXIT
: "${GITHUB_TOKEN:?GITHUB_TOKEN ist nicht gesetzt}"

cd /root
apt-get update -qq && apt-get install -y -qq git git-lfs libgl1 libopengl0 libglib2.0-0 > /dev/null

# Nur Bilder, Skripte und Modelle holen
if [ ! -d character-gen ]; then
  git clone -q --filter=blob:none --sparse --branch "$BRANCH" \
    "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git" character-gen
fi
cd character-gen
git sparse-checkout set output scripts models
git config user.name "runpod"
git config user.email "runpod@users.noreply.github.com"

cd /root
[ -d Hunyuan3D-2 ] || git clone -q --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2
cd Hunyuan3D-2
pip install -q "diffusers==0.32.2" "transformers==4.48.3" "huggingface_hub<1.0" hf_transfer einops \
  opencv-python-headless trimesh pymeshlab pygltflib xatlas omegaconf accelerate rembg onnxruntime scipy 2>&1 | tail -3
pip install -q -e . 2>&1 | tail -3
cp /root/character-gen/scripts/make_models.py .

done_models=0
while [ "$LIMIT" = "0" ] || [ "$done_models" -lt "$LIMIT" ]; do
  out=$(python make_models.py /root/character-gen --limit 1 2>&1 | tee /dev/stderr) || { echo "Modell fehlgeschlagen"; exit 1; }
  echo "$out" | grep -q "^0 open model" && break
  cd /root/character-gen
  git add models
  git diff --cached --quiet || git commit -q -m "3D-Modelle $(date +%F_%H-%M)"
  for i in 1 2 3 4; do
    git pull -q --rebase -X theirs && git push -q origin "HEAD:$BRANCH" && break
    sleep $((2 ** i))
  done
  cd /root/Hunyuan3D-2
  done_models=$((done_models + 1))
done
echo "MODELLE_FERTIG"
