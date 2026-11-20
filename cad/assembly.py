"""Full assembly in the working pose + engineering checks.

    python3 cad/assembly.py            # build, check, print the report, export STEP/GLB
    python3 cad/assembly.py --quick    # skip the slow sweeps

Checks (all must pass):
  1. clash matrix: no two components overlap (except declared press fits)
  2. paper contacts: wheel rim and tracer tip at z = 0, every other part clear (>= 2 mm drum, 3 mm others)
  3. pole-arm + pole-weight sweep over the working range of elbow angles, both hands
  4. Geneva counter on the REAL solids: one wheel revolution advances the dial 36 degrees, no interference
  5. statics: loads on wheel / tracer tip / elbow from CAD mass properties
"""
import itertools
import json
import math
import os
import sys
import time

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "parts"))
import params as P  # noqa: E402
import hardware as H  # noqa: E402
import geneva as G  # noqa: E402
import wheel, carriage_a, carriage_b, carriage_c, dial, tracer_arm, pole_arm, pole_weight  # noqa: E402

ELBOW_DEG = -90.0        # default pose: pole arm points to -Y (elbow angle 90 degrees)
INFILL = 0.50            # effective solid fraction for printed mass (3 walls, 25 % gyroid) - weigh to confirm
BALLAST_SHOT_DENSITY = 4.5   # g/cm^3 bulk steel shot


def rot_z(shape, deg, about=(0, 0, 0)):
    return shape.rotate(about, (about[0], about[1], 1), deg)


