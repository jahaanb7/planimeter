"""Measuring wheel: knurled rim, 50-division drum, two 623 bearing pockets, Geneva lock disc + crank plate.

Assembly pose: axle along +X at (WHEEL_A, WHEEL_B, Z_WHEEL).  The rim bottom touches the paper (z = 0).
Wheel local x (relative to WHEEL_A):
    -16.2 .. -14.0   crank plate (arm + pin pad)            2.2 thick
    -14.0 .. -10.4   lock disc with relief + Geneva pin     3.6 thick
    -10.4 .. -10.0   hub ring
    -10.0 ..  -2.0   knurled rim  (R = WHEEL_R, the rolling surface)
     -2.0 ..  10.0   drum (R = 13.5) with 50 engraved divisions and numerals (skirt cone x -2..0.4)
      bearing 1 pocket x -10..-6,  bearing 2 pocket x 6..10,  central bore dia 8
Print orientation: drum end (local +X) on the bed, axle vertical.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
from common import cyl_x  # noqa: E402
import geneva as G  # noqa: E402

# ---- local layout --------------------------------------------------------------------------
X_PLATE0, X_PLATE1 = -16.2, -14.0
X_LOCK0, X_LOCK1 = -14.0, -10.4
X_RIM0, X_RIM1 = -10.0, -2.0
X_DRUM0, X_DRUM1 = -2.0, 10.0
SKIRT_X1 = 0.4                      # 40-degree skirt under the rim so the rim prints without support
HUB_R = 7.5
POCKET_D = P.BEARING_OD + P.bearing_fit
POCKET_DEPTH = P.BEARING_W
BORE_D = 8.0
KNURL_N = 60
KNURL_DEPTH = 0.40
DRUM_R = P.DRUM_D / 2
GROOVE_W, GROOVE_D = 0.5, 0.35
DIV_DEG = 360.0 / P.DRUM_DIVS


def knurled_rim():
    pts = []
    for i in range(KNURL_N * 2):
        ang = math.radians(i * 180.0 / KNURL_N)
        r = P.WHEEL_R if i % 2 == 0 else P.WHEEL_R - KNURL_DEPTH
        pts.append((r * math.cos(ang), r * math.sin(ang)))
    return cq.Workplane("YZ").polyline(pts).close().extrude(X_RIM1 - X_RIM0).translate((X_RIM0, 0, 0))


def drum_marks():
    """Axial groove solids (one compound) + numerals; value of mark k is 2k cm^2 at rotation +k*7.2 deg."""
    cutters = []
    for k in range(P.DRUM_DIVS):
        major = (k % 5 == 0)
        x0 = 4.2 if major else 5.2
        x1 = 6.8
        g = (cq.Workplane("XY").box(x1 - x0, GROOVE_W, GROOVE_D + 1.0, centered=(False, True, False))
             .translate((x0, 0, DRUM_R - GROOVE_D)))
        cutters.append(g.rotate((0, 0, 0), (1, 0, 0), k * DIV_DEG).val())
    return cutters


def numerals():
    out = []
    for k in range(0, P.DRUM_DIVS, 5):
        label = str(2 * k)
        t = (cq.Workplane(cq.Plane(origin=(0.9, 0, DRUM_R + 0.2), xDir=(1, 0, 0), normal=(0, 0, 1)))
             .text(label, 2.4, -(GROOVE_D + 0.2), combine=False, halign="left", valign="center"))
        out.append(t.rotate((0, 0, 0), (1, 0, 0), k * DIV_DEG).val())
    return out


def to_wheel_frame(solid, x0):
    """Geneva local (x_g, y_g, z_g) -> wheel local: X = z_g + x0, Y = y_g, Z = -x_g."""
    return solid.rotate((0, 0, 0), (0, 1, 0), 90).translate((x0, 0, 0))


def build():
    rim = knurled_rim()
    drum = cyl_x(DRUM_R, X_DRUM0, X_DRUM1)
    hub = cyl_x(HUB_R, X_LOCK1, X_RIM0)                             # hub disc: joins lock disc to rim and supports the pin base
    lock = to_wheel_frame(G.build_drive(t=X_LOCK1 - X_LOCK0, relief_deg=P.GEN_RELIEF_DEG, bore_r=3.0), X_LOCK0)
    plate = to_wheel_frame(G.build_arm_plate(t=X_PLATE1 - X_PLATE0, bore_r=3.0), X_PLATE0)
    # the pin has to reach back to the crank plate: extend it through the dial plane
    pin_ext = (cq.Workplane("XY").center(-G.A, 0).circle(P.GEN_PIN_D / 2).extrude(X_LOCK1 - X_PLATE0 + 0.2))
    pin_ext = to_wheel_frame(pin_ext, X_PLATE0)
    skirt = (cq.Workplane("XY").polyline([(X_DRUM0, 0), (X_DRUM0, P.WHEEL_R - KNURL_DEPTH),
                                          (SKIRT_X1, DRUM_R), (SKIRT_X1, 0)])
             .close().revolve(360, (0, 0, 0), (1, 0, 0)))
    geo = lock.union(plate).union(pin_ext).rotate((0, 0, 0), (1, 0, 0), -P.GEN_PHASE_DEG)   # pin phase: theta = 72 deg at drum zero
    w = rim.union(drum).union(skirt).union(hub).union(geo)

    # bearing pockets + through bore
    w = w.cut(cyl_x(POCKET_D / 2, X_RIM0, X_RIM0 + POCKET_DEPTH))
    w = w.cut(cyl_x(POCKET_D / 2, X_DRUM1 - POCKET_DEPTH, X_DRUM1))
    w = w.cut(cyl_x(BORE_D / 2, X_RIM0 - 0.1, X_DRUM1 + 0.1))
    w = w.cut(cyl_x(3.05, X_LOCK1 - 0.05, X_RIM0 + 0.1))          # hub disc bore (dia 6.1) for the rear standoff ring

    # engraving
    w = w.cut(cq.Workplane("XY").add(cq.Compound.makeCompound(drum_marks())))
    w = w.cut(cq.Workplane("XY").add(cq.Compound.makeCompound(numerals())))
    return w.translate((P.WHEEL_A, P.WHEEL_B, P.Z_WHEEL))


def print_orient(shape):
    """Axle vertical, drum end on the bed: local +X -> down (-Z)."""
    s = shape.translate((-P.WHEEL_A, -P.WHEEL_B, -P.Z_WHEEL))
    s = s.rotate((0, 0, 0), (0, 1, 0), 90)             # (x, z) -> (z, -x): +X goes to -Z
    bb = s.val().BoundingBox()
    return s.translate((0, 0, -bb.zmin))


if __name__ == "__main__":
    from common import export
    w = build()
    v = w.val()
    print("valid:", v.isValid(), " volume mm3:", round(v.Volume(), 1), " mass (solid PLA) g:",
          round(v.Volume() * P.RHO_PLA, 1))
    bb = v.BoundingBox()
    print(f"bbox x {bb.xmin:.2f}..{bb.xmax:.2f}  y {bb.ymin:.2f}..{bb.ymax:.2f}  z {bb.zmin:.2f}..{bb.zmax:.2f}")
    export(w, "wheel", orient=print_orient)
