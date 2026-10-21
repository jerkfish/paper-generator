"""Additional deterministic plots for MAT133 computed questions."""
from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "dejavusans",
    "axes.unicode_minus": False,
})


def _save(fig, out_path: Path) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return out_path


def piecewise_plot(segments, out_path: Path, x_min: float, x_max: float,
                   title: str = "") -> Path:
    """segments: (function, lo, hi, closed_left, closed_right)."""
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    xs = np.linspace(x_min, x_max, 1200)
    for fn, lo, hi, cl, cr in segments:
        mask = (xs >= lo) & (xs <= hi)
        if not mask.any():
            continue
        ys = np.array([fn(float(v)) for v in xs[mask]], dtype=float)
        ax.plot(xs[mask], ys, color="#8b1a1a", linewidth=1.9)
        for value, closed in ((lo, cl), (hi, cr)):
            try:
                y = float(fn(float(value)))
            except Exception:
                continue
            ax.plot(value, y, marker="o", markersize=6,
                    markerfacecolor="#8b1a1a" if closed else "white",
                    markeredgecolor="#8b1a1a")
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def circle_plot(centre, radius, out_path: Path, title: str = "") -> Path:
    from matplotlib.patches import Circle
    fig, ax = plt.subplots(figsize=(4.4, 4.4))
    ax.add_patch(Circle(centre, radius, fill=False, color="#8b1a1a",
                        linewidth=1.9))
    ax.plot(*centre, "o", color="#1a4f8b", markersize=6)
    ax.annotate(f"({centre[0]:g}, {centre[1]:g})", centre,
                textcoords="offset points", xytext=(8, 8), fontsize=9)
    ax.set_aspect("equal")
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    pad = radius * 0.35 + 1
    ax.set_xlim(centre[0] - radius - pad, centre[0] + radius + pad)
    ax.set_ylim(centre[1] - radius - pad, centre[1] + radius + pad)
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def line_plot(points, out_path: Path, slope=None, intercept=None,
              x_min: float | None = None, x_max: float | None = None,
              title: str = "") -> Path:
    fig, ax = plt.subplots(figsize=(4.8, 3.4))
    if slope is not None and intercept is not None:
        if x_min is None or x_max is None:
            x_min, x_max = -6, 6
        xs = np.linspace(x_min, x_max, 400)
        ax.plot(xs, slope * xs + intercept, color="#8b1a1a", linewidth=1.9)
    else:
        xs = [p[0] for p in points]
        ys = [p[1] for p in points]
        ax.plot(xs, ys, color="#8b1a1a", linewidth=1.9)
    for point in points or []:
        ax.plot(point[0], point[1], "o", color="#1a4f8b", markersize=6)
        ax.annotate(f"({point[0]:g}, {point[1]:g})", point,
                    textcoords="offset points", xytext=(6, 6), fontsize=9)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def triangle_plot(points, out_path: Path, labels=None, side_labels=None,
                  angle_labels=None, title: str = "") -> Path:
    from matplotlib.patches import Polygon
    fig, ax = plt.subplots(figsize=(5.0, 3.8))
    ax.add_patch(Polygon(points, closed=True, fill=False,
                         edgecolor="#8b1a1a", linewidth=1.9))
    labels = labels or [chr(65 + i) for i in range(len(points))]
    for point, label in zip(points, labels):
        ax.plot(point[0], point[1], "o", color="#1a4f8b", markersize=6)
        ax.annotate(label, point, textcoords="offset points", xytext=(8, 8),
                    fontsize=11, fontweight="bold")
    if side_labels:
        for i, text in enumerate(side_labels):
            p1, p2 = points[i], points[(i + 1) % len(points)]
            mid = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
            ax.annotate(text, mid, textcoords="offset points", xytext=(0, -14),
                        ha="center", fontsize=9)
    if angle_labels:
        for i, text in enumerate(angle_labels):
            p = points[i]
            ax.annotate(text, p, textcoords="offset points", xytext=(18, -12),
                        fontsize=9)
    ax.set_aspect("equal")
    ax.axis("off")
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    x_pad = max(0.8, 0.15 * (max(xs) - min(xs)))
    y_pad = max(0.8, 0.15 * (max(ys) - min(ys)))
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def sector_plot(radius: float, angle_deg: float, out_path: Path,
                inner_radius: float = 0.0, start_deg: float = 20.0,
                title: str = "") -> Path:
    from matplotlib.patches import Wedge
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    theta1, theta2 = start_deg, start_deg + angle_deg
    if inner_radius > 0:
        ax.add_patch(Wedge((0, 0), radius, theta1, theta2,
                           width=radius - inner_radius,
                           facecolor="#f0c7c7", edgecolor="#8b1a1a",
                           linewidth=1.6))
        ax.add_patch(Wedge((0, 0), inner_radius, theta1, theta2,
                           facecolor="white", edgecolor="#8b1a1a",
                           linewidth=1.2))
    else:
        ax.add_patch(Wedge((0, 0), radius, theta1, theta2,
                           facecolor="#f0c7c7", edgecolor="#8b1a1a",
                           linewidth=1.6))
    ax.plot(0, 0, "o", color="#1a4f8b", markersize=5)
    ax.annotate("O", (0, 0), textcoords="offset points", xytext=(6, 6),
                fontsize=11, fontweight="bold")
    ax.set_aspect("equal")
    ax.axis("off")
    # Crop to the drawn sector rather than the full circle.  A 30-degree
    # sector otherwise occupies a tiny part of a square canvas.
    angles = np.linspace(np.deg2rad(theta1), np.deg2rad(theta2), 120)
    xs = [0.0] + list(radius * np.cos(angles))
    ys = [0.0] + list(radius * np.sin(angles))
    if inner_radius > 0:
        xs += list(inner_radius * np.cos(angles))
        ys += list(inner_radius * np.sin(angles))
    x_pad = max(0.8, 0.12 * (max(xs) - min(xs)))
    y_pad = max(0.8, 0.12 * (max(ys) - min(ys)))
    ax.set_xlim(min(xs) - x_pad, max(xs) + x_pad)
    ax.set_ylim(min(ys) - y_pad, max(ys) + y_pad)
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def feasible_region_plot(inequalities, out_path: Path,
                         x_min: float = -6, x_max: float = 8,
                         y_min: float = -6, y_max: float = 8,
                         title: str = "") -> Path:
    """Shade the region satisfying a x + b y <= c for every item."""
    fig, ax = plt.subplots(figsize=(4.8, 4.2))
    xs = np.linspace(x_min, x_max, 700)
    ys = np.linspace(y_min, y_max, 700)
    xx, yy = np.meshgrid(xs, ys)
    keep = np.ones_like(xx, dtype=bool)
    for item in inequalities:
        a, b, c = item["a"], item["b"], item["c"]
        op = item.get("op", "<=")
        expr = a * xx + b * yy
        if op == "<=":
            keep &= expr <= c + 1e-9
        elif op == ">=":
            keep &= expr >= c - 1e-9
        elif op == "<":
            keep &= expr < c - 1e-9
        elif op == ">":
            keep &= expr > c + 1e-9
    ax.contourf(xx, yy, keep.astype(float), levels=[0.5, 1.5],
                colors=["#f0c7c7"], alpha=0.75)
    for item in inequalities:
        a, b, c = item["a"], item["b"], item["c"]
        if abs(b) > 1e-9:
            ax.plot(xs, (c - a * xs) / b, color="#8b1a1a", linewidth=1.5)
        else:
            ax.axvline(c / a, color="#8b1a1a", linewidth=1.5)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)


