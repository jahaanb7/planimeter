"""Beginner-level explanatory figures for the article (docs/article/figures/)."""
import math
import os
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "cad"))
import params as P  # noqa: E402
import planimeter_sim as S  # noqa: E402

OUT = os.path.join(HERE, "..", "docs", "article", "figures")
INK, RED, BLUE, GREY, SOFT = "#1b2a41", "#c0394b", "#2e86ab", "#9aa5b1", "#eef1f5"
plt.rcParams.update({"font.size": 10, "axes.edgecolor": INK, "text.color": INK, "axes.labelcolor": INK,
                     "xtick.color": INK, "ytick.color": INK, "font.family": "serif", "mathtext.fontset": "cm"})


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(OUT, name + ".png"), bbox_inches="tight", dpi=200)
    plt.close(fig)


def arrow(ax, p, q, color=INK, lw=1.8, ms=12, **kw):
    ax.add_patch(FancyArrowPatch(p, q, arrowstyle="-|>", mutation_scale=ms, color=color, lw=lw,
                                 shrinkA=0, shrinkB=0, **kw))


# 1 ------------------------------------------------------------ an integral adds up strips
def fig_strips():
    f = lambda x: 1.2 + 0.9 * np.sin(1.3 * x) + 0.25 * x
    xs = np.linspace(0, 6, 300)
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 2.8), sharey=True)
    for ax, n, title in ((axs[0], 6, "a few wide strips: a rough area"),
                         (axs[1], 24, "many thin strips: the exact area")):
        edges = np.linspace(0, 6, n + 1)
        for a, b in zip(edges[:-1], edges[1:]):
            ax.add_patch(Rectangle((a, 0), b - a, f((a + b) / 2), fc="#bcd9e6", ec=BLUE, lw=0.6))
        ax.plot(xs, f(xs), color=RED, lw=2)
        ax.set_title(title, fontsize=10)
        ax.set_xlim(0, 6.2)
        ax.set_ylim(0, 3.9)
        ax.set_xticks([])
        ax.set_yticks([])
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
    axs[0].text(0.15, 3.55, r"area $\approx$ sum of (height $\times$ width)", fontsize=9.5)
    axs[1].text(0.15, 3.55, r"area $=\int f(x)\,dx$", fontsize=9.5)
    fig.tight_layout()
    save(fig, "fig_strips")


# 2 ------------------------------------------------------------ a path integral adds up steps along a path
def fig_pathsum():
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.2), gridspec_kw={"width_ratios": [1.15, 1]})
    ax = axs[0]
    t = np.linspace(0, 1, 400)
    x, y = 6 * t, 1.6 * np.sin(5 * t) + 1.2 * t
    ax.plot(x, y, color=GREY, lw=1.4)
    idx = np.linspace(0, len(t) - 1, 13).astype(int)
    ax.plot(x[idx], y[idx], "o", color=RED, ms=4)
    for a, b in zip(idx[:-1], idx[1:]):
        ax.plot([x[a], x[b]], [y[a], y[b]], color=RED, lw=2.2)
    ax.annotate("start", (x[0], y[0]), xytext=(-8, -16), textcoords="offset points")
    ax.annotate("finish", (x[-1], y[-1]), xytext=(-6, 10), textcoords="offset points")
    ax.text(2.1, -1.9, "length of the path = add up the small steps", ha="center", fontsize=9.5)
    ax.set_title("A path integral adds up steps along a path", fontsize=10)
    ax.set_xlim(-0.4, 6.5)
    ax.set_ylim(-2.3, 3.2)
    ax.axis("off")

    ax = axs[1]
    ax.set_title("A wheel counts only part of each step", fontsize=10)
    # wheel (rectangle) with axle along the x axis, rolling along y
    ax.add_patch(Rectangle((-0.25, -0.9), 0.5, 1.8, fc="#d9dee5", ec=INK, lw=1.4))
    ax.plot([-1.3, 1.3], [0, 0], color=GREY, lw=1, ls="--")
    ax.text(1.35, -0.12, "axle", fontsize=9, color=GREY, va="top")
    start = np.array([0, 0.0])
    step = np.array([1.7, 1.5])
    arrow(ax, start, start + step, color=INK, lw=2.2)
    arrow(ax, start, start + [0, step[1]], color=BLUE, lw=2.6)
    arrow(ax, start + [0, step[1]], start + step, color=GREY, lw=2.0)
    ax.text(1.0, 0.45, "one small step", fontsize=9, rotation=0, ha="left", color=INK)
    ax.text(-0.35, 0.9 + 0.65, "counted\n(rolls)", fontsize=9, color=BLUE, ha="right", va="center")
    ax.text(0.85, 1.72, "ignored (skids)", fontsize=9, color="#6b7685", ha="center", va="bottom")
    ax.text(0.9, -1.45, "reading $s$ = sum of the counted parts", ha="center", fontsize=9.5)
    ax.set_xlim(-1.6, 3.0)
    ax.set_ylim(-1.7, 2.7)
    ax.set_aspect("equal")
    ax.axis("off")
    fig.tight_layout()
    save(fig, "fig_pathsum")


