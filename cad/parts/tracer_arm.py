"""Tracer arm: 12 x 8 bar with a slot for the elbow pivot bolt, an L scale and the tracer knob.

Assembly pose (L = 100): pivot axis at x = 0, tracer axis at x = L, arm centreline at z = Z_ARM.
The arm slides in the carriage channel; the pivot bolt passes through the slot so the pivot axis stays ON
the arm centreline, which the planimeter equation requires (a lateral offset d adds an unmeasured -2d*oint dE.u term).

L scale: a mark labelled v sits at x = X_BLOCK1 + 100 - v at the nominal setting, so the value aligned with the
front face of block A (x = X_BLOCK1) is the arm length L.  Marks every 1 mm, long every 5 mm, 90..110 (fine adjustment is done with the check rule).

Print orientation: flat, scale face UP (as in assembly).  The knob is a 12 mm cylinder (no overhang).
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_z, hex_prism_z, export  # noqa: E402

X_REAR = -14.0
X_FRONT = P.L + 14.0
KNOB_H = 10.0
NUT_AF = P.M3_NUT_AF + P.nut_clear
SLOT_W = P.M3_CLEAR + 0.2


def scale_cutters():
    z_top = P.Z_ARM + P.ARM_T / 2
    out = []
    for v in range(90, 111):                       # 1 mm marks (0.5 mm lines, 0.5 mm webs: printable with a 0.4 mm nozzle)
        x = P.X_BLOCK1 + P.L - v
        ln = 7.0 if v % 5 == 0 else 4.0
        g = (cq.Workplane("XY").box(0.5, ln, 0.6, centered=(True, True, False))
             .translate((x, -P.ARM_W / 2 + 0.3 + ln / 2, z_top - 0.3)))
        out.append(g.val())
    for v in range(90, 111, 5):
        x = P.X_BLOCK1 + P.L - v
        t = (cq.Workplane(cq.Plane(origin=(x + 0.7, 3.4, z_top + 0.1), xDir=(0, 1, 0), normal=(0, 0, 1)))
             .text(str(v), 2.4, -0.4, combine=False, halign="center", valign="center"))
        out.append(t.val())
    return out


def build():
    z0, z1 = P.Z_ARM - P.ARM_T / 2, P.Z_ARM + P.ARM_T / 2
    arm = box(X_REAR, X_FRONT, -P.ARM_W / 2, P.ARM_W / 2, z0, z1)
    arm = arm.union(cyl_z(P.ARM_W / 2, z1 - 0.1, z1 + KNOB_H, x=P.L, y=0))                  # knob
    # slot for the pivot bolt, +-6 mm of travel
    travel = 6.0
    slot = (cq.Workplane("XY").center(0, 0).slot2D(2 * travel + SLOT_W, SLOT_W, 0).extrude(P.ARM_T + 2)
            .translate((0, 0, z0 - 1)))
    arm = arm.cut(slot)
    # tracer bolt: bore through the knob and arm, nut trap in the knob top
    arm = arm.cut(cyl_z(P.M3_CLEAR / 2, z0 - 1, z1 + KNOB_H + 1, x=P.L, y=0))
    arm = arm.cut(hex_prism_z(NUT_AF, z1 + KNOB_H - P.M3_NUT_H - 0.2, z1 + KNOB_H + 0.1, x=P.L, y=0))
    for c in scale_cutters():                    # cut one at a time: the label text overlaps nothing, but keep booleans simple
        arm = arm.cut(cq.Workplane("XY").add(c))
    return arm


def print_orient(shape):
    bb = shape.val().BoundingBox()
    return shape.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    a = build()
    v = a.val()
    bb = v.BoundingBox()
    print("tracer arm valid:", v.isValid(), "vol", round(v.Volume()), f"bbox {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f}")
    export(a, "tracer_arm", orient=print_orient)