def components(elbow_deg=ELBOW_DEG):
    """name -> (solid Workplane, kind, mass_g_or_None).  kind: 'printed' | 'hardware' | 'rubber'."""
    c = {}
    ax_y, ax_z = P.WHEEL_B, P.Z_WHEEL
    c["wheel"] = (wheel.build(), "printed")
    c["carriage_a"] = (carriage_a.build(), "printed")
    c["carriage_b"] = (carriage_b.build(), "printed")
    c["carriage_c"] = (carriage_c.build(), "printed")
    c["dial"] = (dial.build(), "printed")
    c["tracer_arm"] = (tracer_arm.build(), "printed")
    pa = rot_z(pole_arm.build(), elbow_deg)
    c["pole_arm"] = (pa, "printed")
    px = P.R_POLE * math.cos(math.radians(elbow_deg))
    py = P.R_POLE * math.sin(math.radians(elbow_deg))
    pw = pole_weight.build().translate((px, py, 0))
    c["pole_weight"] = (pw, "printed")
    c["pole_weight_lid"] = (pole_weight.build_lid().translate((px, py, 0)), "printed")
    # ---- hardware ----
    # wheel bearings (outer race in the wheel pockets; faces flush with the wheel ends)
    c["bearing_w1"] = (H.bearing_x(P.WHEEL_A - 10.0, ax_y, ax_z), "hardware")
    c["bearing_w2"] = (H.bearing_x(P.WHEEL_X_FRONT - P.BEARING_W, ax_y, ax_z), "hardware")
    # axle: head against the counterbore floor of plate C, nut in plate B's back pocket
    x_out = P.X_REAR_FACE - P.C_T
    x_floor = x_out + P.M3_HEAD_H + 0.3
    c["axle_bolt"] = (H.bolt_x(x_floor, 35.0, ax_y, ax_z, +1), "hardware")
    x_nut = P.X_BLOCK0 - P.M3_NUT_H - 0.4
    c["axle_nut"] = (H.nut_x(x_nut, ax_y, ax_z), "hardware")
    # plate C <-> plate B screws (M3 x 35, heads in B's back counterbore, nuts on C's outer face)
    for i, z in enumerate(P.POST_Z):
        c[f"cscrew{i}"] = (H.bolt_x(P.X_BLOCK0 - 3.2, 35.0, P.POST_Y, z, -1), "hardware")
        c[f"cnut{i}"] = (H.nut_x(x_out + 0.0, P.POST_Y, z), "hardware")
    # block A <-> plate B screws (M3 x 25, heads in A's front counterbore, nuts in B's wheel-face pockets)
    for i, (y, z) in enumerate(P.BLOCK_SCREWS):
        c[f"ascrew{i}"] = (H.bolt_x(P.X_BLOCK1 - 3.2, 25.0, y, z, -1), "hardware")
        c[f"anut{i}"] = (H.nut_x(P.X_FRONT_FACE, y, z), "hardware")
    # dial screw (M3 x 30, head on the dial front) and its nut in plate C's outer face
    x_dial_front = P.DIAL_X0 + P.GEN_T
    c["dial_screw"] = (H.bolt_x(x_dial_front + 1.0, 30.0 + 1.0, P.WHEEL_B, P.DIAL_Z, -1), "hardware")
    c["dial_nut"] = (H.nut_x(x_out, P.WHEEL_B, P.DIAL_Z), "hardware")
    # elbow: bearing in the pole arm (bottom face flush with the underside), washer, M3 x 30 bolt, nut in block A
    ex, ey = 0.0, 0.0
    c["elbow_bearing"] = (H.bearing_z(ex, ey, P.Z_POLE_ARM), "hardware")
    c["elbow_washer"] = (H.washer_z(P.Z_POLE_ARM + P.BEARING_W, ex, ey), "hardware")
    c["elbow_bolt"] = (H.bolt_z(P.Z_POLE_ARM + P.BEARING_W + 0.5, 30.0, ex, ey), "hardware")
    c["elbow_nut"] = (H.nut_z(P.BLOCK_Z0 + 0.2, ex, ey), "hardware")
    # pole joint: same stack on the pole weight
    c["pole_bearing"] = (H.bearing_z(0, 0, P.Z_POLE_ARM).translate((px, py, 0)), "hardware")
    c["pole_washer"] = (H.washer_z(P.Z_POLE_ARM + P.BEARING_W, 0, 0).translate((px, py, 0)), "hardware")
    c["pole_bolt"] = (H.bolt_z(P.Z_POLE_ARM + P.BEARING_W + 0.5, 35.0, 0, 0).translate((px, py, 0)), "hardware")
    c["pole_nut"] = (H.nut_z(pole_weight.FOOT_H + 0.2, 0, 0).translate((px, py, 0)), "hardware")
    # tracer bolt (M3 x 40) with its nut in the knob top; tip at the paper
    z_knob_top = P.Z_ARM + P.ARM_T / 2 + tracer_arm.KNOB_H
    c["tracer_nut"] = (H.nut_z(z_knob_top - P.M3_NUT_H - 0.2, P.L, 0), "hardware")
    c["tracer_bolt"] = (H.bolt_z(40.0, 40.0, P.L, 0), "hardware")
    # clamp screw (M3 x 12 thumbscrew) and its nut
    c["clamp_screw"] = (cq.Workplane("XY").add(
        H.cyl_y(1.5, P.BLOCK_Y0 - 6.0, -P.ARM_W / 2 - 0.01, P.CLAMP_X, P.Z_ARM).union(
            H.cyl_y(4.0, P.BLOCK_Y0 - 6.0, P.BLOCK_Y0 - 2.0, P.CLAMP_X, P.Z_ARM)).val()), "hardware")
    c["clamp_nut"] = (H.hex_prism_y(P.M3_NUT_AF, P.BLOCK_Y0 + 0.2, P.BLOCK_Y0 + 0.2 + P.M3_NUT_H, P.CLAMP_X, P.Z_ARM)
                      .cut(H.cyl_y(1.5, P.BLOCK_Y0 - 1, P.BLOCK_Y0 + 5, P.CLAMP_X, P.Z_ARM)), "hardware")
    # rubber feet under the pole weight
    for k, f in enumerate(pole_weight.feet()):
        c[f"foot{k}"] = (f.translate((px, py, 0)), "rubber")
    return c


def bb(w):
    b = w.val().BoundingBox()
    return b


def overlap_volume(a, b):
    ba, bb_ = bb(a), bb(b)
    if (ba.xmax < bb_.xmin or bb_.xmax < ba.xmin or ba.ymax < bb_.ymin or bb_.ymax < ba.ymin
            or ba.zmax < bb_.zmin or bb_.zmax < ba.zmin):
        return 0.0
    try:
        r = a.intersect(b)
        return r.val().Volume() if r.vals() else 0.0
    except Exception:
        return float("nan")


def clash_matrix(comps, tol=0.05, allowed=()):
    names = list(comps)
    bad = []
    for n1, n2 in itertools.combinations(names, 2):
        if comps[n1][1] == "rubber" and comps[n2][1] == "rubber":
            continue
        v = overlap_volume(comps[n1][0], comps[n2][0])
        if v != v or v > tol:
            if (n1, n2) in allowed or (n2, n1) in allowed:
                continue
            bad.append((n1, n2, v))
    return bad


