#!/usr/bin/env python3
"""Copy the generated reference images into the Elyndra repository, in Elyndra's layout and format.

    python scripts/copy_to_elyndra.py /path/to/Elyndra

output/<Race>_<Gender>_<Body>_<Stage>/{front,hinten,links,rechts}.png becomes
Assets/Characters/Races/<Race>/<Gender>/<Body>/<Stage>/References/{01_Front,02_Ruecken,03_Links,04_Rechts}.jpg
as 1024x1536 JPEGs (what Elyndra's Tools/Characters scripts expect). Existing images are replaced.
"""
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
VIEWS = {"front": "01_Front", "hinten": "02_Ruecken", "links": "03_Links", "rechts": "04_Rechts"}
SIZE = (1024, 1536)


def main() -> None:
    races = Path(sys.argv[1]) / "Assets" / "Characters" / "Races"
    copied = 0
    for folder in sorted((ROOT / "output").iterdir()):
        parts = folder.name.split("_")
        if len(parts) != 4 or not all((folder / (v + ".png")).is_file() for v in VIEWS):
            continue
        target = races.joinpath(*parts, "References")
        target.mkdir(parents=True, exist_ok=True)
        for view, name in VIEWS.items():
            with Image.open(folder / (view + ".png")) as image:
                image.convert("RGB").resize(SIZE, Image.LANCZOS).save(target / (name + ".jpg"), quality=95)
        copied += 1
    print("%d set(s) copied" % copied)


if __name__ == "__main__":
    main()
