"""Registry of all deterministic MAT133 generators."""
from __future__ import annotations

import random
from pathlib import Path

from src.mat133.generators import (
    absolute_value,
    circles,
    circular_measure,
    complex_numbers,
    exp_log,
    functions,
    inequalities,
    lines,
    parabolas,
    polynomials,
    system_inequalities,
    systems,
    triangles,
    trigonometry,
)
from src.mat133.generators.base import Generator

MODULES = (
    functions, inequalities, absolute_value,
    lines, circles, parabolas,
    complex_numbers, systems, system_inequalities, polynomials,
    exp_log, trigonometry, circular_measure, triangles,
)

REGISTRY: dict[str, Generator] = {}
for module in MODULES:
    for generator in module.GENERATORS:
        if generator.id in REGISTRY:
            raise RuntimeError(f"duplicate generator id {generator.id}")
        REGISTRY[generator.id] = generator

BY_TOPIC: dict[str, list[Generator]] = {}
for generator in REGISTRY.values():
    BY_TOPIC.setdefault(generator.topic, []).append(generator)

PRIORITY_GROUPS = {
    1: ("functions", "inequalities", "absolute_value"),
    2: ("lines", "circles", "parabolas"),
    3: ("complex_numbers", "systems_of_equations", "systems_of_inequalities",
        "polynomials", "exponential_logarithmic", "trigonometry",
        "circular_measure", "triangle_geometry"),
}


def generate(generator_id: str, seed: int = 1, marks: float | None = None,
             out_dir: Path | None = None):
    generator = REGISTRY[generator_id]
    return generator.generate(random.Random(seed), marks=marks,
                              out_dir=out_dir)


def generate_topic(topic: str, seed: int = 1,
                   out_dir: Path | None = None):
    """Generate one part for every subtopic generator under a topic."""
    parts = []
    for index, generator in enumerate(BY_TOPIC.get(topic, [])):
        parts.append(generator.generate(
            random.Random(seed * 1000 + index), out_dir=out_dir))
    return parts


def generate_priority(priority: int, seed: int = 1,
                      out_dir: Path | None = None):
    """Return {topic: [parts]} for every generator in a priority group."""
    result = {}
    for topic in PRIORITY_GROUPS[priority]:
        result[topic] = generate_topic(topic, seed=seed, out_dir=out_dir)
    return result


def generators_for_topic(topic: str) -> list[Generator]:
    return list(BY_TOPIC.get(topic, []))
