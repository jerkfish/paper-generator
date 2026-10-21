"""Priority 1 generators: inequalities."""
from __future__ import annotations

import random
from pathlib import Path

import sympy as sp

from src.mat133.generators.base import (
    Generator, fmt_num, interval, make_part, nz, pick, poly_text, union,
)
from src.render.mathfig import number_line

x = sp.Symbol("x")


def _latex_solution(expr, op: str) -> str:
    rel = {"<=": sp.Le(expr, 0), "<": sp.Lt(expr, 0),
           ">=": sp.Ge(expr, 0), ">": sp.Gt(expr, 0)}[op]
    try:
        return sp.latex(sp.solve_univariate_inequality(rel, x, relational=False))
    except Exception:
        return ""


def _linear_interval(a, b, c, op: str):
    """Solve a*x + b (op) c."""
    rhs = sp.Rational(c - b, a)
    if op == "<=":
        return (rhs, sp.oo, True, False)
    if op == "<":
        return (rhs, sp.oo, False, False)
    if op == ">=":
        return (-sp.oo, rhs, False, True)
    return (-sp.oo, rhs, False, False)


def linear(rng: random.Random, marks: float, out_dir: Path | None):
    a, b, c = nz(rng, -6, 6), nz(rng, -9, 9), nz(rng, -9, 9)
    op = pick(rng, ("<=", "<", ">=", ">"))
    lo, hi, lc, hc = _linear_interval(a, b, c, op)
    sol = interval(lo, hi, lc, hc)
    flip = " Flip the inequality sign because the coefficient is negative." if a < 0 else ""
    text = (f"Solve the inequality {poly_text(a*x + b)} {op} {c}. "
            "Express the answer in interval notation.")
    answer = sol
    steps = [
        f"Subtract {b} from both sides: {poly_text(a*x)} {op} {c - b}.",
        f"Divide both sides by {a}.{flip}",
        f"The solution is {sol}.",
    ]
    image = None
    if out_dir is not None:
        points = [float(lo)] if lo != -sp.oo else []
        image = number_line([(float(lo) if lo != -sp.oo else -10,
                              float(hi) if hi != sp.oo else 10, lc, hc)],
                            points=points, out_path=out_dir / "ineq_linear.png",
                            x_min=-10, x_max=10)
    from src.mat133.generators.base import diagram
    return make_part(label="", text=text, marks=marks, topic="inequalities",
                     subtopic="linear", answer=answer, steps=steps,
                     answer_latex=_latex_solution(a*x + b - c, op),
                     solution_latex=[
                         sp.latex({"<=": sp.Le(a*x+b, c), "<": sp.Lt(a*x+b, c),
                                   ">=": sp.Ge(a*x+b, c), ">": sp.Gt(a*x+b, c)}[op]),
                         sp.latex({"<=": sp.Le(a*x, c-b), "<": sp.Lt(a*x, c-b),
                                   ">=": sp.Ge(a*x, c-b), ">": sp.Gt(a*x, c-b)}[op]),
                         _latex_solution(a*x + b - c, op),
                     ],
                     notes=["M1 isolate x", "A1 interval"],
                     diagram_spec=diagram(image, "Figure: solution on a number line."))


def compound(rng: random.Random, marks: float, out_dir: Path | None):
    a = nz(rng, -5, 5)
    b = nz(rng, -6, 6)
    while True:
        lo, hi = sorted(rng.sample(range(-8, 9), 2))
        if hi - lo >= 3:
            break
    # lo < a*x + b < hi; solve both ends
    endpoints = [sp.Rational(lo - b, a), sp.Rational(hi - b, a)]
    left, right = sorted(endpoints)
    sol = interval(left, right, False, False)
    text = (f"Solve the compound inequality {lo} < {poly_text(a*x + b)} < {hi}. "
            "Express the answer in interval notation.")
    answer = sol
    steps = [
        f"Subtract {b} from all parts: {lo - b} < {a}x < {hi - b}.",
        f"Divide all parts by {a}"
        + (" and reverse both inequality signs." if a < 0 else "."),
        f"The solution is {sol}.",
    ]
    image = None
    if out_dir is not None:
        image = number_line([(float(left), float(right), False, False)],
                            out_path=out_dir / "ineq_compound.png",
                            x_min=float(left) - 2, x_max=float(right) + 2)
    from src.mat133.generators.base import diagram
    return make_part(label="", text=text, marks=marks, topic="inequalities",
                     subtopic="compound", answer=answer, steps=steps,
                     answer_latex=sp.latex(sp.Interval(left, right, left_open=True, right_open=True)),
                     solution_latex=[
                         rf"{lo} < {sp.latex(a*x + b)} < {hi}",
                         rf"{lo-b} < {sp.latex(a*x)} < {hi-b}",
                         rf"{sp.latex(left)} < x < {sp.latex(right)}",
                     ],
                     notes=["M1 subtract", "M1 divide", "A1 interval"],
                     diagram_spec=diagram(image, "Figure: solution on a number line."))


