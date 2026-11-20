"""Error budget by simulation: scale errors, axle misalignment, pivot play, wheel slip."""
import json
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
import params as P  # noqa: E402
import planimeter_sim as S  # noqa: E402


def trace_with_play(path, pu, pn, side=+1):
    """Pivot play: the carriage pivot sits at (pu, pn) from the pole-arm end, in the tracer-arm frame."""
    L, R = P.L, P.R_POLE
    E0 = S.elbow(path, R, L, side)
    th = np.arctan2(*(path - E0).T[::-1])
    for _ in range(8):
        u = np.column_stack([np.cos(th), np.sin(th)])
        n = np.column_stack([-u[:, 1], u[:, 0]])
        g = path - (L + pu) * u - pn * n
        dg = -(L + pu) * n + pn * u
        f = np.sum(g * g, axis=1) - R * R
        fp = 2 * np.sum(g * dg, axis=1)
        th = th - f / fp
    u = np.column_stack([np.cos(th), np.sin(th)])
    n = np.column_stack([-u[:, 1], u[:, 0]])
    Pc = path - L * u
    W = Pc + P.WHEEL_A * u + P.WHEEL_B * n
    dW = np.roll(W, -1, axis=0) - W
    um = u + np.roll(u, -1, axis=0)
    um /= np.linalg.norm(um, axis=1)[:, None]
    nm = np.column_stack([-um[:, 1], um[:, 0]])
    return np.sum(dW * nm, axis=1).sum()


def main():
    shapes = S.shapes_outside()
    res = {}

    # 1. scale errors (pure scale, removed by calibration)
    res["wheel circumference +1 % -> area error %"] = 1.0
    res["L +0.2 mm -> area error %"] = 100 * 0.2 / P.L

    # 2. axle misalignment, worst over the test shapes (one hand)
    mis = {}
    for d in (0.1, 0.2, 0.3, 0.5, 1.0):
        worst = 0.0
        for nm_, poly in shapes.items():
            if S.shoelace(poly) < 0:
                poly = poly[::-1]
            path = S.densify(poly)
            s, *_ = S.trace(path, delta_deg=d)
            worst = max(worst, abs(100 * (P.L * s - abs(S.shoelace(poly))) / abs(S.shoelace(poly))))
        mis[d] = worst
    res["misalignment worst-case error % vs delta deg"] = {str(k): round(v, 3) for k, v in mis.items()}

    # 3. pivot play 0.15 mm in every direction, worst over shapes
    play = {}
    for r in (0.05, 0.10, 0.15, 0.25):
        worst = 0.0
        for nm_, poly in shapes.items():
            if S.shoelace(poly) < 0:
                poly = poly[::-1]
            path = S.densify(poly)
            A = abs(S.shoelace(poly))
            for ang in np.linspace(0, 2 * np.pi, 24, endpoint=False):
                s = trace_with_play(path, r * np.cos(ang), r * np.sin(ang))
                worst = max(worst, abs(100 * (P.L * s - A) / A))
        play[r] = worst
    res["pivot play worst-case error % vs radius mm"] = {str(k): round(v, 3) for k, v in play.items()}

    # 4. small-shape penalty: the same absolute errors hurt small areas more
    out = os.path.join(HERE, "..", "docs", "article", "figures", "errors.json")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        json.dump(res, f, indent=1)
    print(json.dumps(res, indent=1))
    return mis, play


if __name__ == "__main__":
    main()
