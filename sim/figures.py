"""All figures for the article (PDF + PNG in docs/article/figures/)."""
import json
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import PolyCollection
from matplotlib.patches import Circle, FancyArrowPatch, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
sys.path.insert(0, os.path.join(HERE, "..", "cad", "parts"))
import params as P  # noqa: E402
import planimeter_sim as S  # noqa: E402
import geneva as G  # noqa: E402

OUT = os.path.join(HERE, "..", "docs", "article", "figures")
os.makedirs(OUT, exist_ok=True)
INK, ACC, ACC2, GREY = "#1b2a41", "#d1495b", "#2e86ab", "#9aa5b1"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "font.family": "serif", "mathtext.fontset": "cm"})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)


# ------------------------------------------------------------------ 1. linkage geometry
def fig_geometry():
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    O = np.array([0.0, 0.0])
    T = np.array([95.0, 60.0])
    E = S.elbow(T[None, :], side=-1)[0]
    u = (T - E) / P.L
    n = np.array([-u[1], u[0]])
    W = E + P.WHEEL_A * u + P.WHEEL_B * n
    ax.plot(*zip(O, E), color=ACC2, lw=4, solid_capstyle="round")
    ax.plot(*zip(E, T), color=ACC, lw=4, solid_capstyle="round")
    for p, lab, off in ((O, "pole $O$", (-8, -12)), (E, "elbow $E$", (-6, -14)), (T, "tracer $T$", (4, 5))):
        ax.plot(*p, "o", color=INK, ms=7, zorder=5)
        ax.annotate(lab, p, xytext=off, textcoords="offset points", fontsize=10)
    # wheel: drawn as a rectangle whose long side is along n (it rolls along n, axle along u)
    wl, ww = 9.0, 3.0
    rect = Rectangle((-ww / 2, -wl / 2), ww, wl, color=INK, alpha=0.85)
    ang = math.degrees(math.atan2(u[1], u[0]))
    tr = matplotlib.transforms.Affine2D().rotate_deg(ang - 0).translate(*W) + ax.transData
    rect.set_transform(tr)
    ax.add_patch(rect)
    ax.annotate("wheel $W$", W, xytext=(8, 6), textcoords="offset points")
    for vec, lab, col in ((u, r"$\mathbf{u}$", ACC), (n, r"$\mathbf{n}$", INK)):
        a = FancyArrowPatch(W, W + 16 * vec, arrowstyle="-|>", mutation_scale=10, color=col, lw=1.6)
        ax.add_patch(a)
        ax.annotate(lab, W + 19 * vec, ha="center", va="center", fontsize=11)
    ax.annotate("", E, xytext=O, arrowprops=dict(arrowstyle="<->", color=GREY))
    ax.text(*(0.5 * (O + E) + 7 * np.array([-n[1] * 0 + 1, 0])), r"$R$", color=ACC2)
    ax.text(*(0.5 * (E + T) + 7 * n * -1), r"$L$", color=ACC)
    ax.annotate(r"$\theta$", E + 12 * u, fontsize=11)
    ax.set_aspect("equal")
    ax.axis("off")
    pts = np.array([O, E, T, W, W + 22 * u, W + 22 * n])
    ax.set_xlim(pts[:, 0].min() - 25, pts[:, 0].max() + 25)
    ax.set_ylim(pts[:, 1].min() - 25, pts[:, 1].max() + 25)
    save(fig, "fig_geometry")


