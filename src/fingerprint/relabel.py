"""Apply the owner-approved Topic x Task relabel to the Questions sheet.

- "Topic" column is overwritten with the code-classified topic.
- "Question type" column is renamed to "Task" and filled with the task.
- "Machine-verifiable" is overwritten with code-defined Y/N.
- Inherited topic / inherited inputs are flagged in "Wording note".
- The Task column gets a dropdown with the 7 task names.

Run:  uv run python -m src.fingerprint.relabel
"""
from __future__ import annotations

import re
from collections import defaultdict

from openpyxl import load_workbook
from openpyxl.worksheet.datavalidation import DataValidation

from src.config import TRACKING_XLSX
from src.fingerprint.types import TASK_NAMES, label_group

QUESTIONS_HEADERS = [
    "Paper ID", "Q no.", "Sub-part", "Topic", "Task", "Marks",
    "Has diagram", "Diagram type", "Machine-verifiable", "Wording note",
    "Original question text", "Confidence",
]


def _group_key(row: dict) -> tuple[str, str]:
    q = str(row["Q no."])
    m = re.match(r"^([A-Z])?(\d+)", q)
    root = (m.group(1) or "") + (m.group(2) or q) if m else q
    return (row["Paper ID"], root)


def relabel_rows(rows: list[dict]) -> list[dict]:
    """Label every row via its question group (sibling inheritance applies)."""
    order: dict[tuple[str, str], list[int]] = defaultdict(list)
    for i, row in enumerate(rows):
        order[_group_key(row)].append(i)
    cache: dict[tuple[str, str], list[dict]] = {}
    for key, idxs in order.items():
        cache[key] = label_group([rows[i] for i in idxs])
    for key, idxs in order.items():
        for i, lab in zip(idxs, cache[key]):
            row = rows[i]
            row["Topic"] = lab["topic"]
            row["Task"] = lab["task"]
            row["Machine-verifiable"] = "Y" if lab["machine_verifiable"] else "N"
            if lab["flags"]:
                note = str(row.get("Wording note") or "")
                note = (note + "; " if note and note != "-" else "") \
                    + "; ".join(lab["flags"])
                row["Wording note"] = note
    return rows


def main() -> None:
    wb = load_workbook(TRACKING_XLSX)
    ws = wb["Questions"]
    headers = [c.value for c in ws[1]]
    assert "Question type" in headers, "Questions sheet must exist (run Step 3 first)"
    old_task_idx = headers.index("Question type")
    topic_idx = headers.index("Topic")

    rows = [dict(zip(headers, row)) for row in ws.iter_rows(min_row=2, values_only=True)]
    relabel_rows(rows)
    # O(n^2) group lookup above is fine at this scale; done deliberately for clarity

    ws.cell(row=1, column=old_task_idx + 1).value = "Task"
    for i, row in enumerate(rows, start=2):
        ws.cell(row=i, column=topic_idx + 1).value = row["Topic"]
        ws.cell(row=i, column=old_task_idx + 1).value = row["Task"]
        ws.cell(row=i, column=headers.index("Machine-verifiable") + 1).value = \
            row["Machine-verifiable"]
        ws.cell(row=i, column=headers.index("Wording note") + 1).value = row["Wording note"]

    # dropdown on the Task column
    dv = DataValidation(type="list", formula1='"' + ",".join(TASK_NAMES) + '"',
                        allow_blank=True)
    ws.add_data_validation(dv)
    dv.add(f"{chr(64 + old_task_idx + 1)}2:{chr(64 + old_task_idx + 1)}{ws.max_row}")

    wb.save(TRACKING_XLSX)
    n = len(rows)
    mv = sum(1 for r in rows if r["Machine-verifiable"] == "Y")
    inh = sum(1 for r in rows if "inherited" in str(r.get("Wording note") or ""))
    print(f"relabelled {n} rows ({mv} machine-verifiable, {inh} inherited flags) -> "
          f"{TRACKING_XLSX}")


if __name__ == "__main__":
    main()
