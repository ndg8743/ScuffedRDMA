#!/usr/bin/env python3
"""quant_figures.py: the six pictures of the two slides that compare TurboQuant with our quantizer.

One synthetic vector of 64 coordinates (a few large channels and small noise) goes through both methods:

  tq_*  TurboQuant as the Google Research post of March 24, 2026 presents it: a random rotation matrix
        (QR decomposition of a matrix of normal entries, as in Algorithm 1 of arXiv 2504.19874), the recursive
        polar transformation of PolarQuant (arXiv 2502.02617: pairs of coordinates become a radius and an angle,
        the radii are paired again until one is left; 4 bits for an angle of the first level and 2 bits above),
        and one sign per coordinate of a Gaussian projection of the residual (Algorithm 2 of arXiv 2504.19874).
        This part is our reading of the published steps, written for the picture. It is not the authors' code.
  sq_*  ours: the module middleware/rdma_tensor_cache/scuffed_quant.py of this repository, with the settings of
        the tests and benchmarks (dim 64, 3 bits, 256 signs, seed 42).

Every picture is drawn at the size it has on the slide (inches), so a label of 14 pt is 14 pt on the slide.
No number in these pictures is a result: they show how the steps work on one vector and compare no quality.

Writes assets/diagrams/<name>.png and assets/diagrams/manifest.json (size in inches, alt text, the numbers).
Usage: python3 tools/quant_figures.py"""
import json, os, sys
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.colors import LinearSegmentedColormap, ListedColormap
from matplotlib.patches import Wedge, Rectangle, Circle, Arc, FancyArrowPatch

HERE = os.path.dirname(os.path.abspath(__file__))
PRES = os.path.dirname(HERE)
REPO = os.path.dirname(PRES)
OUT = os.path.join(PRES, "assets", "diagrams")
os.makedirs(OUT, exist_ok=True)
sys.path.insert(0, REPO)
from middleware.rdma_tensor_cache.scuffed_quant import ScuffedQuant  # noqa: E402

# the palette of the deck (tools/deck/theme.json) and the two light fills of the animations
INK, NAVY, BLUE, GRAY, RULE, HAIR, PANEL, LIGHT = "#1A202C", "#173A79", "#005AB5", "#5C6066", "#8A929C", "#C9CED6", "#EEF1F5", "#E3E7EC"
TINT = "#D3DBEA"                                  # navy at about 18 percent: the cell or sector that holds the point
for f in ("Carlito-Regular.ttf", "Carlito-Bold.ttf", "Carlito-Italic.ttf", "Carlito-BoldItalic.ttf"):
    p = "/usr/share/fonts/truetype/crosextra/" + f
    if os.path.exists(p):
        font_manager.fontManager.addfont(p)
plt.rcParams["font.family"] = "Carlito"
DPI = 300
D = 64

SQD = np.sqrt(D)
SECT = 16                                          # 4 bits for an angle of the first level
sq = ScuffedQuant(dim=D, bits=3, qjl_dim=256, seed=42)


# ---------------------------------------------------------------- the example vector
def vector(seed):
    rng = np.random.default_rng(seed)
    x = 0.35 * rng.standard_normal(D)
    for pos, val in zip(rng.choice(D, 3, replace=False), (6.0, -3.6, 2.6)):   # a few channels much larger than the rest
        x[pos] = val
    return x.astype(np.float32)


def rotation(seed):
    Q, Rm = np.linalg.qr(np.random.default_rng(seed).standard_normal((D, D)))
    return Q * np.sign(np.diag(Rm))                # a random rotation matrix


# Two seeds are chosen for the look of the pictures and for nothing else. The seed of the vector is the first
# for which the first two rotated coordinates of ours lie in the upper right quarter, at two different inner
# levels and at least 0.2 units away from them, so that the rounding can be seen. The seed of the rotation matrix is the first for which the
# first two coordinates give an angle between 32 and 58 degrees that lies 6 to 9 degrees from the middle of its
# sector, so that the rounding can be seen, and for which the largest rotated coordinate is as large as with ours to within 0.02, so that the
# two pictures of the rotation suggest no difference between the methods.
def pick_vector():
    for seed in range(1, 2000):
        x = vector(seed)
        u = x.astype(np.float64) / float(np.linalg.norm(x))
        y = sq._rotate(u.astype(np.float32).copy()).astype(np.float64) * SQD
        k = np.searchsorted(sq.boundaries, y[:2] / SQD)
        d = np.abs(y[:2] - sq.codebook[k] * SQD)
        if 0.55 < y[0] < 1.65 and 0.55 < y[1] < 1.65 and k[0] != k[1] and d.min() > 0.2:
            return seed
    raise SystemExit("no seed for the vector")


