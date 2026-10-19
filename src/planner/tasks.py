"""Command-word labels shared by the measurements and the planner.

The planner uses exactly the seven real-paper command labels the brief asks
for. Raw phrasing is mapped onto those labels; `Other` is kept only for the
measurement report, never for a generated question.
"""
from __future__ import annotations

import re

LABELS = ["State", "List", "Explain", "Describe", "Discuss", "Compare", "Justify"]
RAW_TO_LABEL = {
    "state": "State", "give": "State", "identify": "State", "name": "State",
    "list": "List", "enumerate": "List",
    "explain": "Explain", "why": "Explain", "how": "Explain", "what is": "Explain",
    "describe": "Describe", "outline": "Describe", "define": "Describe",
    "discuss": "Discuss", "evaluate": "Discuss", "analyse": "Discuss",
    "analyze": "Discuss", "critically": "Discuss",
    "compare": "Compare", "differentiate": "Compare", "contrast": "Compare",
    "justify": "Justify", "support": "Justify", "propose": "Justify",
    "suggest": "Justify", "recommend": "Justify",
}
DEPENDENT_RE = re.compile(
    r"your answer in\s*\(?a\)?|answer in\s*\(?a\)?|\bthe above\b|"
    r"based on the above|from the above|scenario above|given scenario|"
    r"this scenario|same scenario|in part\s*\(?a\)?|using your answer",
    re.I,
)


def command_word(text: str) -> tuple[str, str | None]:
    """Return (one of the seven labels or Other, raw command word)."""
    t = str(text).lower()
    hits = []
    for raw, label in RAW_TO_LABEL.items():
        m = re.search(r"\b" + re.escape(raw) + r"\b", t)
        if m:
            hits.append((m.start(), label, raw))
    if not hits:
        return "Other", None
    hits.sort()
    return hits[0][1], hits[0][2]
