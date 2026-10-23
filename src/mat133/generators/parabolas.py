"""Priority 2 generators: parabolas."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, nz, pick, poly_text,
)
from src.render.plots import parabola_plot

x, y = sp.symbols("x y")


def _shift(var: str, value) -> str:
    if value == 0:
        return var
    sign = "-" if value > 0 else "+"
    return f"({var} {sign} {abs(value)})"


def _vertical_standard(h, k, p) -> str:
    xpart = f"{_shift('x', h)}²"
    ypart = _shift("y", k)
    return f"{xpart} = {4*p}{ypart}" if k else f"{xpart} = {4*p}y"


def _horizontal_standard(h, k, p) -> str:
    ypart = f"{_shift('y', k)}²"
    xpart = _shift("x", h)
    return f"{ypart} = {4*p}{xpart}" if h else f"{ypart} = {4*p}x"


def standard_form(rng: random.Random, marks: float, out_dir: Path | None):
    h, k = nz(rng, -4, 4), nz(rng, -5, 5)
    p = pick(rng, (-2, -1, 1, 2))
    a = sp.Rational(1, 4 * p)
    general = sp.expand(a * (x - h) ** 2 + k)
    text = (f"Write y = {poly_text(general)} in standard form. Hence state "
            "the vertex, focus and directrix, and sketch the parabola.")
    answer = (f"Standard form: {_vertical_standard(h, k, p)}; vertex ({h}, {k}); "
              f"focus ({h}, {fmt_num(k + p)}); directrix y = {fmt_num(k - p)}.")
    steps = [
        f"Factor out the coefficient of x²: y = {fmt_num(a)}"
        f"({poly_text(x*x - 2*h*x)}) + {fmt_num(sp.expand(a*h*h + k))}.",
        f"Complete the square: y = {fmt_num(a)}{_shift('x', h)}² + {k}.",
        f"Rewrite as {_vertical_standard(h, k, p)}.",
        f"Read vertex ({h}, {k}); the focal length is p = {p}.",
        f"Focus ({h}, {fmt_num(k+p)}); directrix y = {fmt_num(k-p)}.",
    ]
    image = None
    if out_dir is not None:
        image = parabola_plot(h, k, p, out_dir / "parabola_standard.png")
    return make_part(label="", text=text, marks=marks, topic="parabolas",
                     subtopic="standard_form", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq((x-h)**2, 4*p*(y-k))),
                     solution_latex=[
                         sp.latex(sp.Eq(sp.Symbol("y"), general)),
                         sp.latex(sp.Eq(sp.Symbol("y"), a*(x-h)**2 + k)),
                         sp.latex(sp.Eq((x-h)**2, 4*p*(y-k))),
                     ],
                     notes=["M1 complete square", "A1 standard form",
                            "A1 vertex", "A1 focus/directrix"],
                     diagram_spec=diagram(image, "Figure: parabola."))


def vertex_focus_directrix(rng: random.Random, marks: float, out_dir: Path | None):
    vertical = pick(rng, (True, False))
    h, k = nz(rng, -4, 4), nz(rng, -5, 5)
    p = pick(rng, (-2, -1, 1, 2))
    if vertical:
        focus = (h, k + p)
        directrix = f"y = {fmt_num(k - p)}"
        equation = _vertical_standard(h, k, p)
        text = (f"Find the standard equation of the parabola with focus "
                f"({focus[0]}, {focus[1]}) and directrix {directrix}. State its vertex.")
        answer = f"{equation}; vertex ({h}, {k})."
        steps = [
            f"The vertex is the midpoint between the focus and the directrix: "
            f"({h}, {fmt_num(k)}).",
            f"The focal length is p = {p}.",
            f"Use (x - h)² = 4p(y - k): {equation}.",
            f"Thus the vertex is ({h}, {k}).",
        ]
    else:
        focus = (h + p, k)
        directrix = f"x = {fmt_num(h - p)}"
        equation = _horizontal_standard(h, k, p)
        text = (f"Find the standard equation of the parabola with focus "
                f"({focus[0]}, {focus[1]}) and directrix {directrix}. State its vertex.")
        answer = f"{equation}; vertex ({h}, {k})."
        steps = [
            f"The vertex is the midpoint between the focus and the directrix: "
            f"({h}, {k}).",
            f"The focal length is p = {p}.",
            f"Use (y - k)² = 4p(x - h): {equation}.",
            f"Thus the vertex is ({h}, {k}).",
        ]
    image = None
    if out_dir is not None:
        image = parabola_plot(h, k, p, out_dir / "parabola_focus.png",
                              vertical=vertical)
    eq = (sp.Eq((x-h)**2, 4*p*(y-k)) if vertical
          else sp.Eq((y-k)**2, 4*p*(x-h)))
    return make_part(label="", text=text, marks=marks, topic="parabolas",
                     subtopic="vertex_focus_directrix", answer=answer, steps=steps,
                     answer_latex=sp.latex(eq),
                     solution_latex=[
                         rf"\mathrm{{vertex}}\;({h},{k})",
                         rf"p = {p}",
                         sp.latex(eq),
                     ],
                     notes=["M1 vertex", "M1 focal length", "A1 equation"],
                     diagram_spec=diagram(image, "Figure: parabola with focus and directrix."))


def graph(rng: random.Random, marks: float, out_dir: Path | None):
    vertical = pick(rng, (True, False))
    h, k = nz(rng, -4, 4), nz(rng, -5, 5)
    p = pick(rng, (-2, -1, 1, 2))
    if vertical:
        equation = _vertical_standard(h, k, p)
        focus = (h, k + p)
        directrix = f"y = {fmt_num(k - p)}"
    else:
        equation = _horizontal_standard(h, k, p)
        focus = (h + p, k)
        directrix = f"x = {fmt_num(h - p)}"
    text = (f"Sketch the parabola {equation}. Label the vertex, focus and directrix.")
    answer = (f"Vertex ({h}, {k}); focus ({fmt_num(focus[0])}, {fmt_num(focus[1])}); "
              f"directrix {directrix}.")
    steps = [
        f"Compare with the standard form; the vertex is ({h}, {k}).",
        f"The focal length is p = {p}.",
        f"Focus ({fmt_num(focus[0])}, {fmt_num(focus[1])}); directrix {directrix}.",
        "Plot the vertex, focus and directrix, then draw the parabola.",
    ]
    image = None
    if out_dir is not None:
        image = parabola_plot(h, k, p, out_dir / "parabola_graph.png",
                              vertical=vertical)
    eq = (sp.Eq((x-h)**2, 4*p*(y-k)) if vertical
          else sp.Eq((y-k)**2, 4*p*(x-h)))
    return make_part(label="", text=text, marks=marks, topic="parabolas",
                     subtopic="graph", answer=answer, steps=steps,
                     answer_latex=sp.latex(eq),
                     solution_latex=[
                         sp.latex(eq),
                         rf"\mathrm{{vertex}}\;({h},{k})",
                         rf"\mathrm{{focus}}\;({fmt_num(focus[0])},{fmt_num(focus[1])})",
                         rf"\mathrm{{directrix}}\;{directrix}",
                     ],
                     notes=["A1 vertex", "A1 focus", "A1 directrix", "B1 graph"],
                     diagram_spec=diagram(image, "Figure: parabola."))


GENERATORS = [
    Generator("parabolas.standard_form", "parabolas", "standard_form", 5, standard_form),
    Generator("parabolas.vertex_focus_directrix", "parabolas", "vertex_focus_directrix", 5, vertex_focus_directrix),
    Generator("parabolas.graph", "parabolas", "graph", 5, graph),
]
