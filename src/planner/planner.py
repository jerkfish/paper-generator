"""Slot-table planner for the mock paper.

Modes:
  realistic  - computed marks sampled from the 10 clean modern papers
               (mean 4.0 marks/paper); the rest theory.
  practice   - --computed-marks N (default 22).

Styles:
  modern (default) - Caesar, Vigenere, columnar 3x4, columnar keyword,
                     rail fence, OTP (26-letter), ACM.
  older            - adds Playfair and affine; never allowed in realistic mode.

Planner rules implemented here:
  * one topic per question; (a) and (b) share it;
  * dependent (a)->(b) pairs at the measured Part A rate (7/72 = 9.7%);
  * no more than two consecutive questions with the same topic;
  * Part B command words follow the measured Part B distribution;
  * theory topics use the modern marks share with risk/management (ethics)
    added and renormalised;
  * command words are the seven real labels, never "short objective";
  * style examples widen exact -> same topic/any command -> same command/any
    topic; exact n < 3 is labelled low style confidence.

Run:
  uv run python -m src.planner.planner --mode realistic
"""
from __future__ import annotations

import argparse
import json
import random
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from functools import lru_cache

from src.config import OUTPUTS_DIR
from src.planner.calibration import CALIBRATIONS, target_size
from src.planner.fingerprint_data import (
    EXCLUDED_TOPICS,
    THEORY_TOPICS,
    ModernStats,
    load_modern_stats,
    load_part_b_stats,
)
from src.planner.measurements import measure
from src.planner.style import six_mark_examples, style_examples
from src.planner.tasks import LABELS, command_word

SLOT_TEMPLATE: list[tuple[str, int]] = (
    [(f"A{i}a", 2) for i in range(1, 11)]
    + [(f"A{i}b", 6) for i in range(1, 11)]
    + [("B1a", 5), ("B1b", 5), ("B2a", 5), ("B2b", 5)]
)
PAPER_ORDER = (
    [f"A{i}{sub}" for i in range(1, 11) for sub in ("a", "b")]
    + ["B1a", "B1b", "B2a", "B2b"]
)
QUESTION_ORDER = [f"A{i}" for i in range(1, 11)] + ["B1", "B2"]
MODERN_TYPES = ["vigenere", "acm", "columnar_keyword", "rail_fence",
                "otp", "caesar", "columnar_3x4"]
OLDER_TYPES = ["vigenere", "playfair", "affine", "acm", "columnar_keyword",
               "rail_fence", "otp", "caesar", "columnar_3x4"]
TYPE_LABEL = {
    "vigenere": "Vigenere",
    "acm": "ACM/ACL",
    "columnar_keyword": "columnar (keyword)",
    "columnar_3x4": "columnar (3 x 4)",
    "rail_fence": "rail fence",
    "otp": "OTP/Vernam (26-letter; DEC 2019 verified; slide 17 inconsistent)",
    "caesar": "Caesar",
    "playfair": "Playfair (older, not in current slides)",
    "affine": "affine (older, not in current slides)",
}
ACM_SCOPE = {6: "matrix only (6 marks)", 9: "matrix + ACL + CL"}


@dataclass
class Slot:
    slot: str
    marks: int
    kind: str            # computed | theory
    question: str
    part: str            # A | B
    topic: str
    task: str
    computed_type: str = ""
    target: str = ""
    acm_scope: str = ""
    style_n: int = 0
    style_n_widened: int = 0
    style_mode: str = ""
    style_examples: list[dict] = field(default_factory=list)
    low_style_confidence: bool = False
    dependent: bool = False
    dependent_on: str = ""
    note: str = ""


def _paper_order() -> list[str]:
    return PAPER_ORDER


def _question_of(slot: str) -> str:
    m = re.match(r"^([AB]\d+)", slot)
    if not m:
        raise ValueError(slot)
    return m.group(1)


