#!/usr/bin/env python3
"""Check the generated sets for mistakes a person would otherwise have to spot by eye.

    python scripts/check_images.py                      every set in scripts/sets.txt that has images
    python scripts/check_images.py Fey/Female/Body1/Stage1 Merfolk/Male/Body1/Stage1
    python scripts/check_images.py --sheets DIR         also write one contact sheet per set into DIR

Checks per set (only Pillow and numpy needed):
- all four images exist, are PNG and 1056x1584; rechts.png is the mirror image of links.png
- background: plain, light, neutral gray, the same at the top and the bottom (no floor, horizon or vignette)
- the figure is fully in the picture (does not touch the top or bottom edge) and roughly centered
- Fey: the body is not one uniform pink/lilac/purple tone
- Merfolk: the face is not a warm human skin tone

Prints one line per set: OK, WARNUNG (only the background is uneven) or FEHLER with the reasons. Exit code 1 when a set has an error.
The checks are measurements, not taste: a set that passes still needs a look (--sheets).
"""
from __future__ import annotations

import argparse
import colorsys
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter, ImageOps

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output"
SETS = ROOT / "scripts" / "sets.txt"
SIZE = (1056, 1584)
VIEWS = ("front", "hinten", "links", "rechts")


def load(path: Path) -> np.ndarray:
    with Image.open(path) as image:
        return np.asarray(image.convert("RGB")).astype(np.float32)


