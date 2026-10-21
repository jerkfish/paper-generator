"""Priority 3 generators: triangle geometry."""
from __future__ import annotations

import math
import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, pick, poly_text,
)
from src.render.plots import triangle_plot


def _angle_deg(value) -> str:
    return f"{float(value):.2f}°"


def solve_triangle(rng: random.Random, marks: float, out_dir: Path | None):
    a, b, c = pick(rng, ((3, 4, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)))
    scale = rng.randint(1, 3)
    a, b, c = a * scale, b * scale, c * scale
    # right triangle with legs a and b, hypotenuse c
    angle_a = math.degrees(math.atan2(a, b))
    angle_b = 90.0 - angle_a
    text = (f"Solve the triangle with sides a = {a} cm, b = {b} cm and "
            f"c = {c} cm. Find all three angles.")
    answer = (f"A ≈ {angle_a:.2f}°, B ≈ {angle_b:.2f}°, C = 90°.")
    steps = [
        f"Check the sides satisfy the Pythagorean theorem: {a}² + {b}² = {c}².",
        "Therefore the angle opposite the longest side (C) is 90°.",
        f"Use tan A = opposite/adjacent = {a}/{b}: A ≈ {angle_a:.2f}°.",
        f"The remaining angle is B = 90° - A ≈ {angle_b:.2f}°.",
    ]
    image = None
    if out_dir is not None:
        image = triangle_plot([(0, 0), (a, 0), (0, b)],
                              out_dir / "triangle_solve.png",
                              labels=["C", "B", "A"],
                              side_labels=["a", "c", "b"])
    return make_part(label="", text=text, marks=marks, topic="triangle_geometry",
                     subtopic="solve_triangle", answer=answer, steps=steps,
                     answer_latex=rf"A = {angle_a:.2f}^\circ,\quad B = {angle_b:.2f}^\circ,\quad C = 90^\circ",
                     solution_latex=[
                         rf"{a}^2 + {b}^2 = {c}^2",
                         rf"\tan A = \frac{{{a}}}{{{b}}}\Rightarrow A = {angle_a:.2f}^\circ",
                         rf"B = 90^\circ - A = {angle_b:.2f}^\circ",
                     ],
                     notes=["M1 Pythagoras", "A1 right angle", "A1 other angles"],
                     diagram_spec=diagram(image, "Figure: right triangle."))


def sine_rule(rng: random.Random, marks: float, out_dir: Path | None):
    A, B = pick(rng, ((30, 45), (45, 60), (30, 60)))
    a = rng.randint(6, 15)
    b = sp.simplify(a * sp.sin(sp.pi * B / 180) / sp.sin(sp.pi * A / 180))
    text = (f"In triangle ABC, A = {A}°, B = {B}° and a = {a} cm. "
            "Use the sine rule to find b.")
    answer = f"b = {poly_text(b)} cm ≈ {float(b):.2f} cm."
    steps = [
        "Write the sine rule: a/sin A = b/sin B.",
        f"Substitute: {a}/sin {A}° = b/sin {B}°.",
        f"Solve for b: b = {a} sin {B}°/sin {A}° = {poly_text(b)} cm.",
        f"Numerically, b ≈ {float(b):.2f} cm.",
    ]
    image = None
    if out_dir is not None:
        image = triangle_plot([(0, 0), (a + 3, 0), (2, 4)],
                              out_dir / "triangle_sine.png",
                              labels=["C", "B", "A"],
                              side_labels=["c", "b", "a"])
    return make_part(label="", text=text, marks=marks, topic="triangle_geometry",
                     subtopic="sine_rule", answer=answer, steps=steps,
                     answer_latex=rf"b = {sp.latex(b)}",
                     solution_latex=[
                         rf"\frac{{a}}{{\sin A}} = \frac{{b}}{{\sin B}}",
                         rf"\frac{{{a}}}{{\sin {A}^\circ}} = \frac{{b}}{{\sin {B}^\circ}}",
                         rf"b = \frac{{{a}\sin {B}^\circ}}{{\sin {A}^\circ}} = {sp.latex(b)}",
                     ],
                     notes=["M1 sine rule", "M1 substitution", "A1 exact value"],
                     diagram_spec=diagram(image, "Figure: triangle ABC."))


