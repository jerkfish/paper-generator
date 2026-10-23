"""Canonical MAT133 taxonomy used by the question log and generators.

The taxonomy is paper-derived: the topics and subtopics below were identified
from the 41 MAT133 past papers in ``data/papers/MAT133``.  The ids are stable
and are used in JSON data, generators and template builders.  Labels may be
edited for display, but ids must not change once question-log data references
them.
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Subtopic:
    id: str
    label: str
    description: str = ""


@dataclass(frozen=True)
class Topic:
    id: str
    label: str
    priority: int
    description: str
    subtopics: tuple[Subtopic, ...] = field(default_factory=tuple)


TOPICS: tuple[Topic, ...] = (
    Topic(
        "functions", "Functions", 1,
        "Domain and range, composition, inverse functions, piecewise "
        "definitions, transformations and function arithmetic.",
        (
            Subtopic("domain_range", "Domain and range"),
            Subtopic("composition", "Composition of functions"),
            Subtopic("inverse", "Inverse functions"),
            Subtopic("piecewise", "Piecewise-defined functions"),
            Subtopic("transformations", "Graph transformations"),
            Subtopic("even_odd", "Even and odd functions"),
            Subtopic("function_arithmetic", "Function arithmetic"),
            Subtopic("graph", "Graphing functions"),
        ),
    ),
    Topic(
        "inequalities", "Inequalities", 1,
        "Linear, compound, quadratic and rational inequalities, including "
        "interval notation and number-line solutions.",
        (
            Subtopic("linear", "Linear inequality"),
            Subtopic("compound", "Compound inequality"),
            Subtopic("quadratic", "Quadratic inequality"),
            Subtopic("rational", "Rational inequality"),
            Subtopic("interval_notation", "Interval notation"),
        ),
    ),
    Topic(
        "absolute_value", "Absolute Value", 1,
        "Absolute-value equations, inequalities and graphs.",
        (
            Subtopic("equation", "Absolute-value equation"),
            Subtopic("inequality", "Absolute-value inequality"),
            Subtopic("graph", "Absolute-value graph"),
        ),
    ),
    Topic(
        "lines", "Lines", 2,
        "Straight-line equations: slope, intercepts, parallel and "
        "perpendicular lines, and lines through given points.",
        (
            Subtopic("through_points", "Line through points"),
            Subtopic("parallel_perpendicular", "Parallel/perpendicular line"),
            Subtopic("intercepts", "Intercepts and slope"),
        ),
    ),
    Topic(
        "circles", "Circles", 2,
        "Circle equations, centre-radius form, general-to-standard form and "
        "graphing.",
        (
            Subtopic("standard_form", "Equation of a circle"),
            Subtopic("general_to_standard", "General to standard form"),
            Subtopic("diameter_endpoints", "Circle from diameter endpoints"),
            Subtopic("graph", "Sketch a circle"),
        ),
    ),
    Topic(
        "parabolas", "Parabolas", 2,
        "Standard-form parabolas, vertex, focus, directrix and graphs.",
        (
            Subtopic("standard_form", "Standard form"),
            Subtopic("vertex_focus_directrix", "Vertex, focus and directrix"),
            Subtopic("graph", "Sketch a parabola"),
        ),
    ),
    Topic(
        "complex_numbers", "Complex Numbers", 3,
        "Arithmetic in a + bi form, conjugates, division, powers and "
        "modulus/argument.",
        (
            Subtopic("arithmetic", "Arithmetic in standard form"),
            Subtopic("division", "Division and rationalising"),
            Subtopic("powers", "Powers of i / powers of complex numbers"),
            Subtopic("modulus_argument", "Modulus and argument"),
        ),
    ),
    Topic(
        "systems_of_equations", "Systems of Equations", 3,
        "Simultaneous linear systems in two or three variables and nonlinear "
        "systems.",
        (
            Subtopic("linear_2var", "Linear system in two variables"),
            Subtopic("linear_3var", "Linear system in three variables"),
            Subtopic("nonlinear", "Nonlinear simultaneous system"),
        ),
    ),
    Topic(
        "systems_of_inequalities", "Systems of Inequalities", 3,
        "Graphing systems of inequalities and shading or identifying the "
        "feasible region.",
        (
            Subtopic("graph_feasible_region", "Graph the feasible region"),
            Subtopic("write_from_region", "Write inequalities from a region"),
        ),
    ),
    Topic(
        "polynomials", "Polynomials", 3,
        "Long and synthetic division, factor and remainder theorems, and "
        "factorisation.",
        (
            Subtopic("long_division", "Long division"),
            Subtopic("synthetic_division", "Synthetic division"),
            Subtopic("factor_theorem", "Factor theorem"),
            Subtopic("remainder_theorem", "Remainder theorem"),
            Subtopic("factorization", "Complete factorisation"),
        ),
    ),
    Topic(
        "exponential_logarithmic", "Exponential and Logarithmic Equations", 3,
        "Exponential equations, logarithmic equations and logarithmic laws.",
        (
            Subtopic("exponential_equation", "Exponential equation"),
            Subtopic("log_equation", "Logarithmic equation"),
            Subtopic("log_laws", "Logarithm laws"),
        ),
    ),
    Topic(
        "trigonometry", "Trigonometry", 3,
        "Trigonometric equations, identities, exact values, graphs and "
        "compound/double-angle formulae.",
        (
            Subtopic("equation", "Trigonometric equation"),
            Subtopic("identity", "Trigonometric identity"),
            Subtopic("exact_value", "Exact trigonometric value"),
            Subtopic("graph", "Trigonometric graph"),
            Subtopic("compound_double_angle", "Compound/double angle"),
        ),
    ),
    Topic(
        "circular_measure", "Circular Measure", 3,
        "Radian measure, arc length, sector area and perimeter of composite "
        "circular figures.",
        (
            Subtopic("arc_length", "Arc length"),
            Subtopic("sector_area", "Sector area"),
            Subtopic("perimeter", "Perimeter of a sector/region"),
            Subtopic("radians", "Radian measure and angles"),
        ),
    ),
    Topic(
        "triangle_geometry", "Triangle Geometry", 3,
        "Sine rule, cosine rule, triangle area, solving triangles and "
        "composite figures.",
        (
            Subtopic("solve_triangle", "Solve a triangle"),
            Subtopic("sine_rule", "Sine rule"),
            Subtopic("cosine_rule", "Cosine rule"),
            Subtopic("area", "Area of a triangle"),
            Subtopic("combined_figures", "Composite geometric figures"),
        ),
    ),
    Topic(
        "other", "Other", 9,
        "Any graded question that does not fit the paper-derived topics "
        "above; requires review before a generator is written.",
        (Subtopic("other", "Other"),),
    ),
)

TOPIC_BY_ID = {topic.id: topic for topic in TOPICS}
TOPIC_IDS = tuple(topic.id for topic in TOPICS)
SUBTOPIC_IDS = {
    topic.id: tuple(sub.id for sub in topic.subtopics) for topic in TOPICS
}
PRIORITY_1 = tuple(t.id for t in TOPICS if t.priority == 1)
PRIORITY_2 = tuple(t.id for t in TOPICS if t.priority == 2)
PRIORITY_3 = tuple(t.id for t in TOPICS if t.priority == 3)


def topic_label(topic_id: str) -> str:
    topic = TOPIC_BY_ID.get(topic_id)
    return topic.label if topic else topic_id.replace("_", " ").title()


def priority_of(topic_id: str) -> int:
    topic = TOPIC_BY_ID.get(topic_id)
    return topic.priority if topic else 9


def taxonomy_dict() -> dict:
    return {
        "subject": "MAT133",
        "version": 1,
        "topics": [
            {
                "id": topic.id,
                "label": topic.label,
                "priority": topic.priority,
                "description": topic.description,
                "subtopics": [
                    {"id": sub.id, "label": sub.label,
                     "description": sub.description}
                    for sub in topic.subtopics
                ],
            }
            for topic in TOPICS
        ],
    }