def background(a: np.ndarray) -> tuple[np.ndarray, list[str]]:
    """Background color from the image border, and what is wrong with it."""
    h, w, _ = a.shape
    m = max(8, w // 40)
    top = np.concatenate([a[:m, :].reshape(-1, 3), a[: h // 3, :m].reshape(-1, 3), a[: h // 3, -m:].reshape(-1, 3)])
    bottom = np.concatenate([a[-m:, :].reshape(-1, 3), a[-h // 3 :, :m].reshape(-1, 3), a[-h // 3 :, -m:].reshape(-1, 3)])
    border = np.concatenate([top, bottom])
    color = np.median(border, 0)
    problems = []
    if color.max() - color.min() > 22:
        problems.append("Hintergrund farbig %s" % color.round().astype(int).tolist())
    if color.mean() < 120:
        problems.append("Hintergrund zu dunkel (%d)" % color.mean())
    step = abs(np.median(top, 0).mean() - np.median(bottom, 0).mean())
    if step > 22:
        problems.append("Warnung: Hintergrund oben/unten verschieden (%d, Boden oder Verlauf)" % step)
    return color, problems


def figure_mask(a: np.ndarray) -> np.ndarray:
    """Pixels that differ from a smooth background model: a quadratic surface fitted through the image border, so a
    vertical or sideways gradient and a vignette do not count as figure."""
    h, w, _ = a.shape
    step = 4
    small = a[::step, ::step]
    sh, sw, _ = small.shape
    y, x = np.mgrid[0:sh, 0:sw]
    y, x = y / sh - 0.5, x / sw - 0.5
    basis = np.stack([np.ones_like(x), x, y, x * x, y * y, x * y], -1)
    m = max(2, sw // 25)
    border = np.zeros((sh, sw), bool)
    border[:m], border[-m:], border[:, :m], border[:, -m:] = True, True, True, True
    coef, *_ = np.linalg.lstsq(basis[border], small[border], rcond=None)
    model = basis @ coef
    small_mask = np.abs(small - model).max(2) > 40
    return np.repeat(np.repeat(small_mask, step, 0), step, 1)[:h, :w]


def figure_problems(mask: np.ndarray) -> list[str]:
    h, w = mask.shape
    rows = np.where(mask.mean(1) > 0.02)[0]
    cols = np.where(mask.mean(0) > 0.02)[0]
    if len(rows) == 0:
        return ["keine Figur gefunden"]
    problems = []
    if (rows[-1] - rows[0]) < 0.6 * h:
        problems.append("Figur zu klein (%d%% der Bildhöhe)" % (100 * (rows[-1] - rows[0]) / h))
    center = (cols[0] + cols[-1]) / 2 / w
    if abs(center - 0.5) > 0.2:
        problems.append("Figur nicht mittig")
    return problems


def hues(pixels: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    p = pixels / 255.0
    hsv = np.array([colorsys.rgb_to_hsv(*x) for x in p[:: max(1, len(p) // 20000)]])
    return hsv[:, 0] * 360, hsv[:, 1], hsv[:, 2]


def cut_off(mask: np.ndarray) -> list[str]:
    """Does the figure run into the top or bottom edge (middle of the image, the corners are often dark)?"""
    w = mask.shape[1]
    middle = mask[:, w // 6: w - w // 6]
    problems = []
    if middle[:8].mean() > 0.03:
        problems.append("Figur oben abgeschnitten")
    if middle[-8:].mean() > 0.03:
        problems.append("Figur unten abgeschnitten")
    return problems


def race_problems(race: str, a: np.ndarray, mask: np.ndarray) -> list[str]:
    rows = np.where(mask.mean(1) > 0.02)[0]
    if len(rows) == 0:
        return []
    if race == "Fey":
        hue, sat, _ = hues(a[mask])
        coloured = sat > 0.12
        purple = ((hue > 250) & (hue < 345) & coloured).sum() / max(1, coloured.sum())
        if purple > 0.6:
            return ["Fey einfarbig pink/lila (%d%% der Figur)" % (100 * purple)]
    if race == "Merfolk":
        top, height = rows[0], rows[-1] - rows[0]
        face = np.zeros_like(mask)
        h, w = mask.shape
        face[top + int(0.03 * height): top + int(0.11 * height), int(0.40 * w): int(0.60 * w)] = True
        hue, sat, _ = hues(a[face & mask])
        warm = ((hue < 40) | (hue > 340)) & (sat > 0.15)
        if len(hue) and warm.mean() > 0.35:
            return ["Merfolk-Gesicht in Hautfarbe (%d%% warm)" % (100 * warm.mean())]
    return []


def check(parts: list[str]) -> list[str]:
    folder = OUTPUT / "_".join(parts)
    problems = []
    images = {}
    for view in VIEWS:
        path = folder / (view + ".png")
        if not path.is_file():
            problems.append("%s fehlt" % view)
            continue
        with Image.open(path) as image:
            if image.format != "PNG" or image.size != SIZE:
                problems.append("%s: %s %s statt PNG %s" % (view, image.format, image.size, SIZE))
        images[view] = load(path)
    if "links" in images and "rechts" in images:
        if np.abs(images["rechts"] - images["links"][:, ::-1]).mean() > 2:
            problems.append("rechts ist nicht das Spiegelbild von links")
    for view, a in images.items():
        if view == "rechts":
            continue
        color, bg = background(a)
        mask = figure_mask(a)
        problems += ["%s: %s" % (view, p) for p in bg + figure_problems(mask) + cut_off(mask)]
        if view == "front":
            problems += ["front: %s" % p for p in race_problems(parts[0], a, mask)]
    return problems


def sheet(parts: list[str], target: Path) -> None:
    folder = OUTPUT / "_".join(parts)
    w, h = 264, 396
    out = Image.new("RGB", (w * 4, h), "white")
    for i, view in enumerate(("front", "links", "hinten", "rechts")):
        path = folder / (view + ".png")
        if path.is_file():
            with Image.open(path) as image:
                out.paste(ImageOps.fit(image.convert("RGB"), (w, h)), (i * w, 0))
    target.mkdir(parents=True, exist_ok=True)
    out.save(target / (folder.name + ".jpg"), quality=85)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("sets", nargs="*", help="Race/Gender/Body/Stage; default: every set in sets.txt with images")
    parser.add_argument("--sheets", type=Path, help="write a contact sheet per set into this folder")
    args = parser.parse_args()
    names = args.sets or [l.strip() for l in SETS.read_text(encoding="utf-8").splitlines() if l.strip()]
    failed = 0
    for name in names:
        parts = name.strip("/").split("/")
        if not (OUTPUT / "_".join(parts)).is_dir():
            if args.sets:
                print("FEHLT   %s" % name)
            continue
        found = check(parts)
        problems = [p for p in found if "Warnung" not in p]
        if args.sheets:
            sheet(parts, args.sheets)
        label = "FEHLER " if problems else ("WARNUNG" if found else "OK     ")
        print("%s %s%s" % (label, name, (": " + "; ".join(found)) if found else ""))
        failed += bool(problems)
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
