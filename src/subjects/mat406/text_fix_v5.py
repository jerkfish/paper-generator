"""Restore printed equations and sub-items that MinerU dropped.

These corrections were found while proofing the Gate B seed papers against
the source page renders.  They only restore text that is visibly printed in
the supplied past papers; no question, mark or answer is invented.  The bank
questions stay approved, but each corrected question is flagged with its
evidence so Gate B can review the change.

Run:
    uv run python -m src.subjects.mat406.text_fix_v5
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone

from src import config
from src.bank.quality import quality_band, quality_score
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, save_json
from src.subjects.mat406.text_fix_v4 import CORRECTIONS as V4_CORRECTIONS

BANK = config.TRACKING_DIR / "mat406" / "v2" / "bank"
REPORT = config.TRACKING_DIR / "mat406" / "v2" / "text_corrections_v5.json"

# Full printed part text.  The bank stores the part body without the leading
# "a)"/"b)" label, so the replacement keeps that convention.
CORRECTIONS = [
    {
        "question_id": "MAT406-2022-FEB-Q3",
        "label": "a",
        "text": (
            "Consider the following system of equations\n"
            "$x - 2y = 2$\n"
            "$x - 3y = y^2 - 10.$\n"
            "Find the values of x and y using the substitution method.\n"
            "(5 marks)"
        ),
        "evidence": "printed page 3: system x-2y=2, x-3y=y^2-10",
    },
    {
        "question_id": "MAT406-2022-FEB-Q3",
        "label": "b",
        "text": (
            "Sketch and shade the feasible region that satisfies the "
            "following system of inequalities\n"
            "$x \\geq -3$\n"
            "$0 \\leq y < 4$\n"
            "$3y + 2x \\leq 6$\n"
            "$2y - x < 4.$\n"
            "(6 marks)"
        ),
        "evidence": "printed page 3: four inequalities for the feasible region",
    },
    {
        "question_id": "MAT406-2022-FEB-Q7",
        "label": "a",
        "text": (
            "Suppose vector $\\vec{v} = \\langle \\alpha, 1 \\rangle$, where "
            "$\\alpha > 0$, has a magnitude of 2 units.\n"
            "i) Find the value of $\\alpha$ and hence state the component "
            "form of $\\vec{v}$.\n"
            "(3 marks)\n"
            "ii) Determine the scalar product of $2\\vec{v} \\cdot "
            "4\\vec{w}$ if $\\vec{w} = \\langle 1, \\sqrt{3} \\rangle$. "
            "Hence, find the angle between $2\\vec{v}$ and $4\\vec{w}$.\n"
            "(4 marks)"
        ),
        "evidence": "printed page 5: vector v, scalar product and angle",
    },
    {
        "question_id": "MAT406-2022-FEB-Q7",
        "label": "b",
        "text": (
            "Given that $B(1,0)$, $C(2,-9)$ and $L(3,6-2h)$. Find\n"
            "i) the unit vector in the same direction as "
            "$\\overrightarrow{BC}$.\n"
            "(3 marks)\n"
            "ii) the value of $h$ such that $\\overrightarrow{CL}$ is "
            "perpendicular to $\\vec{P} = \\langle 5, -5 \\rangle$.\n"
            "(4 marks)"
        ),
        "evidence": "printed page 5: CL perpendicular to P",
    },
    {
        "question_id": "MAT406-2023-FEB-Q6",
        "label": "b",
        "text": (
            "Write the following system of linear equations in matrix form.\n"
            "$x + y = -2$\n"
            "$3x + 2y + z = 4$\n"
            "$-x + z = 2$\n"
            "Hence, solve the system by finding the inverse of the "
            "coefficient matrix using the adjoint method.\n"
            "(9 marks)"
        ),
        "evidence": "printed page 6: system x+y=-2, 3x+2y+z=4, -x+z=2",
    },
    {
        "question_id": "MAT406-2023-JUL-Q6",
        "label": "b",
        "text": (
            "Consider the following system of linear equations:\n"
            "$x + 2y - 2z = 3$\n"
            "$y - 2z = -1$\n"
            "$-x - 3y = 2$\n"
            "Write the above system in matrix form. Hence, solve the system "
            "by finding the inverse of the coefficient matrix using the "
            "adjoint method.\n"
            "(9 marks)"
        ),
        "evidence": "printed page 6: system x+2y-2z=3, y-2z=-1, -x-3y=2",
    },
    {
        "question_id": "MAT406-2024-JAN-Q6",
        "label": "b",
        "text": (
            "The system of linear equations are given as follows:\n"
            "$x + 2y - 3z = 3$\n"
            "$2x - y - z = 11$\n"
            "$3x + 2y + z = -5$\n"
            "i) Write the system of linear equations as a matrix equation "
            "in the form $AX = B$.\n"
            "(1 mark)\n"
            "ii) Determine the values of $x, y$ and $z$ such that "
            "$X = A^{-1}B$.\n"
            "(9 marks)"
        ),
        "evidence": "printed page 5: system x+2y-3z=3, 2x-y-z=11, 3x+2y+z=-5",
    },
    {
        "question_id": "MAT406-2025-JUL-Q2",
        "label": "b",
        "text": (
            "Find the reference angle for\n"
            "i) $\\theta = 100^{\\circ}$\n"
            "(3 marks)\n"
            "ii) $\\frac{4}{3}\\pi$\n"
            "(3 marks)"
        ),
        "evidence": "printed page 2: reference angles 100 degrees and 4pi/3",
    },
    {
        "question_id": "MAT406-2026-FEB-Q2",
        "label": "b",
        "text": (
            "Given $\\cos \\theta = \\frac{4}{5}$ where $\\theta$ is an "
            "acute angle. Find the value of\n"
            "i) $\\sin 2\\theta$\n"
            "(3 marks)\n"
            "ii) $-\\cot^2 \\theta + \\tan \\theta$\n"
            "(3 marks)"
        ),
        "evidence": "printed page 2: i) sin 2theta, ii) -cot^2 theta + tan theta",
    },
    {
        "question_id": "MAT406-2025-FEB-Q2",
        "label": "b",
        "text": (
            "The circle C has points $(5,-4)$ and $(-1,4)$ as the ends of "
            "its diameter.\n"
            "i) Find the center and radius of the circle.\n"
            "(4 marks)\n"
            "ii) Write the equation of the circle in form of\n"
            "$ax^2 + by^2 + cx + dy + e = 0$\n"
            "where $a, b, c, d$ and $e$ are integers.\n"
            "(2 marks)\n"
            "iii) Sketch the circle. Label the endpoints, radius and center.\n"
            "(3 marks)"
        ),
        "evidence": "printed page 2: ax^2+by^2+cx+dy+e=0",
    },
    {
        "question_id": "MAT406-2022-FEB-Q6",
        "label": "c",
        "text": (
            "Consider the following system of equations\n"
            "$-6x + 4y - 11z = 5$\n"
            "$3x - 2y + 6z = 2$\n"
            "$-2x + y - 3z = -3.$\n"
            "Solve the system of equations using the inverse matrix method.\n"
            "(10 marks)"
        ),
        "evidence": "printed page 5: system -6x+4y-11z=5, 3x-2y+6z=2, -2x+y-3z=-3",
    },
    {
        "question_id": "MAT406-2025-JUL-Q2-2",
        "label": "a",
        "text": (
            "Solve the following equation\n"
            "i) $\\sin^2 x = \\frac{1}{4}$ for "
            "$0^{\\circ} \\leq x \\leq 420^{\\circ}$\n"
            "(5 marks)\n"
            "ii) $2\\tan 2x - 3 = 0$ for "
            "$0^{\\circ} \\leq x \\leq 360^{\\circ}$\n"
            "(5 marks)"
        ),
        "evidence": "printed page 4: sin^2 x = 1/4 and 2tan2x - 3 = 0",
    },
]


def _corrections() -> list[dict]:
    """Explicit Gate B fixes first, then the older V4 fixes for whole parts.

    The V4 module corrected ``native_text`` but its ``b) ...`` find strings
    did not match the bank's part body (which omits the label), so several
    printed equations never reached the assembled paper.  Convert those
    corrections to the same full-part form here; explicit entries above win.
    """
    rows = [dict(row) for row in CORRECTIONS]
    seen = {(row["question_id"], row["label"]) for row in rows}
    for qid, find, replace, evidence in V4_CORRECTIONS:
        match = re.match(r"\s*([a-d])\)\s*", find)
        if not match:
            continue
        label = match.group(1)
        if (qid, label) in seen:
            continue
        text = re.sub(r"^\s*[a-d]\)\s*", "", replace).strip()
        rows.append({
            "question_id": qid,
            "label": label,
            "text": text,
            "evidence": evidence,
        })
        seen.add((qid, label))
    return rows


def _native_text(question: dict) -> str:
    lines = []
    stem = str(question.get("stem") or "").strip()
    if stem:
        lines.append(stem)
    for part in question.get("parts") or []:
        label = str(part.get("label") or "").strip()
        text = str(part.get("text") or "").strip()
        if text:
            lines.append(f"{label}) {text}" if label else text)
    return "\n".join(lines).strip()


def apply() -> dict:
    store = BankStore(BANK)
    assets = {str(row["id"]): row for row in store.assets()}
    applied = []
    missing = []
    touched = set()
    for correction in _corrections():
        qid = correction["question_id"]
        label = correction["label"]
        question = store.load_question(qid)
        if not question:
            missing.append({"question_id": qid, "reason": "question not found"})
            continue
        part = next((row for row in question.get("parts") or []
                     if str(row.get("label") or "").lower() == label),
                    None)
        if part is None:
            missing.append({"question_id": qid,
                            "reason": f"part {label} not found"})
            continue
        old = str(part.get("text") or "")
        if old.strip() == correction["text"].strip():
            continue
        part["text"] = correction["text"]
        question["native_text"] = _native_text(question)
        text = str(question.get("native_text") or "")
        question["native_text_blocks"] = [{
            "text": text,
            "normalised": normalize_text(text),
            "page": (question.get("pages") or [1])[0],
            "bbox": [],
        }]
        question["content_hash"] = question_content_hash(question)
        linked = {aid: assets[aid] for aid in question.get("assets") or []
                  if aid in assets and assets[aid].get("verdict") != "rejected"}
        question["quality_score"] = quality_score(question, linked)
        question["quality_band"] = quality_band(question["quality_score"])
        question["v5_text_correction"] = correction["evidence"]
        save_json(store.question_path(qid), question)
        touched.add(qid)
        applied.append({
            "question_id": qid,
            "part": label,
            "evidence": correction["evidence"],
            "old": old,
            "new": correction["text"],
        })
    # Report every correction that is currently in effect, not only the rows
    # changed by this invocation, so the evidence survives re-runs.
    effective = []
    for correction in _corrections():
        question = store.load_question(correction["question_id"])
        if not question:
            continue
        part = next((row for row in question.get("parts") or []
                     if str(row.get("label") or "").lower()
                     == correction["label"]), None)
        if part is None:
            continue
        if str(part.get("text") or "").strip() != correction["text"].strip():
            continue
        effective.append({
            "question_id": correction["question_id"],
            "part": correction["label"],
            "evidence": correction["evidence"],
            "new": correction["text"],
        })
    report = {
        "schema_version": 1,
        "subject": "MAT406",
        "applied_on": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "note": (
            "Printed-text restorations found during Gate B proofing. The "
            "questions remain the same printed past-paper questions; only "
            "dropped equations, sub-items and marks lines are restored from "
            "the source page renders."
        ),
        "gate_a": "already approved; corrections restore printed text",
        "questions": sorted({row["question_id"] for row in effective}),
        "applied": effective,
        "missing": missing,
    }
    save_json(REPORT, report)
    return report


if __name__ == "__main__":
    result = apply()
    print(json.dumps({
        "report": str(REPORT),
        "questions": result["questions"],
        "applied_count": len(result["applied"]),
        "missing": result["missing"],
    }, indent=2))