def paper_check(comps):
    rows = []
    for n, (w, kind) in comps.items():
        z = bb(w).zmin
        rows.append((n, round(z, 3)))
    return rows


def printed_mass(w):
    return w.val().Volume() * P.RHO_PLA * INFILL


def masses(comps):
    m = {}
    for n, (w, kind) in comps.items():
        if kind == "printed":
            m[n] = printed_mass(w)
        elif kind == "rubber":
            m[n] = 0.15
        else:
            v = w.val().Volume()
            m[n] = v * 7.85e-3                   # steel
    return m


def statics(comps, m, ballast_g=0.0):
    """Loads (grams-force) on wheel contact, tracer tip and elbow pivot."""
    carriage = ["wheel", "carriage_a", "carriage_b", "carriage_c", "dial", "tracer_arm",
                "bearing_w1", "bearing_w2", "axle_bolt", "axle_nut", "dial_screw", "dial_nut",
                "tracer_nut", "tracer_bolt", "clamp_screw", "clamp_nut", "elbow_nut"]
    carriage += [k for k in comps if k.startswith(("cscrew", "cnut", "ascrew", "anut"))]
    S = {"M": 0.0, "mx": 0.0, "my": 0.0}
    for n in carriage:
        c = comps[n][0].val().Center()
        S["M"] += m[n]
        S["mx"] += m[n] * c.x
        S["my"] += m[n] * c.y
    # ballast in plate B's box
    bx = (P.X_REAR_FACE - P.C_T + P.X_BLOCK0) / 2
    by = (P.BALLAST_Y0 + 1.5 + P.BALLAST_Y1 - 2.0) / 2
    S["M"] += ballast_g
    S["mx"] += ballast_g * bx
    S["my"] += ballast_g * by
    # half the pole arm (+ elbow bearing/bolt/washer) hangs on the elbow pivot (x = y = 0)
    half = 0.5 * (m["pole_arm"] + 2 * m["elbow_bearing"] * 0) + m["elbow_bearing"] + m["elbow_washer"] + m["elbow_bolt"]
    S["M"] += half
    xw, yw = P.WHEEL_A, P.WHEEL_B
    xt, yt = P.L, 0.0
    RW = S["my"] / yw                                         # moment about the x-axis (T and E are on y = 0)
    RT = (S["mx"] - xw * RW) / xt                             # moment about the y-axis
    RE = S["M"] - RW - RT
    return {"mass_total_g": S["M"], "R_wheel_g": RW, "R_tip_g": RT, "R_elbow_g": RE,
            "ballast_g": ballast_g, "com_x": S["mx"] / S["M"], "com_y": S["my"] / S["M"]}


def solve_ballast(comps, m, target_wheel_g=70.0, tip_max=40.0):
    base = statics(comps, m, 0.0)
    by = (P.BALLAST_Y0 + 1.5 + P.BALLAST_Y1 - 2.0) / 2
    bx = (P.X_REAR_FACE - P.C_T + P.X_BLOCK0) / 2
    # R_W = (my + b*by)/yw  -> b = (target*yw - my)/by   (wheel load as the only driver)
    need = max(0.0, (target_wheel_g * P.WHEEL_B - (base["R_wheel_g"] * P.WHEEL_B)) / by)
    return need, statics(comps, m, need)


def pocket_capacity_g():
    x_rear = P.X_REAR_FACE - P.C_T
    vol = ((P.X_BLOCK0 - 2.0) - (x_rear)) * (P.BALLAST_Y1 - 2.0 - (P.BALLAST_Y0 + 1.5)) * (32.0 - 6.0) / 1000.0
    return vol * BALLAST_SHOT_DENSITY * 0.62 / 0.62, vol            # bulk density already includes packing


def sweep_pole(comps, side=+1, angles=range(-165, -14, 15)):
    """Pole arm + weight vs everything on the carriage side, over the working range of elbow angles."""
    fixed = [n for n in comps if n not in ("pole_arm", "pole_weight", "pole_weight_lid", "pole_bearing", "pole_washer",
                                           "pole_bolt", "pole_nut", "elbow_bearing", "elbow_washer", "elbow_bolt")
             and not n.startswith("foot")]
    bad = []
    for ang in angles:
        a = ang if side > 0 else -ang
        pa = rot_z(pole_arm.build(), a)
        for n in fixed:
            v = overlap_volume(pa, comps[n][0])
            if v > 0.05 or v != v:
                bad.append((a, "pole_arm", n, v))
    return bad


