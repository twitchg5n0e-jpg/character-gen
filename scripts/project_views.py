"""Malt die vier Vorlagebilder direkt auf die Form von Hunyuan3D-2mv (Vertexfarben, ohne KI).

Aufruf:
    python scripts/project_views.py models_test/Human_Female_Body1_Stage1

Liest shape.glb und inputs/{front,left,back,right}.png (freigestellt, mit Alpha) und schreibt projected.glb.
Jede Ansicht wird orthografisch so auf die Form gelegt, dass ihr Umriss die Höhe und Mitte der Form trifft. Jeder
Punkt nimmt die Farbe der Ansichten, die ihn sehen, gewichtet nach dem Winkel zur Blickrichtung.
"""
import sys
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image

# Drehung um die Hochachse, unter der die Form so aussieht wie die Ansicht (Front schaut nach +Z)
VIEWS = {"front": 0, "left": 270, "back": 180, "right": 90}
DEPTH_SIZE = 1024


def rotation(angle):
    a = np.radians(angle)
    return np.array([[np.cos(a), 0, np.sin(a)], [0, 1, 0], [-np.sin(a), 0, np.cos(a)]])


folder = Path(sys.argv[1])
mesh = trimesh.load(folder / "shape.glb", force="mesh")
vertices, normals = mesh.vertices, mesh.vertex_normals
samples, faces = trimesh.sample.sample_surface(mesh, 3_000_000)
center = (mesh.bounds[0] + mesh.bounds[1]) / 2
colors = np.zeros((len(vertices), 3))
weights = np.zeros(len(vertices))

for view, angle in VIEWS.items():
    image = np.asarray(Image.open(folder / "inputs" / ("%s.png" % view)).convert("RGBA")).astype(float)
    alpha = image[:, :, 3] > 128
    rows, cols = np.nonzero(alpha)
    top, bottom, left, right = rows.min(), rows.max(), cols.min(), cols.max()

    rot = rotation(angle)
    p = (vertices - center) @ rot.T
    s = (samples - center) @ rot.T
    lo, hi = s.min(0), s.max(0)
    # Höhe des Umrisses = Höhe der Form, Mitte auf Mitte
    scale = (bottom - top) / (hi[1] - lo[1])
    def to_image(q):
        x = (q[:, 0] - (lo[0] + hi[0]) / 2) * scale + (left + right) / 2
        y = (hi[1] - q[:, 1]) * scale + top
        return x, y
    vx, vy = to_image(p)

    # Sichtbarkeit: Tiefe der Punkte gegen eine Tiefenkarte
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
    inside = alpha[iy, ix]
    w = facing ** 3 * visible * inside
    colors += image[iy, ix, :3] * w[:, None]
    weights += w
    print("%s: %d of %d vertices seen" % (view, (w > 0.05).sum(), len(vertices)))

seen = weights > 1e-6
colors[seen] /= weights[seen, None]
# Ungesehene Punkte (Achseln, Fusssohlen) bekommen die Farbe des nächsten gesehenen Punkts
if (~seen).any():
    from scipy.spatial import cKDTree
    _, nearest = cKDTree(vertices[seen]).query(vertices[~seen])
    colors[~seen] = colors[seen][nearest]
mesh.visual = trimesh.visual.ColorVisuals(mesh, vertex_colors=np.column_stack([colors, np.full(len(colors), 255)])
                                          .astype(np.uint8))
mesh.export(folder / "projected.glb")
print("projected.glb: %d vertices, %d unseen" % (len(vertices), (~seen).sum()))
