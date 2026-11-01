"""3D-Testmodell aus den vier Ansichten eines Sets mit Hunyuan3D-2mv (Form) und Hunyuan3D-Paint (Textur).

Aufruf (im geklonten Hunyuan3D-2-Ordner, siehe scripts/test_3d_mv.sh):
    python make_model_mv.py output/Human_Female_Body1_Stage1 models_test/Human_Female_Body1_Stage1

Schreibt in den Zielordner:
    shape_raw.glb  Form ohne Textur, wie Hunyuan3D-2mv sie liefert
    shape.glb      Form ohne Textur, direkt aus Hunyuan3D-2mv (nur Schwebeteile entfernt)
    textured.glb   Form auf 40 000 Dreiecke reduziert und von Hunyuan3D-Paint aus den vier Ansichten bemalt
    inputs/        die freigestellten Ansichten, so wie Hunyuan3D sie bekommt
"""
import sys
import time
from pathlib import Path

import torch
from PIL import Image

from hy3dgen.rembg import BackgroundRemover
from hy3dgen.shapegen import DegenerateFaceRemover, FaceReducer, FloaterRemover, Hunyuan3DDiTFlowMatchingPipeline

# Hunyuan3D: left = Nase zum linken Bildrand, wie links.png; right = rechts.png
VIEWS = {"front": "front.png", "left": "links.png", "back": "hinten.png", "right": "rechts.png"}

source, target = Path(sys.argv[1]), Path(sys.argv[2])
(target / "inputs").mkdir(parents=True, exist_ok=True)

remover = BackgroundRemover()
images = {}
for view, name in VIEWS.items():
    image = remover(Image.open(source / name).convert("RGB"))
    image.save(target / "inputs" / ("%s.png" % view))
    images[view] = image

started = time.time()
shape = Hunyuan3DDiTFlowMatchingPipeline.from_pretrained("tencent/Hunyuan3D-2mv", subfolder="hunyuan3d-dit-v2-mv",
                                                         variant="fp16")
mesh = shape(image=images, num_inference_steps=50, octree_resolution=512, num_chunks=20000,
             generator=torch.manual_seed(12345), output_type="trimesh")[0]
mesh.export(target / "shape_raw.glb")
mesh = DegenerateFaceRemover()(FloaterRemover()(mesh))
mesh.export(target / "shape.glb")
print("shape: %d faces in %.0f s" % (len(mesh.faces), time.time() - started), flush=True)

del shape
torch.cuda.empty_cache()

try:
    from hy3dgen.texgen import Hunyuan3DPaintPipeline
except ImportError as error:
    sys.exit("no texture: %s" % error)
started = time.time()
paint = Hunyuan3DPaintPipeline.from_pretrained("tencent/Hunyuan3D-2", subfolder="hunyuan3d-paint-v2-0-turbo")
mesh = paint(FaceReducer()(mesh, max_facenum=40000), image=list(images.values()))
mesh.export(target / "textured.glb")
print("texture in %.0f s" % (time.time() - started), flush=True)