SEED_X = pick_vector()
x = vector(SEED_X)
ell = float(np.linalg.norm(x))
u = x.astype(np.float64) / ell
y_sq = sq._rotate(u.astype(np.float32).copy()).astype(np.float64)


def pick_rotation():
    for seed in range(1, 20000):
        y = rotation(seed) @ u
        th = np.degrees(np.arctan2(y[1], y[0]))
        inside = (th / (360.0 / SECT)) % 1.0
        if 32 < th < 58 and 0.10 < inside < 0.90 and abs(inside - 0.5) > 0.26 and abs(np.max(np.abs(y)) - np.max(np.abs(y_sq))) < 0.02:
            return seed
    raise SystemExit("no seed for the rotation matrix")


# ---------------------------------------------------------------- TurboQuant as the post presents it
SEED_PI = pick_rotation()
PI = rotation(SEED_PI)
y_tq = PI @ u


def polar(v):
    """Recursive polar transformation: angles of every level (level 1 first) and the final radius."""
    angles, r = [], v
    first = True
    while len(r) > 1:
        a, b = r[0::2], r[1::2]
        th = np.arctan2(b, a)
        if first:
            th = np.mod(th, 2 * np.pi)
            first = False
        angles.append(th)
        r = np.hypot(a, b)
    return angles, float(r[0])


def unpolar(angles, radius):
    r = np.array([radius])
    for th in reversed(angles):
        out = np.empty(2 * len(r))
        out[0::2], out[1::2] = r * np.cos(th), r * np.sin(th)
        r = out
    return r


def lloyd(samples, k, rounds=60):
    """One-dimensional k-means (the rule of Lloyd and Max) on samples."""
    c = np.quantile(samples, (np.arange(k) + 0.5) / k)
    for _ in range(rounds):
        b = (c[:-1] + c[1:]) / 2
        idx = np.searchsorted(b, samples)
        c = np.array([samples[idx == i].mean() if np.any(idx == i) else c[i] for i in range(k)])
    return np.sort(c)


LEVELS = int(np.log2(D))                           # 6 levels for 64 coordinates
books = [2 * np.pi * (np.arange(SECT) + 0.5) / SECT]
train = np.random.default_rng(12).standard_normal((20000, D))
train_angles = [np.concatenate(a) for a in zip(*[polar(v)[0] for v in train])]
for lev in range(1, LEVELS):
    books.append(lloyd(train_angles[lev], 4))      # 2 bits for an angle of a higher level

ang, radius = polar(y_tq)
codes_tq, ang_hat = [], []
for lev, th in enumerate(ang):
    if lev == 0:
        k = np.floor(th / (2 * np.pi / SECT)).astype(int) % SECT
    else:
        k = np.abs(th[:, None] - books[lev][None, :]).argmin(axis=1)
    codes_tq.append(k)
    ang_hat.append(books[lev][k])
y_tq_hat = unpolar(ang_hat, radius)
res_tq = u - PI.T @ y_tq_hat                       # the residual of the vector itself, as in Algorithm 2
S_tq = np.random.default_rng(13).standard_normal((D, D))
signs_tq = (S_tq @ res_tq >= 0).astype(int)        # one sign per coordinate

# ---------------------------------------------------------------- ours: the module of this repository
comp = sq.compress(x[None, :])
idx_sq = comp.indices[0].astype(int)
levels = sq.codebook.astype(np.float64)
bounds = sq.boundaries.astype(np.float64)
y_sq_hat = levels[idx_sq]
signs_sq = comp.qjl_signs[0].astype(int)           # 256 signs for the vector
Hm = np.array([sq._rotate(e.copy()) for e in np.eye(D, dtype=np.float32)]).T * np.sqrt(D)   # H D, entries +1 and -1
Dsign = sq._signs[:D].astype(int)
Hpure = (Hm * Dsign[None, :]).round().astype(int)  # H alone
packed = len(comp.pack()) - 20                     # bytes of the vector without the 20-byte block header
assert packed == 64 and np.allclose(np.abs(Hm), 1.0) and abs(np.linalg.norm(y_sq) - 1) < 1e-5 and abs(np.linalg.norm(y_tq) - 1) < 1e-6
assert np.array_equal(Hpure @ Hpure.T, D * np.eye(D, dtype=int))
H2 = np.array([[1, 1], [1, -1]])
Hs = np.array([[1]])
for _ in range(int(np.log2(D))):
    Hs = np.kron(H2, Hs)                           # the matrix built by doubling
