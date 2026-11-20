"""Off-the-shelf hardware as simple solids (assembly frame).  Used for clash checks, mass and the renders."""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402
from common import cyl_x, cyl_y, cyl_z, hex_prism_x, hex_prism_y, hex_prism_z  # noqa: E402

MASS = {"bearing": 1.1, "bolt_per_mm": 0.055, "nut": 0.25, "washer": 0.1}   # grams (M3 steel)


def bearing_x(x0, y, z):
    """623ZZ with its axis along X, one face at x0 (extends to x0 + 4)."""
    return cyl_x(P.BEARING_OD / 2, x0, x0 + P.BEARING_W, y, z).cut(cyl_x(P.BEARING_ID / 2, x0 - 1, x0 + 5, y, z))


def bearing_z(x, y, z0):
    return cyl_z(P.BEARING_OD / 2, z0, z0 + P.BEARING_W, x, y).cut(cyl_z(P.BEARING_ID / 2, z0 - 1, z0 + 5, x, y))


def bolt_x(x_head_under, length, y, z, direction):
    """M3 socket-head bolt along X.  direction = +1: shank runs toward +X from the head underside."""
    if direction > 0:
        shank = cyl_x(1.5, x_head_under, x_head_under + length, y, z)
        head = cyl_x(P.M3_HEAD_D / 2, x_head_under - P.M3_HEAD_H, x_head_under, y, z)
    else:
        shank = cyl_x(1.5, x_head_under - length, x_head_under, y, z)
        head = cyl_x(P.M3_HEAD_D / 2, x_head_under, x_head_under + P.M3_HEAD_H, y, z)
    return shank.union(head)


def bolt_z(z_head_under, length, x, y):
    """M3 bolt along Z, shank running DOWN from the head underside."""
    shank = cyl_z(1.5, z_head_under - length, z_head_under, x, y)
    head = cyl_z(P.M3_HEAD_D / 2, z_head_under, z_head_under + P.M3_HEAD_H, x, y)
    return shank.union(head)


def nut_x(x0, y, z):
    return hex_prism_x(P.M3_NUT_AF, x0, x0 + P.M3_NUT_H, y, z).cut(cyl_x(1.5, x0 - 1, x0 + 4, y, z))


def nut_z(z0, x, y):
    return hex_prism_z(P.M3_NUT_AF, z0, z0 + P.M3_NUT_H, x, y).cut(cyl_z(1.5, z0 - 1, z0 + 4, x, y))


def washer_z(z0, x, y):
    return cyl_z(3.5, z0, z0 + 0.5, x, y).cut(cyl_z(1.6, z0 - 1, z0 + 2, x, y))
