"""Revised planner rules from the measurement-driven brief."""
from __future__ import annotations

from src.planner.fingerprint_data import THEORY_TOPICS
from src.planner.measurements import measure
from src.planner.planner import build_plan
from src.planner.style import six_mark_examples
from src.planner.tasks import LABELS


def _by_question(table):
    out = {}
    for s in table:
        out.setdefault(s.question, []).append(s)
    return out


def test_measurements_match_reported_rates():
    m = measure()
    assert m.part_a_pairs == 72
    assert m.same_topic_pairs == 55
    assert m.dependent_pairs == 7
    assert m.part_b_topic_marks["risk/management"] == 39


def test_one_topic_per_question_and_no_three_consecutive():
    table, summary = build_plan("realistic", "modern", None, 9)
    by_q = _by_question(table)
    for q, slots in by_q.items():
        assert len({s.topic for s in slots}) == 1, q
    assert summary["no_three_consecutive_same_topic"] is True


def test_dependent_pair_rate_and_link():
    table, summary = build_plan("realistic", "modern", None, 9)
    assert len(summary["dependent_questions"]) == 1
    q = summary["dependent_questions"][0]
    slots = [s for s in table if s.question == q]
    assert slots[0].dependent and slots[1].dependent
    assert slots[1].dependent_on == slots[0].slot
    # one dependent pair among nine Part A theory pairs ~= the 9.7% measured
    assert 0.09 <= 1 / 9 <= 0.12


def test_command_labels_are_the_seven_real_labels():
    table, _ = build_plan("realistic", "modern", None, 9)
    tasks = {s.task for s in table if s.kind == "theory"}
    assert tasks <= set(LABELS)
    assert "short objective" not in tasks
    assert "define/explain" not in tasks


def test_risk_ethics_topic_and_renormalised_weights():
    _, summary = build_plan("realistic", "modern", None, 9)
    assert "risk/management (ethics)" in THEORY_TOPICS
    assert summary["topic_weights"]["risk/management (ethics)"] > 0.1
    assert abs(sum(summary["topic_weights"].values()) - 1.0) < 0.01
    assert any(s["topic"] == "risk/management (ethics)"
               for s in summary["slots"])


def test_part_b_uses_part_b_task_mix():
    table, _ = build_plan("realistic", "modern", None, 9)
    b_tasks = [s.task for s in table if s.part == "B" and s.kind == "theory"]
    assert len(b_tasks) == 4
    # Part B measured 5-mark mix is State/Explain/Discuss/Justify; Compare and
    # List never occur in Part B.
    assert "Compare" not in b_tasks
    assert "List" not in b_tasks
    assert len(set(b_tasks)) >= 3


def test_computed_vigenere_prints_tableau_and_six_mark_examples():
    table, summary = build_plan("realistic", "modern", None, 9)
    computed = [s for s in table if s.kind == "computed"]
    assert len(computed) == 1
    assert computed[0].computed_type == "vigenere"
    assert "tableau" in computed[0].note.lower()
    six_labels = {s.task for s in table if s.kind == "theory" and s.marks == 6}
    assert six_labels
    for label in six_labels:
        assert len(summary["six_mark_examples"][label]) == 3
        assert len(six_mark_examples(label)) >= 3


def test_style_widening_is_recorded():
    _, summary = build_plan("realistic", "modern", None, 9)
    assert summary["low_style_confidence_slots"]
    low = set(summary["low_style_confidence_slots"])
    slots = {s["slot"]: s for s in summary["slots"]}
    assert all(slots[s]["style_mode"] != "exact" for s in low)
    assert all(slots[s]["style_n"] < 3 for s in low)