assert np.array_equal(Hpure, Hs)


# ---------------------------------------------------------------- drawing helpers (coordinates in inches)
def canvas(w, h):
    fig = plt.figure(figsize=(w, h), dpi=DPI)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, w); ax.set_ylim(0, h); ax.set_aspect("equal"); ax.axis("off")
    return fig, ax


def label(ax, xx, yy, s, size=14, color=INK, ha="center", va="center", bold=False, italic=False):
    ax.text(xx, yy, s, fontsize=size, color=color, ha=ha, va=va, fontweight="bold" if bold else "normal",
            fontstyle="italic" if italic else "normal")


def bars(ax, x0, yc, w, half, values, vmax, color=NAVY):
    n = len(values); bw = w / n
    ax.plot([x0 - 0.02, x0 + w + 0.02], [yc, yc], color=RULE, lw=0.7, zorder=1)
    for i, v in enumerate(values):
        hh = half * v / vmax
        ax.add_patch(Rectangle((x0 + i * bw + 0.1 * bw, min(yc, yc + hh)), 0.8 * bw, abs(hh), color=color, lw=0, zorder=2))


def arrow(ax, x0, x1, yy):
    ax.add_patch(FancyArrowPatch((x0, yy), (x1, yy), arrowstyle="-|>", mutation_scale=8, color=GRAY, lw=1.1, shrinkA=0, shrinkB=0))


def save(fig, name):
    fig.savefig(os.path.join(OUT, name + ".png"), dpi=DPI, transparent=True)
    plt.close(fig)


def signgrid(ax, x0, ytop, cell, cols, bits):
    for i, b in enumerate(bits):
        r, c = divmod(i, cols)
        ax.add_patch(Rectangle((x0 + c * cell, ytop - (r + 1) * cell), cell, cell, facecolor=BLUE if b else "white", edgecolor=HAIR, lw=0.45))
    rows = (len(bits) + cols - 1) // cols
    ax.add_patch(Rectangle((x0, ytop - rows * cell), cols * cell, rows * cell, fill=False, edgecolor=RULE, lw=0.9))


HH = 2.6                                            # height of every picture
# ---------------------------------------------------------------- pictures 1: the rotation
W1 = 3.6
VMAX = 0.9
MXL, MSIDE, MYC = 1.24, 1.12, 1.50                  # the square of the matrix: left edge, side, center height


def rotation_picture(name, before, after, draw_matrix, top):
    fig, ax = canvas(W1, HH)
    bars(ax, 0.06, MYC, 1.0, 0.78, before, VMAX)
    bars(ax, 2.54, MYC, 1.0, 0.78, after, VMAX)
    arrow(ax, 1.09, 1.21, MYC); arrow(ax, 2.39, 2.51, MYC)
    draw_matrix(ax)
    label(ax, 0.56, 2.40, "before", color=GRAY)
    label(ax, 3.04, 2.40, "after", color=GRAY)
    label(ax, MXL + MSIDE / 2, 2.40, top, size=15, color=NAVY, bold=True)
    label(ax, 0.56, 0.88, "largest %.2f" % np.max(np.abs(before)), color=GRAY)
    label(ax, 3.04, 0.88, "largest %.2f" % np.max(np.abs(after)), color=GRAY)
    save(fig, name)


def dense_matrix(ax):
    cmap = LinearSegmentedColormap.from_list("gn", ["#FFFFFF", HAIR, NAVY])
    lim = float(np.quantile(np.abs(PI), 0.995))
    y0 = MYC - MSIDE / 2
    ax.imshow(PI, extent=(MXL, MXL + MSIDE, y0, y0 + MSIDE), cmap=cmap, vmin=-lim, vmax=lim, interpolation="nearest", zorder=2)
    ax.add_patch(Rectangle((MXL, y0), MSIDE, MSIDE, fill=False, edgecolor=RULE, lw=0.9, zorder=3))
    label(ax, MXL + MSIDE / 2, 0.52, "4,096 random numbers")