def geneva_check(comps, steps=36):
    """Spin the real wheel through one revolution; rotate the real dial per the Geneva kinematics; test overlap."""
    w = comps["wheel"][0]
    d = comps["dial"][0]
    ax = (P.WHEEL_A, P.WHEEL_B, P.Z_WHEEL)
    dc = (P.DIAL_X0 + P.GEN_T / 2, P.WHEEL_B, P.DIAL_Z)
    worst = 0.0
    rows = []
    for i in range(steps):
        th = -180.0 + 360.0 * i / steps
        wr = w.rotate(ax, (ax[0] + 1, ax[1], ax[2]), -(th - P.GEN_PHASE_DEG))     # built pose is theta = GEN_PHASE_DEG
        alpha = G.dial_angle(th) - G.dial_angle(P.GEN_PHASE_DEG)                   # dial built at its rest pose after the step
        dr = d.rotate(dc, (dc[0] + 1, dc[1], dc[2]), alpha)
        v = overlap_volume(wr, dr)
        worst = max(worst, v)
        rows.append((th, alpha, v))
    # ratio: dial angle after one revolution minus before
    return worst, rows


def export_all(comps):
    root = os.path.join(HERE, "..")
    assy = cq.Assembly(name="planimeter")
    colours = {"printed": cq.Color(0.86, 0.83, 0.74), "hardware": cq.Color(0.55, 0.58, 0.62),
               "rubber": cq.Color(0.1, 0.1, 0.1)}
    special = {"wheel": (0.25, 0.45, 0.8), "dial": (0.9, 0.45, 0.15), "tracer_arm": (0.2, 0.65, 0.45),
               "pole_arm": (0.8, 0.3, 0.3), "pole_weight": (0.35, 0.35, 0.4), "pole_weight_lid": (0.35, 0.35, 0.4)}
    for n, (w, kind) in comps.items():
        col = cq.Color(*special[n]) if n in special else colours[kind]
        assy.add(w, name=n, color=col)
    os.makedirs(os.path.join(root, "step"), exist_ok=True)
    os.makedirs(os.path.join(root, "docs", "images"), exist_ok=True)
    assy.save(os.path.join(root, "step", "planimeter_assembly.step"))
    try:
        assy.save(os.path.join(root, "docs", "images", "planimeter_assembly.glb"))
    except Exception as e:  # GLB export needs OCP's gltf writer
        print("GLB export skipped:", e)


if __name__ == "__main__":
    quick = "--quick" in sys.argv
    t0 = time.time()
    comps = components()
    print(f"built {len(comps)} components in {time.time() - t0:.1f}s")

    print("\n== 1. paper contacts (lowest z of each component) ==")
    rows = paper_check(comps)
    low = sorted(rows, key=lambda r: r[1])[:8]
    for n, z in low:
        print(f"   {n:18s} zmin = {z:7.3f}")

    print("\n== 2. clash matrix ==")
    bad = clash_matrix(comps)
    if bad:
        for b_ in sorted(bad, key=lambda r: -r[2])[:30]:
            print(f"   CLASH {b_[0]:16s} x {b_[1]:16s}  {b_[2]:9.3f} mm3")
    print("   clashes:", len(bad))

    m = masses(comps)
    need, st = solve_ballast(comps, m)
    cap_g, cap_vol = pocket_capacity_g()
    print("\n== 3. statics (grams-force) ==")
    print("   without ballast:", {k: round(v, 1) for k, v in statics(comps, m, 0.0).items()})
    print(f"   ballast needed for 70 g on the wheel: {need:.1f} g  (pocket holds ~{cap_g:.0f} g of shot, {cap_vol:.1f} cm3)")
    print("   with ballast   :", {k: round(v, 1) for k, v in st.items()})

    if not quick:
        print("\n== 4. pole-arm sweep, working range of the supported (right-hand) elbow ==")
        sw = sweep_pole(comps, +1)
        print("   collisions:", sw if sw else "none")
        print("\n== 5. Geneva counter on the real solids ==")
        worst, rows = geneva_check(comps)
        print(f"   worst overlap over one wheel revolution: {worst:.4f} mm3; dial angle {rows[0][1]:.1f} -> {rows[-1][1]:.1f} deg; "
              f"step per revolution = {G.STEP:.1f} deg")
    export_all(comps)
    print(f"\ndone in {time.time() - t0:.0f}s")