# ------------------------------------------------------------------ 2. why back-and-forth cancels
def fig_sweep():
    fig, axs = plt.subplots(1, 2, figsize=(7.4, 3.2))
    ax = axs[0]
    ax.set_title("a short sideways step sweeps a thin wedge", fontsize=9)
    Lr = 10.0
    a0, a1 = math.radians(75), math.radians(35)
    p0 = Lr * np.array([math.cos(a0), math.sin(a0)])
    p1 = Lr * np.array([math.cos(a1), math.sin(a1)])
    ax.fill([0, p0[0], p1[0]], [0, p0[1], p1[1]], color=ACC, alpha=0.25)
    ax.plot([0, p0[0]], [0, p0[1]], color=INK, lw=2.5)
    ax.plot([0, p1[0]], [0, p1[1]], color=ACC, lw=2.5)
    th = np.linspace(a1, a0, 30)
    ax.plot(Lr * np.cos(th), Lr * np.sin(th), color=ACC2, lw=2)
    ax.plot(0, 0, "o", color=INK)
    ax.annotate("pivot", (0, 0), xytext=(-2, -1.6), fontsize=9)
    ax.annotate("length $L$", (1.2, 6.3), fontsize=9, rotation=75)
    ax.annotate("sideways step $d$\n(the wheel reads $d$)", (6.8, 11.2), fontsize=8.5, color=ACC2)
    ax.text(10.6, 2.2, "swept area\n$\\propto L\\,d$", fontsize=9, ha="center")
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_xlim(-3, 17); ax.set_ylim(-3, 14)
    ax = axs[1]
    ax.set_title("closed loop: only the inside survives", fontsize=9)
    poly = np.array([[100, 0], [150, -10], [160, 40], [120, 60], [95, 35]], float)
    ax.fill(poly[:, 0], poly[:, 1], color=ACC, alpha=0.18)
    ax.plot(*np.vstack([poly, poly[:1]]).T, color=ACC, lw=2)
    ax.text(125, 22, "$A=L\\,s$", fontsize=12, ha="center")
    ax.set_aspect("equal"); ax.axis("off")
    save(fig, "fig_sweep")


# ------------------------------------------------------------------ 3. validation bars
def fig_validation():
    rows = S.run_tests(verbose=False)
    fig, ax = plt.subplots(figsize=(6.6, 3.0))
    names = [r[1] for r in rows]
    err = [abs(r[4]) for r in rows]
    cols = [ACC2 if r[0] == "outside" else ACC for r in rows]
    ax.barh(range(len(rows)), err, color=cols)
    ax.set_yticks(range(len(rows)))
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel(r"$|$area error$|$ (%) of the exact kinematic model")
    ax.set_xscale("log"); ax.set_xlim(1e-7, 1e-2)
    ax.invert_yaxis()
    ax.set_title("model vs shoelace area; blue = pole outside, red = pole inside", fontsize=9)
    save(fig, "fig_validation")


# ------------------------------------------------------------------ 4. error budget
def fig_errors():
    e = json.load(open(os.path.join(OUT, "errors.json")))
    fig, axs = plt.subplots(1, 2, figsize=(7.0, 3.0))
    d = e["misalignment worst-case error % vs delta deg"]
    axs[0].plot([float(k) for k in d], list(d.values()), "o-", color=ACC)
    axs[0].axhline(0.5, color=GREY, ls="--", lw=1)
    axs[0].set_xlabel("wheel-axle misalignment (degrees)")
    axs[0].set_ylabel("worst area error (%)")
    axs[0].set_title("axle not parallel to the arm", fontsize=9)
    p = e["pivot play worst-case error % vs radius mm"]
    axs[1].plot([float(k) for k in p], list(p.values()), "s-", color=ACC2)
    axs[1].axhline(0.5, color=GREY, ls="--", lw=1)
    axs[1].set_xlabel("elbow pivot play (mm)")
    axs[1].set_title("slop in the elbow bearing", fontsize=9)
    for a in axs:
        a.grid(alpha=0.25)
    save(fig, "fig_errors")


