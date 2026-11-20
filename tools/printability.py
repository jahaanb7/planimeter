"""Printability report for the STLs in stl/ (each already in print orientation: z = 0 is the bed).

For every part: bounding box vs the bed, watertight, and the area of faces that overhang by more than 45 degrees
(normal pointing down more steeply than 45 deg from vertical) and are NOT sitting on the bed.
"""
import glob
import os
import sys

import numpy as np
import trimesh

BED = (220.0, 220.0, 250.0)       # Ender-3 class; --bed override: python tools/printability.py 256 256 256
if len(sys.argv) == 4:
    BED = tuple(float(a) for a in sys.argv[1:4])

root = os.path.join(os.path.dirname(__file__), "..")
print(f"{'part':28s}{'bbox x y z (mm)':>26s}  {'watertight':>10s}  {'overhang mm2':>13s}  {'worst z':>8s}  fits bed")
for f in sorted(glob.glob(os.path.join(root, "stl", "*.stl"))):
    m = trimesh.load(f)
    ext = m.extents
    fits = (max(ext[0], ext[1]) <= max(BED[0], BED[1]) - 10 and min(ext[0], ext[1]) <= min(BED[0], BED[1]) - 10
            and ext[2] <= BED[2])
    n = m.face_normals
    z = m.triangles_center[:, 2]
    zmin = m.bounds[0][2]
    over = (n[:, 2] < -0.7071) & (z > zmin + 0.25)
    area = float(m.area_faces[over].sum())
    # overhang faces that are tiny (< 1 mm2 each) are tessellation noise on teardrops/chamfers; report both
    big = over & (m.area_faces > 0.5)
    worst_z = float(z[big].max()) if big.any() else float("nan")
    print(f"{os.path.basename(f):28s}{ext[0]:8.1f}{ext[1]:8.1f}{ext[2]:8.1f}  {str(m.is_watertight):>10s}  "
          f"{area:13.1f}  {worst_z:8.1f}  {fits}")
