"""Priority 3 generators: polynomials."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, factor_text, fmt_num, make_part, nz, poly_text,
)

x = sp.Symbol("x")


def _division(expr, divisor):
    quotient, remainder = sp.div(expr, divisor, x)
    return sp.expand(quotient), sp.expand(remainder)


def long_division(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(-4, 4)
    a, b, c, d = nz(rng, -4, 4), nz(rng, -5, 5), nz(rng, -6, 6), nz(rng, -6, 6)
    f = a * x**3 + b * x**2 + c * x + d
    divisor = x - r
    q, rem = _division(f, divisor)
    text = (f"Use long division to find the quotient and remainder when "
            f"f(x) = {poly_text(f)} is divided by {poly_text(divisor)}.")
    answer = f"Quotient: {poly_text(q)}; remainder: {fmt_num(rem)}."
    steps = [
        f"Divide the leading term {a}x³ by x to get {a}x².",
        f"Multiply {poly_text(divisor)} by {a}x² and subtract.",
        f"Repeat with the new leading term until the remainder has degree 0.",
        f"Quotient = {poly_text(q)}; remainder = {fmt_num(rem)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="polynomials",
                     subtopic="long_division", answer=answer, steps=steps,
                     answer_latex=rf"q(x) = {sp.latex(q)},\quad r = {sp.latex(rem)}",
                     solution_latex=[
                         sp.latex(sp.Eq(f, (x-r)*q + rem)),
                         rf"q(x) = {sp.latex(q)},\quad r = {sp.latex(rem)}",
                     ],
                     notes=["M1 first term", "M1 subtraction", "A1 quotient",
                            "A1 remainder"])


def synthetic_division(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(-4, 4)
    a, b, c, d = nz(rng, -4, 4), nz(rng, -5, 5), nz(rng, -6, 6), nz(rng, -6, 6)
    f = a * x**3 + b * x**2 + c * x + d
    q, rem = _division(f, x - r)
    text = (f"Use synthetic division to divide f(x) = {poly_text(f)} by "
            f"{poly_text(x-r)}. State the quotient and remainder.")
    answer = f"Quotient: {poly_text(q)}; remainder: {fmt_num(rem)}."
    steps = [
        f"Write the divisor as x - ({r}); use {r} in the synthetic-division bracket.",
        f"Bring down {a}; multiply by {r} and add successively.",
        f"The quotient is {poly_text(q)} and the remainder is {fmt_num(rem)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="polynomials",
                     subtopic="synthetic_division", answer=answer, steps=steps,
                     answer_latex=rf"q(x) = {sp.latex(q)},\quad r = {sp.latex(rem)}",
                     solution_latex=[
                         sp.latex(sp.Eq(f, (x-r)*q + rem)),
                         rf"q(x) = {sp.latex(q)},\quad r = {sp.latex(rem)}",
                     ],
                     notes=["M1 setup", "M1 synthetic steps", "A1 quotient",
                            "A1 remainder"])


def factor_theorem(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(-4, 4)
    qa, qb, qc = nz(rng, -3, 3), nz(rng, -5, 5), nz(rng, -5, 5)
    f = sp.expand((x - r) * (qa * x**2 + qb * x + qc))
    text = (f"Show that {poly_text(x-r)} is a factor of f(x) = {poly_text(f)} "
            "by using the factor theorem. Hence factorise f(x) completely.")
    quotient = sp.expand(qa * x**2 + qb * x + qc)
    factored = sp.factor(f)
    answer = f"f({r}) = 0, so {poly_text(x-r)} is a factor; f(x) = {factor_text(factored)}."
    steps = [
        f"Evaluate f({r}).",
        f"Since f({r}) = 0, the factor theorem gives {poly_text(x-r)} as a factor.",
        f"Divide f(x) by {poly_text(x-r)} to get {poly_text(quotient)}.",
        f"Factorise the quotient if possible: f(x) = {factor_text(factored)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="polynomials",
                     subtopic="factor_theorem", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Eq(f, factored)),
                     solution_latex=[
                         rf"f({r}) = {sp.latex(f.subs(x, r))}",
                         sp.latex(sp.Eq(f, factored)),
                     ],
                     notes=["M1 evaluate", "A1 zero", "M1 division", "A1 factors"])


def remainder_theorem(rng: random.Random, marks: float, out_dir: Path | None):
    r = rng.randint(-4, 4)
    a, b, c, d = nz(rng, -3, 3), nz(rng, -5, 5), nz(rng, -6, 6), nz(rng, -6, 6)
    f = a * x**3 + b * x**2 + c * x + d
    rem = sp.expand(f.subs(x, r))
    text = (f"Use the remainder theorem to find the remainder when "
            f"f(x) = {poly_text(f)} is divided by {poly_text(x-r)}.")
    answer = f"Remainder = {fmt_num(rem)}."
    steps = [
        f"By the remainder theorem, the remainder is f({r}).",
        f"Substitute x = {r}: f({r}) = {fmt_num(rem)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="polynomials",
                     subtopic="remainder_theorem", answer=answer, steps=steps,
                     answer_latex=rf"f({r}) = {sp.latex(rem)}",
                     solution_latex=[
                         sp.latex(f),
                         rf"f({r}) = {sp.latex(rem)}",
                     ],
                     notes=["M1 remainder theorem", "A1 substitution", "A1 value"])


def factorization(rng: random.Random, marks: float, out_dir: Path | None):
    roots = rng.sample(range(-4, 5), 3)
    a = nz(rng, -3, 3)
    f = sp.expand(a * (x - roots[0]) * (x - roots[1]) * (x - roots[2]))
    text = f"Factorise f(x) = {poly_text(f)} completely."
    answer = factor_text(f)
    steps = [
        "Try integer roots using the factor theorem.",
        f"The roots are x = {roots[0]}, x = {roots[1]} and x = {roots[2]}.",
        f"Therefore f(x) = {answer}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="polynomials",
                     subtopic="factorization", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.factor(f)),
                     solution_latex=[
                         sp.latex(f),
                         rf"f({roots[0]}) = 0,\quad f({roots[1]}) = 0,\quad f({roots[2]}) = 0",
                         sp.latex(sp.factor(f)),
                     ],
                     notes=["M1 find a root", "M1 divide", "A1 complete factorisation"])


GENERATORS = [
    Generator("polynomials.long_division", "polynomials", "long_division", 5, long_division),
    Generator("polynomials.synthetic_division", "polynomials", "synthetic_division", 5, synthetic_division),
    Generator("polynomials.factor_theorem", "polynomials", "factor_theorem", 5, factor_theorem),
    Generator("polynomials.remainder_theorem", "polynomials", "remainder_theorem", 3, remainder_theorem),
    Generator("polynomials.factorization", "polynomials", "factorization", 5, factorization),
]
