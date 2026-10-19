"""Run realistic mode for seeds 1-20 and write outputs/eval_realistic.md."""
from __future__ import annotations

import argparse
import json
import traceback
from collections import Counter, defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from src.config import OUTPUTS_DIR
from src.planner.planner import build_plan, to_markdown
from src.theory.generate import generate, report as theory_report
from src.theory.verify import near_copy

OUT_DIR = OUTPUTS_DIR / "eval_realistic"
FINGERPRINT = [0, 0, 0, 0, 0, 2, 6, 6, 12, 14]


def _metrics(seed: int, summary: dict, payload: dict) -> dict:
    accepted = payload.get("accepted", [])
    placeholders = payload.get("placeholders", [])
    groups = payload.get("groups", [])
    attempts = [g.get("attempts", 0) for g in groups]
    near = [near_copy(q["question"]).ratio for q in accepted]
    overlap = payload.get("source_overlap", {})
    return {
        "seed": seed,
        "computed_marks": summary["computed_marks"],
        "computed_distribution": summary["computed_distribution"],
        "theory_slots": len(accepted) + len(placeholders),
        "accepted": len(accepted),
        "placeholders": len(placeholders),
        "placeholder_rate": (len(placeholders) /
                             max(1, len(accepted) + len(placeholders))),
        "attempts_total": sum(attempts),
        "attempts_avg": round(sum(attempts) / len(attempts), 2) if attempts else 0,
        "attempts_max": max(attempts) if attempts else 0,
        "attempts_gt3": sum(1 for a in attempts if a > 3),
        "source_overlap_keys": overlap.get("overlap_key_count", 0),
        "source_overlap_rate": overlap.get("overlap_rate", 0.0),
        "overlap_slot_count": overlap.get("overlap_slot_count", 0),
        "overlap_details": overlap.get("overlap_keys", {}),
        "max_near_copy": round(max(near), 4) if near else 0.0,
        "low_term_overlap_points": len(payload.get("low_term_overlap_points", [])),
        "scenario_count": len(payload.get("scenario_questions", [])),
        "planned_topic_mix": payload.get("planned_topic_mix", {}),
        "actual_topic_mix": payload.get("actual_topic_mix", {}),
        "cost_usd": payload.get("usage", {}).get("cost_usd", 0.0),
        "calls": payload.get("usage", {}).get("calls", 0),
        "tokens": payload.get("usage", {}).get("total_tokens", 0),
        "placeholder_slots": [p["slot"] for p in placeholders],
        "model": payload.get("model"),
    }


def run_seed(seed: int, model: str | None = None,
             skip_existing: bool = False) -> dict:
    plan_path = OUT_DIR / f"seed_{seed:02d}_planner.json"
    theory_path = OUT_DIR / f"seed_{seed:02d}_theory.json"
    if skip_existing and plan_path.exists() and theory_path.exists():
        try:
            summary = json.loads(plan_path.read_text())
            payload = json.loads(theory_path.read_text())
            if payload.get("accepted") is not None:
                return _metrics(seed, summary, payload)
        except Exception:
            pass
    _, summary = build_plan("realistic", "modern", None, seed)
    plan_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (OUT_DIR / f"seed_{seed:02d}_planner.md").write_text(
        to_markdown(summary), encoding="utf-8")
    payload = generate(plan_path, model=model)
    (OUT_DIR / f"seed_{seed:02d}_theory.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8")
    (OUT_DIR / f"seed_{seed:02d}_theory.md").write_text(
        theory_report(payload), encoding="utf-8")
    return _metrics(seed, summary, payload)


def _md_table(headers: list[str], rows: list[list], aligns: list[str] | None = None):
    aligns = aligns or ["---"] * len(headers)
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(aligns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(x).replace("|", "/")
                                       for x in row) + " |")
    return lines