def hadamard_matrix(ax):
    two = ListedColormap([LIGHT, NAVY])
    y0 = MYC - MSIDE / 2
    ax.imshow((Hpure > 0).astype(int), extent=(MXL, MXL + MSIDE, y0, y0 + MSIDE), cmap=two, vmin=0, vmax=1, interpolation="nearest", zorder=2)
    ax.add_patch(Rectangle((MXL, y0), MSIDE, MSIDE, fill=False, edgecolor=RULE, lw=0.9, zorder=3))
    ax.imshow((Dsign[None, :] > 0).astype(int), extent=(MXL, MXL + MSIDE, 0.64, 0.80), cmap=two, vmin=0, vmax=1, interpolation="nearest", zorder=2, aspect="auto")
    ax.add_patch(Rectangle((MXL, 0.64), MSIDE, 0.16, fill=False, edgecolor=RULE, lw=0.9, zorder=3))
    label(ax, MXL + MSIDE / 2, 0.40, "and 64 random signs")


rotation_picture("tq_rotation", u, y_tq, dense_matrix, "rotation matrix")
rotation_picture("sq_rotation", u, y_sq, hadamard_matrix, "Hadamard matrix")

# ---------------------------------------------------------------- pictures 2: where a coordinate goes
W2 = 5.3
CX, CY, RAD = 1.15, 1.42, 0.93
TX0, TX1, NX = 2.62, 4.70, 5.02                     # the tree and the strip chart of ours; the column of counts


def axes_cross(ax):
    ax.plot([CX - RAD - 0.12, CX + RAD + 0.12], [CY, CY], color=RULE, lw=0.8, zorder=1)
    ax.plot([CX, CX], [CY - RAD - 0.12, CY + RAD + 0.12], color=RULE, lw=0.8, zorder=1)
    label(ax, CX + RAD + 0.21, CY - 0.16, "y₁", italic=True, color=GRAY)
    label(ax, CX + 0.18, CY + RAD + 0.13, "y₂", italic=True, color=GRAY)


pair_tq = 0                                        # the circle shows the first two rotated coordinates
th_p, k_p = float(ang[0][pair_tq]), int(codes_tq[0][pair_tq])

fig, ax = canvas(W2, HH)
ax.add_patch(Wedge((CX, CY), RAD, np.degrees(2 * np.pi * k_p / SECT), np.degrees(2 * np.pi * (k_p + 1) / SECT), facecolor=TINT, edgecolor="none", zorder=0))
for k in range(SECT):
    a = 2 * np.pi * k / SECT
    ax.plot([CX, CX + RAD * np.cos(a)], [CY, CY + RAD * np.sin(a)], color=HAIR, lw=0.7, zorder=1)
ax.add_patch(Circle((CX, CY), RAD, fill=False, edgecolor=RULE, lw=1.1, zorder=2))
axes_cross(ax)
rr = 0.70 * RAD
px, py = CX + rr * np.cos(th_p), CY + rr * np.sin(th_p)
a_hat = books[0][k_p]
ax.plot([CX, CX + RAD * np.cos(a_hat)], [CY, CY + RAD * np.sin(a_hat)], color=NAVY, lw=1.2, ls=(0, (3, 2)), zorder=3)
ax.plot([CX, px], [CY, py], color=NAVY, lw=2.4, zorder=4, solid_capstyle="round")
ax.add_patch(Circle((px, py), 0.055, color=NAVY, zorder=5))
ax.add_patch(Arc((CX, CY), 0.64, 0.64, theta1=0, theta2=np.degrees(th_p), color=INK, lw=1.0, zorder=4))
label(ax, CX + 0.45 * np.cos(th_p / 2), CY + 0.45 * np.sin(th_p / 2) - 0.01, "θ", size=15, italic=True)
mx, my = CX + 0.58 * rr * np.cos(th_p), CY + 0.58 * rr * np.sin(th_p)
label(ax, mx - 0.14 * np.sin(th_p), my + 0.14 * np.cos(th_p), "r", size=15, italic=True, color=NAVY, bold=True)
label(ax, CX, 0.19, "16 sectors for the angle", color=GRAY)
# the tree: every joint turns two values into one radius (passed up) and one angle (kept)
Y0, DY = 0.56, 0.268
xs = [np.linspace(TX0, TX1, D)]
for lev in range(LEVELS):
    xs.append((xs[-1][0::2] + xs[-1][1::2]) / 2)
for lev in range(LEVELS):
    ya, yb = Y0 + lev * DY, Y0 + (lev + 1) * DY
    for i, xb in enumerate(xs[lev + 1]):
        for xa in (xs[lev][2 * i], xs[lev][2 * i + 1]):
            ax.plot([xa, xb], [ya, yb], color=RULE, lw=0.5, zorder=1)
