"""Priority 2 generators: circles."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, nz, pick, poly_text,
)
from src.render.plots import circle_plot

x, y = sp.symbols("x y")


def _shift(var: str, value) -> str:
    if value == 0:
        return var
    sign = "-" if value > 0 else "+"
    return f"({var} {sign} {abs(value)})"


def _standard(h, k, r) -> str:
    return f"{_shift('x', h)}² + {_shift('y', k)}² = {r * r}"


def _general(h, k, r) -> str:
    return poly_text(x**2 + y**2 - 2*h*x - 2*k*y + h*h + k*k - r*r)


def standard_form(rng: random.Random, marks: float, out_dir: Path | None):
    h, k = nz(rng, -5, 5), nz(rng, -5, 5)
    r = rng.randint(2, 7)
    text = (f"Write the equation of the circle with centre ({h}, {k}) and "
            "radius " f"{r}. Hence write its general equation and sketch the circle.")
    answer = f"Standard form: {_standard(h, k, r)}; general form: {_general(h, k, r)} = 0."
    steps = [
        f"Use (x - h)² + (y - k)² = r².",
        f"Substitute h = {h}, k = {k}, r = {r}: {_standard(h, k, r)}.",
        f"Expand: {poly_text((x-h)**2 + (y-k)**2)} = {r*r}.",
        f"Bring all terms to one side: {_general(h, k, r)} = 0.",
        f"Plot the centre ({h}, {k}) and mark radius {r} in all directions.",
    ]
    image = None
    if out_dir is not None:
        image = circle_plot((h, k), r, out_dir / "circle_standard.png")
    return make_part(label="", text=text, marks=marks, topic="circles",
                     subtopic="standard_form", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq((x-h)**2 + (y-k)**2, r*r)),
                     solution_latex=[
                         sp.latex(sp.Eq((x-h)**2 + (y-k)**2, r*r)),
                         sp.latex(sp.Eq(sp.expand((x-h)**2 + (y-k)**2), r*r)),
                         sp.latex(sp.Eq(sp.expand((x-h)**2 + (y-k)**2 - r*r), 0)),
                     ],
                     notes=["M1 standard form", "A1 equation", "B1 graph"],
                     diagram_spec=diagram(image, "Figure: circle."))


def general_to_standard(rng: random.Random, marks: float, out_dir: Path | None):
    h, k = nz(rng, -5, 5), nz(rng, -5, 5)
    r = rng.randint(2, 7)
    text = (f"Write {_general(h, k, r)} = 0 in standard form. Hence state "
            "the centre and radius and sketch the circle.")
    answer = f"{_standard(h, k, r)}; centre ({h}, {k}), radius {r}."
    steps = [
        f"Group x-terms and y-terms: (x² - {2*h}x) + (y² - {2*k}y) = {-h*h-k*k+r*r}.",
        f"Complete the square: (x - {h})² - {h*h} + (y - {k})² - {k*k} = "
        f"{-h*h-k*k+r*r}.",
        f"Simplify: {_standard(h, k, r)}.",
        f"Read off centre ({h}, {k}) and radius {r}.",
    ]
    image = None
    if out_dir is not None:
        image = circle_plot((h, k), r, out_dir / "circle_general.png")
    return make_part(label="", text=text, marks=marks, topic="circles",
                     subtopic="general_to_standard", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq((x-h)**2 + (y-k)**2, r*r)),
                     solution_latex=[
                         sp.latex(sp.Eq((x**2 - 2*h*x) + (y**2 - 2*k*y),
                                        -h*h-k*k+r*r)),
                         sp.latex(sp.Eq((x-h)**2 - h*h + (y-k)**2 - k*k,
                                        -h*h-k*k+r*r)),
                         sp.latex(sp.Eq((x-h)**2 + (y-k)**2, r*r)),
                     ],
                     notes=["M1 group", "M1 complete square", "A1 centre",
                            "A1 radius"],
                     diagram_spec=diagram(image, "Figure: circle."))


def diameter_endpoints(rng: random.Random, marks: float, out_dir: Path | None):
    x1, y1 = rng.randint(-6, 6), rng.randint(-6, 6)
    x2, y2 = rng.randint(-6, 6), rng.randint(-6, 6)
    if (x1, y1) == (x2, y2):
        x2 += 3
    cx = sp.Rational(x1 + x2, 2)
    cy = sp.Rational(y1 + y2, 2)
    d2 = (x2 - x1) ** 2 + (y2 - y1) ** 2
    r2 = sp.Rational(d2, 4)
    text = (f"The endpoints of a diameter of a circle are ({x1}, {y1}) and "
            f"({x2}, {y2}). Find the centre, radius and equation of the circle.")
    if r2.is_Integer:
        answer = (f"Centre ({fmt_num(cx)}, {fmt_num(cy)}), radius "
                  f"{fmt_num(sp.sqrt(r2))}; equation "
                  f"{_shift('x', cx)}² + {_shift('y', cy)}² = {fmt_num(r2)}.")
    else:
        answer = (f"Centre ({fmt_num(cx)}, {fmt_num(cy)}), radius² = {fmt_num(r2)}; "
                  f"equation {_shift('x', cx)}² + {_shift('y', cy)}² = "
                  f"{fmt_num(r2)}.")
    steps = [
        f"Centre = midpoint of the diameter: (({x1}+{x2})/2, ({y1}+{y2})/2) = "
        f"({fmt_num(cx)}, {fmt_num(cy)}).",
        f"Radius² = ((x₂-x₁)² + (y₂-y₁)²)/4 = (({x2-x1})² + ({y2-y1})²)/4 "
        f"= {fmt_num(r2)}.",
        f"Use (x - h)² + (y - k)² = r²: {answer.split('; equation ')[-1]}",
    ]
    image = None
    if out_dir is not None:
        image = circle_plot((float(cx), float(cy)), float(sp.sqrt(r2)),
                            out_dir / "circle_diameter.png")
    return make_part(label="", text=text, marks=marks, topic="circles",
                     subtopic="diameter_endpoints", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq((x-cx)**2 + (y-cy)**2, r2)),
                     solution_latex=[
                         rf"\left({sp.latex(cx)},{sp.latex(cy)}\right)",
                         rf"r^2 = {sp.latex(r2)}",
                         sp.latex(sp.Eq((x-cx)**2 + (y-cy)**2, r2)),
                     ],
                     notes=["M1 midpoint", "M1 radius", "A1 equation"],
                     diagram_spec=diagram(image, "Figure: circle from diameter."))


def graph(rng: random.Random, marks: float, out_dir: Path | None):
    h, k = nz(rng, -5, 5), nz(rng, -5, 5)
    r = rng.randint(2, 7)
    text = (f"Sketch the circle {_general(h, k, r)} = 0. State its centre "
            "and radius.")
    answer = f"Centre ({h}, {k}), radius {r}."
    steps = [
        f"Complete the square to get {_standard(h, k, r)}.",
        f"Centre ({h}, {k}), radius {r}.",
        "Plot the centre and four points r units left, right, up and down.",
    ]
    image = None
    if out_dir is not None:
        image = circle_plot((h, k), r, out_dir / "circle_graph.png")
    return make_part(label="", text=text, marks=marks, topic="circles",
                     subtopic="graph", answer=answer, steps=steps,
                     answer_latex=rf"\mathrm{{centre}}\;({h},{k}),\quad r={r}",
                     solution_latex=[
                         sp.latex(sp.Eq((x-h)**2 + (y-k)**2, r*r)),
                         rf"\mathrm{{centre}}\;({h},{k}),\quad r={r}",
                     ],
                     notes=["M1 complete square", "A1 centre", "A1 radius"],
                     diagram_spec=diagram(image, "Figure: circle."))


GENERATORS = [
    Generator("circles.standard_form", "circles", "standard_form", 5, standard_form),
    Generator("circles.general_to_standard", "circles", "general_to_standard", 5, general_to_standard),
    Generator("circles.diameter_endpoints", "circles", "diameter_endpoints", 5, diameter_endpoints),
    Generator("circles.graph", "circles", "graph", 4, graph),
]
