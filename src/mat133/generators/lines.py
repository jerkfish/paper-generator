"""Priority 2 generators: straight lines."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, nz, pick, poly_text,
)
from src.render.plots import line_plot

x, y = sp.symbols("x y")


def _line_text(m, b) -> str:
    if m == 0:
        return f"y = {fmt_num(b)}"
    if b == 0:
        return f"y = {poly_text(m*x)}"
    sign = "+" if b > 0 else "-"
    return f"y = {poly_text(m*x)} {sign} {fmt_num(abs(b))}"


def through_points(rng: random.Random, marks: float, out_dir: Path | None):
    x1, y1 = rng.randint(-5, 5), rng.randint(-5, 5)
    x2, y2 = rng.randint(-5, 5), rng.randint(-5, 5)
    while x1 == x2:
        x2 = rng.randint(-5, 5)
    m = sp.Rational(y2 - y1, x2 - x1)
    b = sp.simplify(y1 - m * x1)
    text = (f"Find the equation of the straight line passing through "
            f"({x1}, {y1}) and ({x2}, {y2}).")
    answer = _line_text(m, b)
    steps = [
        f"Slope m = (y₂ - y₁)/(x₂ - x₁) = ({y2} - {y1})/({x2} - {x1}) = {fmt_num(m)}.",
        f"Use y - y₁ = m(x - x₁): y - {y1} = {fmt_num(m)}(x - {x1}).",
        f"Expand and simplify: {answer}.",
    ]
    image = None
    if out_dir is not None:
        image = line_plot([(x1, y1), (x2, y2)],
                          out_dir / "line_through_points.png",
                          slope=float(m), intercept=float(b))
    return make_part(label="", text=text, marks=marks, topic="lines",
                     subtopic="through_points", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq(y, m*x + b)),
                     solution_latex=[
                         rf"m = {sp.latex(m)}",
                         sp.latex(sp.Eq(y - y1, m*(x - x1))),
                         sp.latex(sp.Eq(y, m*x + b)),
                     ],
                     notes=["M1 slope", "M1 point-slope", "A1 equation"],
                     diagram_spec=diagram(image, "Figure: line through the two points."))


def parallel_perpendicular(rng: random.Random, marks: float, out_dir: Path | None):
    A, B, C = nz(rng, -5, 5), nz(rng, -5, 5), nz(rng, -8, 8)
    px, py = rng.randint(-4, 4), rng.randint(-4, 4)
    relation = pick(rng, ("parallel", "perpendicular"))
    m = sp.Rational(-A, B)
    m_new = m if relation == "parallel" else sp.simplify(-1 / m)
    b_new = sp.simplify(py - m_new * px)
    text = (f"Find the equation of the line passing through ({px}, {py}) "
            f"and {relation} to the line {poly_text(A*x + B*y + C)} = 0.")
    answer = _line_text(m_new, b_new)
    steps = [
        f"Rewrite {poly_text(A*x + B*y + C)} = 0 in slope-intercept form: "
        f"y = {fmt_num(m)}x + {fmt_num(sp.Rational(-C, B))}.",
        f"The required slope is {fmt_num(m_new)} "
        f"({'same slope' if relation == 'parallel' else 'negative reciprocal'}).",
        f"Use y - y₁ = m(x - x₁): y - {py} = {fmt_num(m_new)}(x - {px}).",
        f"Simplify: {answer}.",
    ]
    image = None
    if out_dir is not None:
        image = line_plot([(px, py)], out_dir / "line_parallel_perp.png",
                          slope=float(m_new), intercept=float(b_new))
    return make_part(label="", text=text, marks=marks, topic="lines",
                     subtopic="parallel_perpendicular", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq(y, m_new*x + b_new)),
                     solution_latex=[
                         rf"{sp.latex(A*x+B*y+C)} = 0",
                         sp.latex(sp.Eq(y, m*x + sp.Rational(-C, B))),
                         rf"m_{{\mathrm{{new}}}} = {sp.latex(m_new)}",
                         sp.latex(sp.Eq(y, m_new*x + b_new)),
                     ],
                     notes=["M1 slope of given line", "M1 required slope",
                            "A1 equation"],
                     diagram_spec=diagram(image, "Figure: required line."))


def intercepts(rng: random.Random, marks: float, out_dir: Path | None):
    a = nz(rng, -8, 8)
    b = nz(rng, -8, 8)
    # x/a + y/b = 1 -> y = -(b/a)x + b
    m = sp.Rational(-b, a)
    text = (f"Find the equation of the line with x-intercept {a} and "
            f"y-intercept {b}.")
    answer = _line_text(m, b)
    steps = [
        f"Use the intercept form x/{a} + y/{b} = 1.",
        f"Multiply by {a * b}: {b}x + {a}y = {a * b}.",
        f"Solve for y: {answer}.",
    ]
    image = None
    if out_dir is not None:
        image = line_plot([(a, 0), (0, b)], out_dir / "line_intercepts.png")
    return make_part(label="", text=text, marks=marks, topic="lines",
                     subtopic="intercepts", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq(y, m*x + b)),
                     solution_latex=[
                         sp.latex(sp.Eq(x/a + y/b, 1)),
                         sp.latex(sp.Eq(b*x + a*y, a*b)),
                         sp.latex(sp.Eq(y, m*x + b)),
                     ],
                     notes=["M1 intercept form", "A1 equation"],
                     diagram_spec=diagram(image, "Figure: line and intercepts."))


GENERATORS = [
    Generator("lines.through_points", "lines", "through_points", 4, through_points),
    Generator("lines.parallel_perpendicular", "lines", "parallel_perpendicular", 5, parallel_perpendicular),
    Generator("lines.intercepts", "lines", "intercepts", 4, intercepts),
]
