"""Priority 3 generators: complex numbers."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, fmt_num, make_part, nz, pick,
)

z = sp.Symbol("z")
i = sp.I


def _z(a, b) -> str:
    a_text = str(a)
    b_text = b if isinstance(b, str) else fmt_num(b)
    if b_text in ("0", "0/1"):
        return a_text
    if b_text == "1":
        return "i" if a_text in ("0", "0/1") else f"{a_text} + i"
    if b_text == "-1":
        return "-i" if a_text in ("0", "0/1") else f"{a_text} - i"
    if a_text in ("0", "0/1"):
        return f"{b_text}i"
    if b_text.startswith("-"):
        return f"{a_text} - {b_text[1:]}i"
    return f"{a_text} + {b_text}i"


def arithmetic(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -6, 6), nz(rng, -6, 6)
    c, d = nz(rng, -6, 6), nz(rng, -6, 6)
    op = pick(rng, ("+", "-", "×"))
    z1 = a + b * i
    z2 = c + d * i
    if op == "+":
        result = sp.expand(z1 + z2)
    elif op == "-":
        result = sp.expand(z1 - z2)
    else:
        result = sp.expand(z1 * z2)
    re, im = sp.re(result), sp.im(result)
    text = (f"Given z₁ = {_z(a,b)} and z₂ = {_z(c,d)}, find z₁ {op} z₂ "
            "in the form a + bi.")
    answer = _z(fmt_num(re), fmt_num(im))
    if op == "×":
        steps = [
            f"Expand: ({_z(a,b)})({_z(c,d)}) = {a*c} + {a*d}i + {b*c}i + {b*d}i².",
            f"Use i² = -1: {a*c} - {b*d} + ({a*d + b*c})i.",
            f"Combine real and imaginary parts: {answer}.",
        ]
    elif op == "+":
        steps = [
            f"Add real parts: {a} + {c} = {a+c}.",
            f"Add imaginary parts: {b} + {d} = {b+d}.",
            f"Therefore z₁ + z₂ = {answer}.",
        ]
    else:
        steps = [
            f"Subtract real parts: {a} - {c} = {a-c}.",
            f"Subtract imaginary parts: {b} - {d} = {b-d}.",
            f"Therefore z₁ - z₂ = {answer}.",
        ]
    return make_part(label="", text=text, marks=marks, topic="complex_numbers",
                     subtopic="arithmetic", answer=answer, steps=steps,
                     answer_latex=sp.latex(result),
                     solution_latex=[
                         rf"\left({sp.latex(z1)}\right) {op} \left({sp.latex(z2)}\right)",
                         sp.latex(result),
                     ],
                     notes=["M1 arithmetic", "A1 real part", "A1 imaginary part"])


def division(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -5, 5), nz(rng, -5, 5)
    c, d = nz(rng, -5, 5), nz(rng, -5, 5)
    while c * c + d * d == 0:
        c, d = nz(rng, -5, 5), nz(rng, -5, 5)
    num = sp.expand((a + b * i) * (c - d * i))
    den = c * c + d * d
    re = sp.Rational(sp.re(num), den)
    im = sp.Rational(sp.im(num), den)
    text = (f"Given z₁ = {_z(a,b)} and z₂ = {_z(c,d)}, express z₁/z₂ in "
            "the form a + bi.")
    answer = _z(fmt_num(re), fmt_num(im))
    steps = [
        f"Multiply numerator and denominator by the conjugate of z₂: "
        f"({_z(c,d)})̄ = {_z(c,-d)}.",
        f"Numerator: ({_z(a,b)})({_z(c,-d)}) = {fmt_num(sp.re(num))} + "
        f"{fmt_num(sp.im(num))}i.",
        f"Denominator: {c}² + {d}² = {den}.",
        f"Divide: {answer}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="complex_numbers",
                     subtopic="division", answer=answer, steps=steps,
                     answer_latex=sp.latex(re + im*i),
                     solution_latex=[
                         rf"\frac{{{sp.latex(a+b*i)}}}{{{sp.latex(c+d*i)}}}",
                         rf"= \frac{{\left({sp.latex(a+b*i)}\right)\left({sp.latex(c-d*i)}\right)}}{{\left({sp.latex(c+d*i)}\right)\left({sp.latex(c-d*i)}\right)}}",
                         rf"= \frac{{{sp.latex(num)}}}{{{den}}}",
                         sp.latex(re + im*i),
                     ],
                     notes=["M1 conjugate", "M1 numerator", "A1 denominator",
                            "A1 standard form"])


def powers(rng: random.Random, marks: float, out_dir: Path | None):
    n = rng.randint(5, 40)
    cycle = n % 4
    result = sp.simplify(i ** n)
    answer = {sp.Integer(1): "1", sp.Integer(-1): "-1",
              sp.I: "i", -sp.I: "-i"}.get(result, str(result))
    text = f"Evaluate i^{n} and simplify completely."
    steps = [
        "Use the cycle i¹ = i, i² = -1, i³ = -i, i⁴ = 1.",
        f"Divide the exponent by 4: {n} = 4({n // 4}) + {cycle}.",
        f"Therefore i^{n} = i^{cycle} = {answer}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="complex_numbers",
                     subtopic="powers", answer=answer, steps=steps,
                     answer_latex=rf"i^{{{n}}} = {sp.latex(result)}",
                     solution_latex=[
                         rf"i^{{{n}}} = i^{{4({n // 4}) + {cycle}}}",
                         rf"= \left(i^4\right)^{{{n // 4}}} i^{{{cycle}}} = 1^{{{n // 4}}} i^{{{cycle}}}",
                         rf"= {sp.latex(result)}",
                     ],
                     notes=["M1 cycle", "A1 remainder", "A1 result"])


def modulus_argument(rng: random.Random, marks: float, out_dir: Path | None):
    triples = [(3, 4, 5), (4, 3, 5), (5, 12, 13), (8, 15, 17), (7, 24, 25)]
    a, b, r = pick(rng, triples)
    if rng.random() < 0.5:
        a = -a
    angle = sp.atan2(b, a) * 180 / sp.pi
    text = (f"Find the modulus and argument of z = {_z(a,b)}. Give the "
            "argument in degrees correct to one decimal place.")
    answer = f"|z| = {r}; arg(z) ≈ {float(angle):.1f}°."
    steps = [
        f"Modulus: |z| = √({a}² + {b}²) = √{a*a + b*b} = {r}.",
        f"Argument: tan θ = {b}/{a}.",
        f"Since the point is in quadrant "
        f"{'I' if a>0 and b>0 else 'II' if a<0 and b>0 else 'III' if a<0 and b<0 else 'IV'}, "
        f"θ ≈ {float(angle):.1f}°.",
    ]
    return make_part(label="", text=text, marks=marks, topic="complex_numbers",
                     subtopic="modulus_argument", answer=answer, steps=steps,
                     answer_latex=rf"|z| = {r},\quad \arg(z) = {float(angle):.1f}^\circ",
                     solution_latex=[
                         rf"|z| = \sqrt{{{a}^2 + {b}^2}} = {r}",
                         rf"\tan\theta = \frac{{{b}}}{{{a}}},\quad \theta = {float(angle):.1f}^\circ",
                     ],
                     notes=["M1 modulus", "A1 modulus", "M1 argument", "A1 angle"])


GENERATORS = [
    Generator("complex_numbers.arithmetic", "complex_numbers", "arithmetic", 4, arithmetic),
    Generator("complex_numbers.division", "complex_numbers", "division", 5, division),
    Generator("complex_numbers.powers", "complex_numbers", "powers", 3, powers),
    Generator("complex_numbers.modulus_argument", "complex_numbers", "modulus_argument", 5, modulus_argument),
]