# ------------------------------------------------------------------ 5. Geneva kinematics
def fig_geneva():
    th = np.linspace(-180, 180, 721)
    al = np.array([G.dial_angle(t) for t in th])
    reading = ((th - P.GEN_PHASE_DEG) / 360 * 100) % 100
    fig, ax = plt.subplots(figsize=(6.2, 2.8))
    ax.plot(th, al, color=ACC2, lw=2)
    ax.axvspan(-72, 72, color=ACC, alpha=0.1)
    ax.set_xlabel(r"wheel angle $\theta$ (degrees); shaded = pin engaged")
    ax.set_ylabel("dial angle (degrees)")
    ax.set_yticks([-18, 0, 18])
    ax.annotate("one wheel revolution = one 36° dial step", (-170, -12), fontsize=8)
    ax.grid(alpha=0.25)
    save(fig, "fig_geneva")


# ------------------------------------------------------------------ 6. plan view from the real CAD
def fig_plan():
    import trimesh
    scene = trimesh.load(os.path.join(HERE, "..", "docs", "images", "planimeter_assembly.glb"))
    polys, cols, zs = [], [], []
    for name, g in scene.geometry.items():
        m = g
        tri = m.triangles
        if len(tri) == 0:
            continue
        try:
            bc = getattr(m.visual.material, "baseColorFactor", None)
            col = np.array(bc[:3], float) / 255.0 if bc is not None else np.array(m.visual.main_color[:3]) / 255.0
            if col.max() > 1.0:
                col = col / 255.0
        except Exception:
            col = np.array([0.8, 0.8, 0.8])
        nrm = m.face_normals
        up = nrm[:, 2] > 0.2
        for t, c in zip(tri[up], nrm[up]):
            polys.append(t[:, :2])
            cols.append(col * (0.65 + 0.35 * c[2]))
            zs.append(t[:, 2].mean())
    # scene geometry is already in millimetres with Z up (the GLB exporter keeps CAD axes)
    order = np.argsort(zs)
    fig, ax = plt.subplots(figsize=(6.4, 5.6))
    pc = PolyCollection([polys[i] for i in order], facecolors=[cols[i] for i in order], edgecolors="none", lw=0)
    ax.add_collection(pc)
    ax.set_aspect("equal")
    ax.autoscale_view()
    return fig, ax, scene


def fig_plan_overlay():
    try:
        fig, ax, _ = fig_plan()
    except Exception as exc:
        print("plan view skipped:", exc)
        return
    O = np.array([0.0, -P.R_POLE])
    E = np.array([0.0, 0.0])
    T = np.array([P.L, 0.0])
    ax.plot(*zip(E, T), color=ACC, lw=1.2, ls="--")
    ax.plot(*zip(E, O), color=ACC2, lw=1.2, ls="--")
    for p, lab in ((E, "$E$"), (T, "$T$"), (O, "$O$")):
        ax.plot(*p, "o", color="k", ms=4)
        ax.annotate(lab, p, xytext=(5, 5), textcoords="offset points", fontsize=11)
    ax.annotate("", (P.L, 14), xytext=(0, 14), arrowprops=dict(arrowstyle="<->", color=ACC))
    ax.text(P.L / 2, 17, r"$L=100$ mm", color=ACC, ha="center")
    ax.annotate("", (-14, -P.R_POLE), xytext=(-14, 0), arrowprops=dict(arrowstyle="<->", color=ACC2))
    ax.text(-17, -P.R_POLE / 2, r"$R=160$ mm", color=ACC2, rotation=90, va="center", ha="right")
    ax.annotate("wheel (rolls along $\\mathbf{n}$)", (P.WHEEL_A, P.WHEEL_B), xytext=(-70, 70),
                textcoords="data", arrowprops=dict(arrowstyle="->"), fontsize=9)
    ax.set_xlabel("x (mm)")
    ax.set_ylabel("y (mm)")
    save(fig, "fig_plan")


if __name__ == "__main__":
    fig_geometry()
    fig_sweep()
    fig_validation()
    fig_errors()
    fig_geneva()
    fig_plan_overlay()
    print("figures written to", OUT)
    print(sorted(os.listdir(OUT)))
