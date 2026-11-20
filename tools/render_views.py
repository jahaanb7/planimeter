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


def _make_scene(meshes, centre, colour_fn=None, flat=False):
    scene = pyrender.Scene(bg_color=np.array([1.0, 1.0, 1.0, 1.0]), ambient_light=[0.38, 0.38, 0.38])
    for i, m in enumerate(meshes):
        mm = m.copy()
        mm.apply_translation(-centre)
        if colour_fn is not None:
            mm = mm.copy()
            mm.unmerge_vertices()
            fn = mm.face_normals
            cols = colour_fn(i, fn)
            mm.visual = trimesh.visual.ColorVisuals(mm, face_colors=cols)
        scene.add(pyrender.Mesh.from_trimesh(mm, smooth=False))
    return scene


def _camera(radius, size, ortho, pad):
    if ortho:
        return pyrender.OrthographicCamera(xmag=radius * pad * size[0] / size[1], ymag=radius * pad,
                                           znear=0.1, zfar=radius * 12)
    return pyrender.PerspectiveCamera(yfov=math.radians(22), znear=1, zfar=radius * 12)


def project(pt, cam_pose, size, ortho, radius, pad, yfov=22.0):
    """World point (already centred) -> pixel (x, y) in a render of `size`."""
    v = np.linalg.inv(cam_pose) @ np.append(pt, 1.0)
    aspect = size[0] / size[1]
    if ortho:
        xn = v[0] / (radius * pad * aspect)
        yn = v[1] / (radius * pad)
    else:
        t = math.tan(math.radians(yfov) / 2)
        xn = (v[0] / -v[2]) / (t * aspect)
        yn = (v[1] / -v[2]) / t
    return (xn + 1) / 2 * size[0], (1 - yn) / 2 * size[1]


