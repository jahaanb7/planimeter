"""Plate C: rear wheel plate with rear standoff ring, two posts to plate B, and the Geneva dial axle boss.

Print orientation: outer (rear) face down, posts/rings/boss point up (+X up).
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402
from common import box, cyl_x, hex_prism_x, export  # noqa: E402

NUT_AF = P.M3_NUT_AF + P.nut_clear
AX_Y, AX_Z = P.WHEEL_B, P.Z_WHEEL
X_OUT = P.X_REAR_FACE - P.C_T            # outer (rear) face
X_IN = P.X_REAR_FACE                     # wheel-facing face


def build():
    plate = box(X_OUT, X_IN, 8.0, P.POST_Y + 4.0, 3.0, P.DIAL_Z + 6.0)
    # rear standoff ring: reaches through the crank plate and lock disc to the bearing-1 inner race
    x_race = P.WHEEL_A - 10.0
    plate = plate.union(cyl_x(P.standoff_d / 2, X_IN - 0.1, x_race, y=AX_Y, z=AX_Z))
    # posts to plate B (dia 8 around the screw)
    for z in P.POST_Z:
        plate = plate.union(cyl_x(4.0, X_IN - 0.1, P.X_FRONT_FACE, y=P.POST_Y, z=z))
        plate = plate.cut(cyl_x(P.M3_CLEAR / 2, X_OUT - 1, P.X_FRONT_FACE + 1, y=P.POST_Y, z=z))
        plate = plate.cut(hex_prism_x(NUT_AF, X_OUT - 0.1, X_OUT + P.M3_NUT_H + 0.2, y=P.POST_Y, z=z))
    # axle: bore + head counterbore on the outer face
    plate = plate.cut(cyl_x(P.M3_CLEAR / 2, X_OUT - 1, x_race + 1, y=AX_Y, z=AX_Z))
    plate = plate.cut(cyl_x(3.2, X_OUT - 0.1, X_OUT + P.M3_HEAD_H + 0.3, y=AX_Y, z=AX_Z))
    # dial axle boss (dia 6) up to the dial's back face; screw hole + nut trap on the outer face
    plate = plate.union(cyl_x(3.0, X_IN - 0.1, P.DIAL_X0 - 0.3, y=AX_Y, z=P.DIAL_Z))
    plate = plate.cut(cyl_x(P.M3_CLEAR / 2, X_OUT - 1, P.DIAL_X0, y=AX_Y, z=P.DIAL_Z))
    plate = plate.cut(hex_prism_x(NUT_AF, X_OUT - 0.1, X_OUT + P.M3_NUT_H + 0.2, y=AX_Y, z=P.DIAL_Z))
    return plate


def print_orient(shape):
    """Outer face down: +X -> +Z (rotate -90 about Y), then drop onto z = 0."""
    s = shape.rotate((0, 0, 0), (0, 1, 0), -90)
    bb = s.val().BoundingBox()
    return s.translate((-bb.xmin, -bb.ymin, -bb.zmin))


if __name__ == "__main__":
    b = build()
    v = b.val()
    print("C valid:", v.isValid(), "vol", round(v.Volume()), "mm3")
    export(b, "carriage_c_rear_plate", orient=print_orient)
