"""Measure the real modern papers before changing the planner.

Reports:
  a. Part A (a)/(b) same-topic and dependent-reference rates.
  b. Task/command-word distribution by part.
  c. Topic distribution in Part B.
  d. Three 6-mark examples for each command-word label.
"""
from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from functools import lru_cache

from openpyxl import load_workbook

from src.config import OUTPUTS_DIR, TRACKING_XLSX
from src.fingerprint.types import is_whole_block_row
from src.planner.fingerprint_data import load_modern_stats
from src.planner.tasks import (DEPENDENT_RE, LABELS, RAW_TO_LABEL,
                               command_word)


def _rows() -> list[dict]:
    wb = load_workbook(TRACKING_XLSX, read_only=False, data_only=True)
    ws = wb["Questions"]
    h = [c.value for c in ws[1]]
    return [dict(zip(h, r)) for r in ws.iter_rows(min_row=2, values_only=True)
            if not is_whole_block_row(dict(zip(h, r)))]


def _ab(row: dict) -> tuple[str | None, str | None]:
    m = re.match(r"^([AB])(\d+)$", str(row["Q no."]).strip())
    return (m.group(1), m.group(2)) if m else (None, None)


def _scenario_prefix(text: str) -> str:
    t = str(text)
    low = t.lower()
    positions = []
    for raw in RAW_TO_LABEL:
        m = re.search(r"\b" + re.escape(raw) + r"\b", low)
        if m:
            positions.append(m.start())
    return t[:min(positions)].strip() if positions else t.strip()


def _has_scenario(text: str) -> bool:
    prefix = _scenario_prefix(text)
    if "?" in prefix:
        return False
    words = len(prefix.split())
    cue = re.search(r"\b(based on|given|you are|your|a student|an employee|"
                    r"two personnel|a representative|the company|scenario)\b",
                    prefix.lower())
    return words >= 10 or bool(cue and words >= 5)


@dataclass
class Measure:
    clean_papers: int
    ab_papers: list[str]
    part_a_pairs: int
    same_topic_pairs: int
    dependent_pairs: int
    part_a_label_counts: dict[str, int]
    part_a_label_marks: dict[str, int]
    part_b_label_counts: dict[str, int]
    part_b_label_marks: dict[str, int]
    part_a_raw_counts: dict[str, int]
    part_b_raw_counts: dict[str, int]
    part_b_topic_counts: dict[str, int]
    part_b_topic_marks: dict[str, int]
    part_b_questions: int
    part_b_scenario_questions: int
    part_b_same_topic_pairs: int
    part_b_dependent_pairs: int
    part_b_scenario_examples: list[dict]
    six_mark_examples: dict[str, list[dict]]


@lru_cache(maxsize=1)
def measure() -> Measure:
    stats = load_modern_stats()
    rows = _rows()
    clean = set(stats.clean_ids)
    ab_papers = []
    pairs = []
    pa_counts = Counter()
    pa_marks = Counter()
    pb_counts = Counter()
    pb_marks = Counter()
    pa_raw = Counter()
    pb_raw = Counter()
    pb_topics = Counter()
    pb_topic_marks = Counter()
    pb_questions = 0
    pb_scenario = 0
    pb_same = 0
    pb_dep = 0
    pb_examples: list[dict] = []
    for pid in stats.clean_ids:
        prows = [r for r in rows if str(r["Paper ID"]) == pid]
        if any(_ab(r)[0] for r in prows):
            ab_papers.append(pid)
        by_q: dict[str, dict[str, dict]] = defaultdict(dict)
        pb_by_q: dict[str, dict[str, dict]] = defaultdict(dict)
        for r in prows:
            part, q = _ab(r)
            if part == "A":
                by_q[q][str(r["Sub-part"])] = r
                label, raw = command_word(r["Original question text"])
                pa_counts[label] += 1
                pa_marks[label] += int(r["Marks"] or 0)
                if raw:
                    pa_raw[raw] += 1
            elif part == "B":
                pb_by_q[q][str(r["Sub-part"])] = r
                label, raw = command_word(r["Original question text"])
                pb_counts[label] += 1
                pb_marks[label] += int(r["Marks"] or 0)
                if raw:
                    pb_raw[raw] += 1
                pb_topics[str(r["Topic"])] += 1
                pb_topic_marks[str(r["Topic"])] += int(r["Marks"] or 0)
        for q, sub in by_q.items():
            if "a" in sub and "b" in sub:
                pairs.append((pid, q, sub["a"], sub["b"]))
        for q, sub in pb_by_q.items():
            if "a" not in sub:
                continue
            pb_questions += 1
            if _has_scenario(sub["a"]["Original question text"]):
                pb_scenario += 1
                if len(pb_examples) < 8:
                    pb_examples.append({
                        "paper": pid, "q": f"B{q}",
                        "prefix": _scenario_prefix(
                            sub["a"]["Original question text"])[:220],
                    })
            if "b" in sub:
                if str(sub["a"]["Topic"]) == str(sub["b"]["Topic"]):
                    pb_same += 1
                if DEPENDENT_RE.search(str(sub["b"]["Original question text"])):
                    pb_dep += 1
    same = sum(1 for _, _, a, b in pairs
               if str(a["Topic"]) == str(b["Topic"]))
    dep = sum(1 for _, _, _, b in pairs
              if DEPENDENT_RE.search(str(b["Original question text"])))

    by6 = defaultdict(list)
    for r in rows:
        if int(r["Marks"] or 0) != 6:
            continue
        label, _ = command_word(r["Original question text"])
        if label in LABELS:
            by6[label].append({
                "paper": r["Paper ID"],
                "q": f"Q{r['Q no.']}{r['Sub-part'] or ''}",
                "text": str(r["Original question text"]),
            })
    six = {label: by6[label][:3] for label in LABELS}

    return Measure(
        clean_papers=len(stats.clean_ids),
        ab_papers=ab_papers,
        part_a_pairs=len(pairs),
        same_topic_pairs=same,
        dependent_pairs=dep,
        part_a_label_counts=dict(pa_counts),
        part_a_label_marks=dict(pa_marks),
        part_b_label_counts=dict(pb_counts),
        part_b_label_marks=dict(pb_marks),
        part_a_raw_counts=dict(pa_raw),
        part_b_raw_counts=dict(pb_raw),
        part_b_topic_counts=dict(pb_topics),
        part_b_topic_marks=dict(pb_topic_marks),
        part_b_questions=pb_questions,
        part_b_scenario_questions=pb_scenario,
        part_b_same_topic_pairs=pb_same,
        part_b_dependent_pairs=pb_dep,
        part_b_scenario_examples=pb_examples,
        six_mark_examples=six,
    )