def build_report(metrics: list[dict]) -> str:
    ok = [m for m in metrics if not m.get("error")]
    total_slots = sum(m["theory_slots"] for m in ok)
    total_ph = sum(m["placeholders"] for m in ok)
    total_accepted = sum(m["accepted"] for m in ok)
    total_cost = sum(m["cost_usd"] for m in ok)
    total_calls = sum(m["calls"] for m in ok)
    total_tokens = sum(m["tokens"] for m in ok)
    overlap_keys = sum(m["source_overlap_keys"] for m in ok)
    overlap_slots = sum(m["overlap_slot_count"] for m in ok)
    overlap_papers = sum(1 for m in ok if m["source_overlap_keys"] > 0)
    max_near = max((m["max_near_copy"] for m in ok), default=0.0)
    computed = Counter(m["computed_marks"] for m in ok)
    planned = defaultdict(float)
    actual = defaultdict(float)
    for m in ok:
        for t, v in m["planned_topic_mix"].items():
            planned[t] += v
        for t, v in m["actual_topic_mix"].items():
            actual[t] += v
    planned_total = sum(planned.values()) or 1
    actual_total = sum(actual.values()) or 1

    lines = [
        "# Realistic-mode evaluation - seeds 1-20",
        "",
        "Each seed runs the revised realistic planner and the full theory "
        "module (BM25 retrieval, cheap Qwen model, up to 3 retries, source "
        "overlap/topic/quote checks). Model and price settings are those in "
        "`src/config.py`; costs are estimates, not invoices.",
        "",
        "- Models used: " + ", ".join(f"**{m}**" for m in sorted({x.get("model") for x in ok if x.get("model")})) + " (free-tier quotas rotated; per-seed model in the table).",
        f"- Seeds completed: **{len(ok)}/20**"
        + (f"; failed: {', '.join(str(m['seed']) for m in metrics if m.get('error'))}"
           if len(ok) < 20 else ""),
        f"- Theory slots: {total_slots}; accepted **{total_accepted}**; "
        f"placeholders **{total_ph}**; placeholder rate "
        f"**{total_ph / max(1, total_slots):.1%}**.",
        f"- Source overlap: **{overlap_keys}** keys across "
        f"{overlap_papers}/20 papers; **{overlap_slots}** slots involved; "
        "target 0.",
        f"- Max near-copy similarity against the 35 past papers: "
        f"**{max_near:.2f}** (threshold 0.80).",
        f"- Calls: {total_calls}; tokens: {total_tokens}; "
        f"estimated total cost: **${total_cost:.4f}**; cost per accepted "
        f"question: **${total_cost / max(1, total_accepted):.4f}**.",
        f"- Scenario questions generated: "
        f"**{sum(m['scenario_count'] for m in ok)}** Part B slots.",
        f"- Low term-overlap marking points flagged: "
        f"**{sum(m['low_term_overlap_points'] for m in ok)}**.",
        "",
        "## Computed-marks distribution vs fingerprint",
        "",
        "| Computed marks | Fingerprint count | Eval count |",
        "|---:|---:|---:|",
    ]
    for v in range(0, 15):
        fp = FINGERPRINT.count(v)
        if fp or computed.get(v):
            lines.append(f"| {v} | {fp} | {computed.get(v, 0)} |")
    lines += [
        "",
        f"Fingerprint distribution: `{FINGERPRINT}`; eval mean "
        f"**{sum(m['computed_marks'] for m in ok) / max(1, len(ok)):.2f}** "
        f"marks/paper (fingerprint mean 4.0).",
        "",
        "## Per-seed results",
        "",
    ]
    rows = []
    for m in metrics:
        if m.get("error"):
            rows.append([m["seed"], "", "ERROR", "", "", "", "", "", "",
                         "", m["error"][:80]])
        else:
            rows.append([
                m["seed"], m.get("model", ""), m["computed_marks"],
                m["placeholders"],
                f"{m['attempts_avg']:.2f}", m["attempts_max"],
                m["source_overlap_keys"], f"{m['source_overlap_rate']:.1%}",
                f"{m['max_near_copy']:.2f}", m["scenario_count"],
                f"${m['cost_usd']:.4f}",
            ])
    lines += _md_table(
        ["Seed", "Model", "Computed", "Placeholders", "Attempts avg",
         "Attempts max", "Overlap keys", "Overlap rate", "Max near-copy",
         "Part B scenarios", "Cost"], rows,
        ["---:", "---", "---:", "---:", "---:", "---:", "---:", "---:",
         "---:", "---:", "---:"])
    lines += [
        "",
        "Attempts are per question group (12 groups per paper); a group "
        "contains one slot or an (a)/(b) pair.",
        "",
        "## Topic mix: planned vs actual (marks summed over 20 seeds)",
        "",
        "| Topic | Planned marks | Planned % | Actual marks | Actual % |",
        "|---|---:|---:|---:|---:|",
    ]
    for t in sorted(set(planned) | set(actual)):
        lines.append(f"| {t} | {planned.get(t, 0):.0f} | "
                     f"{planned.get(t, 0) / planned_total:.1%} | "
                     f"{actual.get(t, 0):.0f} | "
                     f"{actual.get(t, 0) / actual_total:.1%} |")
    lines += [
        "",
        "Actual topic mix is inferred from the cited decks (majority deck "
        "topic per accepted question; ties fall back to the slot topic).",
        "",
        "## Placeholder slots by seed",
        "",
    ]
    any_ph = False
    for m in ok:
        if m["placeholder_slots"]:
            any_ph = True
            lines.append(f"- seed {m['seed']}: {', '.join(m['placeholder_slots'])}")
    if not any_ph:
        lines.append("- none")
    lines += [
        "",
        "## Reading the metrics",
        "",
        "- Computed marks are sampled from the clean-modern fingerprint; the "
        "eval count should approximate the fingerprint distribution.",
        "- Placeholder rate counts theory slots left unresolved after the "
        "attempt limit.",
        "- Source overlap is the number of (deck, slide) keys cited by more "
        "than one accepted question; target is 0. A non-zero value is only "
        "allowed when retrieval had fewer than three unused chunks and is "
        "listed in the per-seed theory JSON.",
        "- Max near-copy is the maximum SequenceMatcher ratio of an accepted "
        "question against any of the 35 past papers; the verifier rejects at "
        "0.80.",
        "- Actual topic mix is inferred from cited decks, so it can differ "
        "from the planner's slot topics when a question cites a deck that "
        "serves more than one topic.",
        "- Multiple Qwen models were used because the free-tier quota was "
        "exhausted during the 20-seed run; the per-seed model is shown. The "
        "cost column uses the configurable qwen-flash list-price estimate, "
        "not per-model invoices.",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1-20")
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--model", default=None)
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if "-" in args.seeds:
        a, b = args.seeds.split("-")
        seeds = list(range(int(a), int(b) + 1))
    else:
        seeds = [int(x) for x in args.seeds.split(",")]
    metrics: list[dict] = []
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_seed, s, args.model, args.skip_existing): s for s in seeds}
        for fut in as_completed(futs):
            seed = futs[fut]
            try:
                m = fut.result()
                # group count for aggregate attempts
                payload_path = OUT_DIR / f"seed_{seed:02d}_theory.json"
                try:
                    payload = json.loads(payload_path.read_text())
                    m["groups"] = len(payload.get("groups", []))
                except Exception:
                    m["groups"] = 0
                metrics.append(m)
                print(f"seed {seed}: accepted={m['accepted']} "
                      f"placeholders={m['placeholders']} "
                      f"overlap={m['source_overlap_keys']} "
                      f"cost=${m['cost_usd']:.4f}", flush=True)
            except Exception as e:
                metrics.append({"seed": seed, "error": repr(e),
                                "trace": traceback.format_exc()[-1500:]})
                print(f"seed {seed}: ERROR {e!r}", flush=True)
    metrics.sort(key=lambda m: m["seed"])
    (OUT_DIR / "metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")
    md = build_report(metrics)
    (OUTPUTS_DIR / "eval_realistic.md").write_text(md, encoding="utf-8")
    print(f"wrote {OUTPUTS_DIR / 'eval_realistic.md'}")


if __name__ == "__main__":
    main()
