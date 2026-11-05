"""CSC429 stage-6 deterministic generators."""
from __future__ import annotations

import math
import struct

from src.subjects import plugins
from src.subjects.csc429 import generators
from src.subjects.csc429.planner import build_plan
from src.subjects.registry import get_subject


def _paper(seed: int = 1) -> dict:
    return generators.generate_paper(build_plan(seed))


def test_seed_1_structure_and_marks():
    plan = build_plan(1)
    paper = generators.generate_paper(plan)
    assert paper["total_marks"] == 100
    assert paper["part_marks"] == {"A": 80, "B": 20}
    assert paper["question_count"] == 11
    assert generators.validate_paper(paper, plan) == []
    part_a = [q for q in paper["questions"] if q["part"] == "A"]
    part_b = [q for q in paper["questions"] if q["part"] == "B"]
    assert len(part_a) == 10 and len(part_b) == 1
    assert [q["marks"] for q in part_a] == [
        5, 5, 5, 5, 10, 10, 10, 10, 10, 10]
    assert part_b[0]["marks"] == 20
    assert part_b[0]["topic"] == "instruction_set_assembly"
    assert sum(p["marks"] for p in part_b[0]["parts"]) == 20
    figures = [q for q in paper["questions"] if q.get("figure")]
    assert len(figures) == 3
    assert {q["figure"]["kind"] for q in figures} == {
        "von_neumann", "cpu_datapath", "cache_mapping"}
    assert all("{figure}" in q["stem"] for q in figures)
    assert not any(
        marker in str(paper).lower()
        for marker in ("todo", "tbd", "placeholder", "not implemented"))


def test_all_20_seeds_validate_and_cover_every_generator():
    coverage: set[str] = set()
    figure_kinds: set[str] = set()
    for seed in range(1, 21):
        plan = build_plan(seed)
        paper = generators.generate_paper(plan)
        assert generators.validate_paper(paper, plan) == []
        assert paper == generators.generate_paper(plan)
        coverage.update(q["generator_id"] for q in paper["questions"])
        figures = [q for q in paper["questions"] if q.get("figure")]
        assert len(figures) == 3
        figure_kinds.update(q["figure"]["kind"] for q in figures)
        for question in figures:
            assert "{figure}" in question["stem"]
            assert question["figure"].get("caption")
    assert coverage == set(generators.GENERATOR_IDS)
    assert figure_kinds == set(generators.FIGURE_KINDS)


def test_data_representation_answers_are_recomputed():
    seen: set[tuple[int, str]] = set()
    for seed in range(1, 21):
        paper = _paper(seed)
        for question in paper["questions"]:
            if question["generator_id"] != "csc429.data_representation":
                continue
            v = question["verification"]
            kind = v["kind"]
            seen.add((question["marks"], kind))
            answers = [part["answer"] for part in question["parts"]]
            if kind == "base":
                assert format(v["dec"], "08b") in answers[0]
                assert format(v["binary_value"], "08b") in answers[1]
                assert str(v["binary_value"]) in answers[1]
            elif kind == "signed" and "left" in v:
                assert v["result"] == v["left"] - v["right"]
                assert -128 <= v["result"] <= 127
                assert v["left"] < 0 or v["right"] < 0
                sign = "1" if v["result"] < 0 else "0"
                assert sign + format(abs(v["result"]), "07b") in answers[0]
                assert format(v["result"] & 0xFF, "08b") in answers[1]
            elif kind == "signed":
                value = v["value"]
                sign = "1" if value < 0 else "0"
                assert v["sign_magnitude"] == sign + format(abs(value), "07b")
                assert v["twos"] == format(value & 0xFF, "08b")
                assert v["sign_magnitude"] in answers[0]
                assert v["twos"] in answers[1]
            elif kind == "ieee":
                assert v["hex"] == struct.pack(">f", v["value"]).hex().upper()
                assert math.isclose(
                    struct.unpack(
                        ">f", bytes.fromhex(v["hex"]))[0], v["value"])
                assert v["hex"] in answers[0]
            elif kind == "bases":
                values = v["values"]
                assert format(values[0], "08b") in answers[0]
                assert format(values[1], "02X") in answers[1]
                assert format(values[2], "o") in answers[2]
                assert str(values[3]) in answers[3]
    assert {
        (5, "base"), (5, "signed"), (5, "ieee"),
        (10, "bases"), (10, "signed"), (10, "ieee"),
    } <= seen


def test_assembly_programs_are_independently_verified():
    paper = _paper(1)
    b1 = next(q for q in paper["questions"] if q["part"] == "B")
    values = b1["test_values"]
    expected = eval(b1["expression"], {}, values)  # template-owned expression
    assert math.isclose(b1["expected_value"], expected)
    assert math.isclose(
        generators._simulate_zero(b1["programs"]["zero"], values), expected)
    assert math.isclose(
        generators._simulate_one(b1["programs"]["one"], values), expected)
    assert math.isclose(
        generators._simulate_three(b1["programs"]["three"], values), expected)


def test_enabled_generators_match_labels_and_capabilities():
    subject = get_subject("CSC429")
    enabled = set(subject.enabled_computed_generators)
    labels = set(plugins.resolve(
        "src.subjects.csc429.plugin:generator_labels")())
    assert enabled == labels == set(generators.GENERATOR_IDS)
    assert subject.capabilities["generation"] == "deterministic"
    assert subject.capabilities["needs_llm"] is False
    assert subject.capabilities["deterministic"] is True
    assert subject.has_placeholders is False
    assert subject.capabilities["public_scheme_requires_quote_marker"] is False