# 3 ------------------------------------------------------------ area swept by a moving rod
def fig_rod():
    fig, axs = plt.subplots(1, 2, figsize=(7.2, 3.1), gridspec_kw={"width_ratios": [1.1, 1]})
    ax = axs[0]
    ax.set_title("A rod slides and turns a little", fontsize=10)
    L = 4.0
    E0, T0 = np.array([0.0, 0.0]), np.array([0.0, L])
    ang = math.radians(-14)
    E1 = np.array([1.0, 0.25])
    T1 = E1 + L * np.array([-math.sin(ang), math.cos(ang)])
    ax.add_patch(Polygon([E0, T0, T1, E1], closed=True, fc="#f3d6da", ec="none"))
    ax.plot(*zip(E0, T0), color=INK, lw=2.6, solid_capstyle="round")
    ax.plot(*zip(E1, T1), color=RED, lw=2.6, solid_capstyle="round")
    for f in (0.0, 0.5, 1.0):
        p0 = E0 + f * (T0 - E0)
        p1 = E1 + f * (T1 - E1)
        arrow(ax, p0, p1, color=BLUE, lw=1.6, ms=10)
    ax.text(-0.25, 0.0, r"$E$", ha="right", va="center")
    ax.text(-0.25, L, r"$T$", ha="right", va="center")
    ax.text(-0.25, L / 2, "rod, length $L$", ha="right", va="center", fontsize=9)
    ax.text(1.85, 2.0, "area swept", ha="left", color=RED, fontsize=9.5)
    ax.text(1.55, 0.55, "short push", color=BLUE, fontsize=8.5, rotation=0)
    ax.text(1.5, L + 0.45, "longer push", color=BLUE, fontsize=8.5, ha="center")
    ax.set_xlim(-2.1, 3.4)
    ax.set_ylim(-0.6, 5.0)
    ax.set_aspect("equal")
    ax.axis("off")

    ax = axs[1]
    ax.set_title("Sideways push along the rod", fontsize=10)
    x = np.linspace(0, 1, 50)
    v = 0.4 + 0.9 * x
    ax.fill_between(x, 0, v, color="#bcd9e6", alpha=0.8, lw=0)
    ax.plot(x, v, color=BLUE, lw=2.2)
    mid = 0.4 + 0.45
    ax.plot([0, 1], [mid, mid], color=RED, lw=1.8, ls="--")
    ax.plot(0.5, mid, "o", color=RED, ms=6)
    ax.text(0.02, mid + 0.08, "value at the middle", color=RED, ha="left", fontsize=9)
    ax.text(0.5, 0.17, "area under the line\n$=L\\times$ (value at the middle)", ha="center", fontsize=9)
    ax.set_xticks([0, 0.5, 1])
    ax.set_xticklabels(["$E$", "middle", "$T$"])
    ax.set_yticks([])
    ax.set_xlim(-0.02, 1.02)
    ax.set_ylim(0, 1.6)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    fig.tight_layout()
    save(fig, "fig_rod")


