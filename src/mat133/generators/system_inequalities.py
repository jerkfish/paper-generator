"""Priority 3 generators: systems of inequalities."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, pick,
)
from src.render.plots import feasible_region_plot

x, y = sp.symbols("x y")


def _vertices(inequalities, x_max=10, y_max=10):
    vertices = set()
    for i, first in enumerate(inequalities):
        for second in inequalities[i + 1:]:
            a1, b1, c1 = first["a"], first["b"], first["c"]
            a2, b2, c2 = second["a"], second["b"], second["c"]
            det = a1 * b2 - a2 * b1
            if det == 0:
                continue
            px = sp.Rational(c1 * b2 - c2 * b1, det)
            py = sp.Rational(a1 * c2 - a2 * c1, det)
            ok = True
            for item in inequalities:
                value = item["a"] * px + item["b"] * py
                if item.get("op", "<=") == "<=" and value > item["c"]:
                    ok = False
                if item.get("op", "<=") == ">=" and value < item["c"]:
                    ok = False
            if ok:
                vertices.add((px, py))
    return sorted(vertices)


def graph_feasible_region(rng: random.Random, marks: float, out_dir: Path | None):
    k = rng.randint(4, 9)
    a, b = rng.randint(1, 3), rng.randint(1, 3)
    inequalities = [
        {"a": -1, "b": 0, "c": 0, "op": "<=", "label": "x ≥ 0"},
        {"a": 0, "b": -1, "c": 0, "op": "<=", "label": "y ≥ 0"},
        {"a": a, "b": b, "c": k, "op": "<=", "label": f"{a}x + {b}y ≤ {k}"},
    ]
    vertices = _vertices(inequalities)
    vert_text = ", ".join(f"({fmt_num(px)}, {fmt_num(py)})" for px, py in vertices)
    text = ("Graph the system of inequalities below and shade the feasible region. "
            f"State the vertices of the region.\n"
            f"x ≥ 0, y ≥ 0, {a}x + {b}y ≤ {k}.")
    answer = f"The feasible region is the bounded triangle with vertices {vert_text}."
    steps = [
        "Draw the boundary lines x = 0, y = 0 and " f"{a}x + {b}y = {k}.",
        "Use a test point to decide which side of each line satisfies the inequality.",
        f"The feasible region has vertices {vert_text}.",
        "Shade the region that satisfies all three inequalities.",
    ]
    image = None
    if out_dir is not None:
        image = feasible_region_plot(inequalities, out_dir / "system_ineq_region.png",
                                     x_min=-1, x_max=k + 2, y_min=-1, y_max=k + 2)
    latex_system = (
        r"x \geq 0,\quad y \geq 0,\quad "
        rf"{a}x + {b}y \leq {k}")
    return make_part(label="", text=text, marks=marks, topic="systems_of_inequalities",
                     subtopic="graph_feasible_region", answer=answer, steps=steps,
                     answer_latex=latex_system,
                     solution_latex=[
                         rf"x = 0,\quad y = 0,\quad {a}x + {b}y = {k}",
                         latex_system,
                     ],
                     notes=["B1 boundary lines", "B1 shading", "A1 vertices"],
                     diagram_spec=diagram(image, "Figure: feasible region."))


def write_from_region(rng: random.Random, marks: float, out_dir: Path | None):
    a = rng.randint(3, 8)
    b = rng.randint(3, 8)
    inequalities = [
        {"a": -1, "b": 0, "c": 0, "op": "<=", "label": "x ≥ 0"},
        {"a": 0, "b": -1, "c": 0, "op": "<=", "label": "y ≥ 0"},
        {"a": b, "b": a, "c": a * b, "op": "<=", "label": f"{b}x + {a}y ≤ {a*b}"},
    ]
    text = (f"Write a system of inequalities that describes the shaded triangular "
            f"region with vertices (0, 0), ({a}, 0) and (0, {b}).")
    answer = f"x ≥ 0, y ≥ 0, {b}x + {a}y ≤ {a*b}."
    steps = [
        "The region is bounded by the x-axis (y = 0), the y-axis (x = 0), "
        "and the line through " f"({a}, 0) and (0, {b}).",
        f"The line has equation x/{a} + y/{b} = 1, or {b}x + {a}y = {a*b}.",
        "The shaded region lies below and to the left of the line, so use ≤.",
        f"Therefore the system is {answer}",
    ]
    image = None
    if out_dir is not None:
        image = feasible_region_plot(inequalities, out_dir / "system_ineq_write.png",
                                     x_min=-1, x_max=a + 2, y_min=-1, y_max=b + 2)
    latex_system = (
        r"x \geq 0,\quad y \geq 0,\quad "
        rf"{b}x + {a}y \leq {a*b}")
    return make_part(label="", text=text, marks=marks, topic="systems_of_inequalities",
                     subtopic="write_from_region", answer=answer, steps=steps,
                     answer_latex=latex_system,
                     solution_latex=[
                         rf"\frac{{x}}{{{a}}} + \frac{{y}}{{{b}}} = 1",
                         latex_system,
                     ],
                     notes=["M1 line equation", "A1 boundaries", "A1 inequality directions"],
                     diagram_spec=diagram(image, "Figure: shaded triangular region."))


GENERATORS = [
    Generator("systems_of_inequalities.graph_feasible_region", "systems_of_inequalities", "graph_feasible_region", 5, graph_feasible_region),
    Generator("systems_of_inequalities.write_from_region", "systems_of_inequalities", "write_from_region", 5, write_from_region),
]
