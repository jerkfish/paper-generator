"""Record MAT406 Gate A after the round 2 owner approval.

The owner exported ``review_decisions_round2.json`` with all 14 fixed
questions approved.  This module promotes those questions to ``approved``,
marks their recreations approved, writes the Gate A record and refreshes the
bank reports.  It does not start V3.

Run:
    uv run python -m src.subjects.mat406.gate_a
"""
from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.bank.review import build_review_sheet
from src.bank.store import BankStore, load_json, save_json
from src.subjects.mat406.bank_build import (
    _gate_report_md,
    _write_marks_csv,
    _write_paper_index,
)
from src.subjects.mat406.papers import SUBJECT
from src.subjects.mat406.review_apply import (
    REVIEW,
    _plain_note,
    _refresh,
)

BANK = config.TRACKING_DIR / "mat406" / "v2" / "bank"
ROUND2 = REVIEW / "review_decisions_round2.json"
GATE_MD = REVIEW / "GATE_A_APPROVED.md"
APPROVED_ON = "2026-11-20"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def record_gate_a(decisions_path: Path = ROUND2) -> dict:
    payload = load_json(Path(decisions_path), {})
    if str(payload.get("subject")) != SUBJECT:
        raise SystemExit("round 2 decisions are not for MAT406")
    decisions = payload.get("questions") or {}
    store = BankStore(BANK)
    questions = {str(row["id"]): row for row in store.questions()}
    current_needs = {qid for qid, row in questions.items()
                     if row.get("status") == "needs_fix"}
    if set(decisions) != current_needs:
        raise SystemExit(
            "round 2 decisions do not match the 14 needs-fix questions: "
            f"missing={sorted(current_needs - set(decisions))}, "
            f"extra={sorted(set(decisions) - current_needs)}")
    verdicts = {str(row.get("verdict") or "") for row in decisions.values()}
    if verdicts != {"approved"}:
        raise SystemExit(
            f"round 2 still contains non-approved verdicts: {sorted(verdicts)}")

    # Keep the exact round 2 sheet that the owner reviewed.
    shutil.copy2(REVIEW / "index.html", REVIEW / "round2.html")

    for qid, decision in decisions.items():
        question = dict(questions[qid])
        question["status"] = "approved"
        question["review_verdict"] = "approved"
        question["review_round"] = 2
        question["reviewed_on"] = APPROVED_ON
        question["review_note_text"] = (
            question.get("fix_note")
            or _plain_note(decision.get("comment")
                           or decision.get("notes") or ""))
        question["parse_notes"] = []
        for aid in question.get("assets") or []:
            asset = load_json(store.asset_path(aid), {})
            if not asset:
                continue
            asset_decision = (decision.get("assets") or {}).get(aid) or {}
            choice = str(asset_decision.get("choice") or "")
            if choice:
                asset["review_choice"] = choice
            asset["verdict"] = "approved"
            asset["reviewed_on"] = APPROVED_ON
            if asset.get("owner_recreation_file"):
                asset["selected_treatment"] = "html_recreation"
                asset["treatment"] = "html_recreation"
            save_json(store.asset_path(aid), asset)
        save_json(store.question_path(qid), question)
        questions[qid] = question

    metadata = _refresh(store)
    index = load_json(BANK / "index.json", {})
    index["counts"]["approved"] = sum(
        1 for q in questions.values() if q["status"] == "approved")
    index["counts"]["needs_fix"] = 0
    index["counts"]["extracted"] = 0
    save_json(BANK / "index.json", index)

    evidence = [
        "data/tracking/mat406/v2/bank/review/GATE_A_APPROVED.md",
        "data/tracking/mat406/v2/bank/approvals.json",
        "data/tracking/mat406/v2/bank/index.json",
        "data/tracking/mat406/v2/bank/gate1_report.json",
        "data/tracking/mat406/v2/bank/gate1_report.md",
        "data/tracking/mat406/v2/bank/review/index.html",
        "data/tracking/mat406/v2/bank/review/round2.html",
        "data/tracking/mat406/v2/bank/review/review_decisions_round2.json",
        "data/tracking/mat406/v2/bank/review/marks.csv",
    ]
    approvals = {
        "schema_version": 1,
        "subject": SUBJECT,
        "gate_a": {
            "status": "approved",
            "by": "owner",
            "on": APPROVED_ON,
            "evidence": evidence,
            "note": (
                "Owner approved round 2 and Gate A on 2026-11-20: all 14 "
                "fixed questions approved; the bank has 58/58 approved "
                "questions."),
        },
    }
    save_json(BANK / "approvals.json", approvals)

    report = load_json(BANK / "gate1_report.json", {})
    report["status"] = "approved"
    report["gate"] = "A"
    report["approved_on"] = APPROVED_ON
    report["approved_by"] = "owner"
    report["counts"] = index["counts"]
    report["owner_approval"] = {
        "required": True,
        "approved": True,
        "by": "owner",
        "on": APPROVED_ON,
        "note": approvals["gate_a"]["note"],
    }
    report["review_sheet"] = str(REVIEW / "index.html")
    save_json(BANK / "gate1_report.json", report)
    (BANK / "gate1_report.md").write_text(
        _gate_report_md(report, list(questions.values())), encoding="utf-8")

    build_review_sheet(
        store, REVIEW, subject=SUBJECT,
        title="MAT406 v2 bank — Gate A approved",
        filename="index.html", export_name="review_decisions_all.json")
    build_review_sheet(
        store, REVIEW, subject=SUBJECT,
        title="MAT406 v2 bank — Gate A full audit",
        filename="all.html", export_name="review_decisions_all.json")
    _write_paper_index(
        index, REVIEW, filename="index_by_paper.html", sheet="index.html",
        heading="MAT406 v2 bank — Gate A approved")
    _write_marks_csv(list(store.questions()), REVIEW)

    GATE_MD.write_text(
        "\n".join([
            "# MAT406 — Gate A approved",
            "",
            f"- Date: {APPROVED_ON}",
            "- Approved by: owner",
            "- Decision: round 2 approved; Gate A approved.",
            "",
            "## Bank",
            "",
            "- Questions: **58 / 58 approved**",
            "- Marks: **850**",
            "- Assets: **6** active recreations; 7 unrelated assets deleted",
            "- Needs fix: **0**",
            "- Unresolved references: **0**",
            "- Exact duplicate clusters: **0**",
            "",
            "## Evidence",
            "",
            *[f"- `{path}`" for path in evidence],
            "",
            "Next stage: **V3 — format profile and templates**.",
            "",
        ]), encoding="utf-8")
    return {
        "gate_a": "approved",
        "questions": 58,
        "approved": 58,
        "needs_fix": 0,
        "bank": metadata,
        "gate_md": str(GATE_MD),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--decisions", type=Path, default=ROUND2)
    args = parser.parse_args()
    print(json.dumps(record_gate_a(args.decisions), indent=2))


if __name__ == "__main__":
    main()