def cosine_rule(rng: random.Random, marks: float, out_dir: Path | None):
    b, c = rng.randint(5, 12), rng.randint(5, 12)
    A = pick(rng, (60, 90, 120))
    a2 = sp.simplify(b*b + c*c - 2*b*c*sp.cos(sp.pi*A/180))
    a = sp.sqrt(a2)
    text = (f"In triangle ABC, b = {b} cm, c = {c} cm and A = {A}°. "
            "Use the cosine rule to find a.")
    answer = f"a = {poly_text(a)} cm ≈ {float(a):.2f} cm."
    steps = [
        "Write the cosine rule: a² = b² + c² - 2bc cos A.",
        f"Substitute: a² = {b}² + {c}² - 2({b})({c}) cos {A}°.",
        f"Simplify: a² = {fmt_num(a2)}.",
        f"Take the positive square root: a = {poly_text(a)} cm ≈ {float(a):.2f} cm.",
    ]
    image = None
    if out_dir is not None:
        image = triangle_plot([(0, 0), (c, 0), (b / 2, b * math.sqrt(3) / 2)],
                              out_dir / "triangle_cosine.png",
                              labels=["A", "B", "C"],
                              side_labels=["c", "a", "b"])
    return make_part(label="", text=text, marks=marks, topic="triangle_geometry",
                     subtopic="cosine_rule", answer=answer, steps=steps,
                     answer_latex=rf"a = {sp.latex(a)}",
                     solution_latex=[
                         rf"a^2 = b^2 + c^2 - 2bc\cos A",
                         rf"a^2 = {b}^2 + {c}^2 - 2({b})({c})\cos {A}^\circ = {sp.latex(a2)}",
                         rf"a = {sp.latex(a)}",
                     ],
                     notes=["M1 cosine rule", "A1 substitution", "A1 exact value"],
                     diagram_spec=diagram(image, "Figure: triangle ABC."))


def area(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = rng.randint(5, 15), rng.randint(5, 15)
    C = pick(rng, (30, 45, 60, 90, 120))
    area_val = sp.simplify(sp.Rational(1, 2) * a * b * sp.sin(sp.pi * C / 180))
    text = (f"Find the area of triangle ABC with a = {a} cm, b = {b} cm and "
            f"included angle C = {C}°.")
    answer = f"Area = {poly_text(area_val)} cm² ≈ {float(area_val):.2f} cm²."
    steps = [
        "Use Area = ½ab sin C.",
        f"Substitute: Area = ½({a})({b}) sin {C}°.",
        f"Evaluate: Area = {poly_text(area_val)} cm² ≈ {float(area_val):.2f} cm².",
    ]
    return make_part(label="", text=text, marks=marks, topic="triangle_geometry",
                     subtopic="area", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{Area}} = {sp.latex(area_val)}",
                     solution_latex=[
                         r"\mathrm{Area} = \frac{1}{2}ab\sin C",
                         rf"\mathrm{{Area}} = \frac{{1}}{{2}}({a})({b})\sin {C}^\circ = {sp.latex(area_val)}",
                     ],
                     notes=["M1 formula", "M1 substitution", "A1 area"])


def combined_figures(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = rng.randint(8, 15), rng.randint(8, 15)
    r = rng.randint(3, min(a, b) - 1)
    angle = pick(rng, (30, 45, 60, 90))
    tri_area = sp.Rational(1, 2) * a * b
    sector = sp.simplify(sp.Rational(1, 2) * r * r * sp.Rational(angle, 180) * sp.pi)
    shaded = sp.simplify(tri_area - sector)
    text = (f"A right triangle has legs {a} cm and {b} cm. A sector of radius "
            f"{r} cm and angle {angle}° is cut from it. Find the area of the "
            "remaining shaded region.")
    answer = f"Shaded area = {poly_text(shaded)} cm² ≈ {float(shaded):.2f} cm²."
    steps = [
        f"Area of the right triangle = ½({a})({b}) = {fmt_num(tri_area)} cm².",
        f"Area of the sector = ½({r})²({angle}π/180) = {poly_text(sector)} cm².",
        f"Subtract: {fmt_num(tri_area)} - {poly_text(sector)} = "
        f"{poly_text(shaded)} cm² ≈ {float(shaded):.2f} cm².",
    ]
    return make_part(label="", text=text, marks=marks, topic="triangle_geometry",
                     subtopic="combined_figures", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{shaded}} = {sp.latex(shaded)}",
                     solution_latex=[
                         rf"A_{{\triangle}} = \frac{{1}}{{2}}({a})({b}) = {sp.latex(tri_area)}",
                         rf"A_{{\mathrm{{sector}}}} = \frac{{1}}{{2}}({r})^2\left(\frac{{{angle}\pi}}{{180}}\right) = {sp.latex(sector)}",
                         rf"A_{{\mathrm{{shaded}}}} = {sp.latex(tri_area)} - {sp.latex(sector)} = {sp.latex(shaded)}",
                     ],
                     notes=["M1 triangle area", "M1 sector area", "A1 difference"])


GENERATORS = [
    Generator("triangle_geometry.solve_triangle", "triangle_geometry", "solve_triangle", 5, solve_triangle),
    Generator("triangle_geometry.sine_rule", "triangle_geometry", "sine_rule", 4, sine_rule),
    Generator("triangle_geometry.cosine_rule", "triangle_geometry", "cosine_rule", 4, cosine_rule),
    Generator("triangle_geometry.area", "triangle_geometry", "area", 4, area),
    Generator("triangle_geometry.combined_figures", "triangle_geometry", "combined_figures", 5, combined_figures),
]
