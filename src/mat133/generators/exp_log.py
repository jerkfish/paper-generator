"""Priority 3 generators: exponential and logarithmic equations."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, fmt_num, make_part, nz, pick, poly_text,
)

x = sp.Symbol("x")


def exponential_equation(rng: random.Random, marks: float, out_dir: Path | None):
    base = pick(rng, (2, 3, 5))
    m, p = nz(rng, -3, 3), nz(rng, -3, 3)
    while m == p:
        p = nz(rng, -3, 3)
    n, q = nz(rng, -5, 5), nz(rng, -5, 5)
    sol = sp.Rational(q - n, m - p)
    text = (f"Solve the exponential equation {base}^({poly_text(m*x+n)}) = "
            f"{base}^({poly_text(p*x+q)}).")
    answer = f"x = {fmt_num(sol)}."
    steps = [
        f"The bases are equal ({base}), so equate the exponents: "
        f"{poly_text(m*x+n)} = {poly_text(p*x+q)}.",
        f"Rearrange: {poly_text((m-p)*x)} = {q-n}.",
        f"Divide by {m-p}: x = {fmt_num(sol)}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="exponential_logarithmic",
                     subtopic="exponential_equation", answer=answer, steps=steps,
                     answer_latex=rf"x = {sp.latex(sol)}",
                     solution_latex=[
                         rf"{base}^{{{sp.latex(m*x+n)}}} = {base}^{{{sp.latex(p*x+q)}}}",
                         sp.latex(sp.Eq(m*x+n, p*x+q)),
                         rf"x = {sp.latex(sol)}",
                     ],
                     notes=["M1 equate exponents", "M1 rearrange", "A1 solution"])


def log_equation(rng: random.Random, marks: float, out_dir: Path | None):
    base, k = pick(rng, ((2, 5), (3, 3), (2, 6)))
    total = base ** k
    pairs = [(d, total // d) for d in range(1, int(total ** 0.5) + 1)
             if total % d == 0]
    small, large = pick(rng, pairs)
    c = large - small
    text = (f"Solve the logarithmic equation log_{base}(x) + log_{base}(x - {c}) "
            f"= {k}.")
    answer = f"x = {large}."
    steps = [
        f"Use the product law: log_{base}[x(x - {c})] = {k}.",
        f"Convert to exponential form: x(x - {c}) = {base}^{k} = {total}.",
        f"Expand: x² - {c}x - {total} = 0.",
        f"Factor: (x - {large})(x + {small}) = 0.",
        f"Reject x = -{small} because the logarithm requires x > {c}.",
        f"Therefore x = {large}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="exponential_logarithmic",
                     subtopic="log_equation", answer=answer, steps=steps,
                     answer_latex=rf"x = {large}",
                     solution_latex=[
                         rf"\log_{{{base}}}\left[x(x-{c})\right] = {k}",
                         sp.latex(sp.Eq(x*(x-c), total)),
                         sp.latex(sp.Eq(x*x - c*x - total, 0)),
                         rf"x = {large}",
                     ],
                     notes=["M1 log law", "M1 exponential form", "M1 quadratic",
                            "A1 reject invalid root", "A1 answer"])


def log_laws(rng: random.Random, marks: float, out_dir: Path | None):
    base, m, n, exponent = pick(rng, ((2, 2, 4, 3), (3, 3, 9, 3), (5, 5, 5, 2)))
    text = (f"Express log_{base}({m}) + log_{base}({n}) as a single logarithm "
            "and evaluate it.")
    answer = f"log_{base}({m*n}) = {exponent}."
    steps = [
        f"Use log_a M + log_a N = log_a(MN): log_{base}({m}) + "
        f"log_{base}({n}) = log_{base}({m*n}).",
        f"Since {m*n} = {base}^{exponent}, log_{base}({m*n}) = {exponent}.",
    ]
    return make_part(label="", text=text, marks=marks, topic="exponential_logarithmic",
                     subtopic="log_laws", answer=answer, steps=steps,
                     answer_latex=rf"\log_{{{base}}}({m*n}) = {exponent}",
                     solution_latex=[
                         rf"\log_{{{base}}}({m}) + \log_{{{base}}}({n}) = \log_{{{base}}}({m*n})",
                         rf"\log_{{{base}}}({m*n}) = {exponent}",
                     ],
                     notes=["M1 product law", "A1 single log", "A1 value"])


GENERATORS = [
    Generator("exponential_logarithmic.exponential_equation", "exponential_logarithmic", "exponential_equation", 5, exponential_equation),
    Generator("exponential_logarithmic.log_equation", "exponential_logarithmic", "log_equation", 5, log_equation),
    Generator("exponential_logarithmic.log_laws", "exponential_logarithmic", "log_laws", 3, log_laws),
]
