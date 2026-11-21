"""Apply printed-text corrections found while solving V4.

The corrections insert equations that MinerU omitted. They are read from the
source page renders; no answer or mark is invented.

Run:
    uv run python -m src.subjects.mat406.text_fix_v4
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.quality import quality_band, quality_score
from src.bank.schema import normalize_text, question_content_hash
from src.bank.store import BankStore, save_json

BANK = config.TRACKING_DIR / "mat406" / "v2" / "bank"
REPORT = config.TRACKING_DIR / "mat406" / "v2" / "text_corrections_applied.json"

CORRECTIONS = [
    (
        "MAT406-2022-FEB-Q1",
        "b) Solve the following equations. Give your answers to three decimal places.",
        r"""b) Solve the following equations. Give your answers to three decimal places.
i) $\log_3(5x + 4) - \log_3(4x) = 2$
(3 marks)
ii) $9e^x + 4e^{-x} - 12 = 0$
(5 marks)""",
        "printed page 2: b) i/ii equations",
    ),
    (
        "MAT406-2023-FEB-Q3",
        r"""a) Solve each of the following inequalities for $x$ and express the solutions in interval notation.
iii) $\frac{-4x - 4}{2x - 3} \leq -x.$""",
        r"""a) Solve each of the following inequalities for $x$ and express the solutions in interval notation.
i) $-\sqrt{3} \leq \frac{2x}{\sqrt{3}} - \sqrt{3} \leq \sqrt{3}.$
(4 marks)
ii) $|3x + 6| - 1 < -2x.$
(4 marks)
iii) $\frac{-4x - 4}{2x - 3} \leq -x.$
(6 marks)""",
        "printed page 3: a) i/ii/iii inequalities",
    ),
    (
        "MAT406-2023-FEB-Q3",
        "b) Sketch and shade the region that corresponds to the solution set for the following system of inequalities.",
        r"""b) Sketch and shade the region that corresponds to the solution set for the following system of inequalities.
$-y < x < y$
$x^2 + y \geq 2$""",
        "printed page 4: b) system",
    ),
    (
        "MAT406-2023-FEB-Q3",
        "c) Solve the following system of linear equations using the elimination method.",
        r"""c) Solve the following system of linear equations using the elimination method.
$a + \sqrt{2}b = 0$
$\frac{a}{\sqrt{2}} - b = 1$""",
        "printed page 4: c) system",
    ),
    (
        "MAT406-2023-FEB-Q6",
        "b) Write the following system of linear equations in matrix form.",
        r"""b) Write the following system of linear equations in matrix form.
$x + y = -2$
$3x + 2y + z = 4$
$-x + z = 2$""",
        "printed page 6: b) system",
    ),
    (
        "MAT406-2023-JUL-Q1",
        "a) Simplify the following expressions:\ni)\nii)",
        r"""a) Simplify the following expressions:
i) $\frac{x^2 - 16}{x^2 - 7x + 12}$
ii) $\sqrt{y + 1} - \frac{y - 3}{\sqrt{y + 1}}$""",
        "printed page 2: a) i/ii expressions",
    ),
    (
        "MAT406-2023-JUL-Q3",
        "a) Solve the following inequalities for $x$ and express the solutions in interval notation:\ni)\nii)\niii)",
        r"""a) Solve the following inequalities for $x$ and express the solutions in interval notation:
i) $-5 \leq \frac{4 - 3x}{2} - 1 < 3$
ii) $3|2x + 5| > 9$
iii) $\frac{1}{x - 2} \geq \frac{3}{x + 2}$""",
        "printed page 3: a) i/ii/iii inequalities",
    ),
    (
        "MAT406-2023-JUL-Q3",
        "b) Sketch and shade the region that corresponds to the solution set for the following system of inequalities:",
        r"""b) Sketch and shade the region that corresponds to the solution set for the following system of inequalities:
$x + y < 2$
$x^2 \leq y$""",
        "printed page 3: b) system",
    ),
    (
        "MAT406-2023-JUL-Q3",
        "c) Solve the following system of equations using the substitution method:",
        r"""c) Solve the following system of equations using the substitution method:
$\sqrt{x} - 2y = -11$
$y - 2\sqrt{x} = 1$""",
        "printed page 4: c) system",
    ),
    (
        "MAT406-2023-JUL-Q6",
        "b) Consider the following system of linear equations:",
        r"""b) Consider the following system of linear equations:
