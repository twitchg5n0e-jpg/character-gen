#!/usr/bin/env python3
"""Generate the character reference images with ComfyUI on the rented GPU, set by set.

Run from the repository root while ComfyUI is running (run_pod.sh starts it):
    python scripts/generate.py                                  all open sets
    python scripts/generate.py --limit 5                        the next five open sets
    python scripts/generate.py --set Human/Female/Body1/Stage1  only this set

Every set <Race>/<Gender>/<Body>/<Stage> becomes output/<Race>_<Gender>_<Body>_<Stage>/ with
front.png, hinten.png and links.png (1056x1584). rechts.png is mirrored from links.png by GitHub Actions.
A set is open while one of its three images is missing; the order comes from scripts/sets.txt.
The prompts come from scripts/prompts/<Race>/<Gender>_<Body>_<Stage>.md.

front of stage 1 is made from text (comfyui/text_to_image.json). Every other view is made with the edit model
from a reference (comfyui/edit_image.json): hinten and links from the set's own front, the fronts of stages 2 to 4
from the stage 1 front of the same appearance (Body1..Body4), so face and body stay the same.

links.png shows the character's left side, so the nose points to the left edge of the image (rechts.png is its mirror
image). It is made with comfyui/side_image.json: the edit model plus the Multiple-angles LoRA, which turns the camera
by 90 degrees instead of only turning the head. The direction is not reliable either, so a pose detector (YOLO pose from
ultralytics) finds nose and ears in every side view: a nose pointing right is mirrored. It also measures how far apart
the shoulders are; a side view that is turned towards the camera instead of an exact profile is made again with a new
seed (SIDE_TRIES attempts, the most exact one is kept). Without ultralytics the side view is saved as generated.

It can be stopped at any time with Ctrl+C and started again; every image is written to a temporary file first and
then renamed, broken images are deleted and made again. If ComfyUI is not running yet, it waits for it.

The two workflow files are ComfyUI graphs in API format. Text in them is replaced before sending:
"%PROMPT%", "%NEGATIVE%", "%IMAGE%" (uploaded reference image) and "%SEED%" (a number).
"""
from __future__ import annotations

import argparse
import io
import json
import os
import random
import re
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"
PROMPTS = SCRIPTS / "prompts"
WORKFLOWS = SCRIPTS / "comfyui"
SETS = SCRIPTS / "sets.txt"
# file name in output -> view name in the prompt files
VIEWS = {"front": "01_Front", "hinten": "02_Ruecken", "links": "03_Links"}
SIZE = (1056, 1584)   # Qwen-Image native 2:3 resolution
ACTIVE = None   # the ComfyUI connection, so Ctrl+C can cancel its running image
SIDE_TRIES = int(os.environ.get("SIDE_TRIES", "3"))   # attempts for an exact side profile
MAX_TWIST = float(os.environ.get("MAX_TWIST", "0.06"))   # shoulder distance / figure height still counted as profile
POSE = None   # the YOLO pose model, loaded on first use; False when ultralytics is missing


class ComfyUI:
    def __init__(self, url: str) -> None:
        self.url = url.rstrip("/")
        self.client = "character-gen-%d" % random.randrange(1 << 30)

    def wait(self, timeout: float = 1800) -> None:
        """Block until ComfyUI answers, so it can still be starting when the script begins."""
        said = False
        deadline = time.time() + timeout
        while True:
            try:
                requests.get(self.url + "/system_stats", timeout=5).raise_for_status()
                return
            except requests.RequestException:
                if time.time() > deadline:
                    sys.exit("ComfyUI at %s did not answer; see comfyui.log" % self.url)
                if not said:
                    print("waiting for ComfyUI at %s ..." % self.url)
                    said = True
                time.sleep(5)

    def stop(self) -> None:
        """Cancel the running image and clear the queue after Ctrl+C."""
        try:
            requests.post(self.url + "/interrupt", timeout=5)
            requests.post(self.url + "/queue", json={"clear": True}, timeout=5)
        except requests.RequestException:
            pass

    def upload(self, path: Path) -> str:
        """Put a reference image into ComfyUI's input folder."""
        with path.open("rb") as handle:
            reply = requests.post(self.url + "/upload/image", files={"image": (path.parent.name + ".png", handle, "image/png")},
                                  data={"overwrite": "true"}, timeout=60)
        reply.raise_for_status()
        return reply.json()["name"]

    def run(self, graph: dict) -> Image.Image:
        """Run a workflow and return its first image once it has finished."""
        reply = requests.post(self.url + "/prompt", json={"prompt": graph, "client_id": self.client}, timeout=60)
        if reply.status_code != 200:
            raise RuntimeError("ComfyUI rejected the workflow: %s" % reply.text[:2000])
        prompt_id = reply.json()["prompt_id"]
        while True:
            time.sleep(2)
            history = requests.get(self.url + "/history/" + prompt_id, timeout=60).json()
            if prompt_id not in history:
                continue
            entry = history[prompt_id]
            if entry.get("status", {}).get("status_str") == "error":
                raise RuntimeError("ComfyUI failed: %s" % json.dumps(entry["status"])[:2000])
            if entry.get("status", {}).get("completed"):
                break
        for output in entry.get("outputs", {}).values():
            for image in output.get("images", []):
                data = requests.get(self.url + "/view", params=image, timeout=300).content
                return Image.open(io.BytesIO(data)).convert("RGB")
        raise RuntimeError("ComfyUI finished without an image; does the workflow end in SaveImage?")


