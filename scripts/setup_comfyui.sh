#!/usr/bin/env bash
# Installiert ComfyUI + Qwen-Image-Modelle (einmalig, ~50 GB) und startet ComfyUI im Hintergrund.
# Liegt alles unter $COMFY_DIR (Standard /workspace/ComfyUI = RunPod-Volume), wird beim naechsten Pod nichts neu geladen.
set -euo pipefail

COMFY_DIR="${COMFY_DIR:-/workspace/ComfyUI}"
COMFY_PORT="${COMFY_PORT:-8188}"
HF="https://huggingface.co/Comfy-Org"

# Laeuft ComfyUI schon? Dann nichts tun.
if curl -sf "http://127.0.0.1:${COMFY_PORT}/system_stats" >/dev/null; then
  echo "ComfyUI laeuft bereits"
  exit 0
fi

if [ ! -d "$COMFY_DIR" ]; then
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI "$COMFY_DIR"
fi
pip install -q -r "$COMFY_DIR/requirements.txt"

# Dateinamen muessen zu scripts/comfyui/*.json passen.
download() {   # <Unterordner in models> <URL>
  local target="$COMFY_DIR/models/$1/$(basename "$2")"
  mkdir -p "$(dirname "$target")"
  if [ ! -s "$target" ]; then
    echo "lade $(basename "$2") ..."
    curl -fL --retry 5 -C - -o "$target.part" "$2"
    mv "$target.part" "$target"
  fi
}
download diffusion_models "$HF/Qwen-Image_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_2512_fp8_e4m3fn.safetensors"
download diffusion_models "$HF/Qwen-Image-Edit_ComfyUI/resolve/main/split_files/diffusion_models/qwen_image_edit_2509_fp8_e4m3fn.safetensors"
download text_encoders    "$HF/Qwen-Image_ComfyUI/resolve/main/split_files/text_encoders/qwen_2.5_vl_7b_fp8_scaled.safetensors"
download vae              "$HF/Qwen-Image_ComfyUI/resolve/main/split_files/vae/qwen_image_vae.safetensors"

nohup python "$COMFY_DIR/main.py" --listen 127.0.0.1 --port "$COMFY_PORT" > comfyui.log 2>&1 &
echo "ComfyUI startet (Log: comfyui.log)"
