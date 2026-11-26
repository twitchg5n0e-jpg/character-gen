#!/usr/bin/env python3
"""Scale a too-small mob back view (hinten.png) up to the size of the figure in front.png.

The generator sometimes draws the back view much smaller than the front (the camera seems farther away). The figure
is cut out of hinten.png and scaled so its height matches the figure height in front.png, placed at the same height
and centred horizontally on the same plain background colour. No GPU needed.
    python scripts/fit_back_size.py output/Mobs_F03_felsenhuhn_Stage1 [...]
"""
from __future__ import annotations

import sys
from pathlib import Path

from PIL import Image, ImageChops, ImageFilter


def figure_box(image: Image.Image) -> tuple[int, int, int, int] | None:
    """Bounding box of everything that differs from the corner (background) colour, in full resolution."""
    small = image.convert("RGB").resize((256, 256))
    background = Image.new("RGB", small.size, small.getpixel((2, 2)))
    mask = ImageChops.difference(small, background).convert("L").point(lambda v: 255 if v > 28 else 0)
    box = mask.filter(ImageFilter.MedianFilter(5)).getbbox()
    if not box:
        return None
    sx, sy = image.width / 256, image.height / 256
    return int(box[0] * sx), int(box[1] * sy), int(box[2] * sx), int(box[3] * sy)


def height_ratio(back: Image.Image, front: Image.Image) -> float:
    b, f = figure_box(back), figure_box(front)
    if not b or not f:
        return 1.0
    return (b[3] - b[1]) / max(1, f[3] - f[1])


def fit_back(folder: Path, limit: float = 0.8) -> bool:
    back_path, front_path = folder / "hinten.png", folder / "front.png"
    back, front = Image.open(back_path).convert("RGB"), Image.open(front_path).convert("RGB")
    b, f = figure_box(back), figure_box(front)
    if not b or not f:
        return False
    ratio = (b[3] - b[1]) / max(1, f[3] - f[1])
    if ratio >= limit:
        print("%s: ratio %.2f, ok" % (folder.name, ratio))
        return False
    # only on a plain background: a visible floor or gradient would be cut out with the figure and leave patches
    corners = [back.getpixel(p) for p in ((2, 2), (back.width - 3, 2), (2, back.height - 3), (back.width - 3, back.height - 3))]
    if max(sum(abs(a - b) for a, b in zip(c, corners[0])) for c in corners) > 45:
        print("%s: ratio %.2f, background not plain, left as it is" % (folder.name, ratio))
        return False
    pad = 12
    crop = back.crop((max(0, b[0] - pad), max(0, b[1] - pad), min(back.width, b[2] + pad), min(back.height, b[3] + pad)))
    scale = (f[3] - f[1] + 2 * pad) / crop.height
    # never wider than the image
    scale = min(scale, (back.width - 8) / crop.width)
    crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.LANCZOS)
    canvas = Image.new("RGB", back.size, back.getpixel((2, 2)))
    x = (back.width - crop.width) // 2
    y = max(0, min(back.height - crop.height, f[1] - pad))
    # paste only the figure (plus a soft margin), so no rectangle of the old background shows
    corner = Image.new("RGB", crop.size, crop.getpixel((2, 2)))
    mask = ImageChops.difference(crop, corner).convert("L").point(lambda v: 255 if v > 18 else 0)
    mask = mask.filter(ImageFilter.MaxFilter(9)).filter(ImageFilter.GaussianBlur(6))
    canvas.paste(crop, (x, y), mask)
    canvas.save(back_path, format="PNG", optimize=True)
    print("%s: ratio %.2f -> scaled by %.2f" % (folder.name, ratio, scale))
    return True


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        fit_back(Path(arg))
