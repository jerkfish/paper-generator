"""Deterministic MAT133 paper planner.

MAT133 has no lecture decks and no LLM stage.  A paper is assembled from the
57 paper-derived computed generators: five questions follow the structure
observed in the 41 past papers (inequalities/absolute value, functions and
coordinate geometry, complex numbers/algebra, systems/coordinate geometry,
trigonometry and geometry).  Every choice is driven by the seed, so the same
seed always produces the same paper and marking scheme.
"""
from __future__ import annotations

import random
from datetime import datetime, timezone

from src.mat133.generators.registry import REGISTRY
from src.mat133.models import Mat133Paper, Mat133Question

PLANNER_VERSION = 1

# Short labels used by the Library table.  These are the MAT133 counterparts
# of the CSC662 TOPIC_SHORT map in src.app.jobs.
TOPIC_SHORT = {
    "functions": "FUN",
    "inequalities": "INQ",
    "absolute_value": "ABS",
    "lines": "LIN",
    "circles": "CIR",
    "parabolas": "PAR",
    "complex_numbers": "CPX",
    "systems_of_equations": "SYS",
    "systems_of_inequalities": "SIQ",
    "polynomials": "POL",
    "exponential_logarithmic": "EXP",
    "trigonometry": "TRG",
    "circular_measure": "CME",
    "triangle_geometry": "TRI",
    "other": "OTH",
}

TOPIC_TITLES = {
    "functions": "Functions",
    "inequalities": "Inequalities",
    "absolute_value": "Absolute Value",
    "lines": "Lines",
    "circles": "Circles",
    "parabolas": "Parabolas",
    "complex_numbers": "Complex Numbers",
    "systems_of_equations": "Systems of Equations",
    "systems_of_inequalities": "Systems of Inequalities",
    "polynomials": "Polynomials",
    "exponential_logarithmic": "Exponential and Logarithmic Functions",
    "trigonometry": "Trigonometry",
    "circular_measure": "Circular Measure",
    "triangle_geometry": "Triangle Geometry",
    "other": "Other",
}

# Human-readable labels for the public subject page.  Raw generator ids are
# still available to tooling; this is presentation only.
GENERATOR_LABELS = {
    "absolute_value.equation": "Absolute-value equation",
    "absolute_value.graph": "Absolute-value graph",
    "absolute_value.inequality": "Absolute-value inequality",
    "circles.diameter_endpoints": "Circle from diameter",
    "circles.general_to_standard": "General to standard circle",
    "circles.graph": "Circle graph",
    "circles.standard_form": "Standard circle",
    "circular_measure.arc_length": "Arc length",
    "circular_measure.perimeter": "Sector perimeter",
    "circular_measure.radians": "Radians and degrees",
    "circular_measure.sector_area": "Sector area",
    "complex_numbers.arithmetic": "Complex arithmetic",
    "complex_numbers.division": "Complex division",
    "complex_numbers.modulus_argument": "Modulus and argument",
    "complex_numbers.powers": "Powers of complex numbers",
    "exponential_logarithmic.exponential_equation": "Exponential equation",
    "exponential_logarithmic.log_equation": "Logarithmic equation",
    "exponential_logarithmic.log_laws": "Logarithm laws",
    "functions.composition": "Composition",
    "functions.domain_range": "Domain and range",
    "functions.even_odd": "Even and odd functions",
    "functions.function_arithmetic": "Function arithmetic",
    "functions.graph": "Function graph",
    "functions.inverse": "Inverse function",
    "functions.piecewise": "Piecewise function",
    "functions.transformations": "Graph transformations",
    "inequalities.compound": "Compound inequality",
    "inequalities.interval_notation": "Interval notation",
    "inequalities.linear": "Linear inequality",
    "inequalities.quadratic": "Quadratic inequality",
    "inequalities.rational": "Rational inequality",
    "lines.intercepts": "Intercepts",
    "lines.parallel_perpendicular": "Parallel and perpendicular lines",
    "lines.through_points": "Line through two points",
    "parabolas.graph": "Parabola graph",
    "parabolas.standard_form": "Standard parabola",
    "parabolas.vertex_focus_directrix": "Vertex, focus and directrix",
    "polynomials.factor_theorem": "Factor theorem",
    "polynomials.factorization": "Factorisation",
    "polynomials.long_division": "Long division",
    "polynomials.remainder_theorem": "Remainder theorem",
    "polynomials.synthetic_division": "Synthetic division",
    "systems_of_equations.linear_2var": "Linear system in two variables",
    "systems_of_equations.linear_3var": "Linear system in three variables",
    "systems_of_equations.nonlinear": "Nonlinear system",
    "systems_of_inequalities.graph_feasible_region": "Feasible region",
    "systems_of_inequalities.write_from_region": "Inequalities from a region",
    "triangle_geometry.area": "Triangle area",
    "triangle_geometry.combined_figures": "Combined figures",
    "triangle_geometry.cosine_rule": "Cosine rule",
    "triangle_geometry.sine_rule": "Sine rule",
    "triangle_geometry.solve_triangle": "Solving a triangle",
    "trigonometry.compound_double_angle": "Compound and double angles",
    "trigonometry.equation": "Trigonometric equation",
    "trigonometry.exact_value": "Exact trigonometric values",
    "trigonometry.graph": "Trigonometric graph",
    "trigonometry.identity": "Trigonometric identity",
}

