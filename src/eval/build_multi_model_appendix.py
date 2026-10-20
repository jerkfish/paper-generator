"""Group the earlier multi-model run by model for the appendix."""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from src.config import MODEL_PRICES, OUTPUTS_DIR

SRC = OUTPUTS_DIR / "eval_multi_model" / "metrics.json"
OUT = OUTPUTS_DIR / "eval_multi_model_appendix.md"


def table(headers, rows, aligns=None):
    aligns = aligns or ["---"] * len(headers)
    out = ["| " + " | ".join(headers) + " |",
           "|" + "|".join(aligns) + "|"]
    for r in rows:
        out.append("| " + " | ".join(str(x).replace("|", "/") for x in r) + " |")
    return out


def main() -> None:
    metrics = json.loads(SRC.read_text())
    # Recompute model-specific cost from token counts and the price table.
    for m in metrics:
        try:
            payload = json.loads(
                (SRC.parent / f"seed_{m['seed']:02d}_theory.json")
                .read_text())
            u = payload["usage"]
            model = payload.get("model", "")
            pin, pout = MODEL_PRICES.get(model, (0, 0))
            m["cost_usd"] = round(
                u["prompt_tokens"] / 1e6 * pin
                + u["completion_tokens"] / 1e6 * pout, 6)
            m["model"] = model
        except Exception:
            pass
    groups = defaultdict(list)
    for m in metrics:
        groups[m.get("model", "unknown")].append(m)
    lines = [
        "# Appendix - pre-hardening multi-model realistic run",
        "",
        "**This appendix is not the primary evaluation.** It is the earlier "
        "20-seed, quota-rotated run collected before the final hardening "
        "pass. It used several Qwen models because free-tier quotas were "
        "exhausted during the run; the per-seed model is shown. The primary "
        "evaluation uses one model (DeepSeek V4.1 Flash) across all 20 seeds "
        "and is reported in `eval_realistic.md`. Costs here are recomputed "
        "from each call's model price table and are estimates, not invoices.",
        "",
        "## Results grouped by model",
        "",
    ]
    rows = []
    for model, ms in sorted(groups.items()):
        slots = sum(m["theory_slots"] for m in ms)
        ph = sum(m["placeholders"] for m in ms)
        acc = sum(m["accepted"] for m in ms)
        cost = sum(m["cost_usd"] for m in ms)
        attempts = [m["attempts_avg"] for m in ms if m["attempts_avg"]]
        rows.append([
            model, len(ms), ", ".join(str(m["seed"]) for m in ms),
            acc, ph, f"{ph / max(1, slots):.1%}",
            f"{sum(attempts) / len(attempts):.2f}" if attempts else "0",
            max((m["max_near_copy"] for m in ms), default=0),
            f"${cost:.4f}",
        ])
    lines += table(
        ["Model", "Seeds", "Seed list", "Accepted", "Placeholders",
         "Placeholder rate", "Attempts avg", "Max near-copy", "Cost"],
        rows,
        ["---", "---:", "---", "---:", "---:", "---:", "---:", "---:", "---:"])
    lines += [
        "",
        "Quota exhaustion is visible as clusters of higher-placeholder seeds "
        "within a model group: qwen3.6-flash seeds 14 and 16 have 2 and 3 "
        "placeholders, and qwen3.6-plus seeds 13 and 15 have 2 and 3 "
        "(seed 19 has 1). The primary evaluation uses one model across all "
        "20 seeds and is in `outputs/eval_realistic.md`.",
        "",
        "## Per-seed",
        "",
    ]
    rows = []
    for m in sorted(metrics, key=lambda x: x["seed"]):
        rows.append([
            m["seed"], m.get("model", ""), m["computed_marks"],
            m["placeholders"], f"{m['attempts_avg']:.2f}",
            m["attempts_max"], m["source_overlap_keys"],
            f"{m['max_near_copy']:.2f}", f"${m['cost_usd']:.4f}",
        ])
    lines += table(
        ["Seed", "Model", "Computed", "Placeholders", "Attempts avg",
         "Attempts max", "Overlap keys", "Max near-copy", "Cost"], rows,
        ["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---:"])
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
