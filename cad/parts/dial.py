"""Geneva counter dial: 10 slots, digits 0-9 on the front face.  One wheel revolution = one digit.

Built in its START rest orientation (a scallop centre pointing down at the wheel, reading 0 at the top).
Assembly pose: axis along X at (DIAL_X0 .. DIAL_X0 + GEN_T, WHEEL_B, DIAL_Z).
Print orientation: flat, front face (digits) UP -> axis vertical, rear face on the bed.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
import geneva as G  # noqa: E402
from common import export  # noqa: E402

DIGIT_R = 14.2
DIGIT_H = 3.2
DIGIT_DEPTH = 0.4


def build():
    d = G.build_dial(t=P.GEN_T, with_bore=True)
    d = d.rotate((0, 0, 0), (0, 0, 1), -G.STEP / 2)                # start rest orientation (alpha = -18 deg)
    d = d.rotate((0, 0, 0), (0, 1, 0), 90)                          # x_g -> -Z, z_g -> +X, y_g -> +Y
    # digits on the front face (x = +GEN_T), upright for a viewer looking toward -X
    cutters = []
    for j in range(10):
        ang = math.radians(36.0 * j)
        cy, cz = DIGIT_R * math.sin(ang), DIGIT_R * math.cos(ang)
        t = (cq.Workplane(cq.Plane(origin=(P.GEN_T, cy, cz), xDir=(0, 1, 0), normal=(1, 0, 0)))
             .text(str(j), DIGIT_H, -DIGIT_DEPTH, combine=False, halign="center", valign="center"))
        cutters.append(t.val())
    d = d.cut(cq.Workplane("XY").add(cq.Compound.makeCompound(cutters)))
    return d.translate((P.DIAL_X0, P.WHEEL_B, P.DIAL_Z))


def print_orient(shape):
    s = shape.rotate((0, 0, 0), (0, 1, 0), -90)                   # +X up
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    d = build()
    v = d.val()
    print("dial valid:", v.isValid(), "vol", round(v.Volume()), "mm3")
    export(d, "counter_dial", orient=print_orient)
