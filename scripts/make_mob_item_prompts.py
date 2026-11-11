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
FRONT = "Front view: the creature faces the camera directly, head and body straight towards the viewer, not turned to the side."
BACK = "Back view for a 3D modeling reference, seen directly from behind at mid height, same neutral pose, back of the head visible."
SIDE = ("Exact 90 degree side profile for a 3D modeling reference: the creature has turned to its own left, so its head points "
        "to the right edge of the image. The whole body is seen exactly from the side, neither the chest nor the back faces the camera. Same pose.")
NEG_MOB = ("multiple creatures, two heads unless described, rider, saddle, armor on animals, text, watermark, logo, frame, border, "
           "collage, character sheet, turnaround sheet, multiple views, split image, grid, cropped, cut off, partially out of frame, "
           "visible floor, horizon line, floor shadow, cast shadow, vignette, gradient background, colored background, scenery, "
           "landscape, forest, trees, props, dramatic lighting, rim light, motion blur, action pose, attacking, jumping, flying high, "
           "fisheye, perspective distortion, cartoon, anime, stylized, toy, plastic, clay, low detail, blurry")
ITEM = ("Game inventory icon for a fantasy RPG: one single loot item, „{name}“{hint}. A crafting material or trophy taken "
        "from a defeated creature or found in the wild, shown as a single object (or a small neat bundle of the same material). "
        "Realistic, finely detailed, clear readable silhouette, centered and filling about two thirds of the square image, seen "
        "slightly from above at a three-quarter angle. Isolated on a plain, seamless, uniform light gray background: no shadow, "
        "no table, no hands, no frame, no text, no label. Soft even studio lighting.")
NEG_ITEM = ("text, letters, label, watermark, logo, frame, border, hands, person, creature, table, surface, scene, landscape, "
            "multiple different objects, collage, grid, cast shadow, vignette, gradient background, colored background, "
            "cartoon, flat vector, anime, blurry, low detail, cropped, cut off")


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
        hint = "" if ident.startswith("De") else " (%s)" % words(ident)
        text = "# Item %s\n\n" % item["name"] + block("01_Icon", ITEM.format(name=item["name"], hint=hint)) + block("Negativ-Prompt", NEG_ITEM)
        (PROMPTS / "Items" / ("Loot_%s_Icon.md" % ident)).write_text(text, encoding="utf-8")
        item_sets.append("Items/Loot/%s/Icon" % ident)
    mob_sets = []
    for mob in data["mobs"]:
        kind, pose = BODY.get(mob.get("body", ""), ("a fantasy creature", "in a calm neutral stance"))
        family = "F%02d" % int(mob["family"])
        describe = ("%s called „%s“ (kin: %s, role: %s). Description in German: %s The creature is %s. %s"
                    % (kind[0].upper() + kind[1:], mob["name"], mob.get("kin", mob["name"]), mob.get("role", "-"), mob.get("behaviour", ""), pose, STYLE))
        text = ("# Mob %s (%s, %s)\n\n" % (mob["name"], mob.get("body", "-"), mob.get("spawn", "common"))
                + block("01_Front", describe + "\n" + FRONT) + block("02_Ruecken", describe + "\n" + BACK)
                + block("03_Links", describe + "\n" + SIDE) + block("Negativ-Prompt", NEG_MOB))
        (PROMPTS / "Mobs" / ("%s_%s_Stage1.md" % (family, mob["id"]))).write_text(text, encoding="utf-8")
        mob_sets.append("Mobs/%s/%s/Stage1" % (family, mob["id"]))
    (ROOT / "scripts" / "sets_items.txt").write_text("\n".join(item_sets) + "\n", encoding="utf-8")
    (ROOT / "scripts" / "sets_mobs.txt").write_text("\n".join(mob_sets) + "\n", encoding="utf-8")
    print("%d items, %d mobs" % (len(item_sets), len(mob_sets)))


if __name__ == "__main__":
    main()
