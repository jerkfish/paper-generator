"""Deterministic math figures for paper/scheme generation.

Formulas and diagrams are rendered to high-DPI PNGs and embedded in DOCX.
This keeps symbols (∞, ∪, ≤, √, π), fractions, graphs, sign tables and pie
charts independent of the Word equation editor.  LaTeX is the source format.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import sympy as sp

DOT_BIN = Path(r"C:\Program Files\Graphviz\bin\dot.exe")
matplotlib.rcParams.update({
    "font.family": "DejaVu Sans",
    "mathtext.fontset": "dejavusans",
    "axes.unicode_minus": False,
})


LATEX_ALIASES = {
    r"\le": r"\leq",
    r"\ge": r"\geq",
    r"\Rightarrow": r"\rightarrow",
    r"\Longrightarrow": r"\rightarrow",
}


def normalize_latex(latex: str) -> str:
    # Replace only complete commands.  A plain str.replace("\\le", "\\leq")
    # corrupts \\left into \\leqft and breaks every bracketed formula.
    import re
    for old, new in LATEX_ALIASES.items():
        latex = re.sub(re.escape(old) + r"(?![A-Za-z])",
                       lambda _match, value=new: value, latex)
    return latex


def formula_png(latex: str, out_path: Path, fontsize: int = 14,
                dpi: int = 300) -> Path:
    """Render a LaTeX math expression to a transparent PNG."""
    latex = normalize_latex(latex)
    fig = plt.figure(figsize=(0.01, 0.01))
    fig.text(0, 0, f"${latex}$", fontsize=fontsize, color="black")
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, transparent=True,
                bbox_inches="tight", pad_inches=0.03)
    plt.close(fig)
    return out_path


def function_plot(expr: str, x_min: float, x_max: float, out_path: Path,
                  points: int = 800, title: str = "",
                  dpi: int = 300) -> Path:
    """Plot a SymPy-parseable expression of x."""
    x = sp.Symbol("x")
    parsed = sp.sympify(expr)
    fn = sp.lambdify(x, parsed, modules=["numpy"])
    xs = np.linspace(x_min, x_max, points)
    ys = fn(xs)
    fig, ax = plt.subplots(figsize=(5.2, 3.2))
    ax.plot(xs, ys, color="#8b1a1a", linewidth=1.8)
    ax.axhline(0, color="#333", linewidth=0.8)
    ax.axvline(0, color="#333", linewidth=0.8)
    ax.grid(True, color="#dddddd", linewidth=0.6)
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    if title:
        ax.set_title(title, fontsize=10)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def pie_chart(labels: list[str], values: list[float], out_path: Path,
              title: str = "", dpi: int = 300) -> Path:
    fig, ax = plt.subplots(figsize=(4.4, 3.4))
    ax.pie(values, labels=labels, autopct="%1.0f%%", startangle=90,
           colors=plt.cm.tab20.colors[:len(values)])
    ax.axis("equal")
    if title:
        ax.set_title(title, fontsize=10)
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def number_line(intervals: list[tuple[float, float, bool, bool]],
                points: list[float] | None = None, out_path: Path | None = None,
                x_min: float | None = None, x_max: float | None = None,
                dpi: int = 300) -> Path:
    """Draw intervals and points on a number line.

    intervals: (start, end, closed_start, closed_end)
    """
    points = points or []
    all_values = [v for interval in intervals for v in interval[:2]] + points
    lo = x_min if x_min is not None else min(all_values) - 1
    hi = x_max if x_max is not None else max(all_values) + 1
    fig, ax = plt.subplots(figsize=(5.6, 1.3))
    ax.set_xlim(lo, hi)
    ax.set_ylim(-0.5, 0.5)
    ax.axhline(0, color="#000", linewidth=1.2)
    for start, end, closed_start, closed_end in intervals:
        ax.plot([start, end], [0.18, 0.18], color="#1a4f8b", linewidth=5,
                solid_capstyle="butt")
        for value, closed in ((start, closed_start), (end, closed_end)):
            ax.plot(value, 0.18, marker="o" if closed else "o",
                    markersize=8, markerfacecolor="white" if not closed
                    else "#1a4f8b", markeredgecolor="#1a4f8b")
    for value in points:
        ax.plot(value, 0, "o", color="#8b1a1a", markersize=7)
        ax.text(value, -0.32, str(value), ha="center", va="top", fontsize=9)
    ax.set_yticks([])
    ax.set_xticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)
    out_path = Path(out_path or "number_line.png")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    return out_path


def graphviz_png(dot_source: str, out_path: Path,
                 dot_bin: Path = DOT_BIN) -> Path:
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.run(
        [str(dot_bin), "-Tpng", "-Gdpi=220", "-o", str(out_path)],
        input=dot_source, text=True, capture_output=True, timeout=60)
    if proc.returncode != 0:
        raise RuntimeError(f"Graphviz failed: {proc.stderr.strip()}")
    return out_path
