"""Plate B: front wheel plate with front standoff ring, vernier arc, ballast box and screw nut traps.

Print orientation: back face (x = X_BLOCK0, the face that mates with block A) DOWN; wheel-facing features
(standoff ring, vernier arc, nut traps) point up.  The ballast box is a tall box rising from the plate
toward -X, so nothing overhangs.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_x, hex_prism_x, export  # noqa: E402

NUT_AF = P.M3_NUT_AF + P.nut_clear
AX_Y, AX_Z = P.WHEEL_B, P.Z_WHEEL
VERN_R0, VERN_R1 = P.DRUM_D / 2 + 0.4, P.DRUM_D / 2 + 1.2
VERN_X0 = P.WHEEL_A + 7.3                       # first x of the vernier arc (drum marks end at local 6.8)
VERN_HALF = 40.0                                # angular half-extent about the top (deg)
DIV = 360.0 / P.DRUM_DIVS


def vernier():
    ring = cyl_x(VERN_R1, VERN_X0, P.X_FRONT_FACE + 0.2, y=AX_Y, z=AX_Z).cut(
        cyl_x(VERN_R0, VERN_X0 - 1, P.X_FRONT_FACE + 1, y=AX_Y, z=AX_Z))
    a = math.radians(VERN_HALF)
    R = 40.0
    wedge = (cq.Workplane("YZ").polyline([(AX_Y, AX_Z),
                                          (AX_Y - R * math.sin(a), AX_Z + R * math.cos(a)),
                                          (AX_Y + R * math.sin(a), AX_Z + R * math.cos(a))]).close()
             .extrude(P.X_FRONT_FACE + 1 - (VERN_X0 - 1)).translate((VERN_X0 - 1, 0, 0)))
    plate = ring.intersect(wedge)
    # 11 vernier lines (spacing 0.9 of a drum division), zero line at the top and longer
    cutters = []
    for j in range(P.VERNIER_DIVS + 1):
        beta = 0.9 * DIV * j
        x0 = VERN_X0 + (0.3 if j % 5 else 0.3)
        g = (cq.Workplane("XY").box(P.X_FRONT_FACE - x0 - 0.3, 0.5, 0.3 + 1.0, centered=(False, True, False))
             .translate((x0, 0, VERN_R1 - 0.3)))
        g = g.rotate((0, 0, 0), (1, 0, 0), beta).translate((0, AX_Y, AX_Z))
        cutters.append(g.val())
    return plate.cut(cq.Workplane("XY").add(cq.Compound.makeCompound(cutters)))


def build():
    x0, x1 = P.X_FRONT_FACE, P.X_BLOCK0
    plate = box(x0, x1, P.BLOCK_Y0, P.B_Y1, 3.0, 30.0).union(box(x0, x1, 12.0, P.B_Y1, 3.0, 36.0))
    # ballast box: rises from the plate toward -X (up in the print), pocket open at the -X end
    x_rear = P.X_REAR_FACE - P.C_T
    box_ = box(x_rear, x1, P.BALLAST_Y0 - 0.5, P.BALLAST_Y1, 3.0, 35.0)
    pocket = box(x_rear - 1, x1 - 2.0, P.BALLAST_Y0 + 1.5, P.BALLAST_Y1 - 2.0, 6.0, 32.0)
    plate = plate.union(box_).cut(pocket)
    # arm clearance hole (the arm is guided by block A only)
    plate = plate.cut(box(x0 - 1, x1 + 1, -7.0, 7.0, P.Z_ARM - 5.5, P.Z_ARM + 5.5))
    # wheel axle: front standoff ring + bore + nut trap on the back face
    plate = plate.union(cyl_x(P.standoff_d / 2, P.WHEEL_X_FRONT, x0 + 0.1, y=AX_Y, z=AX_Z))
    plate = plate.cut(cyl_x(P.M3_CLEAR / 2, P.WHEEL_X_FRONT - 1, x1 + 1, y=AX_Y, z=AX_Z))
    plate = plate.cut(hex_prism_x(NUT_AF, x1 - P.M3_NUT_H - 0.4, x1 + 0.1, y=AX_Y, z=AX_Z))
    # block-A screws: nut traps on the wheel-facing face
    for (y, z) in P.BLOCK_SCREWS:
        plate = plate.cut(cyl_x(P.M3_CLEAR / 2, x0 - 1, x1 + 1, y=y, z=z))
        plate = plate.cut(hex_prism_x(NUT_AF, x0 - 0.1, x0 + P.M3_NUT_H + 0.2, y=y, z=z))
    # plate-C screws: heads recessed in the back face
    for z in P.POST_Z:
        plate = plate.cut(cyl_x(P.M3_CLEAR / 2, x0 - 1, x1 + 1, y=P.POST_Y, z=z))
        plate = plate.cut(cyl_x(3.1, x1 - 3.2, x1 + 1, y=P.POST_Y, z=z))
    return plate.union(vernier())


def print_orient(shape):
    """Back face down: +X -> -Z (rotate +90 about Y), then drop onto z = 0."""
    s = shape.rotate((0, 0, 0), (0, 1, 0), 90)
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    b = build()
    v = b.val()
    print("B valid:", v.isValid(), "vol", round(v.Volume()), "mm3")
    export(b, "carriage_b_front_plate", orient=print_orient)
