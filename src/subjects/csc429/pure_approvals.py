"""Import P3 review decisions into approvals/corrections and update statuses."""
from __future__ import annotations

import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
INBOX = BANK / "inbox"
APPROVALS = BANK / "approvals.json"
CORRECTIONS = BANK / "corrections.json"
REPORT = BANK / "gate1_import_report.json"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _save(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")


def import_file(path: Path) -> dict:
    payload = _load(path, {})
    if str(payload.get("subject", "")).upper() != "CSC429":
        return {"file": str(path), "error": "wrong subject", "questions": 0}
    approvals = _load(APPROVALS, {"schema_version": 1, "by_qid": {}})
    corrections = _load(CORRECTIONS, {"schema_version": 1, "by_qid": {}})
    imported = 0
    stale = []
    errors = []
    for qid, decision in (payload.get("questions") or {}).items():
        qpath = QUESTIONS / f"{qid}.json"
        if not qpath.is_file():
            errors.append(f"{qid}: question not found")
            continue
        question = _load(qpath, {})
        expected = str(question.get("content_hash", ""))
        supplied = str(decision.get("content_hash", ""))
        if supplied and supplied != expected:
            stale.append(qid)
            continue
        verdict = str(decision.get("verdict", "")).strip()
        notes = str(decision.get("notes", "")).strip()
        if verdict:
            question["status"] = {
                "approved": "approved",
                "rejected": "rejected",
                "needs_fix": "needs_fix",
            }.get(verdict, question.get("status", "extracted"))
        asset_choices = dict(decision.get("assets") or {})
        for aid, choice in asset_choices.items():
            apath = ASSETS / f"{aid}.json"
            if not apath.is_file():
                errors.append(f"{qid}: asset {aid} not found")
                continue
            asset = _load(apath, {})
            if choice == "use_original":
                asset["treatment"] = "crop"
                asset["verdict"] = "approved"
            elif choice == "use_recreation":
                if not asset.get("native_table"):
                    errors.append(
                        f"{qid}: asset {aid} has no recreation to use")
                    asset["verdict"] = "needs_fix"
                else:
                    asset["treatment"] = "native_table"
                    asset["verdict"] = "approved"
            else:
                errors.append(f"{qid}: unknown asset choice {choice!r}")
            asset["verdict_note"] = notes
            _save(apath, asset)
        _save(qpath, question)
        record = {
            "verdict": verdict,
            "notes": notes,
            "content_hash": expected,
            "source_file": path.name,
            "imported_at": datetime.now(timezone.utc).isoformat(),
            "assets": asset_choices,
        }
        approvals.setdefault("by_qid", {})[qid] = record
        corrections.setdefault("by_qid", {})[qid] = {
            "notes": notes,
            "content_hash": expected,
            "assets": asset_choices,
        }
        imported += 1
    _save(APPROVALS, approvals)
    _save(CORRECTIONS, corrections)
    return {
        "file": str(path),
        "questions": imported,
        "stale": stale,
        "errors": errors,
    }


def import_inbox() -> dict:
    INBOX.mkdir(parents=True, exist_ok=True)
    results = []
    for path in sorted(INBOX.glob("*.json")):
        results.append(import_file(path))
    counts = Counter()
    for qpath in QUESTIONS.glob("*.json"):
        question = _load(qpath, {})
        counts[str(question.get("status", "unknown"))] += 1
    report = {
        "schema_version": 1,
        "subject": "CSC429",
        "imported_at": datetime.now(timezone.utc).isoformat(),
        "results": results,
        "status_counts": dict(sorted(counts.items())),
        "approved": counts.get("approved", 0),
        "pending": counts.get("extracted", 0),
    }
    _save(REPORT, report)
    return report


def main() -> None:
    print(json.dumps(import_inbox(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
