"""Priority 3 generators: systems of equations."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, fmt_num, make_part, nz, poly_text,
)

x, y, z = sp.symbols("x y z")


def linear_2var(rng: random.Random, marks: float, out_dir: Path | None):
    x0, y0 = rng.randint(-5, 5), rng.randint(-5, 5)
    a1, b1 = nz(rng, -5, 5), nz(rng, -5, 5)
    a2, b2 = nz(rng, -5, 5), nz(rng, -5, 5)
    while a1 * b2 - a2 * b1 == 0:
        a2, b2 = nz(rng, -5, 5), nz(rng, -5, 5)
    c1, c2 = a1 * x0 + b1 * y0, a2 * x0 + b2 * y0
    text = (f"Solve the simultaneous equations\n"
            f"{poly_text(a1*x + b1*y)} = {c1}\n"
            f"{poly_text(a2*x + b2*y)} = {c2}.")
    answer = f"x = {x0}, y = {y0}."
    steps = [
        f"Multiply the first equation by {b2} and the second by {b1} to "
        "eliminate y.",
        f"Subtract the resulting equations to solve for x: x = {x0}.",
        f"Substitute x = {x0} into the first equation to find y = {y0}.",
        f"Check in both equations: both give the stated right-hand sides.",
    ]
    return make_part(label="", text=text, marks=marks, topic="systems_of_equations",
                     subtopic="linear_2var", answer=answer, steps=steps,
                     answer_latex=rf"x = {x0},\quad y = {y0}",
                     solution_latex=[
                         sp.latex(sp.Eq(a1*x + b1*y, c1)),
                         sp.latex(sp.Eq(a2*x + b2*y, c2)),
                         rf"x = {x0},\quad y = {y0}",
                     ],
                     notes=["M1 eliminate", "A1 x", "A1 y"])


def linear_3var(rng: random.Random, marks: float, out_dir: Path | None):
    x0, y0, z0 = rng.randint(-4, 4), rng.randint(-4, 4), rng.randint(-4, 4)
    while True:
        rows = [[nz(rng, -4, 4) for _ in range(3)] for _ in range(3)]
        matrix = sp.Matrix(rows)
        if matrix.det() != 0:
            break
    rhs = [sum(rows[i][j] * (x0, y0, z0)[j] for j in range(3)) for i in range(3)]
    eqs = [f"{poly_text(rows[i][0]*x + rows[i][1]*y + rows[i][2]*z)} = {rhs[i]}"
           for i in range(3)]
    text = "Solve the system of equations simultaneously:\n" + "\n".join(eqs)
    answer = f"x = {x0}, y = {y0}, z = {z0}."
    steps = [
        "Use elimination: choose two pairs of equations and eliminate z.",
        "Solve the resulting 2×2 system for x and y.",
        f"Back-substitute x = {x0}, y = {y0} into one equation to find z = {z0}.",
        "Check the solution in all three equations.",
    ]
    return make_part(label="", text=text, marks=marks, topic="systems_of_equations",
                     subtopic="linear_3var", answer=answer, steps=steps,
                     answer_latex=rf"x = {x0},\quad y = {y0},\quad z = {z0}",
                     solution_latex=[
                         sp.latex(sp.Eq(rows[i][0]*x + rows[i][1]*y + rows[i][2]*z, rhs[i]))
                         for i in range(3)
                     ] + [rf"x = {x0},\quad y = {y0},\quad z = {z0}"],
                     notes=["M1 eliminate", "A1 two variables", "A1 third variable"])


def nonlinear(rng: random.Random, marks: float, out_dir: Path | None):
    x1, x2 = rng.sample(range(-5, 6), 2)
    c = nz(rng, -6, 6)
    y1, y2 = x1 * x1 + c, x2 * x2 + c
    m = x1 + x2
    b = c - x1 * x2
    text = (f"Solve the simultaneous equations\n"
            f"y = {poly_text(x*x + c)}\n"
            f"y = {poly_text(m*x + b)}.")
    answer = f"({x1}, {y1}) and ({x2}, {y2})."
    steps = [
        f"Substitute the line into the parabola: {poly_text(m*x + b)} = "
        f"{poly_text(x*x + c)}.",
        f"Rearrange: {poly_text(x*x - m*x + (c-b))} = 0.",
        f"Factor: (x - {x1})(x - {x2}) = 0, so x = {x1} or x = {x2}.",
        f"Substitute back: when x = {x1}, y = {y1}; when x = {x2}, y = {y2}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="systems_of_equations",
                     subtopic="nonlinear", answer=answer, steps=steps,
                     answer_latex=rf"({x1},{y1}),\quad ({x2},{y2})",
                     solution_latex=[
                         sp.latex(sp.Eq(m*x + b, x*x + c)),
                         sp.latex(sp.Eq(x*x - m*x + (c-b), 0)),
                         sp.latex(sp.Eq((x-x1)*(x-x2), 0)),
                         rf"x = {x1}\;\mathrm{{or}}\; x = {x2}",
                         rf"({x1},{y1}),\quad ({x2},{y2})",
                     ],
                     notes=["M1 substitute", "A1 quadratic", "A1 both points"])


GENERATORS = [
    Generator("systems_of_equations.linear_2var", "systems_of_equations", "linear_2var", 4, linear_2var),
    Generator("systems_of_equations.linear_3var", "systems_of_equations", "linear_3var", 5, linear_3var),
    Generator("systems_of_equations.nonlinear", "systems_of_equations", "nonlinear", 5, nonlinear),
]