def render(meshes, elev, azim, path, size=(1400, 1000), ortho=False, pad=1.12, labels=None, ss=2):
    """Render with crease and silhouette edges for depth. `labels`: list of (text, [mesh indices])."""
    allv = np.vstack([m.vertices for m in meshes])
    lo, hi = allv.min(0), allv.max(0)
    centre = (lo + hi) / 2
    radius = np.linalg.norm(hi - lo) / 2
    W, H = size[0] * ss, size[1] * ss
    p = pose(elev, azim, radius * 4.5)
    cam = _camera(radius, (W, H), ortho, pad)

    def shoot(scene):
        scene.add(cam, pose=p)
        r = pyrender.OffscreenRenderer(W, H)
        img, depth = r.render(scene)
        r.delete()
        return img.copy(), depth

    # beauty pass with three lights
    scene = _make_scene(meshes, centre)
    scene.add(cam, pose=p)
    for dx, dy, dz, k in ((1, 0.6, 1.6, 3.0), (-1, 0.2, 0.7, 1.0), (0.1, -1, 0.5, 0.8)):
        d = np.array([dx, dy, dz], float)
        lp = pose(math.degrees(math.asin(d[2] / np.linalg.norm(d))), math.degrees(math.atan2(d[1], d[0])), 10)
        scene.add(pyrender.DirectionalLight(color=[1, 1, 1], intensity=k), pose=lp)
    r = pyrender.OffscreenRenderer(W, H)
    color, depth = r.render(scene)
    r.delete()
    color = color.copy()
    bg = depth == 0
    # normal pass and component-id pass, unlit
    flat = pyrender.RenderFlags.FLAT
    def offscreen_flat(colour_fn):
        sc = _make_scene(meshes, centre, colour_fn)
        sc.add(cam, pose=p)
        rr = pyrender.OffscreenRenderer(W, H)
        im, _ = rr.render(sc, flags=flat)
        rr.delete()
        return im.astype(np.int16)
    def normal_cols(i, fn):
        c = ((fn + 1) / 2 * 255).astype(np.uint8)
        return np.hstack([c, np.full((len(c), 1), 255, np.uint8)])
    def id_cols(i, fn):
        rng = np.random.RandomState(i * 7 + 3)
        c = rng.randint(30, 255, 3).astype(np.uint8)
        return np.tile(np.append(c, 255), (len(fn), 1))
    nrm = offscreen_flat(normal_cols)
    ids = offscreen_flat(id_cols)

    def edges_of(img, thr):
        e = np.zeros(img.shape[:2], bool)
        e[:, :-1] |= np.abs(img[:, 1:, :3] - img[:, :-1, :3]).max(-1) > thr
        e[:-1, :] |= np.abs(img[1:, :, :3] - img[:-1, :, :3]).max(-1) > thr
        return e
    edge = edges_of(nrm, 70) | edges_of(ids, 20)
    dz = np.zeros_like(depth, bool)
    d = np.where(bg, depth.max() if depth.max() > 0 else 1, depth)
    dz[:, :-1] |= np.abs(d[:, 1:] - d[:, :-1]) > radius * 0.02
    dz[:-1, :] |= np.abs(d[1:, :] - d[:-1, :]) > radius * 0.02
    edge |= dz
    # thicken by one pixel
    e2 = edge.copy()
    e2[:, 1:] |= edge[:, :-1]
    e2[1:, :] |= edge[:-1, :]
    color[bg] = 255
    # soft ambient-occlusion-like depth cue: darken far surfaces slightly
    dn = np.clip((d - d[~bg].min()) / max(1e-6, d[~bg].max() - d[~bg].min()), 0, 1) if (~bg).any() else d
    color = (color * (1 - 0.08 * dn[..., None] * (~bg)[..., None])).astype(np.uint8)
    color[e2 & ~bg] = (38, 42, 52)
    color[e2 & bg] = (38, 42, 52)
    img = Image.fromarray(color).resize(size, Image.LANCZOS)

    if labels:
        img = annotate(img, labels, meshes, centre, p, size, ortho, radius, pad)
    from PIL import ImageChops
    bbox = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    if bbox:
        m = 30
        img = img.crop((max(0, bbox[0] - m), max(0, bbox[1] - m), min(img.width, bbox[2] + m), min(img.height, bbox[3] + m)))
    img.save(path)
    print("wrote", os.path.relpath(path, ROOT), img.size)