FUNCTION_POOL = [
    "functions.domain_range",
    "functions.inverse",
    "functions.composition",
    "functions.piecewise",
    "functions.transformations",
    "functions.even_odd",
    "functions.function_arithmetic",
    "functions.graph",
]
INEQUALITY_POOL = [
    "inequalities.rational",
    "inequalities.quadratic",
    "inequalities.compound",
    "inequalities.linear",
    "inequalities.interval_notation",
]
ABSOLUTE_POOL = [
    "absolute_value.inequality",
]
ABSOLUTE_SECOND_POOL = [
    "absolute_value.equation",
    "absolute_value.graph",
]
COORDINATE_POOL = [
    "lines.through_points",
    "lines.parallel_perpendicular",
    "lines.intercepts",
    "circles.standard_form",
    "circles.general_to_standard",
    "circles.diameter_endpoints",
    "circles.graph",
    "parabolas.standard_form",
    "parabolas.vertex_focus_directrix",
    "parabolas.graph",
]
COMPLEX_POOL = [
    "complex_numbers.arithmetic",
    "complex_numbers.division",
]
COMPLEX_SECOND_POOL = [
    "complex_numbers.modulus_argument",
    "complex_numbers.powers",
]
ALGEBRA_POOL = [
    "polynomials.remainder_theorem",
    "polynomials.factor_theorem",
    "polynomials.long_division",
    "polynomials.synthetic_division",
    "polynomials.factorization",
    "exponential_logarithmic.log_laws",
    "exponential_logarithmic.log_equation",
    "exponential_logarithmic.exponential_equation",
]
SYSTEMS_POOL = [
    "systems_of_equations.linear_2var",
    "systems_of_equations.linear_3var",
    "systems_of_equations.nonlinear",
    "systems_of_inequalities.graph_feasible_region",
    "systems_of_inequalities.write_from_region",
]
TRIG_POOL = [
    "trigonometry.equation",
    "trigonometry.identity",
    "trigonometry.exact_value",
    "trigonometry.graph",
    "trigonometry.compound_double_angle",
]
CIRCULAR_POOL = [
    "circular_measure.arc_length",
    "circular_measure.sector_area",
    "circular_measure.perimeter",
    "circular_measure.radians",
]
TRIANGLE_POOL = [
    "triangle_geometry.sine_rule",
    "triangle_geometry.cosine_rule",
    "triangle_geometry.area",
    "triangle_geometry.solve_triangle",
    "triangle_geometry.combined_figures",
]