def quadratic(rng: random.Random, marks: float, out_dir: Path | None):
    r1 = rng.randint(-5, 0)
    r2 = rng.randint(r1 + 2, 6)
    a = pick(rng, (-2, -1, 1, 2, 3))
    op = pick(rng, ("<=", "<", ">=", ">"))
    expr = a * (x - r1) * (x - r2)
    closed = op in ("<=", ">=")
    # sign of a(x-r1)(x-r2)
    if a > 0:
        neg = interval(r1, r2, closed, closed)
        pos_left = interval(-sp.oo, r1, False, closed)
        pos_right = interval(r2, sp.oo, closed, False)
        sol = neg if op in ("<=", "<") else union(pos_left, pos_right)
    else:
        neg_left = interval(-sp.oo, r1, False, closed)
        neg_right = interval(r2, sp.oo, closed, False)
        pos = interval(r1, r2, closed, closed)
        sol = union(neg_left, neg_right) if op in ("<=", "<") else pos
    text = f"Solve the inequality {poly_text(expr)} {op} 0."
    answer = sol
    steps = [
        f"Factor: {poly_text(expr)} = 0 gives x = {r1} and x = {r2}.",
        "Mark the critical values on a number line.",
        f"Test the sign of the leading coefficient ({a}) in each interval.",
        f"The solution is {sol}.",
    ]
    image = None
    if out_dir is not None:
        between = (a > 0 and op in ("<=", "<")) or (a < 0 and op in (">=", ">"))
        if between:
            intervals = [(r1, r2, closed, closed)]
        else:
            intervals = [(-10, r1, False, closed), (r2, 10, closed, False)]
        image = number_line(intervals, points=[r1, r2],
                            out_path=out_dir / "ineq_quadratic.png",
                            x_min=r1 - 2, x_max=r2 + 2)
    from src.mat133.generators.base import diagram
    return make_part(label="", text=text, marks=marks, topic="inequalities",
                     subtopic="quadratic", answer=answer, steps=steps,
                     answer_latex=_latex_solution(expr, op),
                     solution_latex=[
                         sp.latex(sp.Eq(expr, 0)),
                         rf"x = {r1} \quad \mathrm{{or}} \quad x = {r2}",
                         _latex_solution(expr, op),
                     ],
                     notes=["M1 factor", "A1 critical values", "A1 intervals"],
                     diagram_spec=diagram(image, "Figure: critical values."))


def _rational_solution(a, b, c, d, k, op: str):
    num = sp.expand(a * x + b - k * (c * x + d))
    den = c * x + d
    crit = []
    root = sp.solve(num, x)
    if root:
        crit.append(sp.Rational(root[0]))
    crit.append(sp.Rational(-d, c))
    crit = sorted(set(crit))
    test_points = []
    if crit[0] != -sp.oo:
        test_points.append(crit[0] - 1)
    for u, v in zip(crit, crit[1:]):
        test_points.append((u + v) / 2)
    test_points.append(crit[-1] + 1)
    keep = []
    for point in test_points:
        value = sp.simplify((a * point + b) / (c * point + d) - k)
        if (op in ("<=", "<") and value <= 0) or (op in (">=", ">") and value >= 0):
            keep.append(point)
    # build intervals from kept test points and critical values
    left = None
    intervals = []
    for i, point in enumerate(test_points):
        if point in keep:
            lo = -sp.oo if i == 0 else crit[i - 1]
            hi = sp.oo if i == len(test_points) - 1 else crit[i]
            lc = i == 0 and op in ("<=", ">=") or (i > 0 and op in ("<=", ">=")
                                                   and False)
            hc = i == len(test_points) - 1 and op in ("<=", ">=") or False
            # endpoints at finite critical values are included only if the
            # numerator (not the denominator) can be zero there.
            if lo != -sp.oo:
                lc = op in ("<=", ">=") and num.subs(x, lo) == 0
            if hi != sp.oo:
                hc = op in ("<=", ">=") and num.subs(x, hi) == 0
            intervals.append((lo, hi, bool(lc), bool(hc)))
    if not intervals:
        return "no real solution", crit
    return union(*[interval(lo, hi, lc, hc) for lo, hi, lc, hc in intervals]), crit


