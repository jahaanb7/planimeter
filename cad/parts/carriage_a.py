"""Carriage block A: tracer-arm channel, elbow pivot post, clamp screw, four screws to plate B.

Assembly pose: see params.py.  The channel axis is +X (tracer arm direction).
Print orientation: +X UP (rear face x = X_BLOCK0 on the bed).  The channel is then a vertical rectangular
bore, so its outline is as accurate as the printer's XY, and it is parallel to Z by construction.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_x, cyl_y, cyl_z, hex_prism_y, hex_prism_z, export  # noqa: E402

NUT_AF = P.M3_NUT_AF + P.nut_clear


def build():
    blk = box(P.X_BLOCK0, P.X_BLOCK1, P.BLOCK_Y0, P.BLOCK_Y1, P.BLOCK_Z0, P.BLOCK_Z1)
    # elbow pivot shoulder (touches only the bearing inner race): dia 5.0, top at Z_POLE_ARM
    blk = blk.union(cyl_z(P.standoff_d / 2, P.BLOCK_Z1 - 0.1, P.Z_POLE_ARM))
    # tracer-arm channel, through
    zc = P.Z_ARM
    y_lo, y_hi = P.ARM_W / 2 - P.CH_W, P.ARM_W / 2        # datum wall at y = +ARM_W/2: clamped arm centreline = pivot axis
    blk = blk.cut(box(P.X_BLOCK0 - 1, P.X_BLOCK1 + 1, y_lo, y_hi, zc - P.CH_H / 2, zc + P.CH_H / 2))
    # pivot bolt hole through shoulder + block (the arm has a slot for it) and nut trap in the bottom face
    blk = blk.cut(cyl_z(P.M3_CLEAR / 2, P.BLOCK_Z0 - 1, P.Z_POLE_ARM + 1))
    blk = blk.cut(hex_prism_z(NUT_AF, P.BLOCK_Z0 - 0.1, P.BLOCK_Z0 + P.M3_NUT_H + 0.2))
    # clamp screw: from the -Y face, pushes the arm against the +Y datum wall
    blk = blk.cut(cyl_y(P.M3_CLEAR / 2, P.BLOCK_Y0 - 1, y_lo + 0.5, x=P.CLAMP_X, z=zc))
    blk = blk.cut(hex_prism_y(NUT_AF, P.BLOCK_Y0 - 0.1, P.BLOCK_Y0 + P.M3_NUT_H + 0.2, x=P.CLAMP_X, z=zc))
    # four screws to plate B: heads recessed in the front face
    for (y, z) in P.BLOCK_SCREWS:
        blk = blk.cut(cyl_x(P.M3_CLEAR / 2, P.X_BLOCK0 - 1, P.X_BLOCK1 + 1, y=y, z=z))
        blk = blk.cut(cyl_x(3.1, P.X_BLOCK1 - 3.2, P.X_BLOCK1 + 1, y=y, z=z))
    return blk


def print_orient(shape):
    s = shape.rotate((0, 0, 0), (0, 1, 0), -90)           # (x,y,z) -> (-z, y, x): +X up
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    b = build()
    v = b.val()
    print("A valid:", v.isValid(), "vol", round(v.Volume()), "mm3")
    export(b, "carriage_a_block", orient=print_orient)