def to_markdown(m: Measure) -> str:
    pct = lambda a, b: f"{a}/{b} ({a / b:.1%})" if b else "0/0"
    lines = [
        "# Planner measurements - 10 clean modern papers",
        "",
        f"Clean modern papers: {m.clean_papers}. Papers with explicit Part A/B "
        f"labels used for pair/task measures: {len(m.ab_papers)} "
        f"({', '.join(m.ab_papers)}). 2018-01 and 2018-06 use a different "
        "numeric-question layout (no A/B labels) and are excluded from the "
        "pair/part measures; 2025-07 has incomplete/noisy A/B extraction.",
        "",
        "## (a) Part A (a)/(b) pairs",
        "",
        f"- Pairs measured: **{m.part_a_pairs}** across {len(m.ab_papers)} papers.",
        f"- Same topic: **{pct(m.same_topic_pairs, m.part_a_pairs)}**.",
        f"- Dependent b (explicit reference to a / the above / the scenario): "
        f"**{pct(m.dependent_pairs, m.part_a_pairs)}**.",
        "",
        "Dependency detection used: `your answer in (a)`, `answer in (a)`, "
        "`the above`, `based on the above`, `scenario above`, `given scenario`, "
        "`this scenario`, `same scenario`, `in part (a)`, `using your answer`.",
        "",
        "## (b) Command-word distribution by part",
        "",
        "| Label | Part A rows | Part A marks | Part B rows | Part B marks |",
        "|---|---:|---:|---:|---:|",
    ]
    for label in LABELS + ["Other"]:
        lines.append(f"| {label} | {m.part_a_label_counts.get(label, 0)} | "
                     f"{m.part_a_label_marks.get(label, 0)} | "
                     f"{m.part_b_label_counts.get(label, 0)} | "
                     f"{m.part_b_label_marks.get(label, 0)} |")
    lines += [
        "",
        "Top raw command words (mapped to the labels above): "
        f"Part A {m.part_a_raw_counts}; Part B {m.part_b_raw_counts}.",
        "",
        "## (c) Topic distribution in Part B",
        "",
        "| Topic | Rows | Marks |",
        "|---|---:|---:|",
    ]
    for topic, n in sorted(m.part_b_topic_marks.items(), key=lambda x: -x[1]):
        lines.append(f"| {topic} | {m.part_b_topic_counts.get(topic, 0)} | {n} |")
    lines += [
        "",
        "## (c2) Part B scenario and (a)/(b) relation",
        "",
        f"- Part B questions with both a/b rows: **{m.part_b_questions}**.",
        f"- Scenario paragraph detected in the (a) stem: "
        f"**{m.part_b_scenario_questions}/{m.part_b_questions}** "
        f"({m.part_b_scenario_questions / m.part_b_questions:.1%}). "
        "Method: text before the first command verb is at least 10 words, or "
        "a scenario cue plus at least 5 words. 2023-02's Ali scenario may be "
        "in a separate unlogged paragraph, so this is a lower bound.",
        f"- (a)/(b) same topic: **{m.part_b_same_topic_pairs}/"
        f"{m.part_b_questions}**.",
        f"- (b) explicitly refers back to (a)/the above/scenario: "
        f"**{m.part_b_dependent_pairs}/{m.part_b_questions}**.",
        "",
        "| Example | Detected scenario prefix |",
        "|---|---|",
    ]
    for ex in m.part_b_scenario_examples:
        lines.append(f"| {ex['paper']} {ex['q']} | {ex['prefix']} |")
    lines += [
        "",
        "## (d) Three real 6-mark examples per command-word label",
        "",
    ]
    for label in LABELS:
        lines.append(f"### {label}")
        lines.append("")
        for ex in m.six_mark_examples.get(label, []):
            lines.append(f"- **{ex['paper']} {ex['q']}**: {ex['text']}")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    m = measure()
    jp = OUTPUTS_DIR / "planner_measurements.json"
    mp = OUTPUTS_DIR / "planner_measurements.md"
    jp.write_text(json.dumps(asdict(m), indent=2), encoding="utf-8")
    md = to_markdown(m)
    mp.write_text(md, encoding="utf-8")
    print(md)
    print(f"\nwrote {jp} and {mp}")


if __name__ == "__main__":
    main()
