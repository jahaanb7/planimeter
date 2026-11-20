"""10-slot external Geneva indexer: one wheel revolution advances the counter dial by 36 degrees.

Local frame for the 2-D design (extruded along +Z by `t`):
    dial centre  = (0, 0)
    drive centre = (C, 0)
    drive angle theta = 0  <=>  pin on the line of centres, pointing at the dial.

Kinematics (pin in slot):   tan(phi) = a sin(theta) / (C - a cos(theta)),   |theta| <= 90 deg - 180/n.
The dial turns by exactly 360/n per drive revolution and is locked by the lock disc otherwise.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import params as P  # noqa: E402

N = P.GEN_N
A = P.GEN_PIN_A
C = P.GEN_C
STEP = 360.0 / N
HALF = 90.0 - 180.0 / N                     # engagement half-angle of the drive (72 deg)


def dial_angle(theta_deg):
    """Dial orientation (deg) for drive angle theta_deg in (-180, 180]; slot 0 at 0 deg initially."""
    if abs(theta_deg) <= HALF:
        t = math.radians(theta_deg)
        return math.degrees(math.atan2(A * math.sin(t), C - A * math.cos(t)))
    return STEP / 2 if theta_deg > 0 else -STEP / 2


def build_dial(t=P.GEN_T, with_bore=True, hub_r=4.5):
    d = cq.Workplane("XY").circle(P.GEN_TIP_R).extrude(t)
    r_end = C - A - 0.25                           # slot end-circle centre radius
    for k in range(N):
        ang = k * STEP
        slot = (cq.Workplane("XY").center(0, 0)
                .moveTo(r_end, -P.GEN_SLOT_W / 2).lineTo(P.GEN_TIP_R + 2, -P.GEN_SLOT_W / 2)
                .lineTo(P.GEN_TIP_R + 2, P.GEN_SLOT_W / 2).lineTo(r_end, P.GEN_SLOT_W / 2)
                .threePointArc((r_end - P.GEN_SLOT_W / 2, 0), (r_end, -P.GEN_SLOT_W / 2))
                .close().extrude(t).rotate((0, 0, 0), (0, 0, 1), ang))
        d = d.cut(slot)
        mid = ang + STEP / 2
        sx, sy = C * math.cos(math.radians(mid)), C * math.sin(math.radians(mid))
        scallop = cq.Workplane("XY").center(sx, sy).circle(P.GEN_LOCK_R + 0.3).extrude(t)
        d = d.cut(scallop)
    if with_bore:
        d = d.cut(cq.Workplane("XY").circle(P.M3_CLEAR / 2 + 0.1).extrude(t))
    return d


def build_drive(t=P.GEN_T, relief_deg=75.0, bore_r=3.0, arm_w=None):
    """Lock disc + relief + pin, centred on the drive axis (0,0), pin toward -X (angle 180)."""
    arm_w = arm_w or P.GEN_PIN_D
    disc = cq.Workplane("XY").circle(P.GEN_LOCK_R).extrude(t)
    # relief sector centred on the pin direction (180 deg)
    w = cq.Workplane("XY").polyline([(0, 0),
                                     (30 * math.cos(math.radians(180 - relief_deg)),
                                      30 * math.sin(math.radians(180 - relief_deg))),
                                     (30 * math.cos(math.radians(180 + relief_deg)),
                                      30 * math.sin(math.radians(180 + relief_deg)))]
                                    ).close().extrude(t)
    disc = disc.cut(w)
    pin = cq.Workplane("XY").center(-A, 0).circle(P.GEN_PIN_D / 2).extrude(t)
    drive = disc.union(pin)
    if bore_r:
        drive = drive.cut(cq.Workplane("XY").circle(bore_r).extrude(t))
    return drive


def build_arm_plate(t=2.2, bore_r=3.0, arm_w=4.0):
    """Crank plate in the plane BEHIND the dial: hub + arm out to the pin."""
    hub = cq.Workplane("XY").circle(P.GEN_LOCK_R).extrude(t)
    arm = cq.Workplane("XY").center(-A / 2 - 0.5, 0).rect(A + 1.0, arm_w).extrude(t)
    pad = cq.Workplane("XY").center(-A, 0).circle(P.GEN_PIN_D / 2 + 1.1).extrude(t)
    plate = hub.union(arm).union(pad)
    return plate.cut(cq.Workplane("XY").circle(bore_r).extrude(t))


def interference_sweep(dial, drive, steps=144):
    """Max overlap volume (mm^3) between the dial and the drive over one drive revolution."""
    worst, worst_theta = 0.0, None
    for i in range(steps):
        th = -180 + 360.0 * i / steps
        dd = dial.rotate((0, 0, 0), (0, 0, 1), dial_angle(th))
        dr = (drive.rotate((0, 0, 0), (0, 0, 1), -th).translate((C, 0, 0)))
        common = dd.intersect(dr)
        v = common.val().Volume() if common.vals() else 0.0
        if v > worst:
            worst, worst_theta = v, th
    return worst, worst_theta


if __name__ == "__main__":
    dial = build_dial()
    print(f"C = {C:.3f} mm, tip R = {P.GEN_TIP_R}, dial angle at theta=0: {dial_angle(0):.2f}, "
          f"at 72: {dial_angle(72):.3f}, at 100: {dial_angle(100)}")
    for relief in (60, 70, 75, 80, 90):
        drive = build_drive(relief_deg=relief)
        v, th = interference_sweep(dial, drive)
        print(f"relief {relief:3d} deg: worst overlap {v:8.4f} mm^3 at theta={th}")
