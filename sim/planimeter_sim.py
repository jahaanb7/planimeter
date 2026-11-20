"""Exact kinematic model of the polar planimeter.

Pole P at the origin.  Elbow E is on a circle of radius R about P.  The tracer T is
at distance L from E.  The wheel contact W = E + a*u + b*n sits on the tracer arm frame
(u along the arm, n = u rotated +90 degrees).  The wheel axle is parallel to u, so the
wheel rolls by ds = dW . n.  With an axle misalignment delta the rolling direction is
n rotated by delta.

Everything here is derived in docs/article/planimeter.tex.
"""
import os
import sys

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "cad"))
import params as P  # noqa: E402


def shoelace(poly):
    x, y = poly[:, 0], poly[:, 1]
    return 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)


def densify(poly, step=0.25):
    """Closed polyline -> points spaced at most `step` mm apart."""
    pts = []
    closed = np.vstack([poly, poly[:1]])
    for p, q in zip(closed[:-1], closed[1:]):
        n = max(1, int(np.ceil(np.linalg.norm(q - p) / step)))
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        pts.append(p + t * (q - p))
    return np.vstack(pts)


def elbow(T, R=P.R_POLE, L=P.L, side=+1):
    """Circle-circle intersection: |E|=R and |T-E|=L."""
    d = np.hypot(T[:, 0], T[:, 1])
    if np.any(d > R + L) or np.any(d < abs(R - L)):
        raise ValueError("tracer path leaves the reachable annulus [|R-L|, R+L]")
    e = (R * R - L * L + d * d) / (2 * d)
    h = np.sqrt(np.maximum(R * R - e * e, 0.0))
    ux, uy = T[:, 0] / d, T[:, 1] / d
    return np.column_stack([e * ux - side * h * uy, e * uy + side * h * ux])


def trace(path, R=P.R_POLE, L=P.L, a=P.WHEEL_A, b=P.WHEEL_B, side=+1,
          delta_deg=0.0, wheel_scale=1.0):
    """Return (wheel_roll_mm, E, theta) for a closed tracer path (already densified).

    wheel_scale multiplies the rolled length (models a wheel-diameter error).
    """
    E = elbow(path, R, L, side)
    u = (path - E) / L
    n = np.column_stack([-u[:, 1], u[:, 0]])
    W = E + a * u + b * n
    dW = np.roll(W, -1, axis=0) - W
    um = u + np.roll(u, -1, axis=0)
    um /= np.linalg.norm(um, axis=1)[:, None]
    nm = np.column_stack([-um[:, 1], um[:, 0]])
    d = np.radians(delta_deg)
    roll_dir = np.cos(d) * nm + np.sin(d) * um        # axle rotated by delta
    s = np.sum(dW * roll_dir, axis=1).sum() * wheel_scale
    theta = np.unwrap(np.arctan2(u[:, 1], u[:, 0]))
    return s, E, theta


def area_from_reading(s, L=P.L, a=P.WHEEL_A, R=P.R_POLE, pole_inside=False):
    A = L * s
    if pole_inside:
        A += np.pi * (R * R + L * L - 2 * a * L)
    return A


# ---------------------------------------------------------------- test shapes -----------
def circle(c, r, n=720):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.column_stack([c[0] + r * np.cos(t), c[1] + r * np.sin(t)])


def ellipse(c, ra, rb, rot=0.0, n=720):
    t = np.linspace(0, 2 * np.pi, n, endpoint=False)
    x, y = ra * np.cos(t), rb * np.sin(t)
    cr, sr = np.cos(rot), np.sin(rot)
    return np.column_stack([c[0] + cr * x - sr * y, c[1] + sr * x + cr * y])


def shapes_outside():
    star = []
    for k in range(10):
        r = 45 if k % 2 == 0 else 20
        a = k * np.pi / 5
        star.append([130 + r * np.cos(a), 60 + r * np.sin(a)])
    return {
        "circle r=40": circle((140, 40), 40),
        "square 80x80": np.array([[100, 0], [180, 0], [180, 80], [100, 80]], float),
        "triangle": np.array([[110, -30], [190, 10], [120, 70]], float),
        "irregular polygon": np.array([[100, 0], [170, -20], [210, 30], [180, 80], [130, 90], [95, 50]], float),
        "star": np.array(star),
        "ellipse 90x40": ellipse((150, 50), 45, 20, 0.5),
    }


def shapes_inside():
    return {
        "circle r=150 about pole": circle((0, 0), 150),
        "ellipse 180x120 about pole": ellipse((10, 5), 180, 120, 0.3),
    }


def run_tests(verbose=True):
    rows = []
    for name, poly in shapes_outside().items():
        # CCW orientation => positive area
        if shoelace(poly) < 0:
            poly = poly[::-1]
        path = densify(poly)
        s, *_ = trace(path)
        A_true = abs(shoelace(poly))
        A_meas = area_from_reading(s)
        rows.append(("outside", name, A_true / 100, A_meas / 100, 100 * (A_meas - A_true) / A_true))
    for name, poly in shapes_inside().items():
        if shoelace(poly) < 0:
            poly = poly[::-1]
        path = densify(poly, step=0.5)
        s, *_ = trace(path)
        A_true = abs(shoelace(poly))
        A_meas = area_from_reading(s, pole_inside=True)
        rows.append(("inside", name, A_true / 100, A_meas / 100, 100 * (A_meas - A_true) / A_true))
    if verbose:
        print(f"{'mode':8s}{'shape':30s}{'true cm2':>10s}{'meas cm2':>10s}{'err %':>9s}")
        for r in rows:
            print(f"{r[0]:8s}{r[1]:30s}{r[2]:10.3f}{r[3]:10.3f}{r[4]:9.4f}")
    return rows


def misalignment_study(deltas=(0.0, 0.1, 0.2, 0.5, 1.0)):
    """Area error vs wheel-axle misalignment; also the left/right average."""
    poly = circle((140, 40), 40)
    path = densify(poly)
    A_true = abs(shoelace(poly))
    out = []
    for d in deltas:
        sl, *_ = trace(path, side=+1, delta_deg=d)
        sr, *_ = trace(path, side=-1, delta_deg=d)
        # right-hand elbow gives the opposite sign of the area from the same CCW path
        # because the wheel sits on the other side of the arm, so compare with orientation.
        eL = 100 * (P.L * sl - A_true) / A_true
        eR = 100 * (abs(P.L * sr) - A_true) / A_true
        out.append((d, eL, eR, 0.5 * (eL + eR)))
    return out


if __name__ == "__main__":
    print("== Tracing tests (exact linkage) ==")
    rows = run_tests()
    worst_out = max(abs(r[4]) for r in rows if r[0] == "outside")
    print(f"\nworst pole-outside error: {worst_out:.4f} %")
    print("\n== Axle misalignment study (circle r=40) ==")
    print(f"{'delta deg':>10s}{'left %':>10s}{'right %':>10s}{'mean %':>10s}")
    for r in misalignment_study():
        print(f"{r[0]:10.2f}{r[1]:10.4f}{r[2]:10.4f}{r[3]:10.4f}")
