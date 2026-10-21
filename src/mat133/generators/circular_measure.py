"""Priority 3 generators: circular measure."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, diagram, fmt_num, make_part, pick,
)
from src.render.plots import sector_plot

ANGLES = (30, 45, 60, 90, 120, 135, 150, 180)


def _pi_text(angle: int) -> str:
    r = sp.Rational(angle, 180)
    if r == 0:
        return "0"
    if r == 1:
        return "π"
    if r.denominator == 1:
        return f"{r.numerator}π"
    if r.numerator == 1:
        return f"π/{r.denominator}"
    return f"{r.numerator}π/{r.denominator}"


def _num_text(value, angle: int) -> str:
    """Format a value containing a factor pi as an exact multiple of pi."""
    r = sp.Rational(angle, 180)
    coeff = sp.simplify(value / sp.pi)
    if coeff == 0:
        return "0"
    if coeff.denominator == 1:
        return f"{coeff.numerator}π"
    if coeff.numerator == 1:
        return f"π/{coeff.denominator}"
    return f"{coeff.numerator}π/{coeff.denominator}"


def arc_length(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(4, 15)
    angle = pick(rng, ANGLES)
    theta = sp.Rational(angle, 180) * sp.pi
    s = sp.simplify(r * theta)
    exact = _num_text(s, angle)
    text = (f"A circle has radius {r} cm. Find the length of the arc subtended "
            f"by a central angle of {angle}°.")
    answer = f"s = {exact} cm ≈ {float(s):.2f} cm."
    steps = [
        f"Convert the angle to radians: θ = {angle}° × π/180 = {_pi_text(angle)}.",
        f"Use s = rθ: s = {r} × {_pi_text(angle)} = {exact} cm.",
        f"Numerically, s ≈ {float(s):.2f} cm.",
    ]
    image = None
    if out_dir is not None:
        image = sector_plot(r, angle, out_dir / "arc_length.png")
    return make_part(label="", text=text, marks=marks, topic="circular_measure",
                     subtopic="arc_length", answer=answer, steps=steps,
                     answer_latex=rf"s = {sp.latex(s)}\ \mathrm{{cm}}",
                     solution_latex=[
                         rf"\theta = {angle}^\circ \times \frac{{\pi}}{{180}} = {sp.latex(theta)}",
                         rf"s = r\theta = {r}\left({sp.latex(theta)}\right) = {sp.latex(s)}",
                     ],
                     notes=["M1 radians", "M1 arc formula", "A1 exact value"],
                     diagram_spec=diagram(image, "Figure: arc and sector.", width_cm=8.0))


def sector_area(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(4, 15)
    angle = pick(rng, ANGLES)
    theta = sp.Rational(angle, 180) * sp.pi
    area = sp.simplify(sp.Rational(1, 2) * r * r * theta)
    exact = _num_text(area, angle)
    text = (f"Find the area of the sector of a circle with radius {r} cm and "
            f"central angle {angle}°.")
    answer = f"Area = {exact} cm² ≈ {float(area):.2f} cm²."
    steps = [
        f"Convert the angle to radians: θ = {_pi_text(angle)}.",
        f"Use A = ½r²θ: A = ½({r})²({_pi_text(angle)}) = {exact} cm².",
        f"Numerically, A ≈ {float(area):.2f} cm².",
    ]
    image = None
    if out_dir is not None:
        image = sector_plot(r, angle, out_dir / "sector_area.png")
    return make_part(label="", text=text, marks=marks, topic="circular_measure",
                     subtopic="sector_area", answer=answer, steps=steps,
                     answer_latex=rf"A = {sp.latex(area)}\ \mathrm{{cm}}^2",
                     solution_latex=[
                         rf"\theta = {sp.latex(theta)}",
                         rf"A = \frac{{1}}{{2}}r^2\theta = \frac{{1}}{{2}}({r})^2\left({sp.latex(theta)}\right) = {sp.latex(area)}",
                     ],
                     notes=["M1 radians", "M1 area formula", "A1 exact value"],
                     diagram_spec=diagram(image, "Figure: sector.", width_cm=8.0))


def perimeter(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(4, 15)
    angle = pick(rng, ANGLES)
    theta = sp.Rational(angle, 180) * sp.pi
    arc = sp.simplify(r * theta)
    per = sp.simplify(2 * r + arc)
    text = (f"Find the perimeter of the sector with radius {r} cm and central "
            f"angle {angle}°.")
    answer = (f"Perimeter = 2({r}) + {_num_text(arc, angle)} = "
              f"{2*r} + {_num_text(arc, angle)} cm ≈ {float(per):.2f} cm.")
    steps = [
        f"Arc length: s = rθ = {_num_text(arc, angle)} cm.",
        f"Perimeter = 2r + s = {2*r} + {_num_text(arc, angle)} cm.",
        f"Numerically, perimeter ≈ {float(per):.2f} cm.",
    ]
    image = None
    if out_dir is not None:
        image = sector_plot(r, angle, out_dir / "sector_perimeter.png")
    return make_part(label="", text=text, marks=marks, topic="circular_measure",
                     subtopic="perimeter", answer=answer, steps=steps,
                     answer_latex=rf"P = {sp.latex(per)}\ \mathrm{{cm}}",
                     solution_latex=[
                         rf"s = r\theta = {sp.latex(arc)}",
                         rf"P = 2r + s = {2*r} + {sp.latex(arc)} = {sp.latex(per)}",
                     ],
                     notes=["M1 arc length", "A1 add two radii", "A1 total"],
                     diagram_spec=diagram(image, "Figure: sector.", width_cm=8.0))


def radians(rng: random.Random, marks: float, out_dir: Path | None):
    angle = pick(rng, ANGLES)
    rad_angle = pick(rng, (30, 45, 60, 90, 120, 180))
    theta = sp.Rational(angle, 180) * sp.pi
    text = (f"Convert {angle}° to radians, and convert {_pi_text(rad_angle)} "
            "radians to degrees.")
    answer = f"{angle}° = {_pi_text(angle)} rad; {_pi_text(rad_angle)} rad = {rad_angle}°."
    steps = [
        f"Multiply by π/180: {angle}° = {angle}π/180 = {_pi_text(angle)} rad.",
        f"Multiply by 180/π: {_pi_text(rad_angle)} × 180/π = {rad_angle}°.",
    ]
    return make_part(label="", text=text, marks=marks, topic="circular_measure",
                     subtopic="radians", answer=answer, steps=steps,
                     answer_latex=rf"{angle}^\circ = {sp.latex(theta)},\quad {sp.latex(sp.Rational(rad_angle,180)*sp.pi)} = {rad_angle}^\circ",
                     solution_latex=[
                         rf"{angle}^\circ \times \frac{{\pi}}{{180}} = {sp.latex(theta)}",
                         rf"{sp.latex(sp.Rational(rad_angle,180)*sp.pi)} \times \frac{{180}}{{\pi}} = {rad_angle}^\circ",
                     ],
                     notes=["M1 conversion", "A1 first", "A1 second"])


GENERATORS = [
    Generator("circular_measure.arc_length", "circular_measure", "arc_length", 4, arc_length),
    Generator("circular_measure.sector_area", "circular_measure", "sector_area", 4, sector_area),
    Generator("circular_measure.perimeter", "circular_measure", "perimeter", 4, perimeter),
    Generator("circular_measure.radians", "circular_measure", "radians", 3, radians),
]