# 4 ------------------------------------------------------------ tracing a closed loop
def fig_loop():
    fig, ax = plt.subplots(figsize=(6.2, 4.0))
    th = np.linspace(0, 2 * np.pi, 400, endpoint=False)
    c = np.array([150.0, -10.0])
    r = 46 + 9 * np.sin(2 * th + 0.5) + 5 * np.cos(3 * th)
    path = np.column_stack([c[0] + r * np.cos(th), c[1] + r * np.sin(th)])
    E = S.elbow(path, side=+1)
    ax.fill(path[:, 0], path[:, 1], color="#f3d6da", zorder=1)
    ax.plot(E[:, 0], E[:, 1], color=BLUE, lw=2.4, zorder=3)
    for k in range(0, 400, 80):
        ax.plot([E[k, 0], path[k, 0]], [E[k, 1], path[k, 1]], color=INK, lw=1.0, alpha=0.7, zorder=2)
    ax.plot(*np.vstack([path, path[:1]]).T, color=RED, lw=2.2, zorder=4)
    k = 40
    ax.plot([0, E[k, 0]], [0, E[k, 1]], color=GREY, lw=3, solid_capstyle="round", zorder=2)
    ax.plot(0, 0, "s", color=INK, ms=9, zorder=5)
    ax.text(-6, -14, "pole", fontsize=9.5, ha="right", va="top")
    ax.text(c[0], c[1], "outline\narea $A$", ha="center", va="center", fontsize=10)
    ex = E[:, 0].max()
    ax.annotate("elbow: rocks along\nthis arc, encloses\nno area", xy=E[300], xytext=(E[300, 0] + 28, E[300, 1] + 18),
                fontsize=9, color=BLUE, arrowprops=dict(arrowstyle="-", color=BLUE, lw=0.8))
    ax.annotate("tracer follows\nthe outline", xy=path[330], xytext=(c[0] + 62, c[1] - 55), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="-", color=RED, lw=0.8))
    mid = E[k] / 2
    ang = math.degrees(math.atan2(E[k, 1], E[k, 0]))
    ax.text(mid[0] - 6, mid[1] + 6, "pole arm", fontsize=9, color="#6b7685", rotation=ang, ha="right", va="bottom",
            rotation_mode="anchor")
    ax.set_aspect("equal")
    ax.set_xlim(-45, 300)
    ax.set_ylim(-90, 175)
    ax.axis("off")
    fig.tight_layout()
    save(fig, "fig_loop")


# 5 ------------------------------------------------------------ reading drum and vernier
def fig_reading():
    fig, ax = plt.subplots(figsize=(7.2, 2.4))
    lo, hi = 29.0, 55.0
    ax.add_patch(Rectangle((lo, 0.9), hi - lo, 1.1, fc=SOFT, ec=INK, lw=1.2))
    for v in range(int(lo) + 1, int(hi), 1):
        if v % 2 == 0:
            ln = 0.5 if v % 10 == 0 else 0.3
            ax.plot([v, v], [2.0, 2.0 - ln], color=INK, lw=1.0)
    for v in (30, 40, 50):
        ax.text(v, 2.15, str(v), ha="center", fontsize=9)
    x0 = 36.6
    ax.add_patch(Rectangle((x0, 0.0), 16.2, 0.9, fc="white", ec=INK, lw=1.2))
    for k in range(10):
        x = x0 + 1.8 * k
        hit = k == 3
        ax.plot([x, x], [0.9, 0.9 - (0.42 if hit else 0.35)], color=RED if hit else INK, lw=2.0 if hit else 1.0)
        ax.text(x, 0.08, str(k), ha="center", fontsize=8.5, color=RED if hit else INK)
    ax.plot([x0, x0], [0.9, 2.0], color=BLUE, lw=1.4, ls="--")
    ax.plot([42, 42], [0.4, 2.0], color=RED, lw=1.0, ls=":")
    ax.annotate("vernier zero: just past 36", xy=(x0, 0.45), xytext=(30.2, -0.55), fontsize=9, color=BLUE,
                arrowprops=dict(arrowstyle="->", color=BLUE, lw=1))
    ax.annotate("line 3 lines up", xy=(42, 0.5), xytext=(41.0, -0.55), fontsize=9, color=RED,
                arrowprops=dict(arrowstyle="->", color=RED, lw=1))
    ax.text(29.2, 2.75, r"drum (each mark = 2 cm$^2$)", fontsize=9)
    ax.text(55.0, 2.75, r"reading = 36 + 3 $\times$ 0.2 = 36.6 cm$^2$", fontsize=9.5, color=INK, ha="right")
    ax.set_xlim(28.5, 55.5)
    ax.set_ylim(-0.95, 3.1)
    ax.axis("off")
    fig.tight_layout()
    save(fig, "fig_reading")


