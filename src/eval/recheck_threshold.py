"""Re-run accepted questions that fail a tighter near-copy threshold.

This reuses the primary 0.80 set: questions already below the new threshold
are kept; rejected questions are regenerated through the normal generator.
It is a sensitivity run, not a second independent 20-seed generation.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import config
from src.config import OUTPUTS_DIR
from src.eval import evaluate as E
from src.planner.planner import to_markdown
from src.theory.generate import generate, report as theory_report
from src.theory.models import Placeholder
from src.theory.verify import near_copy

BASE_DIR = OUTPUTS_DIR / "eval_realistic_primary"
OUT_DIR = OUTPUTS_DIR / "eval_realistic_070"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--threshold", type=float, default=0.70)
    ap.add_argument("--model", default=config.QWEN_CHEAP_MODEL)
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    metrics = []
    for plan_path in sorted(BASE_DIR.glob("seed_*_planner.json")):
        seed = int(plan_path.stem.split("_")[1])
        base_path = BASE_DIR / f"seed_{seed:02d}_theory.json"
        summary = json.loads(plan_path.read_text())
        base = json.loads(base_path.read_text())
        slots = {s["slot"]: s for s in summary["slots"]}
        kept, rejected = [], []
        for q in base.get("accepted", []):
            if near_copy(q["question"]).ratio < args.threshold:
                kept.append(q)
            else:
                rejected.append(q["slot"])
        # Existing placeholders plus newly rejected slots.
        placeholders = list(base.get("placeholders", []))
        for sid in rejected:
            s = slots[sid]
            placeholders.append(Placeholder(
                slot=sid, marks=s["marks"], topic=s["topic"],
                task=s["task"],
                reason=f"near-copy >= {args.threshold:.2f}; regenerated",
                attempts=0,
                low_style_confidence=bool(
                    s.get("low_style_confidence"))).model_dump())
        previous = {
            "accepted": kept,
            "placeholders": placeholders,
            "usage": base.get("usage", {}),
            "groups": [],
        }
        payload = generate(plan_path, model=args.model, previous=previous,
                           near_copy_threshold=args.threshold)
        payload["threshold_recheck"] = {
            "base": "eval_realistic_primary (0.80)",
            "threshold": args.threshold,
            "rejected_from_base": len(rejected),
            "reused": len(kept),
            "base_cost_usd": base.get("usage", {}).get("cost_usd", 0.0),
            "incremental_cost_usd": round(
                payload["usage"]["cost_usd"]
                - base.get("usage", {}).get("cost_usd", 0.0), 6),
        }
        (OUT_DIR / f"seed_{seed:02d}_planner.json").write_text(
            json.dumps(summary, indent=2), encoding="utf-8")
        (OUT_DIR / f"seed_{seed:02d}_planner.md").write_text(
            to_markdown(summary), encoding="utf-8")
        (OUT_DIR / f"seed_{seed:02d}_theory.json").write_text(
            json.dumps(payload, indent=2), encoding="utf-8")
        (OUT_DIR / f"seed_{seed:02d}_theory.md").write_text(
            theory_report(payload), encoding="utf-8")
        metrics.append(E._metrics(seed, summary, payload))
    E.OUT_DIR = OUT_DIR
    E.REPORT_PATH = OUTPUTS_DIR / "eval_realistic_070.md"
    E.METRICS_PATH = OUT_DIR / "metrics.json"
    E.NEAR_COPY_THRESHOLD = args.threshold
    E.METRICS_PATH.write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    md = E.build_report(metrics)
    E.REPORT_PATH.write_text(md, encoding="utf-8")
    print(f"wrote {E.REPORT_PATH}")


if __name__ == "__main__":
    main()
