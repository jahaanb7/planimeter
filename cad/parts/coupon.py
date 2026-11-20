"""Tolerance coupon.  Print this FIRST (0.2 mm layers, same settings as the real parts) and find:
  - which bearing-pocket diameter gives a firm press fit for a 623ZZ  -> params.bearing_fit
  - which channel clearance lets the 12 x 8 arm slide without rocking -> params.arm_clearance
  - which nut-trap size holds an M3 nut                                -> params.nut_clear
Printed flat.  Labels are engraved so the right size is identifiable.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_z, hex_prism_z, export  # noqa: E402

T = 6.0


def build():
    base = box(0, 84, 0, 62, 0, T)
    # row 1: bearing pockets (through) bearing_fit = 0.00 .. 0.25
    for i, fit in enumerate((0.00, 0.05, 0.10, 0.15, 0.20, 0.25)):
        x = 8 + 13.5 * i
        base = base.cut(cyl_z((P.BEARING_OD + fit) / 2, -1, T - 1.2, x=x, y=50))
        base = base.cut(cyl_z(3.0, -1, T + 1, x=x, y=50))
        t = (cq.Workplane("XY").workplane(offset=T).center(x, 41.0)
             .text(f"{fit:.2f}", 2.4, -0.4, combine=False, halign="center", valign="center"))
        base = base.cut(t)
    # row 2: channel slots for the arm: clearance per side 0.10 .. 0.40, through
    for i, c in enumerate((0.10, 0.20, 0.25, 0.30, 0.40)):
        x = 9 + 15.5 * i
        base = base.cut(box(x - (P.ARM_W + 2 * c) / 2 * 0 - 0, x + (P.ARM_W + 2 * c), 22, 22 + P.ARM_T + 2 * c, -1, T + 1)
                        .translate((-(P.ARM_W) / 2 + 0.0, 0, 0))) if False else base
        w = P.ARM_W + 2 * c
        h = P.ARM_T + 2 * c
        base = base.cut(box(x, x + w, 24, 24 + h, -1, T + 1))
        t = (cq.Workplane("XY").workplane(offset=T).center(x + w / 2, 20.0)
             .text(f"{c:.2f}", 2.4, -0.4, combine=False, halign="center", valign="center"))
        base = base.cut(t)
    # row 3: M3 nut traps af + 0.05 .. 0.35 (blind) and M3 clearance holes 3.2 / 3.3 / 3.4 / 3.5
    for i, c in enumerate((0.05, 0.15, 0.20, 0.30, 0.35)):
        x = 8 + 13.0 * i
        base = base.cut(hex_prism_z(P.M3_NUT_AF + c, T - P.M3_NUT_H - 0.2, T + 1, x=x, y=9))
        base = base.cut(cyl_z(P.M3_CLEAR / 2, -1, T + 1, x=x, y=9))
        t = (cq.Workplane("XY").workplane(offset=T).center(x, 2.6)
             .text(f"{c:.2f}", 2.0, -0.4, combine=False, halign="center", valign="center"))
        base = base.cut(t)
    return base


def print_orient(shape):
    return shape


if __name__ == "__main__":
    c = build()
    print("coupon valid:", c.val().isValid(), " bbox", round(c.val().BoundingBox().xlen, 1), "x", round(c.val().BoundingBox().ylen, 1))
    export(c, "tolerance_coupon", orient=print_orient)
