"""Priority 1 generators: functions."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, interval, make_part, nz, pick, poly_text,
)
from src.render.plots import piecewise_plot
from src.render.mathfig import function_plot

x = sp.Symbol("x")


def domain_range(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -6, 6)
    c, d = nz(rng, -4, 4), nz(rng, -6, 6)
    p, q = pick(rng, (2, 3, 4)), nz(rng, -6, 6)
    f = (a * x + b) / (c * x + d)
    g = sp.sqrt(p * x + q)
    bad = sp.Rational(-d, c)
    lower = sp.Rational(-q, p)
    text = (f"Given f(x) = {poly_text(f)} and g(x) = √({poly_text(p*x + q)}), "
            "state the domain of each function.")
    answer = (f"Domain of f: x ≠ {fmt_num(bad)}. "
              f"Domain of g: x ≥ {fmt_num(lower)}.")
    steps = [
        f"For f(x), the denominator cannot be zero: {c}x + {d} ≠ 0.",
        f"Solve {c}x + {d} = 0, giving x = {fmt_num(bad)}.",
        f"For g(x), the radicand must be non-negative: {poly_text(p*x + q)} ≥ 0.",
        f"Solve {poly_text(p*x + q)} ≥ 0, giving x ≥ {fmt_num(lower)}.",
        f"Therefore domain(f) = {{x : x ≠ {fmt_num(bad)}}} and "
        f"domain(g) = [{fmt_num(lower)}, ∞).",
    ]
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="domain_range", answer=answer, steps=steps,
                     answer_latex=rf"x \neq {sp.latex(bad)}, \quad x \geq {sp.latex(lower)}",
                     solution_latex=[
                         rf"{c}x + {d} \neq 0",
                         rf"x \neq {sp.latex(bad)}",
                         rf"{p}x + {q} \geq 0",
                         rf"x \geq {sp.latex(lower)}",
                     ],
                     notes=["M1 denominator restriction", "A1 domain of f",
                            "M1 radical restriction", "A1 domain of g"])


def composition(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -4, 4), nz(rng, -6, 6)
    c, d, e = nz(rng, -5, 5), nz(rng, -4, 4), nz(rng, -6, 6)
    f = a * x + b
    g = c / (d * x + e)
    comp = sp.simplify(g.subs(x, f))
    denom = sp.denom(sp.together(comp))
    pole = sp.solve(denom, x)
    pole_text = ", ".join(fmt_num(p) for p in pole) if pole else "none"
    text = (f"Given f(x) = {poly_text(f)} and g(x) = {poly_text(g)}, "
            "find (g ∘ f)(x) and state its domain.")
    answer = f"(g ∘ f)(x) = {poly_text(comp)}, x ≠ {pole_text}."
    steps = [
        f"Write (g ∘ f)(x) = g(f(x)).",
        f"Substitute f(x) into g: g({poly_text(f)}) = "
        f"{c}/({poly_text(d*f + e)}).",
        f"Expand the denominator: {c}/({poly_text(sp.expand(d * f + e))}).",
        f"Reduce to (g ∘ f)(x) = {poly_text(comp)}.",
        f"The denominator cannot be zero, so x ≠ {pole_text}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="composition", answer=answer, steps=steps,
                     answer_latex=rf"\left(g \circ f\right)(x) = {sp.latex(comp)}",
                     solution_latex=[
                         r"\left(g \circ f\right)(x) = g\left(f(x)\right)",
                         rf"g\left({sp.latex(f)}\right) = {sp.latex(comp)}",
                         rf"x \neq {', '.join(sp.latex(v) for v in pole)}",
                     ],
                     notes=["M1 substitute", "A1 simplified expression",
                            "B1 domain restriction"])


def inverse(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -6, 6)
    c, d = nz(rng, -4, 4), nz(rng, -6, 6)
    while a * d - b * c == 0:
        a = nz(rng, -5, 5)
    f = (a * x + b) / (c * x + d)
    y = sp.Symbol("y")
    sol = sp.solve(sp.Eq(y, f), x)
    inv = sp.simplify(sol[0].subs(y, x)) if sol else sp.nan
    pole = sp.Rational(a, c) if c else sp.oo
    text = (f"Given f(x) = {poly_text(f)}, x ≠ {fmt_num(sp.Rational(-d, c))}, "
            "find f⁻¹(x) and state its domain.")
    answer = f"f⁻¹(x) = {poly_text(inv)}, x ≠ {fmt_num(pole)}."
    steps = [
        f"Write y = {poly_text(f)}.",
        f"Swap x and y: x = ({a}y + {b})/({c}y + {d}).",
        f"Cross-multiply: x({c}y + {d}) = {a}y + {b}.",
        f"Collect y-terms: y({c}x - {a}) = {b} - {d}x.",
        f"Solve for y: f⁻¹(x) = {poly_text(inv)}.",
        f"The inverse denominator cannot be zero, so x ≠ {fmt_num(pole)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="inverse", answer=answer, steps=steps,
                     answer_latex=rf"f^{{-1}}(x) = {sp.latex(inv)}",
                     solution_latex=[
                         rf"y = {sp.latex(f)}",
                         rf"x\left({c}y + {d}\right) = {a}y + {b}",
                         rf"y\left({c}x - {a}\right) = {b} - {d}x",
                         rf"f^{{-1}}(x) = {sp.latex(inv)}",
                     ],
                     notes=["M1 swap x and y", "M1 solve for y",
                            "A1 inverse", "B1 domain"])


def piecewise(rng: random.Random, marks: float, out_dir: Path | None):
    a, b, c = nz(rng, -4, 4), nz(rng, -4, 4), nz(rng, -5, 5)
    def f(v):
        if v < -1:
            return a * v + b
        if v <= 2:
            return c
        return v * v + a
    text = (f"The piecewise function is defined by\n"
            f"f(x) = {poly_text(a*x + b)}, if x < -1;\n"
            f"f(x) = {c}, if -1 ≤ x ≤ 2;\n"
            f"f(x) = {poly_text(x*x + a)}, if x > 2.\n"
            "Sketch the graph and find f(-2), f(0) and f(3).")
    answer = f"f(-2) = {f(-2)}, f(0) = {f(0)}, f(3) = {f(3)}."
    steps = [
        f"On x < -1, draw the line y = {poly_text(a*x + b)}.",
        f"On -1 ≤ x ≤ 2, draw the horizontal line y = {c}.",
        f"On x > 2, draw the right branch of y = {poly_text(x*x + a)}.",
        f"Evaluate f(-2) using the first rule: {a}(-2) + {b} = {f(-2)}.",
        f"Evaluate f(0) using the second rule: f(0) = {f(0)}.",
        f"Evaluate f(3) using the third rule: 3² + {a} = {f(3)}.",
    ]
    image = None
    if out_dir is not None:
        image = piecewise_plot([
            (lambda v: a * v + b, -5, -1, False, False),
            (lambda v: c, -1, 2, True, True),
            (lambda v: v * v + a, 2, 5, False, False),
        ], out_dir / "functions_piecewise.png", -5, 5)
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="piecewise", answer=answer, steps=steps,
                     answer_latex=rf"f(-2)={f(-2)},\quad f(0)={f(0)},\quad f(3)={f(3)}",
                     solution_latex=[
                         rf"f(x) = {sp.latex(a*x + b)},\quad x < -1",
                         rf"f(x) = {c},\quad -1 \leq x \leq 2",
                         rf"f(x) = {sp.latex(x*x + a)},\quad x > 2",
                         rf"f(-2) = {f(-2)},\quad f(0) = {f(0)},\quad f(3) = {f(3)}",
                     ],
                     notes=["B1 each piece", "A1 values"],
                     diagram_spec=diagram(image, "Figure: piecewise graph."))


def transformations(rng: random.Random, marks: float, out_dir: Path | None):
    a = pick(rng, (-3, -2, -1, 2, 3))
    h, k = nz(rng, -5, 5), nz(rng, -6, 6)
    expr = a * (x - h) ** 2 + k
    y_int = sp.expand(expr).subs(x, 0)
    xpart = ("x²" if h == 0 else
             f"(x - {h})²" if h > 0 else f"(x + {abs(h)})²")
    constant = "" if k == 0 else (" + " + str(k) if k > 0 else " - " + str(abs(k)))
    lead = "" if a == 1 else "-" if a == -1 else str(a)
    text = (f"Apply graph-transformation techniques to sketch "
            f"y = {lead}{xpart}{constant}. State the vertex and the y-intercept.")
    answer = f"Vertex ({h}, {k}); y-intercept (0, {fmt_num(y_int)})."
    steps = [
        "Start with the graph of y = x².",
        f"Shift the graph {abs(h)} units to the {'right' if h > 0 else 'left'}.",
        f"Stretch/compress vertically by a factor {abs(a)}"
        + (" and reflect in the x-axis." if a < 0 else "."),
        f"Shift the graph {abs(k)} units {'up' if k > 0 else 'down'}.",
        f"The vertex is ({h}, {k}).",
        f"Set x = 0: y = {poly_text(expr)} = {fmt_num(y_int)}.",
    ]
    image = None
    if out_dir is not None:
        image = function_plot(sp.sstr(expr), h - 5, h + 5,
                              out_dir / "functions_transformation.png")
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="transformations", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{vertex}}\;({h},{k});\quad y(0)={sp.latex(y_int)}",
                     solution_latex=[
                         rf"y = {sp.latex(expr)}",
                         rf"\mathrm{{vertex}}\;({h},{k})",
                         rf"y(0) = {sp.latex(y_int)}",
                     ],
                     notes=["B1 shape/reflection", "B1 shifts", "A1 vertex",
                            "A1 intercept"],
                     diagram_spec=diagram(image, "Figure: transformed graph."))


def even_odd(rng: random.Random, marks: float, out_dir: Path | None):
    kind = pick(rng, ("even", "odd", "neither"))
    if kind == "even":
        terms = [(nz(rng, -4, 4), 4), (nz(rng, -5, 5), 2), (nz(rng, -6, 6), 0)]
    elif kind == "odd":
        terms = [(nz(rng, -4, 4), 5), (nz(rng, -5, 5), 3), (nz(rng, -6, 6), 1)]
    else:
        terms = [(nz(rng, -4, 4), 4), (nz(rng, -5, 5), 3), (nz(rng, -6, 6), 0)]
    expr = sum(coef * x ** power for coef, power in terms)
    expanded = sp.expand(expr)
    fneg = sp.expand(expanded.subs(x, -x))
    if kind == "even":
        relation = "f(-x) = f(x), so f is even; the graph is symmetric about the y-axis."
    elif kind == "odd":
        relation = "f(-x) = -f(x), so f is odd; the graph is symmetric about the origin."
    else:
        relation = "f(-x) ≠ f(x) and f(-x) ≠ -f(x), so f is neither even nor odd."
    text = (f"Determine algebraically whether f(x) = {poly_text(expanded)} is even, "
            "odd or neither. State the symmetry of its graph.")
    answer = relation
    conclusion = (r"f(-x)=f(x)" if kind == "even" else
                  r"f(-x)=-f(x)" if kind == "odd" else
                  r"f(-x)\neq f(x),\quad f(-x)\neq -f(x)")
    steps = [
        f"Replace x by -x: f(-x) = {poly_text(fneg)}.",
        f"Compare with f(x) = {poly_text(expanded)} and -f(x) = {poly_text(-expanded)}.",
        relation,
    ]
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="even_odd", answer=answer, steps=steps,
                     answer_latex=conclusion,
                     solution_latex=[
                         rf"f(x) = {sp.latex(expanded)}",
                         rf"f(-x) = {sp.latex(fneg)}",
                         rf"-f(x) = {sp.latex(-expanded)}",
                         conclusion,
                     ],
                     notes=["M1 substitute -x", "A1 comparison", "A1 symmetry"])


def function_arithmetic(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -6, 6)
    c, d = nz(rng, -4, 4), nz(rng, -6, 6)
    f, g = a * x + b, c * x + d
    text = (f"Given f(x) = {poly_text(f)} and g(x) = {poly_text(g)}, find "
            "(f + g)(x), (f - g)(x) and (f g)(x). State the domain of each.")
    answer = (f"(f+g)(x) = {poly_text(sp.expand(f + g))}, "
              f"(f-g)(x) = {poly_text(sp.expand(f - g))}, "
              f"(fg)(x) = {poly_text(sp.expand(f * g))}; domain = ℝ.")
    steps = [
        f"(f+g)(x) = ({poly_text(f)}) + ({poly_text(g)}) = "
        f"{poly_text(sp.expand(f + g))}.",
        f"(f-g)(x) = ({poly_text(f)}) - ({poly_text(g)}) = "
        f"{poly_text(sp.expand(f - g))}.",
        f"(fg)(x) = ({poly_text(f)})({poly_text(g)}) = "
        f"{poly_text(sp.expand(f * g))}.",
        "Both functions are polynomials, so all three combinations have domain ℝ.",
    ]
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="function_arithmetic", answer=answer, steps=steps,
                     answer_latex=(
                         rf"(f+g)(x) = {sp.latex(sp.expand(f+g))},\quad "
                         rf"(f-g)(x) = {sp.latex(sp.expand(f-g))},\quad "
                         rf"(fg)(x) = {sp.latex(sp.expand(f*g))}"),
                     solution_latex=[
                         rf"(f+g)(x) = {sp.latex(sp.expand(f+g))}",
                         rf"(f-g)(x) = {sp.latex(sp.expand(f-g))}",
                         rf"(fg)(x) = {sp.latex(sp.expand(f*g))}",
                     ],
                     notes=["M1 each operation", "A1 simplified forms",
                            "B1 domain"])


def graph(rng: random.Random, marks: float, out_dir: Path | None):
    family = pick(rng, ("square", "root", "abs"))
    if family == "square":
        expr = (x - 1) ** 2 - 3
        text = "Sketch y = (x - 1)² - 3 for -2 ≤ x ≤ 4. State the domain and range."
        answer = "Domain [-2, 4]; range [-3, 6]."
        steps = ["Plot the parabola with vertex (1, -3).",
                 "Evaluate endpoints: x=-2 gives 6; x=4 gives 6.",
                 "Read the minimum -3 at x=1 and maximum 6 at the endpoints.",
                 "Domain is the given interval; range is [-3, 6]."]
        fn = lambda v: (v - 1) ** 2 - 3
        lo, hi = -2, 4
        range_text = "[-3, 6]"
    elif family == "root":
        expr = sp.sqrt(x + 2)
        text = "Sketch y = √(x + 2) for -2 ≤ x ≤ 7. State the domain and range."
        answer = "Domain [-2, 7]; range [0, 3]."
        steps = ["The radicand requires x + 2 ≥ 0, so x ≥ -2.",
                 "On the given interval the graph starts at (-2, 0).",
                 "At x=7, y=3.", "Domain [-2, 7]; range [0, 3]."]
        fn = lambda v: (v + 2) ** 0.5
        lo, hi = -2, 7
        range_text = "[0, 3]"
    else:
        expr = sp.Abs(x - 2) + 1
        text = "Sketch y = |x - 2| + 1 for -2 ≤ x ≤ 6. State the domain and range."
        answer = "Domain [-2, 6]; range [1, 5]."
        steps = ["The vertex is (2, 1).",
                 "At x=-2, y=5; at x=6, y=5.",
                 "Domain [-2, 6]; range [1, 5]."]
        fn = lambda v: abs(v - 2) + 1
        lo, hi = -2, 6
        range_text = "[1, 5]"
    image = None
    if out_dir is not None:
        image = function_plot(sp.sstr(expr), lo, hi,
                              out_dir / f"functions_graph_{family}.png")
    return make_part(label="", text=text, marks=marks, topic="functions",
                     subtopic="graph", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{domain}}\; [{lo},{hi}];\quad \mathrm{{range}}\; {range_text}",
                     solution_latex=[
                         rf"y = {sp.latex(expr)}",
                         rf"\mathrm{{domain}}\; [{lo},{hi}]",
                         rf"\mathrm{{range}}\; {range_text}",
                     ],
                     notes=["B1 shape", "B1 key points", "A1 domain", "A1 range"],
                     diagram_spec=diagram(image, "Figure: function graph."))


GENERATORS = [
    Generator("functions.domain_range", "functions", "domain_range", 4, domain_range),
    Generator("functions.composition", "functions", "composition", 5, composition),
    Generator("functions.inverse", "functions", "inverse", 5, inverse),
    Generator("functions.piecewise", "functions", "piecewise", 5, piecewise),
    Generator("functions.transformations", "functions", "transformations", 5, transformations),
    Generator("functions.even_odd", "functions", "even_odd", 4, even_odd),
    Generator("functions.function_arithmetic", "functions", "function_arithmetic", 4, function_arithmetic),
    Generator("functions.graph", "functions", "graph", 4, graph),
]