s0 = 0.022
for xa in xs[0]:
    ax.add_patch(Rectangle((xa - s0 / 2, Y0 - s0 / 2), s0, s0, color=GRAY, lw=0, zorder=2))
sizes = [0.014, 0.020, 0.028, 0.037, 0.047, 0.058]
for lev in range(LEVELS):
    for xb in xs[lev + 1]:
        ax.add_patch(Circle((xb, Y0 + (lev + 1) * DY), sizes[lev], color=NAVY, lw=0, zorder=3))
    label(ax, NX, Y0 + (lev + 1) * DY, str(D >> (lev + 1)), size=15, color=NAVY, bold=True)
top_y = Y0 + LEVELS * DY
ax.add_patch(Circle((xs[-1][0], top_y), 0.095, fill=False, edgecolor=NAVY, lw=1.2, zorder=3))
label(ax, NX, top_y + 0.27, "angles", color=NAVY)
label(ax, xs[-1][0] - 0.17, top_y + 0.02, "one radius", ha="right")
label(ax, (TX0 + TX1) / 2, 0.19, "64 coordinates", color=GRAY)
save(fig, "tq_polar")

# ours: the same two coordinates on a grid of eight fixed levels per axis, and all 64 coordinates on the levels
SC = RAD / 2.75                                     # inches per unit of 1/sqrt(d)
lv, bd = levels * SQD, bounds * SQD
pair_sq = 0                                        # the grid shows the first two rotated coordinates
a_p, b_p = float(y_sq[2 * pair_sq] * SQD), float(y_sq[2 * pair_sq + 1] * SQD)
ia, ib = int(idx_sq[2 * pair_sq]), int(idx_sq[2 * pair_sq + 1])

fig, ax = canvas(W2, HH)
edge = np.concatenate(([-2.75], bd, [2.75]))
ax.add_patch(Rectangle((CX + edge[ia] * SC, CY + edge[ib] * SC), (edge[ia + 1] - edge[ia]) * SC, (edge[ib + 1] - edge[ib]) * SC, facecolor=TINT, edgecolor="none", zorder=0))
for v in lv:
    ax.plot([CX + v * SC, CX + v * SC], [CY - RAD, CY + RAD], color=HAIR, lw=0.7, zorder=1)
    ax.plot([CX - RAD, CX + RAD], [CY + v * SC, CY + v * SC], color=HAIR, lw=0.7, zorder=1)
ax.add_patch(Rectangle((CX - RAD, CY - RAD), 2 * RAD, 2 * RAD, fill=False, edgecolor=RULE, lw=1.1, zorder=2))
axes_cross(ax)
px, py = CX + a_p * SC, CY + b_p * SC
qx, qy = CX + lv[ia] * SC, CY + lv[ib] * SC
ax.plot([CX, px], [CY, CY], color=NAVY, lw=2.4, zorder=4, solid_capstyle="round")
ax.plot([px, px], [CY, py], color=NAVY, lw=2.4, zorder=4, solid_capstyle="round")
ax.plot([px, qx], [py, qy], color=NAVY, lw=1.0, zorder=4)
ax.add_patch(Rectangle((qx - 0.05, qy - 0.05), 0.10, 0.10, fill=False, edgecolor=NAVY, lw=1.3, zorder=5))
ax.add_patch(Circle((px, py), 0.045, color=NAVY, zorder=6))
label(ax, CX, 0.19, "8 levels for each coordinate", color=GRAY)
# the 64 rotated coordinates against the eight levels
SY = 0.86 / 2.75
for v in lv:
    ax.plot([TX0 - 0.04, TX1 + 0.04], [CY + v * SY, CY + v * SY], color=HAIR, lw=1.0, zorder=1)
xi = np.linspace(TX0, TX1, D)
for i in range(D):
    v, q = y_sq[i] * SQD, lv[idx_sq[i]]
    ax.plot([xi[i], xi[i]], [CY + v * SY, CY + q * SY], color=NAVY, lw=0.8, zorder=2)
    ax.add_patch(Circle((xi[i], CY + v * SY), 0.019, color=NAVY, lw=0, zorder=3))
label(ax, NX, CY + 0.15, "8", size=19, color=NAVY, bold=True)
label(ax, NX, CY - 0.11, "levels", color=NAVY)
label(ax, (TX0 + TX1) / 2, 0.19, "64 coordinates", color=GRAY)
save(fig, "sq_levels")

