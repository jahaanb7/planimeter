"""Render assembled and exploded views of the planimeter from the CAD model.

Run with an interpreter that has cadquery, trimesh, pyrender and Pillow:
    python tools/render_views.py
Writes docs/images/views/*.png
"""
import math
import os
import platform
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.join(HERE, "..")
sys.path.insert(0, os.path.join(ROOT, "cad"))
sys.path.insert(0, os.path.join(ROOT, "cad", "parts"))

import cadquery as cq  # noqa: E402
import pyrender  # noqa: E402
import trimesh  # noqa: E402
from PIL import Image  # noqa: E402

import assembly  # noqa: E402

COL = {"printed": (0.86, 0.83, 0.74), "hardware": (0.55, 0.58, 0.62), "rubber": (0.12, 0.12, 0.12),
       "wheel": (0.25, 0.45, 0.8), "dial": (0.9, 0.45, 0.15), "tracer_arm": (0.2, 0.65, 0.45),
       "pole_arm": (0.8, 0.3, 0.3), "pole_weight": (0.35, 0.35, 0.4), "pole_weight_lid": (0.35, 0.35, 0.4)}

# explode offsets (mm): the carriage stack opens along X, the arms lift along Z
EXPLODE = {
    "carriage_c": (-70, 0, 0), "cnut": (-85, 0, 0), "dial_nut": (-85, 0, 0), "axle_bolt": (-100, 0, 0),
    "wheel": (-35, 0, 0), "bearing_w1": (-52, 0, 0), "bearing_w2": (-20, 0, 0), "anut": (-18, 0, 0),
    "cscrew": (30, 0, 0), "axle_nut": (30, 0, 0), "carriage_a": (60, 0, 0), "ascrew": (90, 0, 0),
    "dial": (-45, 0, 0), "dial_screw": (-30, 0, 0),
    "tracer_arm": (0, 0, 35), "tracer_nut": (0, 0, 35), "tracer_bolt": (0, 0, 55),
    "clamp_screw": (0, -30, 0), "clamp_nut": (0, -15, 0),
    "elbow_nut": (0, 0, -25), "pole_arm": (0, 0, 80), "elbow_bearing": (0, 0, 62),
    "elbow_washer": (0, 0, 98), "elbow_bolt": (0, 0, 120),
    "pole_weight_lid": (0, 0, 40), "pole_nut": (0, 0, -20), "pole_bearing": (0, 0, 62),
    "pole_washer": (0, 0, 98), "pole_bolt": (0, 0, 120),
}


def offset_for(name):
    if name in EXPLODE:
        return EXPLODE[name]
    base = name.rstrip("0123456789")
    return EXPLODE.get(base, (0, 0, 0))


def mesh_of(wp, colour):
    v, f = wp.val().tessellate(0.05, 0.2)
    m = trimesh.Trimesh(np.array([[p.x, p.y, p.z] for p in v]), np.array(f), process=True)
    m.visual.vertex_colors = (np.array(colour) * 255).astype(np.uint8).tolist() + [255]
    m.visual = trimesh.visual.ColorVisuals(m, vertex_colors=np.tile(
        (np.array(list(colour) + [1.0]) * 255).astype(np.uint8), (len(m.vertices), 1)))
    return m


def pose(elev, azim, dist):
    el, az = math.radians(elev), math.radians(azim)
    eye = dist * np.array([math.cos(el) * math.cos(az), math.cos(el) * math.sin(az), math.sin(el)])
    fwd = -eye / np.linalg.norm(eye)
    up = np.array([0, 0, 1.0])
    right = np.cross(fwd, up)
    if np.linalg.norm(right) < 1e-6:
        up = np.array([0, 1.0, 0])
        right = np.cross(fwd, up)
    right /= np.linalg.norm(right)
    cu = np.cross(right, fwd)
    p = np.eye(4)
    p[:3, 0], p[:3, 1], p[:3, 2], p[:3, 3] = right, cu, -fwd, eye
    return p


def render(meshes, elev, azim, path, size=(1400, 1000), ortho=False, pad=1.12):
    allv = np.vstack([m.vertices for m in meshes])
    lo, hi = allv.min(0), allv.max(0)
    centre = (lo + hi) / 2
    radius = np.linalg.norm(hi - lo) / 2
    scene = pyrender.Scene(bg_color=np.array([1.0, 1.0, 1.0, 1.0]), ambient_light=[0.55, 0.55, 0.55])
    for m in meshes:
        mm = m.copy()
        mm.apply_translation(-centre)
        scene.add(pyrender.Mesh.from_trimesh(mm, smooth=False))
    p = pose(elev, azim, radius * 4.5)
    cam = (pyrender.OrthographicCamera(xmag=radius * pad * size[0] / size[1], ymag=radius * pad,
                                       znear=0.1, zfar=radius * 12)
           if ortho else pyrender.PerspectiveCamera(yfov=math.radians(22), znear=1, zfar=radius * 12))
    scene.add(cam, pose=p)
    for dx, dy, dz, s in ((1, 1, 2, 2.6), (-1, 0.3, 1, 1.4), (0.2, -1, 1, 1.2)):
        d = np.array([dx, dy, dz], float)
        lp = pose(math.degrees(math.asin(d[2] / np.linalg.norm(d))), math.degrees(math.atan2(d[1], d[0])), 10)
        scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=s), pose=lp)
    r = pyrender.OffscreenRenderer(*size)
    color, depth = r.render(scene)
    color = color.copy()
    color[depth == 0] = 255
    r.delete()
    img = Image.fromarray(color).convert("RGB")
    from PIL import ImageChops
    bbox = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    if bbox:
        m = 30
        img = img.crop((max(0, bbox[0] - m), max(0, bbox[1] - m), min(img.width, bbox[2] + m), min(img.height, bbox[3] + m)))
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT))


def main():
    out = os.path.join(ROOT, "docs", "images", "views")
    os.makedirs(out, exist_ok=True)
    comps = assembly.components()
    asm, exp = [], []
    for name, (wp, kind) in comps.items():
        m = mesh_of(wp, COL.get(name, COL[kind]))
        asm.append(m)
        o = offset_for(name)
        e = m.copy()
        e.apply_translation(o)
        exp.append(e)
    render(asm, 28, 40, os.path.join(out, "iso_front.png"))
    render(asm, 28, 215, os.path.join(out, "iso_rear.png"))
    render(asm, 90, -90, os.path.join(out, "top.png"), size=(1400, 1100), ortho=True)
    render(asm, 0, -90, os.path.join(out, "side.png"), size=(1400, 700), ortho=True)
    render(asm, 35, 130, os.path.join(out, "iso_wheel_side.png"))
    # close-up of the carriage (wheel, counter, plates, block, clamp) without the long arms
    keep = {"wheel", "carriage_a", "carriage_b", "carriage_c", "dial", "bearing_w1", "bearing_w2", "axle_bolt", "axle_nut",
            "dial_screw", "dial_nut", "clamp_screw"}
    keep |= {n for n in comps if n.startswith(("cscrew", "cnut", "ascrew", "anut"))}
    close = [m for (n, _), m in zip(comps.items(), asm) if n in keep]
    render(close, 32, 140, os.path.join(out, "carriage_closeup.png"), size=(1200, 1000))
    render(exp, 24, 150, os.path.join(out, "exploded.png"), size=(1800, 1500))


if __name__ == "__main__":
    main()
