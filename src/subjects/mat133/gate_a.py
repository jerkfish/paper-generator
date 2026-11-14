"""Record MAT133 V1 completion and stop at the V2 Gate A review.

Run after the MinerU extraction and ``src.subjects.mat133.bank_build``:

    uv run python -m src.subjects.mat133.gate_a

This is a state-recording helper.  It never approves Gate A; the owner does
that after reviewing the bank.
"""
from __future__ import annotations

import json
from pathlib import Path

from src import config
from src.subjects.lifecycle import load_state, save_state
from src.subjects.mat133 import extract

TRACKING = config.TRACKING_DIR / "mat133" / "v2"
BANK = TRACKING / "bank"
REGISTER = TRACKING / "papers_register.json"
INDEX = BANK / "index.json"
UNSURE = BANK / "unsure.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def record() -> dict:
    root = config.PROJECT_ROOT
    state = load_state(root, "MAT133")
    if state is None or "V0_intake" not in state.get("stages", {}):
        raise SystemExit("MAT133 v2 lifecycle state is missing")
    register = _load(REGISTER, {})
    expected = [row["paper_id"]
                for row in register.get("unique_papers") or []]
    status = _load(TRACKING / "extraction_status.json", {})
    done = [paper_id for paper_id, entry in
            (status.get("papers") or {}).items()
            if entry.get("status") == "done"]
    failed = [{"paper_id": paper_id,
               "error": entry.get("error", "")}
              for paper_id, entry in (status.get("papers") or {}).items()
              if entry.get("status") == "failed"]
    missing = [paper_id for paper_id in expected if paper_id not in done]

    v1 = state["stages"]["V1_extract"]
    v1["evidence"] = [
        "data/tracking/mat133/v2/papers_register.json",
        "data/tracking/mat133/v2/papers_summary.json",
        "data/tracking/mat133/v2/V1_PILOT_REPORT.md",
        "data/tracking/mat133/v2/V1_REPORT.md",
        "data/tracking/mat133/v2/extraction_status.json",
    ]
    v1["notes"] = (
        f"MinerU VLM extracted {len(done)} of {len(expected)} unique "
        f"papers; {len(failed)} failed, {len(missing)} missing.")
    v1["blockers"] = ([f"missing dossier: {paper_id}" for paper_id in missing]
                      + [f"failed extraction: {row['paper_id']}: "
                         f"{row['error']}" for row in failed])
    v1["status"] = "done" if not missing and not failed else "in_progress"
    state["parser_provenance"] = extract.parser_provenance()

    index = _load(INDEX, {})
    counts = dict(index.get("counts") or {})
    v2 = state["stages"]["V2_bank"]
    if index:
        v2["status"] = "in_progress"
        v2["evidence"] = [
            "data/tracking/mat133/v2/bank/index.json",
            "data/tracking/mat133/v2/bank/gate1_report.json",
            "data/tracking/mat133/v2/bank/gate1_report.md",
            "data/tracking/mat133/v2/bank/review/index.html",
            "data/tracking/mat133/v2/bank/review/index_by_paper.html",
            "data/tracking/mat133/v2/bank/review/marks.csv",
            "data/tracking/mat133/v2/bank/unsure.json",
            "data/tracking/mat133/v2/bank/duplicates.json",
        ]
        v2["notes"] = (
            f"{counts.get('questions', 0)} questions from "
            f"{counts.get('papers', 0)} papers; "
            f"{counts.get('extracted', 0)} extracted, "
            f"{counts.get('needs_fix', 0)} needs fix. Gate A review is "
            "pending.")
        v2["blockers"] = ["Gate A approval is pending owner review."]
        state["bank"] = {
            "questions": int(counts.get("questions", 0)),
            "approved": 0,
            "needs_fix": int(counts.get("needs_fix", 0)),
            "rejected": 0,
            "extracted": int(counts.get("extracted", 0)),
            "assets": int(counts.get("assets", 0)),
            "duplicate_clusters": int(counts.get("duplicate_clusters", 0)),
            "near_duplicate_pairs": int(
                counts.get("near_duplicate_pairs", 0)),
            "references": int(counts.get("references", 0)),
            "unresolved_references": int(
                counts.get("unresolved_references", 0)),
            "papers": int(counts.get("papers", 0)),
            "papers_expected": int(counts.get("papers_expected", 0)),
            "papers_missing": int(counts.get("papers_missing", 0)),
        }
        state["gates"]["A"] = {
            "status": "pending",
            "by": "",
            "on": "",
            "evidence": [
                "data/tracking/mat133/v2/bank/gate1_report.json",
                "data/tracking/mat133/v2/bank/gate1_report.md",
                "data/tracking/mat133/v2/bank/review/index.html",
                "data/tracking/mat133/v2/bank/review/index_by_paper.html",
                "data/tracking/mat133/v2/bank/review/marks.csv",
                "data/tracking/mat133/v2/bank/unsure.json",
                "data/tracking/mat133/v2/bank/duplicates.json",
            ],
            "note": (
                f"{counts.get('questions', 0)} questions in "
                f"{counts.get('papers', 0)} papers; "
                f"{counts.get('needs_fix', 0)} needs fix; "
                f"{counts.get('papers_missing', 0)} missing papers."),
        }
    else:
        v2["status"] = "pending"
        v2["blockers"] = ["V2 bank has not been built."]
        state["gates"]["A"] = {
            "status": "pending", "by": "", "on": "", "evidence": [],
            "note": "V2 bank has not been built.",
        }

    bank_unsure = _load(UNSURE, {}).get("items") or []
    state["unsure"] = [
        item for item in state.get("unsure") or []
        if item.get("stage") != "V2_bank"
    ]
    grouped: dict[str, dict] = {}
    for item in bank_unsure:
        key = (item.get("question_id") or item.get("paper_id")
               or item.get("asset_id") or "bank")
        row = grouped.setdefault(key, {
            "stage": "V2_bank",
            "count": 0,
            "blocking": False,
            "opened": item.get("opened", "2026-11-14"),
        })
        row["count"] += 1
        row["blocking"] = row["blocking"] or bool(item.get("blocking", True))
    for key, row in sorted(grouped.items()):
        state["unsure"].append({
            "stage": "V2_bank",
            "item": (f"{key}: {row['count']} unresolved bank issue(s); see "
                     "data/tracking/mat133/v2/bank/gate1_report.md"),
            "blocking": row["blocking"],
            "opened": row["opened"],
        })
    state["lifecycle_status"] = (
        "awaiting_gate_a" if index and v1["status"] == "done"
        else "in_progress")
    state["stop_reason"] = (
        "Gate A bank review." if index and v1["status"] == "done"
        else "V1 extraction has missing or failed papers.")
    state.setdefault("documents", {})["v2_status"] = (
        "V2_bank_pending_gate_a" if index else "V1_extract")
    path = save_state(root, "MAT133", state)
    return {
        "lifecycle": str(path),
        "v1_status": v1["status"],
        "v2_status": v2["status"],
        "papers_done": len(done),
        "papers_expected": len(expected),
        "missing": missing,
        "failed": failed,
        "bank": state.get("bank", {}),
        "gate_a": state["gates"]["A"],
    }


def main() -> None:
    print(json.dumps(record(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