def trig_plot(expr, x_min: float, x_max: float, out_path: Path,
              title: str = "") -> Path:
    from src.render.mathfig import function_plot
    return function_plot(expr, x_min, x_max, out_path, title=title)


def parabola_plot(h: float, k: float, p: float, out_path: Path,
                  vertical: bool = True, title: str = "") -> Path:
    """Plot a standard parabola with vertex (h,k) and focal length p."""
    fig, ax = plt.subplots(figsize=(4.8, 4.0))
    t = np.linspace(-6, 6, 800)
    if vertical:
        xs = h + t
        ys = k + t * t / (4 * p)
        ax.plot(xs, ys, color="#8b1a1a", linewidth=1.9)
        ax.plot(h, k + p, "o", color="#1a4f8b", markersize=6)
        ax.annotate("focus", (h, k + p), textcoords="offset points",
                    xytext=(8, 6), fontsize=9)
        ax.axhline(k - p, color="#1a4f8b", linewidth=1.1, linestyle="--")
        ax.annotate("directrix", (h + 1, k - p), textcoords="offset points",
                    xytext=(8, -10), fontsize=9)
    else:
        xs = h + t * t / (4 * p)
        ys = k + t
        ax.plot(xs, ys, color="#8b1a1a", linewidth=1.9)
        ax.plot(h + p, k, "o", color="#1a4f8b", markersize=6)
        ax.annotate("focus", (h + p, k), textcoords="offset points",
                    xytext=(8, 6), fontsize=9)
        ax.axvline(h - p, color="#1a4f8b", linewidth=1.1, linestyle="--")
        ax.annotate("directrix", (h - p, k + 1), textcoords="offset points",
                    xytext=(-45, 8), fontsize=9)
    ax.plot(h, k, "o", color="#1a4f8b", markersize=6)
    ax.annotate("vertex", (h, k), textcoords="offset points",
                xytext=(8, -12), fontsize=9)
    ax.axhline(0, color="#333", linewidth=0.7)
    ax.axvline(0, color="#333", linewidth=0.7)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=10)
    return _save(fig, out_path)
