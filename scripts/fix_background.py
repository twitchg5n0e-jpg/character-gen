#!/usr/bin/env python3
"""Turn a (nearly) white background into the usual plain light gray, keeping the creature untouched.

    python scripts/fix_background.py output/Mobs_F09_bachhuhn_Flug [...]   (all four views of each folder)
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter

GRAY = (196, 201, 204)   # typical background of the other sets


def regray(path: Path) -> None:
    image = Image.open(path).convert("RGB")
    corner = image.getpixel((4, 4))
    if sum(corner) / 3 < 235:
        print("%s: background %s already gray" % (path, corner))
        return
    background = Image.new("RGB", image.size, corner)
    mask = ImageChops.difference(image, background).convert("L").point(lambda v: 255 if v > 14 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.GaussianBlur(3))
    result = Image.composite(image, Image.new("RGB", image.size, GRAY), mask)
    result.save(path, format="PNG", optimize=True)
    print("%s: background %s -> %s" % (path, corner, GRAY))


if __name__ == "__main__":
    for folder in sys.argv[1:]:
        for view in ("front", "hinten", "links", "rechts"):
            if (Path(folder) / (view + ".png")).is_file():
                regray(Path(folder) / (view + ".png"))
