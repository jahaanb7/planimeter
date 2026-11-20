"""Small CadQuery helpers shared by every part (all in the assembly frame, mm)."""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(__file__))
import params as P  # noqa: E402,F401


def box(x0, x1, y0, y1, z0, z1):
    return (cq.Workplane("XY").box(x1 - x0, y1 - y0, z1 - z0, centered=False)
            .translate((x0, y0, z0)))


def cyl_x(r, x0, x1, y=0.0, z=0.0):
    return cq.Workplane("YZ").circle(r).extrude(x1 - x0).translate((x0, y, z))


def cyl_y(r, y0, y1, x=0.0, z=0.0):
    return cq.Workplane("XZ").circle(r).extrude(-(y1 - y0)).translate((x, y0, z))


def cyl_z(r, z0, z1, x=0.0, y=0.0):
    return cq.Workplane("XY").circle(r).extrude(z1 - z0).translate((x, y, z0))


def hex_prism_x(af, x0, x1, y=0.0, z=0.0):
    d = af / 0.8660254
    return (cq.Workplane("YZ").polygon(6, d).extrude(x1 - x0).translate((x0, y, z)))


def hex_prism_z(af, z0, z1, x=0.0, y=0.0):
    d = af / 0.8660254
    return cq.Workplane("XY").polygon(6, d).extrude(z1 - z0).translate((x, y, z0))


def hex_prism_y(af, y0, y1, x=0.0, z=0.0):
    d = af / 0.8660254
    return (cq.Workplane("XZ").polygon(6, d).extrude(-(y1 - y0)).translate((x, y0, z)))


def export(shape, path_stem, outdir_stl="stl", outdir_step="step", orient=None):
    """Export STL (in print orientation if `orient` is given) and STEP (assembly pose)."""
    root = os.path.join(os.path.dirname(__file__), "..")
    os.makedirs(os.path.join(root, outdir_stl), exist_ok=True)
    os.makedirs(os.path.join(root, outdir_step), exist_ok=True)
    cq.exporters.export(shape, os.path.join(root, outdir_step, path_stem + ".step"))
    printable = orient(shape) if orient else shape
    cq.exporters.export(printable, os.path.join(root, outdir_stl, path_stem + ".stl"),
                        tolerance=0.01, angularTolerance=0.1)