# 6 ------------------------------------------------------------ the two arms, labelled
def fig_linkage():
    fig, ax = plt.subplots(figsize=(6.4, 3.0))
    O = np.array([0.0, 0.0])
    T = np.array([228.0, 38.0])
    E = S.elbow(T[None, :], side=-1)[0]
    u = (T - E) / np.linalg.norm(T - E)
    n = np.array([-u[1], u[0]])
    if n[1] < 0:
        n = -n
    ax.plot(*zip(O, E), color=BLUE, lw=5, solid_capstyle="round", zorder=2)
    ax.plot(*zip(E, T), color=RED, lw=5, solid_capstyle="round", zorder=2)
    for p_, lab, off, ha in ((O, "pole $O$", (-4, -20), "right"), (E, "elbow $E$", (-6, -22), "right"),
                             (T, "pointer $T$", (4, 10), "left")):
        ax.plot(*p_, "o", color=INK, ms=8, zorder=5)
        ax.annotate(lab, p_, xytext=off, textcoords="offset points", fontsize=11, ha=ha)
    m1 = (O + E) / 2
    ang1 = math.degrees(math.atan2(E[1], E[0]))
    ax.text(*(m1 + 11 * (np.array([-E[1], E[0]]) / np.linalg.norm(E))), "pole arm, $R$", color=BLUE, fontsize=10.5,
            ha="center", va="center", rotation=ang1, rotation_mode="anchor")
    m2 = (E + T) / 2
    ang2 = math.degrees(math.atan2(u[1], u[0]))
    ax.text(*(E + 64 * u + 17 * n), "tracer arm, $L$", color=RED, fontsize=10.5, ha="center", va="center",
            rotation=ang2, rotation_mode="anchor")
    # wheel on the lower side of the arm; its axle runs along the arm, so it rolls sideways
    a = 38.0
    c = E + a * u - 16 * n
    along, side = 6.0, 12.0
    corners = [c + sx * along * u + sy * side * n for sx, sy in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
    ax.add_patch(Polygon(corners, closed=True, fc="#d9dee5", ec=INK, lw=1.5, zorder=3))
    ax.annotate("wheel (axle parallel to the arm)", c - side * n, xytext=(c[0] + 14, c[1] - 52), fontsize=10,
                ha="left", arrowprops=dict(arrowstyle="-", color=INK, lw=0.8))
    off = 9 * n
    ax.annotate("", xy=E + off, xytext=E + a * u + off, arrowprops=dict(arrowstyle="<->", color=INK, lw=1.1))
    ax.text(*(E + a / 2 * u + 1.9 * off), "$a$", ha="center", va="center", fontsize=11)
    ax.set_aspect("equal")
    ax.set_xlim(-45, 285)
    ax.set_ylim(-95, 90)
    ax.axis("off")
    fig.tight_layout()
    save(fig, "fig_linkage")


if __name__ == "__main__":
    fig_linkage()
    fig_strips()
    fig_pathsum()
    fig_rod()
    fig_loop()
    fig_reading()
    print("ok")
