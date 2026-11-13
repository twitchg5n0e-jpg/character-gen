#!/usr/bin/env python3
"""Prompts for the mobs (4 views like the races) and the loot items (one icon each).

    python scripts/make_mob_item_prompts.py

Reads scripts/data/elyndra_mobs_v0.1.json (copy of Elyndra/Data/Source/Mobs/elyndra_mobs_v0.1.json) and writes
    scripts/prompts/Items/Loot_<Id>_Icon.md     + scripts/sets_items.txt   (Items/Loot/<Id>/Icon)
    scripts/prompts/Mobs/<Family>_<id>_Stage1.md + scripts/sets_mobs.txt   (Mobs/<Family>/<id>/Stage1)
scripts/generate.py works through scripts/sets.txt first, then sets_items.txt, then sets_mobs.txt.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "scripts" / "data" / "elyndra_mobs_v0.1.json"
PROMPTS = ROOT / "scripts" / "prompts"

BODY = {
    "Säugetier": ("a wild fantasy mammal", "standing naturally on all its legs in a calm neutral stance"),
    "Insekt": ("a giant fantasy insect or arthropod", "standing on all its legs in a calm neutral stance, wings folded if it has any"),
    "Humanoid": ("a humanoid fantasy creature or person", "standing upright in a relaxed A-pose, arms slightly away from the body"),
    "Reptil": ("a fantasy reptile", "standing on its legs in a calm neutral stance, tail hanging calmly behind the body"),
    "Vogel": ("a fantasy bird", "standing on its feet, wings folded against the body"),
    "Untoter": ("an undead fantasy creature", "standing upright in a calm neutral stance"),
    "Geist": ("a ghostly fantasy spirit with a clearly readable body shape", "hovering upright in a calm neutral stance"),
    "Riese": ("a fantasy giant", "standing upright in a relaxed A-pose, arms slightly away from the body"),
    "Elementar": ("a fantasy elemental creature made of its element", "standing upright in a calm neutral stance"),
    "Wassertier": ("a fantasy water creature", "shown whole in a calm neutral pose as if floating, fins relaxed"),
    "Drache": ("a fantasy dragon", "standing on all four legs, wings folded against the body, tail hanging calmly behind"),
    "Pflanze": ("a living fantasy plant creature", "standing upright in a calm neutral stance"),
    "Amphibie": ("a fantasy amphibian", "sitting or standing calmly on its legs"),
    "Dämon": ("a fantasy demon", "standing upright in a relaxed A-pose"),
    "Schleim": ("a fantasy slime creature", "resting calmly on the ground, a single compact body"),
    "Fee": ("a small fantasy fairy creature", "hovering upright in a calm neutral pose, wings half open behind the body"),
}
STYLE = ("High-quality realistic creature render for a fantasy RPG, in the style of a modern AAA game made in Unreal Engine 5: "
         "lifelike materials, fine surface detail, sharp focus, high detail; not plastic, not clay, not a toy, not a cartoon. "
         "One single creature, the whole body fully in frame from the highest point to the feet or lowest point, centered, "
         "with a little space on every side. No rider, no saddle, no harness, no chains, no text. "
         "Isolated on a plain, seamless, uniform light gray background: no floor, no horizon line, no gradient, no vignette, "
         "no cast shadow and no props, so the creature can be cut out cleanly. Soft even diffuse studio lighting, no rim light. "
         "Camera at the creature's mid height with a long lens, almost no perspective distortion. Square format. "
         "One single image from one single camera angle; not a character sheet, not a turnaround, not a collage.")
# pose per body plan (anatomy comes from scripts/data/mob_descriptions_en.json, written per mob)
POSE = {
    "quadruped": "It stands still on all four legs in a calm neutral stance: all four legs straight, evenly spaced and fully visible, "
                 "head held level and looking straight ahead, tail hanging calmly.",
    "biped": "It stands upright in a relaxed A-pose: arms slightly away from the body, legs straight, feet slightly apart, "
             "looking straight ahead.",
    "bird": "It stands upright on both feet, wings folded neatly against the body, head held level and looking straight ahead.",
    "flyer": "It hovers motionless in mid-air in the middle of the image, body level, wings spread symmetrically and fully visible.",
    "snake": "It lies flat on its belly, fully stretched out in one straight line like a rope laid out straight, the head resting "
             "low just above the ground at the front end and the tail tip straight behind; no coils, no loops, no rings, the body "
             "never crosses or touches itself and is not raised, so every part of it is clearly separate.",
    "insect": "It stands still on all six legs, body level, the legs spread evenly and fully visible, wings folded on the back if it has any.",
    "spider": "It stands still on all eight legs, body level, the legs spread evenly and symmetrically and fully visible.",
    "crawler": "It lies fully stretched out flat in one long, almost straight line, body level, no coils or loops, the body never "
               "crosses or touches itself, all its legs (if it has any) spread evenly and visible.",
    "fish": "It floats horizontally in a calm neutral pose, body straight and level, all fins relaxed and spread.",
    "serpent_water": "It floats horizontally, fully stretched out in one long, almost straight line with only a very slight gentle "
                     "curve, no coils or loops, the body never crosses itself, head raised slightly and looking straight ahead.",
    "octopus": "It floats upright, the mantle or bell at the top, the tentacles hanging down loosely and evenly spread.",
    "slime": "It rests calmly as one single compact blob.",
    "ghost": "It floats upright in a calm neutral pose, arms slightly away from the body, the lower body fading out.",
    "plant": "It stands upright in a calm neutral stance, limbs slightly away from the body.",
    "elemental": "It stands upright in a calm neutral stance, arms slightly away from the body.",
    "dragon": "It stands still on all its legs in a calm neutral stance, wings folded against the body, tail lying calmly behind it, "
              "head held level and looking straight ahead.",
    "other": "It rests in a calm neutral pose, the whole body clearly readable.",
}
UPRIGHT = {"biped", "ghost", "plant", "elemental", "octopus", "slime"}
FRONT_UP = ("Strict front view, like an orthographic front elevation for 3D modeling: the creature faces the camera squarely, "
            "face, chest and both shoulders straight towards the viewer, perfectly mirror-symmetrical left and right, both arms "
            "and both legs equally visible; not a three-quarter view, not turned to the side.")
FRONT_LONG = ("Strict head-on front view, like an orthographic front elevation for 3D modeling: the camera looks straight along the "
              "creature's spine from directly in front, the face looks straight into the camera with both eyes equally visible, "
              "the left and right front legs stand side by side and equally visible, the rest of the body is hidden straight behind "
              "the chest, perfectly mirror-symmetrical left and right; not a three-quarter view, the flank of the body is not visible.")
FRONT_SNAKE = ("Front view seen from slightly above: the snake points straight at the camera, its head at the front nearest to the "
               "viewer and looking straight into the camera, and its straight body extends straight away from the viewer behind the "
               "head so its whole length is visible, perfectly mirror-symmetrical left and right; not turned to the side.")
# said first as well: at the end of a long prompt the model still drifts into a three-quarter view
FRONT_LEAD = ("Exact head-on front view, the creature faces the camera squarely and is perfectly mirror-symmetrical "
              "left and right, no flank visible. ")
BACK = ("Strict back view, like an orthographic rear elevation for 3D modeling: the camera is directly behind the creature at mid "
        "height and looks straight along its spine, the creature faces away from the viewer, its head points away from the camera "
        "and its face is not visible, perfectly mirror-symmetrical left and right; not a three-quarter view. Same creature, same pose, "
        "same colors.")
SIDE = ("Exact 90 degree side profile for a 3D modeling reference: the creature has turned to its own left, so its head points "
        "to the right edge of the image and its tail or back end to the left edge. The whole body is seen exactly from the side, "
        "the full length from head to tail fully in frame, neither the front nor the back faces the camera. Same creature, same pose, same colors.")
NEG_MOB = ("multiple creatures, extra heads, extra limbs, missing limbs, fused legs, deformed anatomy, rider, saddle, text, watermark, "
           "logo, frame, border, collage, character sheet, turnaround sheet, multiple views, split image, grid, cropped, cut off, "
           "partially out of frame, visible floor, ground, horizon line, floor shadow, cast shadow, vignette, gradient background, "
           "colored background, scenery, landscape, forest, water surface, trees, props, dramatic lighting, rim light, motion blur, "
           "action pose, attacking, running, jumping, open jaws roaring, three-quarter view, angled view, diagonal view, fisheye, perspective distortion, cartoon, anime, stylized, "
           "toy, plastic, clay, low detail, blurry")
MOBDESC_FILE = ROOT / "scripts" / "data" / "mob_descriptions_en.json"
MOBDESC = json.loads(MOBDESC_FILE.read_text(encoding="utf-8")) if MOBDESC_FILE.is_file() else {}
ITEM = ("Game inventory icon for a fantasy RPG showing exactly one object: {desc} (item „{name}“). The object itself, "
        "realistic and finely detailed, true to its real material and shape, with a clear readable silhouette, centered and "
        "filling about two thirds of the square image, seen slightly from above at a three-quarter angle. Isolated on a plain, "
        "seamless, uniform light gray background: no shadow, no table, no hands, no frame, no text, no label. Soft even "
        "studio lighting.")
NEG_ITEM = ("text, letters, label, watermark, logo, frame, border, app icon, rounded square, tile, badge, dark background, "
            "black background, hands, person, creature, whole animal, living animal, table, surface, scene, landscape, multiple different objects, "
            "collage, grid, cast shadow, vignette, gradient background, colored background, cartoon, flat vector, anime, "
            "blurry, low detail, cropped, cut off")
NEG_STICKS = ", bundle of sticks, twigs, firewood, tied bundle, rope, twine"
WOODY = ("wood", "log", "bark", "root", "stalk", "straw", "reed", "plank", "bamboo", "twine", "cord", "fiber", "vine")
PART = (" eye", "eyeball", " wing", " tail", " beak", " ear", "claw", "talon", "stinger", "tentacle", "pincer", " mane", " toe", " paw")
PART_TEXT = ", only this single severed body part lying alone with no animal attached"
NEG_PART = ", whole animal body, head, legs, wings attached to a body"
DESC = json.loads((ROOT / "scripts" / "data" / "item_descriptions_en.json").read_text(encoding="utf-8"))


def block(title: str, text: str) -> str:
    return "## %s\n\n```text\n%s\n```\n\n" % (title, text)


def words(identifier: str) -> str:
    return re.sub(r"(?<=[a-z])(?=[A-Z])", " ", identifier).strip()


def main() -> None:
    data = json.loads(DATA.read_text(encoding="utf-8"))
    (PROMPTS / "Items").mkdir(parents=True, exist_ok=True)
    (PROMPTS / "Mobs").mkdir(parents=True, exist_ok=True)
    item_sets = []
    for ident, item in data["items"].items():
        desc = DESC[item["name"] if ident.startswith("De") else ident]
        extra = ""
        if isinstance(desc, list):  # [description, extra negative words]
            desc, extra = desc[0], ", " + desc[1]
        neg = (NEG_ITEM if any(w in desc for w in WOODY) else NEG_ITEM + NEG_STICKS) + extra
        if any(w in " " + desc for w in PART) and "charm" not in desc:
            desc, neg = desc + PART_TEXT, neg + NEG_PART
        text = "# Item %s\n\n" % item["name"] + block("01_Icon", ITEM.format(name=item["name"], desc=desc)) + block("Negativ-Prompt", neg)
        (PROMPTS / "Items" / ("Loot_%s_Icon.md" % ident)).write_text(text, encoding="utf-8")
        item_sets.append("Items/Loot/%s/Icon" % ident)
    mob_sets = []
    for mob in data["mobs"]:
        family = "F%02d" % int(mob["family"])
        info = MOBDESC.get(mob["id"])
        if info:
            anatomy = info["anatomy"] if info["anatomy"] in POSE else "other"
            pose = POSE[anatomy]
            if anatomy in ("ghost", "elemental", "other") and ("no body" in info["desc"] or "no limbs" in info["desc"]):
                # wisps and orbs: the ghost pose (arms, lower body) would turn them into a glowing humanoid
                pose = ("It hovers motionless in the middle of the image as one single compact floating shape, with no "
                        "body, no arms, no legs and no human figure anywhere.")
            if anatomy == "biped" and "held horizontally" in info["desc"]:
                # running lizards: the upright A-pose would stand them up like a man
                pose = ("It stands still on its two hind legs like a small raptor dinosaur or a running bird: the body held "
                        "level and horizontal, head forward, the long tail stretched straight back for balance, the small "
                        "forearms tucked in front of the chest.")
            describe = "%s. %s %s" % (info["desc"].rstrip(". ")[0].upper() + info["desc"].rstrip(". ")[1:], pose, STYLE)
            front = FRONT_UP if anatomy in UPRIGHT else FRONT_LONG
            negative = NEG_MOB + (", " + info["neg"] if info.get("neg") else "")
            if anatomy in ("snake", "serpent_water", "crawler"):
                negative += ", coiled, coils, loops, ring, circle, knotted, curled up, body overlapping itself, spiral, raised head, cobra pose, rearing up, S-curve"
            if anatomy in ("snake", "crawler"):
                front = FRONT_SNAKE
            side = SIDE
            if anatomy in ("snake", "crawler", "serpent_water"):
                side = SIDE + (" It has exactly one head, at the right end of the body; the left end is the thin, pointed tail tip "
                               "without any head.")
                negative += ", two heads, head at both ends, double-headed"
            if " arms" in info["desc"]:
                side += (" Its arms stay attached and clearly visible in the profile: the near arm hangs down along the side "
                         "of the body in front of it, the far arm partly visible behind.")
                negative += ", armless, missing arms"
            if anatomy in ("snake", "fish", "serpent_water", "slime", "ghost", "crawler", "octopus", "other"):
                negative = negative.replace("missing limbs, ", "")
            if pose is not POSE[anatomy] and anatomy != "biped":
                negative += ", humanoid, human body, torso, arms, legs, person"
            if pose is not POSE[anatomy] and anatomy == "biped":
                negative += ", upright human posture, standing upright like a man, A-pose"
            if " heads" in info["desc"]:
                negative = negative.replace("extra heads, ", "")
        else:   # fallback without an English description
            kind, pose = BODY.get(mob.get("body", ""), ("a fantasy creature", "in a calm neutral stance"))
            describe = ("%s called „%s“ (kin: %s, role: %s). Description in German: %s The creature is %s. %s"
                        % (kind[0].upper() + kind[1:], mob["name"], mob.get("kin", mob["name"]), mob.get("role", "-"), mob.get("behaviour", ""), pose, STYLE))
            front, negative, side = FRONT_UP, NEG_MOB, SIDE
        text = ("# Mob %s (%s, %s)\n\n" % (mob["name"], mob.get("body", "-"), mob.get("spawn", "common"))
                + block("01_Front", (FRONT_LEAD if front != FRONT_SNAKE else "") + describe + "\n" + front) + block("02_Ruecken", describe + "\n" + BACK)
                + block("03_Links", describe + "\n" + side) + block("Negativ-Prompt", negative))
        (PROMPTS / "Mobs" / ("%s_%s_Stage1.md" % (family, mob["id"]))).write_text(text, encoding="utf-8")
        mob_sets.append("Mobs/%s/%s/Stage1" % (family, mob["id"]))
    (ROOT / "scripts" / "sets_items.txt").write_text("\n".join(item_sets) + "\n", encoding="utf-8")
    (ROOT / "scripts" / "sets_mobs.txt").write_text("\n".join(mob_sets) + "\n", encoding="utf-8")
    print("%d items, %d mobs" % (len(item_sets), len(mob_sets)))


if __name__ == "__main__":
    main()