def _computed_mark_counts(target: int) -> tuple[int, int]:
    """Return (six_count, two_count) summing to target; adjust odd targets."""
    if target < 0:
        raise ValueError("computed marks cannot be negative")
    if target % 2:
        target -= 1  # only 2/6-mark slots exist; report the adjustment
    six = min(target // 6, 10)
    rem = target - six * 6
    while rem not in (0, 2, 4) and six > 0:
        six -= 1
        rem = target - six * 6
    if rem not in (0, 2, 4):
        raise ValueError(f"cannot make {target} from 2/6-mark slots")
    twos = rem // 2
    if twos > 10:
        raise ValueError(f"cannot make {target}: too many 2-mark slots")
    return six, twos


def _choose_types(count: int, marks: int, style: str,
                  used: set[str], rng: random.Random) -> list[str]:
    pool = OLDER_TYPES if style == "older" else MODERN_TYPES
    if marks == 2:
        pool = ["caesar", "vigenere", "columnar_3x4", "rail_fence"]
    elif marks == 5:
        pool = [t for t in pool if t != "acm"]
    fresh = [t for t in pool if t not in used]
    chosen: list[str] = []
    for _ in range(count):
        if fresh:
            t = fresh.pop(0)
        else:
            t = rng.choice(pool)
        chosen.append(t)
        used.add(t)
    return chosen


def _largest_remainder(weights: dict[str, float], total: int,
                      keys: list[str] | None = None) -> dict[str, int]:
    keys = keys or THEORY_TOPICS
    total_w = sum(weights.get(t, 0) for t in keys) or 1
    raw = {t: weights.get(t, 0) / total_w * total for t in keys}
    out = {t: int(raw[t]) for t in keys}
    left = total - sum(out.values())
    for t in sorted(keys, key=lambda x: raw[x] - out[x], reverse=True)[:left]:
        out[t] += 1
    return out


def _weighted_sample_without_replacement(weights: dict[str, int | float],
                                         k: int,
                                         rng: random.Random) -> list[str]:
    pool = [t for t, w in weights.items() if w > 0]
    out: list[str] = []
    while pool and len(out) < k:
        chosen = rng.choices(pool, weights=[weights[t] for t in pool])[0]
        out.append(chosen)
        pool.remove(chosen)
    for t in THEORY_TOPICS:
        if len(out) >= k:
            break
        if t not in out:
            out.append(t)
    return out[:k]


def _consecutive_ok(topics: list[str]) -> bool:
    run = 1
    for i in range(1, len(topics)):
        if topics[i] == topics[i - 1]:
            run += 1
            if run > 2:
                return False
        else:
            run = 1
    return True


def _assign_question_topics(stats: ModernStats, theory_slots: list[Slot],
                            computed_topics: dict[str, str],
                            rng: random.Random) -> tuple[dict[str, str],
                                                         dict[str, int]]:
    """Assign a topic to every question and return (qtopics, Part B marks)."""
    qtopics: dict[str, str] = dict(computed_topics)
    part_b = load_part_b_stats()
    pb_weights = {t: part_b["topic_marks"].get(t, 0)
                  for t in THEORY_TOPICS}
    if not any(pb_weights.values()):
        pb_weights = dict(stats.topic_marks)
    # Two Part B questions: use the two largest measured Part B topic shares
    # rather than a two-draw sample that can land on a low-probability pair.
    ranked = sorted(THEORY_TOPICS, key=lambda t: (-pb_weights[t], t))
    b_topics = ranked[:2]
    rng.shuffle(b_topics)
    for q, topic in zip(["B1", "B2"], b_topics):
        qtopics[q] = topic

    theory_total = sum(s.marks for s in theory_slots)
    classical_theory = sum(s.marks for s in theory_slots
                           if s.topic == "classical ciphers")
    target = _largest_remainder(stats.topic_weights,
                                theory_total - classical_theory)
    pb_marks: dict[str, int] = defaultdict(int)
    for topic in b_topics:
        pb_marks[topic] += 10
    residual = {t: max(0, target[t] - pb_marks.get(t, 0))
                for t in THEORY_TOPICS}
    if sum(residual.values()) == 0:
        residual = {t: stats.topic_weights[t] for t in THEORY_TOPICS}

    a_theory = [q for q in QUESTION_ORDER
                if q.startswith("A") and q not in computed_topics]
    counts = _largest_remainder(residual, len(a_theory))
    bag = [t for t, n in counts.items() for _ in range(n)]
    fallback_topic = max(residual, key=residual.get)
    while len(bag) < len(a_theory):
        bag.append(fallback_topic)

    base = dict(qtopics)
    best: list[str] | None = None
    for _ in range(5000):
        rng.shuffle(bag)
        trial = dict(base)
        for q, topic in zip(a_theory, bag):
            trial[q] = topic
        seq = [trial[q] for q in QUESTION_ORDER]
        if _consecutive_ok(seq):
            best = bag.copy()
            break
    if best is None:
        best = bag  # extremely unlikely; the report flags any violation
    for q, topic in zip(a_theory, best):
        qtopics[q] = topic
    for q in QUESTION_ORDER:
        qtopics.setdefault(q, fallback_topic)
    return qtopics, dict(pb_marks)


def _label_weights(stats: ModernStats, part: str, marks: int) -> dict[str, int]:
    rows = [r for r in stats.rows
            if str(r["Q no."]).strip().startswith(part)
            and int(r["Marks"] or 0) == marks
            and str(r["Task"]) != "compute"]
    counts = Counter()
    for r in rows:
        label, _ = command_word(r["Original question text"])
        if label in LABELS:
            counts[label] += 1
    if counts:
        return dict(counts)
    # fall back to the same part at any mark, then the whole modern sample
    rows = [r for r in stats.rows
            if str(r["Q no."]).strip().startswith(part)
            and str(r["Task"]) != "compute"]
    for r in rows:
        label, _ = command_word(r["Original question text"])
        if label in LABELS:
            counts[label] += 1
    if counts:
        return dict(counts)
    for r in stats.rows:
        if str(r["Task"]) == "compute":
            continue
        label, _ = command_word(r["Original question text"])
        if label in LABELS:
            counts[label] += 1
    return dict(counts) or {label: 1 for label in LABELS}


def _pick_label(weights: dict[str, int], rng: random.Random) -> str:
    labels = [l for l in LABELS if weights.get(l, 0) > 0]
    if not labels:
        return "Explain"
    return rng.choices(labels, weights=[weights[l] for l in labels])[0]


def _quota_labels(weights: dict[str, int], n: int,
                  rng: random.Random) -> list[str]:
    """Allocate command labels to n slots by the measured marks share."""
    positive = {l: weights.get(l, 0) for l in LABELS if weights.get(l, 0) > 0}
    if not positive:
        positive = {l: 1 for l in LABELS}
    quota = _largest_remainder(positive, n, keys=LABELS)
    bag = [l for l, count in quota.items() for _ in range(count)]
    while len(bag) < n:
        bag.append(max(positive, key=positive.get))
    rng.shuffle(bag)
    return bag[:n]


def _assign_tasks(stats: ModernStats, slots: dict[str, Slot],
                  rng: random.Random) -> None:
    # Group theory slots by part/marks and allocate the measured command-word
    # mix as a quota.  Part B therefore uses Part B's mix, never Part A's.
    groups: dict[tuple[str, int], list[Slot]] = defaultdict(list)
    for s in slots.values():
        if s.kind == "theory":
            groups[(s.part, s.marks)].append(s)
    for (part, marks), group in groups.items():
        weights = _label_weights(stats, part, marks)
        bag = _quota_labels(weights, len(group), rng)
        for s, label in zip(group, bag):
            s.task = label
    for s in slots.values():
        if s.kind == "computed":
            s.task = "compute"

    for q in QUESTION_ORDER:
        qslots = [s for s in slots.values() if s.question == q]
        if qslots and qslots[0].dependent:
            b = next((s for s in qslots if s.slot.endswith("b")), None)
            if b is not None:
                weights = _label_weights(stats, b.part, b.marks)
                options = {l: weights.get(l, 0) for l in ("Justify", "Explain",
                                                          "Discuss")}
                if any(options.values()):
                    b.task = _pick_label(options, rng)
                elif b.task in ("State", "List", "Compare"):
                    b.task = "Explain"
                b.note = ("dependent pair: (b) builds on (a); generated together"
                          if not b.note else b.note + "; dependent pair")
        for s in qslots:
            if s.kind != "theory":
                continue
            result = style_examples(s.topic, s.task, s.marks)
            s.style_n = result.exact_n
            s.style_n_widened = result.final_n
            s.style_mode = result.mode
            s.style_examples = result.examples
            s.low_style_confidence = result.low_confidence
            bits = [f"style n={s.style_n}"]
            if result.widened:
                bits.append(f"widened to {result.mode}")
            if result.low_confidence:
                bits.append("low style confidence")
            if s.dependent:
                bits.append("dependent pair")
            s.note = "; ".join(bits)


def _mark_computed(slots: dict[str, Slot], target: int, style: str,
                   rng: random.Random) -> dict[str, str]:
    six, twos = _computed_mark_counts(target)
    used_types: set[str] = set()
    six_slots = [f"A{i}b" for i in (2, 4, 5, 7, 9, 10, 1, 3, 6, 8)][:six]
    two_slots = [f"A{i}a" for i in (1, 3, 6, 8, 10, 2, 4, 5, 7, 9)
                 if f"A{i}a" not in six_slots][:twos]
    six_types = _choose_types(six, 6, style, used_types, rng)
    two_types = _choose_types(twos, 2, style, used_types, rng)
    computed_topics: dict[str, str] = {}
    for slot_id, kind in zip(six_slots, six_types):
        s = slots[slot_id]
        s.kind = "computed"
        s.topic = "access control models" if kind == "acm" else "classical ciphers"
        s.task = "compute"
        s.computed_type = kind
        s.target = target_size(kind, 6)
        s.note = "computed slot"
        if kind == "acm":
            s.acm_scope = ACM_SCOPE[6]
        if kind == "vigenere":
            s.note += "; print the 26 x 26 Vigenere tableau in the question"
        computed_topics[s.question] = s.topic
    for slot_id, kind in zip(two_slots, two_types):
        s = slots[slot_id]
        s.kind = "computed"
        s.topic = "access control models" if kind == "acm" else "classical ciphers"
        s.task = "compute"
        s.computed_type = kind
        s.target = target_size(kind, 2)
        s.note = "computed slot"
        computed_topics[s.question] = s.topic
    return computed_topics


def build_plan(mode: str, style: str, computed_marks: int | None,
               seed: int) -> tuple[list[Slot], dict]:
    stats = load_modern_stats()
    rng = random.Random(seed)
    if style == "older" and mode == "realistic":
        raise SystemExit("--style older cannot be used with realistic mode")
    if mode == "realistic":
        target = (computed_marks if computed_marks is not None
                  else rng.choice(stats.mv_distribution))
        if target % 2:
            target -= 1
    elif mode == "practice":
        target = 22 if computed_marks is None else computed_marks
    else:
        raise SystemExit("mode must be realistic or practice")

    slots = {slot: Slot(slot=slot, marks=marks, kind="theory",
                        question=_question_of(slot),
                        part=_question_of(slot)[0], topic="", task="")
             for slot, marks in SLOT_TEMPLATE}
    computed_topics = _mark_computed(slots, target, style, rng)
    for s in slots.values():
        if s.kind == "theory":
            s.topic = computed_topics.get(s.question, "")

    theory_slots = [s for s in slots.values() if s.kind == "theory"]
    qtopics, pb_marks = _assign_question_topics(
        stats, theory_slots, computed_topics, rng)

    # One topic per question: every slot in a question takes the question topic.
    for s in slots.values():
        s.topic = qtopics[s.question]

    # Dependent pairs: one Part A theory-only pair for a 9-question theory set
    # (1/9 = 11.1%, close to the measured 7/72 = 9.7%).  Never a computed pair.
    a_theory = [q for q in QUESTION_ORDER
                if q.startswith("A") and q not in computed_topics]
    dependent_q = rng.choice(a_theory) if a_theory else None
    if dependent_q:
        for s in slots.values():
            if s.question == dependent_q:
                s.dependent = True
                if s.slot.endswith("b"):
                    s.dependent_on = dependent_q + "a"
                s.note = "dependent pair (b builds on a); measured rate 9.7%"

    _assign_tasks(stats, slots, rng)

    table = [slots[s] for s in _paper_order()]
    assigned = defaultdict(int)
    theory_assigned = defaultdict(int)
    for s in table:
        if s.kind == "theory":
            assigned[s.topic] += s.marks
            if s.topic in THEORY_TOPICS:
                theory_assigned[s.topic] += s.marks
    target_topic_marks = _largest_remainder(
        stats.topic_weights,
        sum(s.marks for s in table if s.kind == "theory"
            and s.topic in THEORY_TOPICS))

    m = measure()
    six_labels = sorted({s.task for s in table
                         if s.kind == "theory" and s.marks == 6})
    six_examples = {label: six_mark_examples(label, 3) for label in six_labels}
    seq = [qtopics[q] for q in QUESTION_ORDER]
    low = [s.slot for s in table
           if s.kind == "theory" and s.low_style_confidence]
    dependent = sorted({s.question for s in table if s.dependent})
    summary = {
        "mode": mode,
        "style": style,
        "seed": seed,
        "computed_marks": target,
        "computed_distribution": stats.mv_distribution,
        "computed_distribution_mean": round(
            sum(stats.mv_distribution) / len(stats.mv_distribution), 2),
        "clean_modern_papers": len(stats.clean_ids),
        "topic_weights": {k: round(v, 3) for k, v in stats.topic_weights.items()},
        "topic_marks_modern": dict(stats.topic_marks),
        "target_topic_marks": target_topic_marks,
        "assigned_topic_marks": dict(assigned),
        "assigned_theory_topic_marks": dict(theory_assigned),
        "part_b_topic_marks_measured": load_part_b_stats()["topic_marks"],
        "part_b_assigned_marks": pb_marks,
        "question_topics": qtopics,
        "question_topic_sequence": seq,
        "no_three_consecutive_same_topic": _consecutive_ok(seq),
        "dependent_questions": dependent,
        "measurement": {
            "clean_papers": m.clean_papers,
            "ab_papers": m.ab_papers,
            "part_a_pairs": m.part_a_pairs,
            "same_topic_pairs": m.same_topic_pairs,
            "dependent_pairs": m.dependent_pairs,
            "part_a_label_counts": m.part_a_label_counts,
            "part_a_label_marks": m.part_a_label_marks,
            "part_b_label_counts": m.part_b_label_counts,
            "part_b_label_marks": m.part_b_label_marks,
            "part_b_topic_marks": m.part_b_topic_marks,
        },
        "six_mark_examples": six_examples,
        "low_style_confidence_slots": low,
        "coverage_notes": _coverage_notes(stats),
        "slots": [asdict(s) for s in table],
        "calibration": [asdict(c) for c in CALIBRATIONS],
    }
    return table, summary


def _coverage_notes(stats: ModernStats) -> list[str]:
    excluded = sum(stats.excluded_topic_marks.values())
    total = excluded + stats.theory_marks
    notes = [
        f"Seven theory topics cover {stats.theory_marks}/{total} modern "
        f"non-compute marks; {excluded} marks ({excluded / total:.1%}) fall "
        "outside the seven topics and are reported, not reallocated: "
        + ", ".join(f"{k} {v}" for k, v in sorted(
            stats.excluded_topic_marks.items(), key=lambda x: -x[1])) + ".",
        "risk/management (ethics) weight is the modern risk/management marks "
        "(119) renormalised with the other six topics; source deck: KB folder "
        "'CSC662', deck 071 Ethics.",
        "A theory slot paired with a computed slot inherits the computed "
        "topic (classical ciphers or access control models) because (a) and "
        "(b) must share one topic; this mark is outside the seven-topic "
        "target and is shown separately.",
        "2018-01 and 2018-06 have no A/B labels and are excluded from the "
        "pair/part measures; 2025-07 has incomplete A/B extraction.",
    ]
    return notes


def to_markdown(summary: dict) -> str:
    m = summary["measurement"]
    lines = [
        "# Planner slot table - revised",
        "",
        f"- mode: **{summary['mode']}**; style: **{summary['style']}**; "
        f"seed: {summary['seed']}",
        f"- computed marks: **{summary['computed_marks']}**; clean-modern "
        f"distribution: {summary['computed_distribution']} "
        f"(mean {summary['computed_distribution_mean']})",
        f"- clean modern papers: {summary['clean_modern_papers']}",
        "",
        "## Measurements used",
        "",
        f"- Part A pairs: {m['part_a_pairs']} across {len(m['ab_papers'])} "
        f"papers; same topic {m['same_topic_pairs']}/{m['part_a_pairs']} "
        f"({m['same_topic_pairs'] / m['part_a_pairs']:.1%}); dependent (b) "
        f"{m['dependent_pairs']}/{m['part_a_pairs']} "
        f"({m['dependent_pairs'] / m['part_a_pairs']:.1%}).",
        "- Part A command-word rows/marks: "
        + ", ".join(f"{k} {v}" for k, v in m["part_a_label_counts"].items())
        + ".",
        "- Part B command-word rows/marks: "
        + ", ".join(f"{k} {v}" for k, v in m["part_b_label_counts"].items())
        + ".",
        "",
        "## Slots",
        "",
        "| Slot | Q | Marks | Kind | Topic | Command | Computed type | "
        "Target size / key | Style n | Style mode | Low conf. | Dependent | "
        "Notes |",
        "|---|---|---:|---|---|---|---|---|---:|---|---|---|---|",
    ]
    for s in summary["slots"]:
        lines.append(
            f"| {s['slot']} | {s['question']} | {s['marks']} | {s['kind']} | "
            f"{s['topic']} | {s['task']} | "
            f"{TYPE_LABEL.get(s['computed_type'], s['computed_type'])} | "
            f"{s['target']} | "
            f"{s['style_n'] if s['kind'] == 'theory' else ''} | "
            f"{s['style_mode']} | "
            f"{'yes' if s['low_style_confidence'] else ''} | "
            f"{'yes' if s['dependent'] else ''} | "
            f"{s['acm_scope'] or s['note']} |")
    lines += [
        "",
        "## Topic allocation",
        "",
        "| Topic | Modern weight | Target marks | Assigned theory marks |",
        "|---|---:|---:|---:|",
    ]
    for t in THEORY_TOPICS:
        lines.append(f"| {t} | {summary['topic_weights'][t]:.3f} | "
                     f"{summary['target_topic_marks'].get(t, 0)} | "
                     f"{summary['assigned_theory_topic_marks'].get(t, 0)} |")
    lines += [
        "",
        "Question topic sequence (A1..A10, B1, B2): "
        + " -> ".join(f"{q}:{t}" for q, t in
                       zip(QUESTION_ORDER, summary["question_topic_sequence"])),
        f"Max two consecutive same-topic questions: "
        f"**{'PASS' if summary['no_three_consecutive_same_topic'] else 'FAIL'}**.",
        f"Dependent question(s): {', '.join(summary['dependent_questions']) or 'none'}.",
        "",
        "## Part B measured task distribution (used for B slots)",
        "",
        "| Command | Rows | Marks |",
        "|---|---:|---:|",
    ]
    for label in LABELS:
        lines.append(f"| {label} | {m['part_b_label_counts'].get(label, 0)} | "
                     f"{m['part_b_label_marks'].get(label, 0)} |")
    lines += [
        "",
        "## Three real 6-mark examples per command label used at 6 marks",
        "",
    ]
    for label, examples in summary["six_mark_examples"].items():
        lines.append(f"### {label}")
        lines.append("")
        for ex in examples:
            lines.append(f"- **{ex['paper']} {ex['q']}**: {ex['text']}")
        lines.append("")
    lines += [
        "## Style widening and low-confidence slots",
        "",
        f"Slots with exact style n < 3: "
        f"{', '.join(summary['low_style_confidence_slots']) or 'none'}.",
        "Widening order: exact -> same topic/any command -> same command/any "
        "topic; all are recorded in the slot table.",
        "",
        "## Coverage notes",
        "",
    ]
    lines += [f"- {n}" for n in summary["coverage_notes"]]
    lines += [
        "",
        "## Calibration used for computed sizes",
        "",
        "| Type | Marks | n | Length range | Key | Working steps | Note |",
        "|---|---:|---:|---|---|---|---|",
    ]
    for c in summary["calibration"]:
        lines.append(f"| {c['kind']} | {c['marks']} | {c['n']} | "
                     f"{c['length_range']} | {c['key']} | {c['steps']} | {c['note']} |")
    lines += [
        "",
        "ACM rule: 6 marks = matrix only; about 9 marks = matrix + ACL + CL. "
        "Playfair and affine are never used in realistic mode. Vigenere "
        "questions print the 26 x 26 tableau (2006-10 Q2d, 2017-07 Q10 style).",
    ]
    return "\n".join(lines)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--mode", choices=("realistic", "practice"), default="realistic")
    ap.add_argument("--style", choices=("modern", "older"), default="modern")
    ap.add_argument("--computed-marks", type=int, default=None)
    ap.add_argument("--seed", type=int, default=9)
    ap.add_argument("--out-prefix", default="")
    args = ap.parse_args()
    table, summary = build_plan(args.mode, args.style, args.computed_marks,
                                args.seed)
    prefix = args.out_prefix or f"outputs/planner_{args.mode}_{args.style}"
    json_path = OUTPUTS_DIR / f"{prefix.split('/')[-1]}.json"
    md_path = OUTPUTS_DIR / f"{prefix.split('/')[-1]}.md"
    json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    md = to_markdown(summary)
    md_path.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {json_path} and {md_path}")


if __name__ == "__main__":
    main()
