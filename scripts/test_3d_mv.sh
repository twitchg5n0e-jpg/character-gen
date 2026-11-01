#!/usr/bin/env bash
# Laeuft auf einer gemieteten GPU: ein 3D-Testmodell mit Hunyuan3D-2mv aus den vier Ansichten eines Sets,
# Ergebnis nach models_test/<Set>/ pushen, GPU stoppen.
#   SET=Human_Female_Body1_Stage1 BRANCH=claude/3d-mole-ny8opz bash scripts/test_3d_mv.sh
set -uo pipefail

REPO="twitchg5n0e-jpg/character-gen"
SET="${SET:-Human_Female_Body1_Stage1}"
BRANCH="${BRANCH:-claude/3d-mole-ny8opz}"
AUTO_STOP="${AUTO_STOP:-1}"

stop_pod() {
  if [ "$AUTO_STOP" = "1" ] && [ -n "${RUNPOD_POD_ID:-}" ]; then
    runpodctl stop pod "$RUNPOD_POD_ID" || runpodctl pod stop "$RUNPOD_POD_ID"
  fi
}
trap stop_pod EXIT
: "${GITHUB_TOKEN:?GITHUB_TOKEN ist nicht gesetzt}"

cd /root
apt-get update -qq && apt-get install -y -qq libgl1 libglib2.0-0 > /dev/null

# Nur dieses Set und die Skripte holen, nicht alle Bilder
git clone -q --filter=blob:none --sparse --branch "$BRANCH" \
  "https://x-access-token:${GITHUB_TOKEN}@github.com/${REPO}.git" character-gen
cd character-gen
git sparse-checkout set "output/$SET" scripts models_test
git config user.name "runpod"
git config user.email "runpod@users.noreply.github.com"
OUT="models_test/$SET"
mkdir -p "$OUT"

cd /root
git clone -q --depth 1 https://github.com/Tencent-Hunyuan/Hunyuan3D-2
cd Hunyuan3D-2
pip install -q diffusers transformers einops opencv-python-headless trimesh pymeshlab pygltflib xatlas omegaconf \
  accelerate rembg onnxruntime pybind11 ninja 2>&1 | tail -3
pip install -q -e . 2>&1 | tail -3
# Textur: zwei CUDA-Erweiterungen bauen; scheitert das, gibt es nur die Form
( cd hy3dgen/texgen/custom_rasterizer && python setup.py install ) > /root/build_rasterizer.log 2>&1 \
  || echo "custom_rasterizer konnte nicht gebaut werden"
( cd hy3dgen/texgen/differentiable_renderer && python setup.py install ) > /root/build_renderer.log 2>&1 \
  || echo "differentiable_renderer konnte nicht gebaut werden"

cp /root/character-gen/scripts/make_model_mv.py .
python make_model_mv.py "/root/character-gen/output/$SET" "/root/character-gen/$OUT" 2>&1 | tee /root/run.log
tail -40 /root/build_rasterizer.log > "/root/character-gen/$OUT/build_rasterizer.log"
tail -40 /root/build_renderer.log > "/root/character-gen/$OUT/build_renderer.log"
grep -v "it/s\]" /root/run.log | tail -200 > "/root/character-gen/$OUT/run.log"

cd /root/character-gen
git add "$OUT"
git commit -q -m "3D-Test Hunyuan3D-2mv: $SET"
for i in 1 2 3 4; do
  git pull -q --rebase && git push -q origin "HEAD:$BRANCH" && echo "TEST_FERTIG" && exit 0
  sleep $((2 ** i))
done
echo "Push fehlgeschlagen"