def fill(node, values: dict):
    """Replace the placeholders anywhere in the workflow graph."""
    if isinstance(node, dict):
        return {key: fill(value, values) for key, value in node.items()}
    if isinstance(node, list):
        return [fill(value, values) for value in node]
    if isinstance(node, str):
        if node in values and not isinstance(values[node], str):
            return values[node]   # "%SEED%" becomes a number
        for key, value in values.items():
            node = node.replace(key, str(value))
    return node


def prompt_file(race: str, gender: str, body: str, stage: str) -> Path:
    return PROMPTS / race / ("%s_%s_%s.md" % (gender, body, stage))


def read_prompts(parts: tuple[str, ...]) -> tuple[dict, str]:
    text = prompt_file(*parts).read_text(encoding="utf-8")
    blocks = dict(re.findall(r"## (\S+?)(?:\.jpg)?\n\n```text\n(.*?)\n```", text, re.S))
    return {name: blocks[view] for name, view in VIEWS.items()}, blocks["Negativ-Prompt"]


def folder_of(parts: tuple[str, ...]) -> Path:
    return OUTPUT / "_".join(parts)


def is_valid(path: Path) -> bool:
    """A finished image: a complete PNG of the right size."""
    if not path.is_file():
        return False
    try:
        with Image.open(path) as image:
            image.load()
            return image.format == "PNG" and image.size == SIZE
    except OSError:
        return False


def clean_folder(folder: Path) -> None:
    """Delete leftovers of a stopped run: temporary files and broken images."""
    if not folder.is_dir():
        return
    for leftover in folder.glob("*.part"):
        leftover.unlink()
    for name in VIEWS:
        path = folder / (name + ".png")
        if path.exists() and not is_valid(path):
            print("deleting broken image %s" % path.relative_to(ROOT))
            path.unlink()