def rational(rng: random.Random, marks: float, out_dir: Path | None):
    a, b = nz(rng, -4, 4), nz(rng, -6, 6)
    c, d = nz(rng, -4, 4), nz(rng, -6, 6)
    k = nz(rng, -3, 3)
    op = pick(rng, ("<=", "<", ">=", ">"))
    sol, crit = _rational_solution(a, b, c, d, k, op)
    text = (f"Solve the rational inequality ({poly_text(a*x+b)})/"
            f"({poly_text(c*x+d)}) {op} {k}. Express the answer in interval notation.")
    answer = sol
    num = sp.expand(a * x + b - k * (c * x + d))
    num_root = sp.solve(num, x)
    steps = [
        "Move all terms to the left-hand side so the right-hand side is zero.",
        f"Combine over the common denominator: ({poly_text(num)})/({poly_text(c*x+d)}) {op} 0.",
        f"Critical values: numerator zero at x = "
        f"{fmt_num(num_root[0]) if num_root else 'none'}; "
        f"denominator zero at x = {fmt_num(sp.Rational(-d, c))}.",
        "Test the sign in each interval and include/exclude endpoints.",
        f"The solution is {sol}.",
    ]
    image = None
    if out_dir is not None:
        pts = [float(v) for v in crit]
        image = number_line([(-10, 10, False, False)], points=pts,
                            out_path=out_dir / "ineq_rational.png",
                            x_min=min(pts) - 3, x_max=max(pts) + 3)
    from src.mat133.generators.base import diagram
    return make_part(label="", text=text, marks=marks, topic="inequalities",
                     subtopic="rational", answer=answer, steps=steps,
                     answer_latex=_latex_solution((a*x+b)/(c*x+d) - k, op),
                     solution_latex=[
                         sp.latex({"<=": sp.Le((a*x+b)/(c*x+d) - k, 0),
                                   "<": sp.Lt((a*x+b)/(c*x+d) - k, 0),
                                   ">=": sp.Ge((a*x+b)/(c*x+d) - k, 0),
                                   ">": sp.Gt((a*x+b)/(c*x+d) - k, 0)}[op]),
                         sp.latex({"<=": sp.Le(num/(c*x+d), 0),
                                   "<": sp.Lt(num/(c*x+d), 0),
                                   ">=": sp.Ge(num/(c*x+d), 0),
                                   ">": sp.Gt(num/(c*x+d), 0)}[op]),
                         _latex_solution((a*x+b)/(c*x+d) - k, op),
                     ],
                     notes=["M1 combine", "A1 critical values", "A1 sign table",
                            "A1 interval"],
                     diagram_spec=diagram(image, "Figure: critical values."))


def interval_notation(rng: random.Random, marks: float, out_dir: Path | None):
    op = pick(rng, ("<=", "<", ">=", ">"))
    a, b, c = nz(rng, -6, 6), nz(rng, -9, 9), nz(rng, -9, 9)
    lo, hi, lc, hc = _linear_interval(a, b, c, op)
    text = (f"Write the solution of {poly_text(a*x + b)} {op} {c} in interval notation "
            "and on a number line.")
    answer = interval(lo, hi, lc, hc)
    steps = [f"Solve the inequality: {poly_text(a*x + b)} {op} {c}.",
             f"In interval notation: {answer}."]
    image = None
    if out_dir is not None:
        image = number_line([(float(lo) if lo != -sp.oo else -10,
                              float(hi) if hi != sp.oo else 10, lc, hc)],
                            out_path=out_dir / "ineq_interval.png",
                            x_min=-10, x_max=10)
    from src.mat133.generators.base import diagram
    return make_part(label="", text=text, marks=marks, topic="inequalities",
                     subtopic="interval_notation", answer=answer, steps=steps,
                     answer_latex=_latex_solution(a*x + b - c, op),
                     solution_latex=[
                         sp.latex({"<=": sp.Le(a*x+b, c), "<": sp.Lt(a*x+b, c),
                                   ">=": sp.Ge(a*x+b, c), ">": sp.Gt(a*x+b, c)}[op]),
                         sp.latex({"<=": sp.Le(a*x, c-b), "<": sp.Lt(a*x, c-b),
                                   ">=": sp.Ge(a*x, c-b), ">": sp.Gt(a*x, c-b)}[op]),
                         _latex_solution(a*x + b - c, op),
                     ],
                     notes=["M1 solve", "A1 interval"],
                     diagram_spec=diagram(image, "Figure: solution set."))


GENERATORS = [
    Generator("inequalities.linear", "inequalities", "linear", 4, linear),
    Generator("inequalities.compound", "inequalities", "compound", 4, compound),
    Generator("inequalities.quadratic", "inequalities", "quadratic", 5, quadratic),
    Generator("inequalities.rational", "inequalities", "rational", 5, rational),
    Generator("inequalities.interval_notation", "inequalities", "interval_notation", 3, interval_notation),
]
