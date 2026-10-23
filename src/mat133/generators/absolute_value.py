"""Priority 1 generators: absolute value."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, interval, make_part, nz, pick, poly_text, union,
)
from src.render.mathfig import function_plot, number_line

x = sp.Symbol("x")


def equation(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -6, 6)
    c = rng.randint(2, 9)
    s1 = sp.Rational(c - b, a)
    s2 = sp.Rational(-c - b, a)
    text = f"Solve the equation |{poly_text(a*x + b)}| = {c}."
    answer = f"x = {fmt_num(s1)} or x = {fmt_num(s2)}."
    steps = [
        f"Set the inside equal to {c}: {poly_text(a*x + b)} = {c}.",
        f"Solve: x = {fmt_num(s1)}.",
        f"Set the inside equal to -{c}: {poly_text(a*x + b)} = -{c}.",
        f"Solve: x = {fmt_num(s2)}.",
        "Check both values in the original equation.",
    ]
    return make_part(label="", text=text, marks=marks, topic="absolute_value",
                     subtopic="equation", answer=answer, steps=steps,
                     answer_latex=rf"x = {sp.latex(s1)} \quad \mathrm{{or}} \quad x = {sp.latex(s2)}",
                     solution_latex=[
                         sp.latex(sp.Eq(sp.Abs(a*x+b), c)),
                         sp.latex(sp.Eq(a*x+b, c)),
                         sp.latex(sp.Eq(a*x+b, -c)),
                     ],
                     notes=["M1 two cases", "A1 first solution", "A1 second solution"])


def inequality(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -6, 6)
    c = rng.randint(2, 9)
    op = pick(rng, ("<=", "<", ">=", ">"))
    op_text = {"<=": "≤", "<": "<", ">=": "≥", ">": ">"}[op]
    op_latex = {"<=": r"\leq", "<": "<", ">=": r"\geq", ">": ">"}[op]
    left = sp.Rational(-c - b, a)
    right = sp.Rational(c - b, a)
    lo, hi = sorted((left, right))
    closed = op in ("<=", ">=")
    if op in ("<=", "<"):
        sol = interval(lo, hi, closed, closed)
        desc = "The distance from x to the centre is at most the radius."
    else:
        sol = union(interval(-sp.oo, lo, False, closed),
                    interval(hi, sp.oo, closed, False))
        desc = "The distance from x to the centre is at least the radius."
    text = (f"Solve the inequality |{poly_text(a*x + b)}| {op_text} {c}. "
            "Express the answer in interval notation and on a number line.")
    answer = sol
    if op in ("<=", "<"):
        rewrite = (f"-{c} {op_text} {poly_text(a*x + b)} {op_text} {c}.")
    else:
        other_text = "<" if op == ">" else "≤"
        rewrite = (f"{poly_text(a*x + b)} {op_text} {c} or "
                   f"{poly_text(a*x + b)} {other_text} -{c}.")
    steps = [
        f"Rewrite the absolute value: {rewrite}",
        "Solve each resulting inequality separately.",
        f"Combine the result: {sol}.",
        desc,
    ]
    image = None
    if out_dir is not None:
        if op in ("<=", "<"):
            image = number_line([(float(lo), float(hi), closed, closed)],
                                out_path=out_dir / "abs_inequality.png",
                                x_min=float(lo) - 2, x_max=float(hi) + 2)
        else:
            image = number_line([(-10, float(lo), False, closed),
                                 (float(hi), 10, closed, False)],
                                out_path=out_dir / "abs_inequality.png",
                                x_min=-10, x_max=10)
    expr = sp.Abs(a*x + b) - c
    rel = {"<=": sp.Le(expr, 0), "<": sp.Lt(expr, 0),
           ">=": sp.Ge(expr, 0), ">": sp.Gt(expr, 0)}[op]
    sol_set = sp.solve_univariate_inequality(rel, x, relational=False)
    return make_part(label="", text=text, marks=marks, topic="absolute_value",
                     subtopic="inequality", answer=answer, steps=steps,
                     answer_latex=sp.latex(sol_set),
                     solution_latex=[
                         sp.latex(rel),
                         (rf"-{c} {op_latex} {sp.latex(a*x+b)} {op_latex} {c}"
                          if op in ("<=", "<") else
                          rf"{sp.latex(a*x+b)} {op_latex} {c}\;\mathrm{{or}}\; "
                          rf"{sp.latex(a*x+b)} \leq -{c}"),
                         sp.latex(sol_set),
                     ],
                     notes=["M1 compound inequality", "A1 endpoints",
                            "A1 interval"],
                     diagram_spec=diagram(image, "Figure: solution on a number line."))


def graph(rng: random.Random, marks: float, out_dir: Path | None):
    a = pick(rng, (-3, -2, 2, 3))
    h, k = nz(rng, -4, 4), nz(rng, -5, 5)
    expr = a * sp.Abs(x - h) + k
    y_int = a * abs(-h) + k
    # x-intercepts: a|x-h| + k = 0 -> |x-h| = -k/a
    ratio = sp.Rational(-k, a)
    intercepts = []
    if ratio >= 0:
        intercepts = [sp.Rational(h) - ratio, sp.Rational(h) + ratio]
    intercept_text = (", ".join(fmt_num(v) for v in intercepts)
                      if intercepts else "none")
    inside = ("|x|" if h == 0 else
              f"|x - {h}|" if h > 0 else f"|x + {abs(h)}|")
    constant = ("" if k == 0 else
                f" + {k}" if k > 0 else f" - {abs(k)}")
    text = (f"Sketch y = {a}{inside}{constant}. State the vertex, the "
            "y-intercept and any x-intercepts.")
    answer = (f"Vertex ({h}, {k}); y-intercept (0, {fmt_num(y_int)}); "
              f"x-intercept(s): {intercept_text}.")
    steps = [
        f"The graph is a V-shape with vertex ({h}, {k}).",
        f"Set x=0: y = {a}({abs(h)}){constant} = {fmt_num(y_int)}.",
        f"Set y=0: {inside} = {fmt_num(ratio)}." if ratio >= 0
        else "Set y=0: the equation has no real solution.",
        f"x-intercept(s): {intercept_text}.",
    ]
    image = None
    if out_dir is not None:
        image = function_plot(sp.sstr(expr), h - 5, h + 5,
                              out_dir / "abs_graph.png")
    return make_part(label="", text=text, marks=marks, topic="absolute_value",
                     subtopic="graph", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{vertex}}\;({h},{k});\quad y(0)={sp.latex(y_int)}",
                     solution_latex=[
                         sp.latex(sp.Eq(sp.Symbol("y"), expr)),
                         rf"\mathrm{{vertex}}\;({h},{k})",
                         (sp.latex(sp.Eq(sp.Abs(x-h), ratio)) if ratio >= 0
                          else r"\mathrm{no\ real\ intercepts}"),
                     ],
                     notes=["B1 V-shape", "A1 vertex", "A1 intercepts"],
                     diagram_spec=diagram(image, "Figure: absolute-value graph."))


GENERATORS = [
    Generator("absolute_value.equation", "absolute_value", "equation", 4, equation),
    Generator("absolute_value.inequality", "absolute_value", "inequality", 5, inequality),
    Generator("absolute_value.graph", "absolute_value", "graph", 5, graph),
]
