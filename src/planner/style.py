"""Style-example selection with the widening order requested in the brief.

Exact match: same topic + command label + marks.
Then: same topic, any command, same marks.
Then: same command, any topic, same marks.

Every widening is recorded.  A slot whose exact match count is below 3 is
labelled `low_style_confidence` even when the widened pool reaches 3.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from src.planner.fingerprint_data import load_all_rows, normalize_topic
from src.planner.tasks import command_word


@dataclass
class StyleResult:
    exact_n: int
    final_n: int
    mode: str
    examples: list[dict] = field(default_factory=list)
    low_confidence: bool = False

    @property
    def widened(self) -> bool:
        return self.mode != "exact"


def _example(row: dict) -> dict:
    return {
        "paper": str(row["Paper ID"]),
        "q": f"Q{row['Q no.']}{row['Sub-part'] or ''}",
        "text": str(row["Original question text"]),
        "topic": normalize_topic(row["Topic"]),
        "task": command_word(row["Original question text"])[0],
        "marks": int(row["Marks"] or 0),
    }


def _pool(rows: list[dict], topic: str, label: str, marks: int,
          mode: str) -> list[dict]:
    out = []
    for r in rows:
        if str(r["Task"]) == "compute":
            continue
        if int(r["Marks"] or 0) != marks:
            continue
        row_topic = normalize_topic(r["Topic"])
        row_label = command_word(r["Original question text"])[0]
        if mode == "exact" and not (row_topic == topic and row_label == label):
            continue
        if mode == "topic" and row_topic != topic:
            continue
        if mode == "label" and row_label != label:
            continue
        out.append(_example(r))
    return out


def style_examples(topic: str, label: str, marks: int,
                   limit: int = 5) -> StyleResult:
    rows = load_all_rows()
    topic = normalize_topic(topic)
    exact = _pool(rows, topic, label, marks, "exact")
    if len(exact) >= 3:
        return StyleResult(len(exact), len(exact), "exact", exact[:limit], False)
    if exact:
        # Keep exact examples first; widen within the same topic.
        widened = exact + [e for e in _pool(rows, topic, label, marks, "topic")
                           if e not in exact]
        if len(widened) >= 3:
            return StyleResult(len(exact), len(widened),
                               "topic+marks (any command)",
                               widened[:limit], True)
    widened = [e for e in _pool(rows, topic, label, marks, "topic")]
    if len(widened) >= 3:
        return StyleResult(len(exact), len(widened),
                           "topic+marks (any command)", widened[:limit], True)
    by_label = _pool(rows, topic, label, marks, "label")
    merged = widened + [e for e in by_label if e not in widened]
    if len(merged) >= 3:
        return StyleResult(len(exact), len(merged),
                           "command+marks (any topic)", merged[:limit], True)
    if merged:
        return StyleResult(len(exact), len(merged),
                           "command+marks (any topic) - still <3",
                           merged[:limit], True)
    return StyleResult(0, 0, "no style example", [], True)


def six_mark_examples(label: str, limit: int = 3) -> list[dict]:
    """Real six-mark questions for a command label, across all 35 papers."""
    rows = load_all_rows()
    out = []
    for r in rows:
        if str(r["Task"]) == "compute" or int(r["Marks"] or 0) != 6:
            continue
        if command_word(r["Original question text"])[0] != label:
            continue
        out.append(_example(r))
        if len(out) >= limit:
            break
    return out
