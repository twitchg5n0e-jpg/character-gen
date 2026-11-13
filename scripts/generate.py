#!/usr/bin/env python3
"""Generate the character reference images with ComfyUI on the rented GPU, set by set.

Run from the repository root while ComfyUI is running (run_pod.sh starts it):
    python scripts/generate.py                                  all open sets
    python scripts/generate.py --limit 5                        the next five open sets
    python scripts/generate.py --set Human/Female/Body1/Stage1  only this set

Every set <Race>/<Gender>/<Body>/<Stage> becomes output/<Race>_<Gender>_<Body>_<Stage>/ with
front.png, hinten.png and links.png (1056x1584). rechts.png is mirrored from links.png by GitHub Actions.
A set is open while one of its three images is missing; the order comes from scripts/sets.txt.
After the races come the loot items (scripts/sets_items.txt: Items/Loot/<Id>/Icon -> one square icon.png, made from
text) and the mobs (scripts/sets_mobs.txt: Mobs/<Family>/<id>/Stage1 -> front, hinten, links as square images, made
like a race's stage 1); scripts/make_mob_item_prompts.py writes both lists and their prompts.
The prompts come from scripts/prompts/<Race>/<Gender>_<Body>_<Stage>.md.

front of stage 1 is made from text (comfyui/text_to_image.json). Every other view is made with the edit model
from a reference (comfyui/edit_image.json): hinten and links from the set's own front, the fronts of stages 2 to 4
from the stage 1 front of the same appearance (Body1..Body4), so face and body stay the same.

links.png shows the character's left side, so the nose points to the left edge of the image (rechts.png is its mirror
image). It is made with comfyui/side_image.json: the edit model plus the Multiple-angles LoRA, which turns the camera
by 90 degrees instead of only turning the head. The direction is not reliable either, so a pose detector (YOLO pose from
ultralytics) finds nose and ears in every side view: a nose pointing right is mirrored. It also measures how far apart
the shoulders are; a side view that is turned towards the camera instead of an exact profile is made again with a new
seed (SIDE_TRIES attempts, the most exact one is kept). hinten.png is made the same way with comfyui/back_image.json (camera turned by 180 degrees), meant to keep the colors of
the front better than the plain edit model. A back view in which the detector sees nose and both eyes
is really a front view and is made again. Without ultralytics all views are saved as generated.

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
from PIL import Image, ImageChops, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
OUTPUT = ROOT / "output"
PROMPTS = SCRIPTS / "prompts"
WORKFLOWS = SCRIPTS / "comfyui"
SETS = SCRIPTS / "sets.txt"   # nur Body1 (Basismodell); alle 4 Varianten: sets_alle.txt
# file name in output -> view name in the prompt files
VIEWS = {"front": "01_Front", "hinten": "02_Ruecken", "links": "03_Links"}
SIZE = (1056, 1584)   # Qwen-Image native 2:3 resolution
# After the races (sets.txt) come the loot items (one square icon each) and the mobs (front, hinten, links in a
# square, so long animals fit in the side view); see scripts/make_mob_item_prompts.py.
EXTRA_SETS = ("sets_items.txt", "sets_mobs.txt")
ITEM_VIEWS = {"icon": "01_Icon"}
ITEM_SIZE = (1024, 1024)
MOB_SIZE = (1328, 1328)   # Qwen-Image native 1:1 resolution


def views_of(parts: tuple[str, ...]) -> dict:
    return ITEM_VIEWS if parts[0] == "Items" else VIEWS


def size_of(parts: tuple[str, ...]) -> tuple[int, int]:
    return {"Items": ITEM_SIZE, "Mobs": MOB_SIZE}.get(parts[0], SIZE)


def sized(graph: dict, size: tuple[int, int]) -> dict:
    """The workflow with its empty latent image set to this size."""
    graph = json.loads(json.dumps(graph))
    for node in graph.values():
        if node.get("class_type") == "EmptySD3LatentImage":
            node["inputs"]["width"], node["inputs"]["height"] = size
    return graph
ACTIVE = None   # the ComfyUI connection, so Ctrl+C can cancel its running image
SIDE_TRIES = int(os.environ.get("SIDE_TRIES", "4"))   # attempts for an exact side profile
MAX_TWIST = float(os.environ.get("MAX_TWIST", "0.06"))   # shoulder distance / figure height still counted as profile
POSE = None   # the YOLO pose model, loaded on first use; False when ultralytics is missing
# Races whose stage 1 front comes out with the head turned to the side when made from text (long animal snouts):
# their stage 1 front is made by editing the finished Human front of the same gender and body, which keeps its
# straight front pose.
POSE_FROM_HUMAN = set(os.environ.get("POSE_FROM_HUMAN", "Lizardfolk").split(",")) - {""}
FROM_HUMAN = ("Edit this image: turn the person into the character described below. Keep exactly the same straight "
              "front-facing A-pose, the same camera, framing, size in the picture and the plain light gray background; "
              "the new head faces the camera straight on like the human head did, not turned to the side. Remove the "
              "clothing; the body covering described below replaces it. ")
KEEP_FRONT = ("Edit this image: keep exactly the same front view, pose, camera, framing and plain light gray background; the "
              "character still faces the camera with its face and chest, it is not turned around and not seen from behind. "
              "Change only what the description below says about this stage. ")


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
    return {name: blocks[view] for name, view in views_of(parts).items()}, blocks["Negativ-Prompt"]


def folder_of(parts: tuple[str, ...]) -> Path:
    return OUTPUT / "_".join(parts)


def is_valid(path: Path, size: tuple[int, int] = SIZE) -> bool:
    """A finished image: a complete PNG of the right size."""
    if not path.is_file():
        return False
    try:
        with Image.open(path) as image:
            image.load()
            return image.format == "PNG" and image.size == size
    except OSError:
        return False


def clean_folder(folder: Path, parts: tuple[str, ...]) -> None:
    """Delete leftovers of a stopped run: temporary files and broken images."""
    if not folder.is_dir():
        return
    for leftover in folder.glob("*.part"):
        leftover.unlink()
    for name in views_of(parts):
        path = folder / (name + ".png")
        if path.exists() and not is_valid(path, size_of(parts)):
            print("deleting broken image %s" % path.relative_to(ROOT))
            path.unlink()


def all_sets() -> list[tuple[str, ...]]:
    files = [SETS] + [SCRIPTS / name for name in EXTRA_SETS if (SCRIPTS / name).is_file()]
    return [tuple(line.strip().split("/")) for path in files
            for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def is_open(parts: tuple[str, ...]) -> bool:
    folder = folder_of(parts)
    clean_folder(folder, parts)
    return any(not (folder / (name + ".png")).is_file() for name in views_of(parts))


def fit(image: Image.Image, size: tuple[int, int] = SIZE) -> Image.Image:
    """Scale and crop to exactly this size without distorting the figure."""
    SIZE = size
    if image.size == SIZE:
        return image
    scale = max(SIZE[0] / image.width, SIZE[1] / image.height)
    image = image.resize((round(image.width * scale), round(image.height * scale)), Image.LANCZOS)
    left, top = (image.width - SIZE[0]) // 2, (image.height - SIZE[1]) // 2
    return image.crop((left, top, left + SIZE[0], top + SIZE[1]))


def keypoints(image: Image.Image) -> tuple[list, list, float] | None:
    """COCO keypoints (xy, confidence) and box height of the main figure, or None without detector or figure."""
    global POSE
    if POSE is None:
        try:
            from ultralytics import YOLO
            POSE = YOLO(os.environ.get("POSE_MODEL", "yolo11n-pose.pt"))   # downloaded on first use
        except Exception as error:   # missing package or weights: keep generating without the check
            print("pose check unavailable (%s); views are saved as generated" % error)
            POSE = False
    if not POSE:
        return None
    result = POSE(image, verbose=False)[0]
    if result.keypoints is None or result.boxes is None or len(result.boxes) == 0:
        return None
    best = int(result.boxes.conf.argmax())
    return result.keypoints.xy[best].tolist(), result.keypoints.conf[best].tolist(), float(result.boxes.xywh[best][3])


def face_visible(image: Image.Image) -> bool:
    """True when nose and both eyes are clearly seen, i.e. a "back view" that actually shows the front."""
    found = keypoints(image)
    return found is not None and all(found[1][i] > 0.3 for i in (0, 1, 2))   # 0.3: animal faces score lower


def side_view(image: Image.Image) -> tuple[str | None, float]:
    """Where the nose points ("left", "right" or None if unclear) and how far the figure is turned towards the camera.

    The turn is the horizontal shoulder distance divided by the figure height: close to 0 for an exact profile,
    about 0.2 for a front view.
    """
    found = keypoints(image)
    if found is None:
        return None, 0.0
    xy, conf, height = found
    seen = [c > 0.3 for c in conf]
    # COCO keypoints: 0 nose, 1/2 eyes, 3/4 ears, 5/6 shoulders
    head = [xy[i][0] for i in (3, 4) if seen[i]] or [xy[i][0] for i in (1, 2) if seen[i]]
    direction = None
    if seen[0] and head:
        direction = "right" if xy[0][0] > sum(head) / len(head) else "left"
    twist = abs(xy[5][0] - xy[6][0]) / height if seen[5] and seen[6] and height else 0.0
    return direction, twist


MIN_SYMMETRY = float(os.environ.get("MIN_SYMMETRY", "0.45"))   # mob front/back: minimum straightness() of a head-on view


def symmetry(image: Image.Image) -> float:
    """How mirror-symmetric the figure's outline is (1 = perfectly, ~0.3 = three-quarter view).

    The background is a plain light gray, so the figure is everything that differs from the corner color; its outline
    is compared with its own mirror image (intersection over union), centred on its bounding box.
    """
    small = image.convert("RGB").resize((256, 256))
    background = Image.new("RGB", small.size, small.getpixel((2, 2)))
    mask = ImageChops.difference(small, background).convert("L").point(lambda v: 255 if v > 28 else 0)
    mask = mask.filter(ImageFilter.MedianFilter(5))
    box = mask.getbbox()
    if not box:
        return 0.0
    mask = mask.crop((box[0], 0, box[2], small.height))
    both = ImageChops.multiply(mask, ImageOps.mirror(mask)).histogram()[255]
    either = ImageChops.lighter(mask, ImageOps.mirror(mask)).histogram()[255]
    return both / either if either else 0.0


def straightness(image: Image.Image) -> float:
    """How straight-on a front or back view is: 0.4 x outline symmetry + 0.6 x content symmetry.

    The outline alone is fooled by bulky animals seen at an angle; comparing the picture itself with its mirror
    image (inside the figure's bounding box) catches a face or body that sits off-centre."""
    small = image.convert("RGB").resize((256, 256))
    background = Image.new("RGB", small.size, small.getpixel((2, 2)))
    mask = ImageChops.difference(small, background).convert("L").point(lambda v: 255 if v > 28 else 0)
    box = mask.filter(ImageFilter.MedianFilter(5)).getbbox()
    if not box:
        return 0.0
    gray = small.convert("L").crop(box)
    difference = ImageChops.difference(gray, ImageOps.mirror(gray)).histogram()
    mean = sum(value * count for value, count in enumerate(difference)) / max(1, sum(difference))
    content = max(0.0, 1 - mean / 255 * 4)
    return 0.4 * symmetry(image) + 0.6 * content


def fix_mob_back(comfy, back_image: dict, folder: Path, prompt: str, negative: str, size: tuple[int, int]) -> None:
    """A strict head-on front often turns into a side view instead of a back view. If hinten.png is not symmetric,
    turn the finished side profile by 90 degrees both ways and keep the symmetric result that looks least like the
    front (the back, not the front again)."""
    back, front, side = folder / "hinten.png", folder / "front.png", folder / "links.png"
    if not (back.is_file() and front.is_file() and side.is_file()):
        return
    old = Image.open(back)
    if symmetry(old) >= 0.45 and straightness(old) >= MIN_SYMMETRY:
        return
    def look(image: Image.Image) -> list:
        return list(image.convert("L").resize((48, 48)).getdata())
    front_look = look(Image.open(front))
    best = None
    for turn in ("将镜头向左旋转90度 (rotate the camera 90 degrees to the left)",
                 "将镜头向右旋转90度 (rotate the camera 90 degrees to the right)"):
        graph = json.loads(json.dumps(back_image))
        for node in graph.values():
            if node.get("class_type") == "TextEncodeQwenImageEditPlus" and "%PROMPT%" in str(node["inputs"].get("prompt")):
                node["inputs"]["prompt"] = (turn + ". The same creature as in the image, now seen exactly from behind: its rump "
                                            "and tail face the camera, its head points away and its face is not visible, "
                                            "perfectly mirror-symmetrical left and right. Same body, same colors, same plain "
                                            "light gray studio background. %PROMPT%")
        try:
            values = {"%PROMPT%": prompt, "%NEGATIVE%": negative, "%SEED%": random.randrange(1 << 31),
                      "%IMAGE%": comfy.upload(side)}
            candidate = comfy.run(fill(sized(graph, size), values))
        except (requests.RequestException, RuntimeError) as error:
            print("    back turn failed: %s" % error)
            continue
        score = straightness(candidate)
        difference = sum(abs(a - b) for a, b in zip(look(candidate), front_look)) / len(front_look)
        print("    back turn %s: straightness %.2f, difference to front %.1f" % (turn[:8], score, difference))
        if score >= MIN_SYMMETRY and (best is None or difference > best[1]):
            best = (candidate, difference)
    if best is not None:
        save(best[0], back, size)
        print("    hinten.png replaced by a turned side view")


def save(image: Image.Image, target: Path, size: tuple[int, int] = SIZE) -> None:
    """Write next to the target and rename, so a stop never leaves half an image."""
    part = target.with_name(target.name + ".part")
    fit(image, size).save(part, format="PNG", optimize=True)
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
    back_image = json.loads((WORKFLOWS / "back_image.json").read_text(encoding="utf-8"))
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
        size = size_of(parts)
        for view in views_of(parts):
            target = folder / (view + ".png")
            if target.is_file():
                continue
            prompt = prompts[view]
            human_front = OUTPUT / ("Human_%s_%s_Stage1" % (parts[1], parts[2])) / "front.png"
            # all stages: editing the lizard's own stage 1 front for stages 2-4 kept turning it into a back view
            from_human = view == "front" and parts[0] in POSE_FROM_HUMAN and human_front.is_file()
            if from_human:
                reference, prompt = human_front, FROM_HUMAN + prompt
            elif view == "front" and parts[0] in POSE_FROM_HUMAN and parts[3] != "Stage1" and stage1_front.is_file():
                reference, prompt = stage1_front, KEEP_FRONT + prompt   # the edit model tends to turn them around
            elif view in ("front", "icon"):
                reference = stage1_front if parts[3] != "Stage1" and stage1_front.is_file() else None
            else:
                reference = folder / "front.png"
            started = time.time()

            def make(edit: dict = edit_image) -> Image.Image:
                values = {"%PROMPT%": prompt, "%NEGATIVE%": negative, "%SEED%": random.randrange(1 << 31)}
                while True:
                    try:
                        if reference:
                            values["%IMAGE%"] = comfy.upload(reference)
                            return comfy.run(fill(sized(edit, size), values))
                        return comfy.run(fill(sized(text_to_image, size), values))
                    except requests.RequestException:
                        comfy.wait()   # ComfyUI was restarted: wait for it and make this image again

            note = ""
            if view == "links":
                best = None
                for attempt in range(1, SIDE_TRIES + 1):
                    candidate = make(side_image)
                    direction, twist = side_view(candidate)
                    print("    links attempt %d: nose %s, turn %.3f" % (attempt, direction or "unclear", twist))
                    # a known direction beats a slightly more exact profile: a wrong direction is the worse error
                    if best is None or (direction is None, twist) < (best[1] is None, best[2]):
                        best = (candidate, direction, twist)
                    if POSE is False or (twist <= MAX_TWIST and direction):
                        break
                    # animal heads (dragon, lizard, bird) never get a clear nose: two tries are enough there
                    if direction is None and twist <= MAX_TWIST and (attempt >= 2 or parts[0] == "Mobs"):
                        break
                image, direction, twist = best
                if direction != "left":
                    # unclear (e.g. animal heads the detector does not know): the Multiple-angles LoRA mostly
                    # puts the nose to the right, so mirror, and leave a note so the set gets checked by eye
                    image = ImageOps.mirror(image)   # links shows the left side: the nose points to the left edge
                if direction is None:
                    (folder / "links_richtung_pruefen.txt").write_text(
                        "Blickrichtung von links.png wurde nicht erkannt; bitte ansehen (Nase muss nach links zeigen).\n",
                        encoding="utf-8")
                note = " (nose was %s, turn %.3f)" % (direction or "unclear", twist)
            elif parts[0] == "Mobs" and view in ("front", "hinten"):
                # animals tend to come out as a three-quarter view; a true front/back view is mirror-symmetric
                best = None
                tries = 2 if view == "front" else 3   # a front that stays oblique is turned straight below (~5.5 min per turn)
                for attempt in range(1, tries + 1):
                    candidate = make(back_image) if view == "hinten" else make()
                    score = straightness(candidate)
                    print("    %s attempt %d: straightness %.2f (outline %.2f)" % (view, attempt, score, symmetry(candidate)))
                    if best is None or score > best[1]:
                        best = (candidate, score)
                    if score >= MIN_SYMMETRY:
                        break
                    if view == "hinten" and symmetry(candidate) < 0.45:
                        break   # clearly a side view: fix_mob_back() turns the profile into the back view later
                if view == "front" and best[1] < MIN_SYMMETRY:
                    # still a three-quarter view: let the Multiple-angles LoRA turn the camera by 30 degrees either way
                    # and keep whichever result is the most symmetric (the back view is made from this front)
                    rescue = folder / "front_kandidat.png"
                    save(best[0], rescue, size)
                    for turn in ("将镜头向左旋转30度 (rotate the camera 30 degrees to the left)",
                                 "将镜头向右旋转30度 (rotate the camera 30 degrees to the right)"):
                        graph = json.loads(json.dumps(side_image))
                        for node in graph.values():
                            if node.get("class_type") == "TextEncodeQwenImageEditPlus" and "%PROMPT%" in str(node["inputs"].get("prompt")):
                                node["inputs"]["prompt"] = (turn + ". The same creature as in the image, now seen exactly head-on from "
                                                            "the front, perfectly mirror-symmetrical left and right. Same body, same "
                                                            "colors, same plain light gray studio background. %PROMPT%")
                        try:
                            values = {"%PROMPT%": prompt, "%NEGATIVE%": negative, "%SEED%": random.randrange(1 << 31),
                                      "%IMAGE%": comfy.upload(rescue)}
                            candidate = comfy.run(fill(sized(graph, size), values))
                        except (requests.RequestException, RuntimeError) as error:
                            print("    front turn failed: %s" % error)
                            continue
                        score = straightness(candidate)
                        print("    front turn %s: straightness %.2f" % (turn[:8], score))
                        if score > best[1]:
                            best = (candidate, score)
                        if best[1] >= 0.65:
                            break   # straight enough, no need to try the other direction
                    rescue.unlink(missing_ok=True)
                image = best[0]
                note = " (straightness %.2f)" % best[1]
            elif view == "hinten":
                for attempt in range(1, SIDE_TRIES + 1):
                    image = make(back_image)   # the Multiple-angles LoRA turns the camera by 180 degrees
                    if not face_visible(image):
                        break
                    print("    hinten attempt %d: face visible, not a back view" % attempt)
            else:
                # the check only means something when the detector sees the face of the stage 1 front at all
                # (animal heads such as dragons are not recognised, then every try would fail)
                check_face = view == "front" and reference and not from_human and POSE is not False and face_visible(Image.open(reference).convert("RGB"))
                for attempt in range(1, SIDE_TRIES + 1):
                    image = make()
                    # the edit model sometimes turns a stage 2-4 front into a back view
                    if not check_face or face_visible(image):
                        break
                    print("    front attempt %d: no face visible, not a front view" % attempt)
            save(image, target, size)
            print("[%d/%d] %s/%s.png in %.0f s%s" % (number, len(todo), name, view, time.time() - started, note))
            if parts[0] == "Mobs" and view == "links":
                fix_mob_back(comfy, back_image, folder, prompt, negative, size)
    print("done")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        if ACTIVE:
            ACTIVE.stop()
        sys.exit("stopped; finished images are saved, the next run continues where this one stopped")
