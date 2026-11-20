"""Pole weight (centred on its pivot axis at the origin) and its lid.

Body stands on three 10 mm self-adhesive rubber feet (FOOT_H thick) so it does not slide on the paper.
The pivot bolt (M3 x 40) runs up the central column from a nut trap in the base; the pole arm's bearing sits on the
column shoulder exactly as at the carriage.  The annular cavity takes ~80 g of steel shot / washers, closed by the lid.

Print: body upright (as built), lid flat.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import cyl_z, hex_prism_z, export  # noqa: E402

FOOT_H = 1.5
OUT_R = 22.5
COL_R = 5.5
CAV_R = 19.0
LID_T = 2.0
Z_TOP = P.BLOCK_Z1                  # 29.25: same shoulder base as the carriage
FLOOR = 4.0
NUT_AF = P.M3_NUT_AF + P.nut_clear
FEET_R = 15.0


def build_body():
    z_lid = Z_TOP - LID_T
    body = cyl_z(OUT_R, FOOT_H, z_lid)
    body = body.cut(cyl_z(CAV_R, FOOT_H + FLOOR, z_lid + 1).cut(cyl_z(COL_R, FOOT_H + FLOOR - 1, z_lid + 2)))
    body = body.union(cyl_z(COL_R, z_lid - 0.1, z_lid + 0.1))
    body = body.cut(cyl_z(P.M3_CLEAR / 2, FOOT_H - 1, Z_TOP + 1))
    body = body.cut(hex_prism_z(NUT_AF, FOOT_H - 0.1, FOOT_H + P.M3_NUT_H + 0.2))
    return body


def build_column_top():
    """Shoulder ring that carries the bearing inner race (part of the lid so the lid locates on the column)."""
    return cyl_z(P.standoff_d / 2, Z_TOP - 0.1, P.Z_POLE_ARM)


def build_lid():
    z_lid = Z_TOP - LID_T
    lid = cyl_z(OUT_R, z_lid, Z_TOP).cut(cyl_z(COL_R + 0.15, z_lid - 1, Z_TOP + 1))
    # lid is slipped over the column; the column carries the shoulder ring
    return lid


def build_column_cap():
    """Column extension through the lid up to the shoulder."""
    z_lid = Z_TOP - LID_T
    col = cyl_z(COL_R, z_lid, Z_TOP).union(cyl_z(P.standoff_d / 2, Z_TOP - 0.1, P.Z_POLE_ARM))
    return col.cut(cyl_z(P.M3_CLEAR / 2, z_lid - 1, P.Z_POLE_ARM + 1))


def build():
    return build_body().union(build_column_cap())


def feet():
    out = []
    for k in range(3):
        a = math.radians(90 + 120 * k)
        out.append(cyl_z(5.0, 0, FOOT_H, x=FEET_R * math.cos(a), y=FEET_R * math.sin(a)))
    return out


def print_orient(shape):
    bb = shape.val().BoundingBox()
    return shape.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    b = build()
    l = build_lid()
    print("weight valid:", b.val().isValid(), "lid valid:", l.val().isValid(),
          "cavity volume cm3:", round(math.pi * (CAV_R ** 2 - COL_R ** 2) * (Z_TOP - LID_T - FOOT_H - FLOOR) / 1000, 1))
    export(b, "pole_weight", orient=print_orient)
    export(l, "pole_weight_lid", orient=lambda s: s.translate((0, 0, -(Z_TOP - LID_T))))
