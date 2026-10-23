"""Priority 3 generators: trigonometry."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, pick, poly_text, trig_text,
)
from src.render.plots import trig_plot

x = sp.Symbol("x")


def _angles_for_sin(value) -> list[int]:
    table = {
        sp.Integer(1): [90], sp.Integer(-1): [270], sp.Integer(0): [0, 180],
        sp.Rational(1, 2): [30, 150], sp.Rational(-1, 2): [210, 330],
    }
    return table.get(sp.nsimplify(value), [])


def _angles_for_cos(value) -> list[int]:
    table = {
        sp.Integer(1): [0], sp.Integer(-1): [180], sp.Integer(0): [90, 270],
        sp.Rational(1, 2): [60, 300], sp.Rational(-1, 2): [120, 240],
    }
    return table.get(sp.nsimplify(value), [])


def _angles_for_tan(value) -> list[int]:
    table = {
        sp.Integer(0): [0, 180], sp.Integer(1): [45, 225],
        sp.Integer(-1): [135, 315],
        sp.sqrt(3): [60, 240], -sp.sqrt(3): [120, 300],
    }
    return table.get(sp.nsimplify(value), [])


def equation(rng: random.Random, marks: float, out_dir: Path | None):
    fn_name = pick(rng, ("sin", "cos"))
    roots_pool = [sp.Integer(1), sp.Integer(-1), sp.Integer(0),
                  sp.Rational(1, 2), sp.Rational(-1, 2)]
    r1, r2 = rng.sample(roots_pool, 2)
    a = pick(rng, (1, 2, -1, -2))
    trig = sp.sin(x) if fn_name == "sin" else sp.cos(x)
    expr = sp.expand(a * (trig - r1) * (trig - r2))
    angles = sorted(set((_angles_for_sin(r1) + _angles_for_sin(r2))
                        if fn_name == "sin" else
                        (_angles_for_cos(r1) + _angles_for_cos(r2))))
    text = (f"Solve the trigonometric equation {trig_text(expr)} = 0 for "
            "0° ≤ x < 360°.")
    answer = "x = " + ", ".join(f"{v}°" for v in angles) + "."
    steps = [
        f"Factor the equation: {trig_text(expr)} = 0.",
        f"Set each factor to zero: {fn_name} x = {fmt_num(r1)} or "
        f"{fn_name} x = {fmt_num(r2)}.",
        f"Solve in the required interval: " + ", ".join(f"x = {v}°" for v in angles) + ".",
    ]
    angle_tex = ", ".join(rf"{v}^\circ" for v in angles)
    return make_part(label="", text=text, marks=marks, topic="trigonometry",
                     subtopic="equation", answer=answer, steps=steps,
                     answer_latex=rf"x = {angle_tex}",
                     solution_latex=[
                         sp.latex(sp.Eq(expr, 0)),
                         sp.latex(sp.Eq((trig-r1)*(trig-r2), 0)),
                         rf"\{fn_name} x = {sp.latex(r1)}\;\mathrm{{or}}\; \{fn_name} x = {sp.latex(r2)}",
                         rf"x = {angle_tex}",
                     ],
                     notes=["M1 factor", "A1 reference angles", "A1 all solutions"])


def identity(rng: random.Random, marks: float, out_dir: Path | None):
    template = pick(rng, (1, 2, 3, 4))
    if template == 1:
        lhs = (1 + sp.cos(x)) / sp.sin(x) + sp.sin(x) / (1 + sp.cos(x))
        rhs = 2 / sp.sin(x)
        text = ("Prove the identity (1 + cos x)/sin x + sin x/(1 + cos x) "
                "= 2 csc x.")
        steps = [
            "Start with the left-hand side.",
            "Common denominator: [(1 + cos x)² + sin² x]/[sin x(1 + cos x)].",
            "Use sin² x + cos² x = 1: numerator = 1 + 2cos x + cos² x + sin² x "
            "= 2 + 2cos x.",
            "Factor: 2(1 + cos x)/[sin x(1 + cos x)] = 2/sin x = 2 csc x.",
        ]
        identity_lines = [
            sp.latex(sp.Eq(lhs, rhs, evaluate=False)),
            sp.latex(sp.Eq(lhs, ((1+sp.cos(x))**2 + sp.sin(x)**2)
                            / (sp.sin(x)*(1+sp.cos(x))), evaluate=False)),
            sp.latex(sp.Eq(((1+sp.cos(x))**2 + sp.sin(x)**2)
                            / (sp.sin(x)*(1+sp.cos(x))), 2/sp.sin(x),
                            evaluate=False)),
            sp.latex(sp.Eq(2/sp.sin(x), 2*sp.csc(x), evaluate=False)),
        ]
    elif template == 2:
        lhs = sp.tan(x) + sp.cos(x) / (1 + sp.sin(x))
        rhs = sp.sec(x)
        text = "Prove the identity tan x + cos x/(1 + sin x) = sec x."
        steps = [
            "Write tan x = sin x/cos x.",
            "Common denominator: [sin x(1 + sin x) + cos² x]/"
            "[cos x(1 + sin x)].",
            "Use sin² x + cos² x = 1: numerator = sin x + 1.",
            "Cancel (1 + sin x): 1/cos x = sec x.",
        ]
        identity_lines = [
            sp.latex(sp.Eq(lhs, rhs, evaluate=False)),
            sp.latex(sp.Eq(sp.tan(x), sp.sin(x)/sp.cos(x), evaluate=False)),
            sp.latex(sp.Eq(lhs, (sp.sin(x)*(1+sp.sin(x)) + sp.cos(x)**2)
                            / (sp.cos(x)*(1+sp.sin(x))), evaluate=False)),
            sp.latex(sp.Eq(lhs, 1/sp.cos(x), evaluate=False)),
            sp.latex(sp.Eq(1/sp.cos(x), sp.sec(x), evaluate=False)),
        ]
    elif template == 3:
        lhs = (1 - sp.cos(x) ** 2) / (sp.sin(x) * sp.cos(x))
        rhs = sp.tan(x)
        text = "Prove the identity (1 - cos² x)/(sin x cos x) = tan x."
        steps = [
            "Use 1 - cos² x = sin² x.",
            "The left-hand side becomes sin² x/(sin x cos x).",
            "Cancel one factor sin x: sin x/cos x = tan x.",
        ]
        identity_lines = [
            sp.latex(sp.Eq(lhs, rhs, evaluate=False)),
            sp.latex(sp.Eq(1 - sp.cos(x)**2, sp.sin(x)**2, evaluate=False)),
            sp.latex(sp.Eq(lhs, sp.sin(x)**2/(sp.sin(x)*sp.cos(x)),
                            evaluate=False)),
            sp.latex(sp.Eq(lhs, sp.tan(x), evaluate=False)),
        ]
    else:
        lhs = sp.sin(x) ** 2 / (1 - sp.cos(x))
        rhs = 1 + sp.cos(x)
        text = "Prove the identity sin² x/(1 - cos x) = 1 + cos x."
        steps = [
            "Use sin² x = 1 - cos² x.",
            "Factor the numerator: (1 - cos x)(1 + cos x).",
            "Cancel (1 - cos x) to obtain 1 + cos x.",
        ]
        identity_lines = [
            sp.latex(sp.Eq(lhs, rhs, evaluate=False)),
            sp.latex(sp.Eq(sp.sin(x)**2, 1 - sp.cos(x)**2, evaluate=False)),
            sp.latex(sp.Eq(lhs, (1-sp.cos(x))*(1+sp.cos(x))/(1-sp.cos(x)),
                            evaluate=False)),
            sp.latex(sp.Eq(lhs, 1 + sp.cos(x), evaluate=False)),
        ]
    # Safety check: generated identity must actually be true.
    if sp.simplify(sp.trigsimp(lhs - rhs)) != 0:
        raise RuntimeError("generated trigonometric identity is not true")
    answer = "The identity is proven by the steps shown."
    return make_part(label="", text=text, marks=marks, topic="trigonometry",
                     subtopic="identity", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq(lhs, rhs, evaluate=False)),
                     solution_latex=identity_lines,
                     notes=["M1 use identity", "M1 simplify", "A1 conclusion"])


def exact_value(rng: random.Random, marks: float, out_dir: Path | None):
    data = pick(rng, ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)))
    sin_abs, cos_abs, hyp = data
    quadrant = pick(rng, (1, 2, 3, 4))
    sin_sign = 1 if quadrant in (1, 2) else -1
    cos_sign = 1 if quadrant in (1, 4) else -1
    sin_a = sp.Rational(sin_sign * sin_abs, hyp)
    cos_a = sp.Rational(cos_sign * cos_abs, hyp)
    tan_a = sp.simplify(sin_a / cos_a)
    text = (f"Given sin A = {fmt_num(sin_a)} and A is in quadrant {quadrant}, "
            "find the exact values of cos A, tan A and sec A.")
    answer = (f"cos A = {fmt_num(cos_a)}, tan A = {fmt_num(tan_a)}, "
              f"sec A = {fmt_num(1/cos_a)}.")
    steps = [
        f"Use sin² A + cos² A = 1: cos² A = 1 - ({fmt_num(sin_a)})² = "
        f"{fmt_num(cos_a**2)}.",
        f"In quadrant {quadrant}, cos A is {'positive' if cos_sign > 0 else 'negative'}, "
        f"so cos A = {fmt_num(cos_a)}.",
        f"tan A = sin A/cos A = {fmt_num(tan_a)}.",
        f"sec A = 1/cos A = {fmt_num(1/cos_a)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="trigonometry",
                     subtopic="exact_value", answer=answer, steps=steps,
                     answer_latex=(
                         rf"\cos A = {sp.latex(cos_a)},\quad \tan A = {sp.latex(tan_a)},"
                         rf"\quad \sec A = {sp.latex(1/cos_a)}"),
                     solution_latex=[
                         rf"\sin^2 A + \cos^2 A = 1",
                         rf"\cos A = {sp.latex(cos_a)}",
                         rf"\tan A = {sp.latex(tan_a)}",
                         rf"\sec A = {sp.latex(1/cos_a)}",
                     ],
                     notes=["M1 Pythagorean identity", "A1 sign", "A1 ratios"])


def graph(rng: random.Random, marks: float, out_dir: Path | None):
    A = pick(rng, (-3, -2, 2, 3))
    B = pick(rng, (1, 2, 3))
    C = pick(rng, (-60, -45, -30, 0, 30, 45, 60))
    D = pick(rng, (-2, -1, 0, 1, 2))
    period = sp.Rational(360, B)
    phase = sp.Rational(-C, B)
    expr = A * sp.sin(sp.pi * (B * x + C) / 180) + D
    inner = f"{B}x" + (f" + {C}" if C >= 0 else f" - {abs(C)}")
    text = (f"For y = {A} sin({inner}) + {D}, state the amplitude, period "
            "and phase shift, then sketch the graph for -180° ≤ x ≤ 180°.")
    answer = (f"Amplitude {abs(A)}; period {fmt_num(period)}°; "
              f"phase shift {fmt_num(phase)}°.")
    steps = [
        f"Amplitude = |{A}| = {abs(A)}.",
        f"Period = 360°/|{B}| = {fmt_num(period)}°.",
        f"Phase shift = -C/B = -({C})/{B} = {fmt_num(phase)}°.",
        "Sketch one full cycle using the amplitude, period and phase shift.",
    ]
    image = None
    if out_dir is not None:
        image = trig_plot(sp.sstr(expr), -180, 180,
                          out_dir / "trig_graph.png")
    return make_part(label="", text=text, marks=marks, topic="trigonometry",
                     subtopic="graph", answer=answer, steps=steps,
                     answer_latex=(
                         rf"\mathrm{{amplitude}}={abs(A)},\quad "
                         rf"\mathrm{{period}}={sp.latex(period)}^\circ,\quad "
                         rf"\mathrm{{phase}}={sp.latex(phase)}^\circ"),
                     solution_latex=[
                         rf"\mathrm{{amplitude}} = {abs(A)}",
                         rf"\mathrm{{period}} = \frac{{360^\circ}}{{{B}}} = {sp.latex(period)}^\circ",
                         rf"\mathrm{{phase\ shift}} = -\frac{{{C}}}{{{B}}} = {sp.latex(phase)}^\circ",
                     ],
                     notes=["A1 amplitude", "A1 period", "A1 phase shift", "B1 graph"],
                     diagram_spec=diagram(image, "Figure: trigonometric graph."))


def compound_double_angle(rng: random.Random, marks: float, out_dir: Path | None):
    sin_abs, cos_abs, hyp = pick(rng, ((3, 4, 5), (5, 12, 13), (8, 15, 17)))
    # A is in quadrant II, B in quadrant IV
    sin_a = sp.Rational(sin_abs, hyp)
    cos_a = sp.Rational(-cos_abs, hyp)
    cos_b = sp.Rational(cos_abs, hyp)
    sin_b = sp.Rational(-sin_abs, hyp)
    sin2a = sp.simplify(2 * sin_a * cos_a)
    cos_ab = sp.simplify(cos_a * cos_b - sin_a * sin_b)
    text = (f"Given sin A = {fmt_num(sin_a)} where A is in quadrant II and "
            f"cos B = {fmt_num(cos_b)} where B is in quadrant IV, find "
            "sin 2A and cos(A + B).")
    answer = f"sin 2A = {fmt_num(sin2a)}; cos(A + B) = {fmt_num(cos_ab)}."
    steps = [
        f"Find cos A using sin²A + cos²A = 1 and quadrant II: cos A = {fmt_num(cos_a)}.",
        f"Find sin B using sin²B + cos²B = 1 and quadrant IV: sin B = {fmt_num(sin_b)}.",
        f"sin 2A = 2 sin A cos A = 2({fmt_num(sin_a)})({fmt_num(cos_a)}) = "
        f"{fmt_num(sin2a)}.",
        f"cos(A + B) = cos A cos B - sin A sin B = {fmt_num(cos_ab)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="trigonometry",
                     subtopic="compound_double_angle", answer=answer, steps=steps,
                     answer_latex=rf"\sin 2A = {sp.latex(sin2a)},\quad \cos(A+B) = {sp.latex(cos_ab)}",
                     solution_latex=[
                         rf"\cos A = {sp.latex(cos_a)},\quad \sin B = {sp.latex(sin_b)}",
                         rf"\sin 2A = 2\sin A\cos A = {sp.latex(sin2a)}",
                         rf"\cos(A+B) = \cos A\cos B - \sin A\sin B = {sp.latex(cos_ab)}",
                     ],
                     notes=["M1 cos A", "M1 sin B", "A1 sin 2A", "A1 cos(A+B)"])


GENERATORS = [
    Generator("trigonometry.equation", "trigonometry", "equation", 5, equation),
    Generator("trigonometry.identity", "trigonometry", "identity", 5, identity),
    Generator("trigonometry.exact_value", "trigonometry", "exact_value", 4, exact_value),
    Generator("trigonometry.graph", "trigonometry", "graph", 5, graph),
    Generator("trigonometry.compound_double_angle", "trigonometry", "compound_double_angle", 5, compound_double_angle),
]