# ---------------------------------------------------------------- pictures 3: the signs kept for the error
W3, CELL = 2.4, 0.125
GX = (W3 - 16 * CELL) / 2
fig, ax = canvas(W3, HH)
signgrid(ax, GX, 1.71, CELL, 16, signs_tq)
label(ax, W3 / 2, 0.93, "64 signs")
save(fig, "tq_signs")
fig, ax = canvas(W3, HH)
signgrid(ax, GX, 2.46, CELL, 16, signs_sq)
label(ax, W3 / 2, 0.21, "256 signs")
save(fig, "sq_signs")

# ---------------------------------------------------------------- manifest: sizes, alt text, numbers
big_before = float(np.max(np.abs(u)))
num = {
    "dimension": D,
    "seed_of_the_vector": SEED_X,
    "seed_of_the_rotation_matrix": SEED_PI,
    "largest_entry_before": round(big_before, 2),
    "largest_entry_after_random_rotation": round(float(np.max(np.abs(y_tq))), 2),
    "largest_entry_after_hadamard_rotation": round(float(np.max(np.abs(y_sq))), 2),
    "polar_pair": [2 * pair_tq + 1, 2 * pair_tq + 2],
    "polar_pair_angle_degrees": round(float(np.degrees(th_p)), 1),
    "polar_pair_sector_of_16": k_p + 1,
    "levels_pair": [2 * pair_sq + 1, 2 * pair_sq + 2],
    "levels_in_units_of_one_over_sqrt_d": [round(float(v), 3) for v in lv],
    "plus_signs_of_64": int(signs_tq.sum()),
    "plus_signs_of_256": int(signs_sq.sum()),
    "packed_bytes_of_the_vector": packed,
}
alt = {
    "tq_rotation": "Picture in three parts. Left, labeled before: the 64 coordinates of the example vector as bars; three bars are tall, the tallest is %.2f, and the rest are short. "
                   "Middle, labeled rotation matrix: a square of 64 by 64 cells in many shades, which looks like noise, with the text 4,096 random numbers under it. "
                   "Right, labeled after: 64 bars of similar, small size; the tallest is %.2f. Under each set of bars its largest value is printed." % (big_before, np.max(np.abs(y_tq))),
    "tq_polar": "Picture in two parts. Left: a circle divided into 16 equal sectors, with the axes y 1 and y 2. A point is joined to the center by a line labeled r, an arc from the "
                "y 1 axis to that line is labeled theta, the sector that holds the point is shaded, a dashed line marks the middle of that sector, and the text under the circle reads 16 sectors for the angle. "
                "Right: a tree over 64 coordinates. Neighbors are joined in pairs, the 32 joints are joined in pairs again, and so on up to one joint at the top, which is "
                "labeled one radius. A column labeled angles counts the joints of each row: 32, 16, 8, 4, 2 and 1.",
    "tq_signs": "A grid of 64 cells in 4 rows of 16, some filled and some empty, with the text 64 signs under it.",
    "sq_rotation": "Picture in three parts. Left, labeled before: the same 64 coordinates as bars; three bars are tall, the tallest is %.2f. "
                   "Middle, labeled Hadamard matrix: a square of 64 by 64 cells in two shades that form a regular pattern, which repeats at every scale, and under it one row of 64 cells "
                   "in the same two shades with the text and 64 random signs. Right, labeled after: 64 bars of similar, small size; the tallest is %.2f. Under each set of bars its largest value is printed." % (big_before, np.max(np.abs(y_sq))),
    "sq_levels": "Picture in two parts. Left: a square with the axes y 1 and y 2 and eight vertical and eight horizontal lines, closer together near the center. "
                 "A point is reached by one step along y 1 and one step along y 2, the rectangle of the grid that holds it is shaded, and a short line joins the point to the "
                 "nearest crossing of two lines, which is marked with a small square; the text under the square reads 8 levels for each coordinate. Right: the 64 rotated coordinates as dots over eight horizontal lines labeled 8 levels, "
                 "each dot joined to the nearest line by a short stroke.",
    "sq_signs": "A grid of 256 cells in 16 rows of 16, some filled and some empty, with the text 256 signs under it. The cells have the size of those on the slide before.",
}
size = {"tq_rotation": (W1, HH), "tq_polar": (W2, HH), "tq_signs": (W3, HH), "sq_rotation": (W1, HH), "sq_levels": (W2, HH), "sq_signs": (W3, HH)}
man = {k: {"w": size[k][0], "h": size[k][1], "alt": alt[k]} for k in size}
man["_numbers"] = num
json.dump(man, open(os.path.join(OUT, "manifest.json"), "w"), indent=1)
print(json.dumps(num, indent=1))