def all_sets() -> list[tuple[str, ...]]:
    return [tuple(line.strip().split("/")) for line in SETS.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_open(parts: tuple[str, ...]) -> bool:
    folder = folder_of(parts)
    clean_folder(folder)
    return any(not (folder / (name + ".png")).is_file() for name in VIEWS)


def fit(image: Image.Image) -> Image.Image:
    """Scale and crop to exactly SIZE without distorting the figure."""
    if image.size == SIZE:
        return image
    scale = max(SIZE[0] / image.width, SIZE[1] / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (image.width - SIZE[0]) // 2, (image.height - SIZE[1]) // 2
    return image.crop((left, top, left + SIZE[0], top + SIZE[1]))


def side_view(image: Image.Image) -> tuple[str | None, float]:
    """Where the nose points ("left", "right" or None if unclear) and how far the figure is turned towards the camera.

    The turn is the horizontal shoulder distance divided by the figure height: close to 0 for an exact profile,
    about 0.2 for a front view.
    """
    global POSE
    if POSE is None:
        try:
            from ultralytics import YOLO
            POSE = YOLO(os.environ.get("POSE_MODEL", "yolo11n-pose.pt"))   # downloaded on first use
        except Exception as error:   # missing package or weights: keep generating without the check
            print("pose check unavailable (%s); side views are saved as generated" % error)
            POSE = False
    if not POSE:
        return None, 0.0
    result = POSE(image, verbose=False)[0]
    if result.keypoints is None or result.boxes is None or len(result.boxes) == 0:
        return None, 0.0
    best = int(result.boxes.conf.argmax())
    xy = result.keypoints.xy[best].tolist()
    conf = result.keypoints.conf[best].tolist()
    seen = [c > 0.3 for c in conf]
    # COCO keypoints: 0 nose, 1/2 eyes, 3/4 ears, 5/6 shoulders
    head = [xy[i][0] for i in (3, 4) if seen[i]] or [xy[i][0] for i in (1, 2) if seen[i]]
    direction = None
    if seen[0] and head:
        direction = "right" if xy[0][0] > sum(head) / len(head) else "left"
    height = float(result.boxes.xywh[best][3])
    twist = abs(xy[5][0] - xy[6][0]) / height if seen[5] and seen[6] and height else 0.0
    return direction, twist


def save(image: Image.Image, target: Path) -> None:
    """Write next to the target and rename, so a stop never leaves half an image."""
    part = target.with_name(target.name + ".part")
    fit(image).save(part, format="PNG", optimize=True)
    os.replace(part, target)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--comfy", default=os.environ.get("COMFY_URL", "http://127.0.0.1:8188"), help="ComfyUI address")
    parser.add_argument("--limit", type=int, default=int(os.environ.get("LIMIT", "0")),
                        help="stop after this many sets (0 = all)")
    parser.add_argument("--set", default=os.environ.get("SET") or None,
                        help="only this set, e.g. Human/Female/Body1/Stage1")
    args = parser.parse_args()

    text_to_image = json.loads((WORKFLOWS / "text_to_image.json").read_text(encoding="utf-8"))
    edit_image = json.loads((WORKFLOWS / "edit_image.json").read_text(encoding="utf-8"))
    side_image = json.loads((WORKFLOWS / "side_image.json").read_text(encoding="utf-8"))
    global ACTIVE
    comfy = ACTIVE = ComfyUI(args.comfy)

    if args.set:
        wanted = tuple(args.set.replace("\\", "/").strip("/").split("/"))
        if len(wanted) != 4 or not prompt_file(*wanted).is_file():
            sys.exit("unknown set %s; expected <Race>/<Gender>/<Body>/<Stage>, e.g. Human/Female/Body1/Stage1" % args.set)
        todo = [wanted] if is_open(wanted) else []
        if not todo:
            print("%s is already complete; delete its images to make them again" % args.set)
    else:
        todo = [parts for parts in all_sets() if is_open(parts)]
    if args.limit:
        todo = todo[:args.limit]
    print("%d open set(s)" % len(todo))
    if not todo:
        return
    comfy.wait()

    for number, parts in enumerate(todo, 1):
        name = "/".join(parts)
        folder = folder_of(parts)
        folder.mkdir(parents=True, exist_ok=True)
        prompts, negative = read_prompts(parts)
        stage1_front = folder_of(parts[:3] + ("Stage1",)) / "front.png"
        for view in VIEWS:
            target = folder / (view + ".png")
            if target.is_file():
                continue
            if view == "front":
                reference = stage1_front if parts[3] != "Stage1" and stage1_front.is_file() else None
            else:
                reference = folder / "front.png"
            started = time.time()

            def make(edit: dict = edit_image) -> Image.Image:
                values = {"%PROMPT%": prompts[view], "%NEGATIVE%": negative, "%SEED%": random.randrange(1 << 31)}
                while True:
                    try:
                        if reference:
                            values["%IMAGE%"] = comfy.upload(reference)
                            return comfy.run(fill(edit, values))
                        return comfy.run(fill(text_to_image, values))
                    except requests.RequestException:
                        comfy.wait()   # ComfyUI was restarted: wait for it and make this image again

            note = ""
            if view == "links":
                best = None
                for attempt in range(1, SIDE_TRIES + 1):
                    candidate = make(side_image)
                    direction, twist = side_view(candidate)
                    print("    links attempt %d: nose %s, turn %.3f" % (attempt, direction or "unclear", twist))
                    if best is None or twist < best[2]:
                        best = (candidate, direction, twist)
                    if POSE is False or (twist <= MAX_TWIST and direction):
                        break
                image, direction, twist = best
                if direction == "right":
                    image = ImageOps.mirror(image)   # links shows the left side: the nose points to the left edge
                note = " (nose was %s, turn %.3f)" % (direction or "unclear", twist)
            else:
                image = make()
            save(image, target)
            print("[%d/%d] %s/%s.png in %.0f s%s" % (number, len(todo), name, view, time.time() - started, note))
    print("done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if ACTIVE:
            ACTIVE.stop()
        sys.exit("stopped; finished images are saved, the next run continues where this one stopped")
