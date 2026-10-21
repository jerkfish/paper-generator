"""Shared helpers for deterministic MAT133 computed generators."""
from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import sympy as sp

from src.mat133.models import DiagramSpec, FormulaSpec, Mat133Part
from src.render.mathfig import formula_png

INF = "∞"


def nz(rng: random.Random, low: int = -6, high: int = 6) -> int:
    value = 0
    while value == 0:
        value = rng.randint(low, high)
    return value


def pick(rng: random.Random, values):
    return values[rng.randrange(len(values))]


def frac(n, d=1) -> str:
    n, d = int(n), int(d)
    if d == 0:
        return "undefined"
    if d < 0:
        n, d = -n, -d
    g = sp.gcd(abs(n), d) or 1
    n, d = n // g, d // g
    if d == 1:
        return str(n)
    return f"{n}/{d}"


def fmt_num(value) -> str:
    """Format an exact sympy/numeric value for exam text."""
    value = sp.simplify(value)
    if value.is_Integer:
        return str(int(value))
    if value.is_Rational:
        return f"{value.p}/{value.q}"
    if value.is_Float:
        return f"{float(value):.4g}"
    return str(value).replace("**", "^").replace("*", "")


def poly_text(expr: sp.Expr) -> str:
    expr = sp.cancel(sp.together(sp.simplify(expr)))
    text = sp.sstr(expr)
    text = text.replace("**", "^").replace("*", "")
    text = text.replace("sqrt", "√").replace("pi", "π").replace("^2", "²")
    return text


def factor_text(expr: sp.Expr) -> str:
    text = sp.sstr(sp.factor(expr))
    text = text.replace("**", "^").replace("*", "")
    text = text.replace("sqrt", "√").replace("pi", "π").replace("^2", "²")
    return text


def trig_text(expr: sp.Expr) -> str:
    import re
    text = poly_text(expr)
    for fn in ("sin", "cos", "tan", "sec", "csc", "cot"):
        text = text.replace(f"{fn}(x)²", f"{fn}² x")
        text = text.replace(f"{fn}(x)^2", f"{fn}² x")
        text = text.replace(f"{fn}(x)", f"{fn} x")
    text = re.sub(r"\b1\s*\*\s*", "", text)
    return text


def interval(lo, hi, lo_closed: bool, hi_closed: bool) -> str:
    left = "[" if lo_closed else "("
    right = "]" if hi_closed else ")"
    lo_s = f"-{INF}" if lo == -sp.oo else fmt_num(lo)
    hi_s = INF if hi == sp.oo else fmt_num(hi)
    return f"{left}{lo_s}, {hi_s}{right}"


def union(*parts: str) -> str:
    return " ∪ ".join(parts)


def degrees(theta: sp.Expr) -> str:
    return f"{fmt_num(theta)}°"


def radians(theta: sp.Expr) -> str:
    return f"{fmt_num(theta)} rad"


def diagram(path: Path | None, caption: str = "", width_cm: float = 10.0):
    if path is None:
        return None
    return DiagramSpec(path=str(path), caption=caption, width_cm=width_cm)


def formula(path: Path | None, caption: str = "", width_cm: float = 6.0):
    if path is None:
        return None
    return FormulaSpec(path=str(path), caption=caption, width_cm=width_cm)


def latex_png(latex: str, out_dir: Path | None, name: str,
              caption: str = "") -> FormulaSpec | None:
    if out_dir is None:
        return None
    path = formula_png(latex, out_dir / f"{name}.png")
    return FormulaSpec(path=str(path), caption=caption, width_cm=6.0)


@dataclass(frozen=True)
class Generator:
    id: str
    topic: str
    subtopic: str
    default_marks: float
    fn: Callable[..., Mat133Part]

    def generate(self, rng: random.Random, marks: float | None = None,
                 out_dir: Path | None = None) -> Mat133Part:
        return self.fn(rng, marks or self.default_marks, out_dir)


def make_part(*, label: str, text: str, marks: float, topic: str,
              subtopic: str, answer: str, steps: list[str],
              answer_latex: str = "", solution_latex: list[str] | None = None,
              solution_marks: list[str] | None = None,
              notes: list[str] | None = None, diagram_spec=None,
              formula_spec=None) -> Mat133Part:
    return Mat133Part(
        label=label, text=text, marks=marks, topic=topic, subtopic=subtopic,
        answer=answer, answer_latex=answer_latex,
        solution_steps=steps, solution_latex=solution_latex or [],
        solution_marks=solution_marks or [],
        marking_notes=notes or [],
        diagram=diagram_spec, formula=formula_spec)
