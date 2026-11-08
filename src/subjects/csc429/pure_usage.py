"""Shared CSC429 pure-extraction usage ledger and cost cap."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"
USAGE = TRACKING / "usage.json"
DEFAULT_CAP_USD = 5.0


def _cap() -> float:
    raw = os.environ.get("CSC429_COST_CAP_USD", "").strip()
    if raw:
        try:
            return float(raw)
        except ValueError:
            pass
    return DEFAULT_CAP_USD


def load() -> dict:
    payload = {
        "schema_version": 1,
        "subject": "CSC429",
        "cap_usd": _cap(),
        "spent_usd": 0.0,
        "by_stage": {},
        "calls": {"llm": 0, "vision": 0, "ocr": 0},
        "updated": None,
    }
    if USAGE.is_file():
        try:
            payload.update(json.loads(USAGE.read_text(encoding="utf-8")))
        except (OSError, ValueError):
            pass
    payload["cap_usd"] = _cap()
    return payload


def save(payload: dict) -> None:
    payload["updated"] = datetime.now(timezone.utc).isoformat()
    USAGE.parent.mkdir(parents=True, exist_ok=True)
    USAGE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")


def check(cost: float = 0.0) -> None:
    payload = load()
    if float(payload.get("spent_usd", 0.0)) + float(cost) > float(
            payload.get("cap_usd", DEFAULT_CAP_USD)):
        raise RuntimeError(
            f"CSC429 cost cap exceeded: spent ${payload['spent_usd']:.6f}, "
            f"cap ${payload['cap_usd']:.2f}")


def record(stage: str, *, cost_usd: float = 0.0, llm: int = 0,
           vision: int = 0, ocr: int = 0) -> dict:
    payload = load()
    payload["spent_usd"] = round(
        float(payload.get("spent_usd", 0.0)) + float(cost_usd), 6)
    stages = payload.setdefault("by_stage", {})
    row = stages.setdefault(stage, {"cost_usd": 0.0, "llm": 0, "vision": 0,
                                    "ocr": 0})
    row["cost_usd"] = round(float(row.get("cost_usd", 0.0)) + cost_usd, 6)
    row["llm"] = int(row.get("llm", 0)) + llm
    row["vision"] = int(row.get("vision", 0)) + vision
    row["ocr"] = int(row.get("ocr", 0)) + ocr
    calls = payload.setdefault("calls", {})
    calls["llm"] = int(calls.get("llm", 0)) + llm
    calls["vision"] = int(calls.get("vision", 0)) + vision
    calls["ocr"] = int(calls.get("ocr", 0)) + ocr
    save(payload)
    return payload


def main() -> None:
    payload = load()
    save(payload)
    print(json.dumps(payload, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