# One tuple per question: (pool, repeated?).  A repeated slot draws a second
# distinct generator from the same pool.  This mirrors the paper structure
# seen in the 41-paper question log.
QUESTION_POOLS: list[list[tuple[list[str], bool]]] = [
    [(INEQUALITY_POOL, False), (ABSOLUTE_POOL, False),
     (ABSOLUTE_SECOND_POOL, False)],
    [(FUNCTION_POOL, False), (FUNCTION_POOL, True), (COORDINATE_POOL, False)],
    [(COMPLEX_POOL, False), (COMPLEX_SECOND_POOL, False),
     (ALGEBRA_POOL, False)],
    [(SYSTEMS_POOL, False), (SYSTEMS_POOL, True), (COORDINATE_POOL, False)],
    [(TRIG_POOL, False), (CIRCULAR_POOL, False), (TRIANGLE_POOL, False)],
]

QUESTION_TITLES = [
    "Inequalities and absolute value",
    "Functions and coordinate geometry",
    "Complex numbers and algebra",
    "Systems and coordinate geometry",
    "Trigonometry and geometry",
]


def _choose(rng: random.Random, pool: list[str], used: set[str],
            offset: int = 0) -> str:
    candidates = [item for item in pool if item not in used]
    if not candidates:
        candidates = list(pool)
    if offset:
        chosen = candidates[offset % len(candidates)]
    else:
        chosen = candidates[rng.randrange(len(candidates))]
    used.add(chosen)
    return chosen


def _month_name(now: datetime) -> str:
    return now.strftime("%B").upper()


def build_paper(seed: int, *, year: int | None = None,
                month: str | None = None, out_dir=None) -> tuple[Mat133Paper, dict]:
    """Build one deterministic MAT133 paper.

    ``out_dir`` is the directory for diagrams and other generated figures.
    The same seed and directory produce identical files.
    """
    if int(seed) < 1:
        raise ValueError("seed must be a positive integer")
    seed = int(seed)
    now = datetime.now(timezone.utc)
    year = int(year or now.year)
    month = (month or _month_name(now)).upper()
    rng = random.Random(seed * 7919 + 133)
    used: set[str] = set()
    questions: list[Mat133Question] = []
    generator_ids: list[str] = []
    for number, pools in enumerate(QUESTION_POOLS, 1):
        parts = []
        for index, (pool, _repeat) in enumerate(pools):
            # Rotate the algebra slot across seeds so the 20-seed Library
            # exercises every generator in the polynomial/exp pool.
            offset = seed if (number == 3 and index == 2) else 0
            generator_id = _choose(rng, pool, used, offset=offset)
            generator = REGISTRY[generator_id]
            part_dir = None
            if out_dir is not None:
                from pathlib import Path
                part_dir = Path(out_dir) / f"q{number}{chr(97 + index)}"
            part = generator.generate(
                random.Random(seed * 1009 + number * 37 + index),
                out_dir=part_dir)
            part.label = chr(97 + index)
            parts.append(part)
            generator_ids.append(generator_id)
        questions.append(Mat133Question(number=number, parts=parts))
    paper = Mat133Paper(
        month=month, year=year, duration="2 HOURS", questions=questions,
        seed=seed, generator_notes=generator_ids,
    )
    topic_marks: dict[str, float] = {}
    for question in questions:
        for part in question.parts:
            topic_marks[part.topic] = (topic_marks.get(part.topic, 0)
                                       + float(part.marks))
    metadata = {
        "planner_version": PLANNER_VERSION,
        "subject": "MAT133",
        "seed": seed,
        "mode": "realistic",
        "topic_marks": {key: int(value) if float(value).is_integer() else value
                        for key, value in sorted(topic_marks.items())},
        "generator_ids": generator_ids,
        "accepted": sum(len(question.parts) for question in questions),
        "placeholders": 0,
        "total_marks": paper.total_marks,
        "question_count": len(questions),
    }
    return paper, metadata