$x + 2y - 2z = 3$
$y - 2z = -1$
$-x - 3y = 2$""",
        "printed page 6: b) system",
    ),
    (
        "MAT406-2024-JAN-Q1",
        "c) Find the point of intersection of two straight lines:",
        r"""c) Find the point of intersection of two straight lines:
$3x - y + 5 = 0$
$4x + 2y + 1 = 0$""",
        "printed page 2: c) equations",
    ),
    (
        "MAT406-2024-JAN-Q6",
        "b) The system of linear equations are given as follows:",
        r"""b) The system of linear equations are given as follows:
$x + 2y - 3z = 3$
$2x - y - z = 11$
$3x + 2y + z = -5$""",
        "printed page 5: b) system",
    ),
    (
        "MAT406-2024-JUL-Q1",
        "ii) the equation of the straight-line PR.\n(3 marks)\n(4 marks)",
        r"""ii) the equation of the straight-line PR.
(3 marks)
iii) the coordinates of R and distance of QR.
(4 marks)""",
        "printed page 2: a) iii text",
    ),
    (
        "MAT406-2024-JUL-Q1",
        "c) Find the point of intersection of two straight lines:",
        r"""c) Find the point of intersection of two straight lines:
$3x + 5y - 31 = 0$
$7x - 3y - 21 = 0$""",
        "printed page 2: c) equations",
    ),
    (
        "MAT406-2025-FEB-Q1",
        r"c) The intersection point of the following two lines is (9,5). Find $\beta$ .",
        r"""c) The intersection point of the following two lines is (9,5). Find $\beta$ .
$2x + \beta y - 3 = 0$
$-3x + 5y + 2 = 0$""",
        "printed page 2: c) equations",
    ),
    (
        "MAT406-2025-JUL-Q1-2",
        "b) By using the elimination method, find the point of intersection of the two straight lines given by",
        r"""b) By using the elimination method, find the point of intersection of the two straight lines given by
$4x + 3y - 12 = 0$
$5x - 2y + 10 = 0$""",
        "printed page 4: b) equations",
    ),
    (
        "MAT406-2025-JUL-Q2",
        "b) Find the reference angle for",
        r"""b) Find the reference angle for
i) $\theta = 100^{\circ}$
(3 marks)
ii) $\frac{4}{3}\pi$
(3 marks)""",
        "printed page 2: b) i/ii",
    ),
    (
        "MAT406-2025-JUL-Q2-2",
        "(a) Solve the following equation",
        r"""(a) Solve the following equation
i) $\sin^2 x = \frac{1}{4}$ for $0^{\circ} \leq x \leq 420^{\circ}$
(5 marks)
ii) $2\tan 2x - 3 = 0$ for $0^{\circ} \leq x \leq 360^{\circ}$
(5 marks)""",
        "printed page 4: (a) i/ii equations",
    ),
    (
        "MAT406-2026-FEB-Q1-2",
        "b) Find the point of intersection between the two lines $L_{1}$ and $L_{2}$ given by",
        r"""b) Find the point of intersection between the two lines $L_{1}$ and $L_{2}$ given by
$L_{1}: 2x - 3y = 1$
$L_{2}: -2x + y = 5$""",
        "printed page 4: b) L1/L2 equations",
    ),
]


def apply() -> dict:
    store = BankStore(BANK)
    assets = {str(row["id"]): row for row in store.assets()}
    applied = []
    missing = []
    touched = set()
    for qid, find, replace, evidence in CORRECTIONS:
        question = store.load_question(qid)
        if not question:
            missing.append({"question_id": qid, "reason": "question not found"})
            continue
        changed = False
        for key in ("native_text", "stem"):
            old = str(question.get(key) or "")
            if find in old:
                question[key] = old.replace(find, replace)
                changed = True
        for part in question.get("parts") or []:
            old = str(part.get("text") or "")
            if find in old:
                part["text"] = old.replace(find, replace)
                changed = True
        if not changed:
            missing.append({"question_id": qid,
                            "reason": f"text not found: {find[:80]}"})
            continue
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
        question["v4_text_correction"] = evidence
        save_json(store.question_path(qid), question)
        touched.add(qid)
        applied.append({"question_id": qid, "evidence": evidence,
                        "correction": {"find": find, "replace": replace}})
    report = {
        "schema_version": 1,
        "subject": "MAT406",
        "applied_on": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "questions": sorted(touched),
        "applied": applied,
        "missing": missing,
        "gate_a": "already approved; corrections are printed-text insertions",
    }
    save_json(REPORT, report)
    return report


if __name__ == "__main__":
    print(json.dumps({k: v for k, v in apply().items()
                      if k != "applied"}, indent=2))
