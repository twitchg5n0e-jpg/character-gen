#!/usr/bin/env python3
"""3D-Modelle aller fertigen Sets: Form mit Hunyuan3D-2mv, Farbe aus den vier Vorlagebildern projiziert.

Läuft auf der GPU im geklonten Hunyuan3D-2-Ordner (scripts/make_models.sh richtet alles ein):
    python make_models.py /root/character-gen                 alle fertigen Sets ohne Modell
    python make_models.py /root/character-gen --limit 1       nur das nächste
    python make_models.py /root/character-gen --set Human/Female/Body1/Stage1

Pro Set <Volk>_<Geschlecht>_<Body>_<Stufe> entsteht models/<Set>/model.glb: die Form von Hunyuan3D-2mv aus den vier
Ansichten (front, links, hinten, rechts), Schwebeteile entfernt, auf MAX_FACES Dreiecke reduziert und mit den
Farben der Vorlagebilder als Vertexfarben bemalt (wie scripts/project_views.py im 3D-Test, ohne KI-Textur).
Dazu models/<Set>/vorschau.png mit dem Modell von vorn, links, hinten und rechts.
Die Form-KI wird nur einmal geladen. Ein Set ist offen, solange model.glb fehlt und alle vier Bilder da sind.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
import torch
import trimesh
from PIL import Image

MAX_FACES = 150_000
SEED = 12345
# Hunyuan3D: left = Nase zum linken Bildrand, wie links.png; right = rechts.png
VIEWS = {"front": "front.png", "left": "links.png", "back": "hinten.png", "right": "rechts.png"}
# Drehung um die Hochachse, unter der die Form so aussieht wie die Ansicht (Front schaut nach +Z)
ANGLES = {"front": 0, "left": 270, "back": 180, "right": 90}
DEPTH_SIZE = 1024


def rotation(angle: float) -> np.ndarray:
    a = np.radians(angle)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


def project(mesh: trimesh.Trimesh, images: dict[str, Image.Image]) -> trimesh.Trimesh:
    """Malt die freigestellten Ansichten orthografisch auf die Form (Vertexfarben). Jeder Punkt nimmt die Farbe der
    Ansichten, die ihn sehen, gewichtet nach dem Winkel zur Blickrichtung; ungesehene Punkte die des nächsten."""
    vertices, normals = mesh.vertices, mesh.vertex_normals
    samples, _ = trimesh.sample.sample_surface(mesh, 3_000_000)
    center = (mesh.bounds[0] + mesh.bounds[1]) / 2
    colors = np.zeros((len(vertices), 3))
    weights = np.zeros(len(vertices))
    for view, angle in ANGLES.items():
        image = np.asarray(images[view].convert("RGBA")).astype(float)
        alpha = image[:, :, 3] > 128
        rows, cols = np.nonzero(alpha)
        top, bottom, left, right = rows.min(), rows.max(), cols.min(), cols.max()
        rot = rotation(angle)
        p = (vertices - center) @ rot.T
        s = (samples - center) @ rot.T
        lo, hi = s.min(0), s.max(0)
        scale = (bottom - top) / (hi[1] - lo[1])   # Höhe des Umrisses = Höhe der Form, Mitte auf Mitte

        def to_image(q):
            return (q[:, 0] - (lo[0] + hi[0]) / 2) * scale + (left + right) / 2, (hi[1] - q[:, 1]) * scale + top

        vx, vy = to_image(p)
        grid = DEPTH_SIZE / max(image.shape[:2])
        sx, sy = to_image(s)
        pix = np.stack([np.clip(sx * grid, 0, DEPTH_SIZE - 1), np.clip(sy * grid, 0, DEPTH_SIZE - 1)], 1).astype(int)
        depth = np.full((DEPTH_SIZE, DEPTH_SIZE), -np.inf)
        np.maximum.at(depth, (pix[:, 1], pix[:, 0]), s[:, 2])
        vpx = np.clip((vx * grid).astype(int), 0, DEPTH_SIZE - 1)
        vpy = np.clip((vy * grid).astype(int), 0, DEPTH_SIZE - 1)
        visible = p[:, 2] >= depth[vpy, vpx] - 0.01
        facing = np.clip((normals @ rot.T)[:, 2], 0, 1)
        ix = np.clip(vx.astype(int), 0, image.shape[1] - 1)
        iy = np.clip(vy.astype(int), 0, image.shape[0] - 1)
        w = facing ** 3 * visible * alpha[iy, ix]
        colors += image[iy, ix, :3] * w[:, None]
        weights += w
    seen = weights > 1e-6
    colors[seen] /= weights[seen, None]
    if (~seen).any():
        from scipy.spatial import cKDTree
        _, nearest = cKDTree(vertices[seen]).query(vertices[~seen])
        colors[~seen] = colors[seen][nearest]
    rgba = np.column_stack([colors, np.full(len(colors), 255)]).astype(np.uint8)
    mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=rgba)
    return mesh


def preview(mesh: trimesh.Trimesh, target: Path) -> None:
    """Vier Ansichten des Modells als Punktwolke aus den Vertexfarben, ohne OpenGL (läuft überall)."""
    size = 512
    sheet = Image.new("RGB", (size * 4, size), (235, 235, 235))
    colors = mesh.visual.vertex_colors[:, :3]
    center = (mesh.bounds[0] + mesh.bounds[1]) / 2
    extent = (mesh.bounds[1] - mesh.bounds[0]).max()
    for i, angle in enumerate((0, 270, 180, 90)):
        p = (mesh.vertices - center) @ rotation(angle).T
        order = np.argsort(p[:, 2])   # hinten zuerst, vorn malt drüber
        x = ((p[order, 0] / extent) * 0.9 + 0.5) * size
        y = ((-p[order, 1] / extent) * 0.9 + 0.5) * size
        canvas = np.full((size, size, 3), 235, np.uint8)
        xi, yi = np.clip(x.astype(int), 0, size - 1), np.clip(y.astype(int), 0, size - 1)
        canvas[yi, xi] = colors[order]
        sheet.paste(Image.fromarray(canvas), (i * size, 0))
    sheet.save(target)


def open_sets(root: Path, only: str | None) -> list[str]:
    names = [only] if only else [l.strip() for l in (root / "scripts" / "sets.txt").read_text().splitlines() if l.strip()]
    result = []
    for name in names:
        folder = name.replace("/", "_")
        images = root / "output" / folder
        if all((images / f).is_file() for f in VIEWS.values()) and not (root / "models" / folder / "model.glb").is_file():
            result.append(folder)
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path, help="der character-gen-Ordner")
    parser.add_argument("--limit", type=int, default=0)
    parser.add_argument("--set", help="z. B. Human/Female/Body1/Stage1")
    args = parser.parse_args()
    todo = open_sets(args.root, args.set)
    if args.limit:
        todo = todo[: args.limit]
    print("%d open model(s)" % len(todo), flush=True)
    if not todo:
        return

    from hy3dgen.rembg import BackgroundRemover
    from hy3dgen.shapegen import (DegenerateFaceRemover, FaceReducer, FloaterRemover,
                                  Hunyuan3DDiTFlowMatchingPipeline)
    remover = BackgroundRemover()
    shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2mv",
                                                             subfolder="hunyuan3d-dit-v2-mv", variant="fp16")
    for folder in todo:
        started = time.time()
        source, target = args.root / "output" / folder, args.root / "models" / folder
        target.mkdir(parents=True, exist_ok=True)
        images = {view: remover(Image.open(source / name).convert("RGB")) for view, name in VIEWS.items()}
        mesh = shape(image=images, num_inference_steps=50, octree_resolution=512, num_chunks=20000,
                     generator=torch.manual_seed(SEED), output_type="trimesh")[0]
        mesh = DegenerateFaceRemover()(FloaterRemover()(mesh))
        if len(mesh.faces) > MAX_FACES:
            mesh = FaceReducer()(mesh, max_facenum=MAX_FACES)
        mesh = project(trimesh.Trimesh(mesh.vertices, mesh.faces, process=False), images)
        partial = target / "model.glb.part"
        mesh.export(partial, file_type="glb")
        partial.rename(target / "model.glb")
        preview(mesh, target / "vorschau.png")
        print("model %s: %d faces in %.0f s" % (folder, len(mesh.faces), time.time() - started), flush=True)
        torch.cuda.empty_cache()


if __name__ == "__main__":
    sys.exit(main())