def annotate(img, labels, meshes, centre, cam_pose, size, ortho, radius, pad):
    from PIL import ImageDraw, ImageFont
    font = None
    for f in ("/System/Library/Fonts/Helvetica.ttc", "/System/Library/Fonts/Supplemental/Arial.ttf"):
        try:
            font = ImageFont.truetype(f, 46)
            break
        except OSError:
            pass
    font = font or ImageFont.load_default()
    anchors = []
    for i, (text, idx) in enumerate(labels):
        c = meshes[idx[0]].bounds.mean(0) - centre
        anchors.append((text, project(c, cam_pose, size, ortho, radius, pad)))
    from PIL import ImageChops
    bb = ImageChops.difference(img, Image.new("RGB", img.size, (255, 255, 255))).getbbox()
    margin = 700
    canvas = Image.new("RGB", (img.width + 2 * margin, img.height), (255, 255, 255))
    canvas.paste(img, (margin, 0))
    d = ImageDraw.Draw(canvas)
    xs = sorted(a[1][0] for a in anchors)
    mid = xs[len(xs) // 2]
    left = sorted([a for a in anchors if a[1][0] < mid], key=lambda a: a[1][1])
    right = sorted([a for a in anchors if a[1][0] >= mid], key=lambda a: a[1][1])
    ink = (38, 42, 52)
    for side, items in (("L", left), ("R", right)):
        ys = []
        for k, (text, (ax, ay)) in enumerate(items):
            y = ay
            if ys and y < ys[-1] + 62:
                y = ys[-1] + 62
            ys.append(y)
        # keep the stack inside the image
        shift = max(0, ys[-1] - (img.height - 20)) if ys else 0
        ys = [y - shift for y in ys]
        for (text, (ax, ay)), y in zip(items, ys):
            ax += margin
            tw = d.textlength(text, font=font)
            if side == "L":
                tx = margin + bb[0] - 40
                d.text((tx - tw, y - 24), text, fill=ink, font=font)
                d.line([(tx + 6, y), (tx + 26, y), (ax, ay)], fill=(120, 126, 140), width=2)
            else:
                tx = margin + bb[2] + 40
                d.text((tx, y - 24), text, fill=ink, font=font)
                d.line([(tx - 6, y), (tx - 26, y), (ax, ay)], fill=(120, 126, 140), width=2)
            d.ellipse([ax - 5, ay - 5, ax + 5, ay + 5], fill=(192, 57, 75))
    return canvas


def main():
    out = os.path.join(ROOT, "docs", "images", "views")
    os.makedirs(out, exist_ok=True)
    comps = assembly.components()
    names = list(comps)
    asm, exp = [], []
    for name, (wp, kind) in comps.items():
        m = mesh_of(wp, COL.get(name, COL[kind]))
        asm.append(m)
        e = m.copy()
        e.apply_translation(offset_for(name))
        exp.append(e)
    ix = {n: i for i, n in enumerate(names)}
    render(asm, 28, 40, os.path.join(out, "iso_front.png"), size=(2000, 1400))
    render(asm, 28, 215, os.path.join(out, "iso_rear.png"), size=(2000, 1400))
    render(asm, 90, -90, os.path.join(out, "top.png"), size=(2000, 1700), ortho=True)
    render(asm, 0, -90, os.path.join(out, "side.png"), size=(2000, 900), ortho=True)
    render(asm, 35, 130, os.path.join(out, "iso_wheel_side.png"), size=(2000, 1400))
    keep = {"wheel", "carriage_a", "carriage_b", "carriage_c", "dial", "bearing_w1", "bearing_w2", "axle_bolt", "axle_nut",
            "dial_screw", "dial_nut", "clamp_screw"}
    keep |= {n for n in comps if n.startswith(("cscrew", "cnut", "ascrew", "anut"))}
    render([m for n, m in zip(names, asm) if n in keep], 32, 140, os.path.join(out, "carriage_closeup.png"), size=(1400, 1200))
    L = [("Pole arm", ["pole_arm"]), ("Pole weight", ["pole_weight"]), ("Weight lid", ["pole_weight_lid"]),
         ("Pole-joint bolt M3 x 35", ["pole_bolt"]), ("Elbow bolt M3 x 30", ["elbow_bolt"]),
         ("Bearing 623ZZ (elbow, pole)", ["elbow_bearing", "pole_bearing"]),
         ("Tracer arm (L = 100 mm)", ["tracer_arm"]), ("Tracer bolt M3 x 40", ["tracer_bolt"]),
         ("Block A: arm channel", ["carriage_a"]), ("Block screws M3 x 25 (x4)", ["ascrew0", "ascrew1", "ascrew2", "ascrew3"]),
         ("Front plate B: vernier, ballast", ["carriage_b"]), ("Rear plate C: dial axle", ["carriage_c"]),
         ("Wheel, 100 mm circumference", ["wheel"]), ("Counter dial, Geneva 10:1", ["dial"]),
         ("Wheel bearings 623ZZ (x2)", ["bearing_w1", "bearing_w2"]), ("Axle bolt M3 x 35", ["axle_bolt"]),
         ("Rubber feet (x3)", ["foot0", "foot1", "foot2"])]
    labels = [(t, [ix[n] for n in ns]) for t, ns in L]
    render(exp, 24, 150, os.path.join(out, "exploded.png"), size=(1800, 1500), labels=labels)


if __name__ == "__main__":
    main()
