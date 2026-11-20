"""Pole arm: 13 x 6 bar, one 623 bearing at each end (pivot-to-pivot R_POLE = 160 mm).

Built along +X from the elbow pivot at (0, 0); the assembly rotates it about Z.
Underside at z = Z_POLE_ARM.  Bearings press in from below (pockets open downward).
Print orientation: flat with the underside UP (pockets open upward, so nothing bridges).
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_z, export  # noqa: E402

W = 13.0
END_R = W / 2
POCKET_D = P.BEARING_OD + P.bearing_fit
TOP_HOLE_D = 8.0
Z0 = P.Z_POLE_ARM
Z1 = Z0 + P.POLE_T


def build():
    arm = box(0, P.R_POLE, -W / 2, W / 2, Z0, Z1)
    for x in (0.0, P.R_POLE):
        arm = arm.union(cyl_z(END_R, Z0, Z1, x=x, y=0))
    for x in (0.0, P.R_POLE):
        arm = arm.cut(cyl_z(POCKET_D / 2, Z0 - 1, Z0 + P.BEARING_W, x=x, y=0))
        arm = arm.cut(cyl_z(TOP_HOLE_D / 2, Z0, Z1 + 1, x=x, y=0))
    return arm


def print_orient(shape):
    s = shape.rotate((0, 0, 0), (1, 0, 0), 180)           # underside up
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    a = build()
    v = a.val()
    print("pole arm valid:", v.isValid(), "vol", round(v.Volume()))
    export(a, "pole_arm", orient=print_orient)
