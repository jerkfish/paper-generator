"""Gate reports and approval checks for the Type D pipeline."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src import config
from src.subjects.csc429 import pure_usage

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
REPORT_JSON = BANK / "gate1_report.json"
REPORT_MD = BANK / "gate1_report.md"
LIFECYCLE = config.PROJECT_ROOT / "subjects" / "CSC429" / "lifecycle_state.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def gate1_report() -> dict:
    index = _load(BANK / "index.json", {})
    unsure = _load(BANK / "unsure.json", {}).get("items", [])
    compare = _load(BANK / "compare_report.json", {})
    review = _load(BANK / "review_index.json", {})
    usage = pure_usage.load()
    questions = list((BANK / "questions").glob("*.json"))
    assets = list((BANK / "assets").glob("*.json"))
    status = Counter()
    flags = Counter()
    for path in questions:
        row = _load(path, {})
        status[str(row.get("status", "unknown"))] += 1
        for flag in row.get("review_flags") or []:
            flags[str(flag)] += 1
    payload = {
        "schema_version": 1,
        "subject": "CSC429",
        "stage": "P3",
        "gate": "GATE 1",
        "status": "awaiting_owner_review",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "counts": {
            "papers": index.get("papers"),
            "questions": len(questions),
            "subparts": index.get("subparts"),
            "questions_with_assets": index.get("questions_with_assets"),
            "assets": len(assets),
            "asset_kinds": index.get("asset_kinds", {}),
            "status": dict(sorted(status.items())),
            "review_flags": dict(sorted(flags.items())),
            "unsure": len(unsure),
        },
        "tables": {
            "native_accepted": compare.get("native_table_accepted"),
            "crop_fallback": compare.get("table_crop_fallback"),
            "original_only": compare.get("original_only"),
        },
        "review": review,
        "unsure": unsure,
        "cost": {
            "spent_usd": usage.get("spent_usd", 0.0),
            "cap_usd": usage.get("cap_usd"),
            "calls": usage.get("calls", {}),
            "by_stage": usage.get("by_stage", {}),
        },
        "templates": _load(TRACKING / "p0_reset_report.json", {}).get(
            "templates", []),
        "rejected_registry": _load(
            TRACKING / "rejected_registry.json", {}).get("counts", {}),
        "what_changed": [
            "Locked CSC429 to Type D / pure_extraction; generators and parametric variants disabled.",
            "Archived every earlier CSC429 seed, cache, asset and question bank.",
            "Wrote rejected_registry.json with seed ids, asset hashes and seed-file hashes.",
            "Reset the lifecycle to schema v2 and recorded P0 approvals.",
            "Built the new bank/ contracts: 215 questions and 96 source-crop assets.",
            "Locked pictures, figures, diagrams and formulas to original crops.",
            "Accepted 15 native tables after OCR comparison; kept 21 table crops.",
            "Generated 20 local HTML review sheets.",
        ],
        "could_not_verify": [
            "No vision API provider is configured in this repository; scanned pages use the existing Windows OCR/layout cache.",
            "OCR text can still be noisy; the affected questions are marked needs_fix or carry ocr_source.",
            "Four questions have unresolved reference or mark ambiguity and must be corrected by the owner.",
            "No owner verdicts have been imported yet; approved is 0.",
            "No file named scheme_updated.docx was found; the accepted experiment scheme_template.docx is used and flagged for confirmation.",
        ],
    }
    _save(REPORT_JSON, payload)
    lines = [
        "# CSC429 — GATE 1 report",
        "",
        f"Status: **{payload['status']}**",
        "",
        "## Counts",
        "",
        f"- Papers: {payload['counts']['papers']}",
        f"- Questions: {payload['counts']['questions']}",
        f"- Sub-parts: {payload['counts']['subparts']}",
        f"- Questions with assets: {payload['counts']['questions_with_assets']}",
        f"- Assets: {payload['counts']['assets']} "
        f"({payload['counts']['asset_kinds']})",
        f"- Question status: {payload['counts']['status']}",
        f"- Open unsure items: {payload['counts']['unsure']}",
        f"- Native tables accepted: {payload['tables']['native_accepted']}",
        f"- Table crops kept: {payload['tables']['crop_fallback']}",
        "",
        "## Unsure items",
        "",
    ]
    for item in unsure:
        lines.append(
            f"- `{item.get('code')}` — {item.get('paper_id')} "
            f"page {item.get('pages')} — {item.get('detail')} — "
            f"`{item.get('path')}`")
    lines += [
        "",
        "## Cost",
        "",
        f"- Spent: **${payload['cost']['spent_usd']:.6f}** "
        f"of ${payload['cost']['cap_usd']:.2f}",
        f"- Calls: {payload['cost']['calls']}",
        "",
        "## Review sheets",
        "",
        f"- `{payload['review'].get('index', 'data/tracking/csc429/bank/review/index.html')}`",
        "",
        "## What changed",
        "",
    ]
    lines += [f"- {item}" for item in payload["what_changed"]]
    lines += ["", "## Could not verify", ""]
    lines += [f"- {item}" for item in payload["could_not_verify"]]
    lines += [
        "",
        "## Gate instruction",
        "",
        "Open the review index, review every question and asset, then export",
        "the per-paper decisions JSON into `bank/inbox/` and run",
        "`uv run python -m src.subjects.csc429.pure_approvals`.",
        "GATE 1 is not approved until the owner records the approval.",
        "",
    ]
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return payload


def gate_approved() -> bool:
    state = _load(LIFECYCLE, {})
    return bool(state.get("gate1_approved")) or (
        state.get("gate") == "GATE 1"
        and state.get("gate_status") == "approved")


def gate2_approved() -> bool:
    state = _load(LIFECYCLE, {})
    return (state.get("gate") == "GATE 2"
            and state.get("gate_status") == "approved")


def require_gate() -> None:
    if not gate_approved():
        raise RuntimeError(
            "GATE 1 is not approved; seed assembly is blocked")


def main() -> None:
    print(json.dumps(gate1_report(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
