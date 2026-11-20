"""Calibration rule.  Pin the pivot hole into the board, rest the tracer tip in the cone seat and sweep one full circle:
the area enclosed is exactly CHECK_AREA_CM2 (100 cm^2, r = 56.419 mm).  The reading tells you how to correct L.

Print: flat.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_z, export  # noqa: E402

T = 3.0
W = 12.0
R = P.CHECK_R


def build():
    rule = box(-6, R + 8, -W / 2, W / 2, 0, T)
    rule = rule.union(cyl_z(W / 2, 0, T, x=-6, y=0)).union(cyl_z(W / 2, 0, T, x=R + 8, y=0))
    rule = rule.cut(cyl_z(0.6, -1, T + 1, x=0, y=0))                                     # pivot pin (dress pin / needle)
    # 90-degree cone seat for the M3 tracer tip: dia 5.4 at the top, 2.5 deep
    seat = (cq.Workplane("XY").workplane(offset=T - 2.5).center(R, 0).circle(0.2)
            .workplane(offset=2.5 + 0.01).circle(2.7).loft(combine=True))
    rule = rule.cut(seat)
    t = (cq.Workplane("XY").workplane(offset=T).center(R / 2 + 3, 0)
         .text("100 cm2  r=56.42", 3.2, -0.4, combine=False, halign="center", valign="center"))
    return rule.cut(t)


def print_orient(shape):
    return shape.translate((0, 0, 0))


if __name__ == "__main__":
    r = build()
    print("check rule valid:", r.val().isValid(), " seat radius", round(R, 3))
    export(r, "check_rule", orient=print_orient)
