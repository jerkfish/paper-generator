"""Build the revised evaluation report with quota disclosure and sensitivity."""
from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path

from src.config import MODEL_PRICES, OUTPUTS_DIR
from src.eval.evaluate import _md_table
from src.theory.bm25 import TOPIC_DECKS
from src.theory.verify import near_copy

FULL = OUTPUTS_DIR / "eval_multi_model"
HARD = OUTPUTS_DIR / "eval_realistic_primary"
OUT = OUTPUTS_DIR / "eval_realistic_prior.md"
FINGERPRINT = [0, 0, 0, 0, 0, 2, 6, 6, 12, 14]


def _cost(payload: dict) -> float:
    u = payload.get("usage", {})
    model = payload.get("model") or u.get("model", "")
    pin, pout = MODEL_PRICES.get(model, (0, 0))
    return (u.get("prompt_tokens", 0) / 1e6 * pin
            + u.get("completion_tokens", 0) / 1e6 * pout)


def _load(directory: Path):
    rows = []
    for p in sorted(directory.glob("seed_*_theory.json")):
        seed = int(p.stem.split("_")[1])
        payload = json.loads(p.read_text())
        plan = json.loads((directory / f"seed_{seed:02d}_planner.json")
                          .read_text())
        rows.append({"seed": seed, "payload": payload, "plan": plan})
    return rows


def _metrics(rows):
    accepted = sum(len(r["payload"].get("accepted", [])) for r in rows)
    placeholders = sum(len(r["payload"].get("placeholders", [])) for r in rows)
    slots = accepted + placeholders
    points = sum(len(q["marking_points"]) for r in rows
                 for q in r["payload"].get("accepted", []))
    low = sum(1 for r in rows for q in r["payload"].get("accepted", [])
              for pt in q["marking_points"] if pt.get("low_term_overlap"))
    overlap = sum(r["payload"].get("source_overlap", {}).get(
        "overlap_key_count", 0) for r in rows)
    violations = sum(len(r["payload"].get("deck_topic_violations", []))
                     for r in rows)
    cost = sum(_cost(r["payload"]) for r in rows)
    calls = sum(r["payload"].get("usage", {}).get("calls", 0) for r in rows)
    tokens = sum(r["payload"].get("usage", {}).get("total_tokens", 0)
                 for r in rows)
    ratios = [near_copy(q["question"]).ratio for r in rows
              for q in r["payload"].get("accepted", [])]
    attempts = [g.get("attempts", 0) for r in rows
                for g in r["payload"].get("groups", [])]
    point_retries = sum(g.get("point_retry_calls", 0) for r in rows
                        for g in r["payload"].get("groups", []))
    scen_sampled = sum(1 for r in rows for g in r["payload"].get("groups", [])
                      if g.get("scenario_sampled"))
    scen_slots = sum(len(r["payload"].get("scenario_questions", []))
                     for r in rows)
    return {
        "seeds": [r["seed"] for r in rows], "accepted": accepted,
        "placeholders": placeholders, "slots": slots,
        "placeholder_rate": placeholders / max(1, slots),
        "points": points, "low": low, "low_rate": low / max(1, points),
        "overlap": overlap, "violations": violations,
        "max_near": max(ratios, default=0), "cost": cost,
        "per_accepted": cost / max(1, accepted), "calls": calls,
        "tokens": tokens, "attempt_max": max(attempts, default=0),
        "point_retries": point_retries, "scen_sampled": scen_sampled,
        "scen_slots": scen_slots,
        "computed": [r["plan"]["computed_marks"] for r in rows],
    }


def main() -> None:
    full = _load(FULL)
    hard = _load(HARD)
    hard_valid = [r for r in hard
                  if r["payload"].get("usage", {}).get("cost_usd", 0) > 0
                  and r["payload"].get("accepted")]
    fm = _metrics(full)
    hm = _metrics(hard_valid)
    groups = defaultdict(list)
    for r in full:
        groups[r["payload"].get("model", "unknown")].append(r)
    model_rows = []
    for model, rs in sorted(groups.items()):
        mm = _metrics(rs)
        model_rows.append([model, len(rs), mm["accepted"], mm["placeholders"],
                           f"{mm['placeholder_rate']:.1%}",
                           f"${mm['cost']:.4f}",
                           f"${mm['per_accepted']:.4f}"])
    accepted_rows = []
    low_rows = []
    for r in full:
        for q in r["payload"].get("accepted", []):
            nc = near_copy(q["question"])
            accepted_rows.append((nc.ratio, r["seed"], q, nc))
            for pt in q["marking_points"]:
                if pt.get("low_term_overlap"):
                    low_rows.append((r["seed"], q["slot"],
                                     pt.get("term_overlap", 0),
                                     pt["point"], pt["quote"]))
    accepted_rows.sort(key=lambda x: -x[0])
    top = accepted_rows[:10]
    rejected70 = sum(1 for ratio, _, _, _ in accepted_rows if ratio >= 0.70)
    proj_ph = fm["placeholders"] + rejected70
    # Rejected questions become placeholders; they do not add theory slots.
    proj_rate = proj_ph / max(1, fm["slots"])
    comp = Counter(fm["computed"])
    lines = [
        "# Revised realistic-mode evaluation",
        "",
        "## Quota blocker and model choice",
        "",
        "The requested one-model 20-seed rerun could not be completed. Free-tier "
        "quota was exhausted on every available Qwen model and on the DeepSeek "
        "backups after 5-9 seeds. The report therefore distinguishes:",
        "",
        "- **Full 20-seed dataset** below: the quota-rotated multi-model run "
        "(pre-hardening), kept complete so every requested metric has a "
        "20-seed basis. Grouped appendix: `eval_multi_model_appendix.md`.",
        f"- **Hardened single-model validation**: `deepseek-v4-flash-0731`, "
        f"{len(hard_valid)} seeds completed before quota; post-hardening "
        "metrics are shown separately.",
        "",
        "Model selection from the earlier multi-model data:",
        "",
    ]
    lines += _md_table(
        ["Model", "Seeds", "Accepted", "Placeholders", "Placeholder rate",
         "Cost (actual model price)", "Cost / accepted"], model_rows,
        ["---", "---:", "---:", "---:", "---:", "---:", "---:"])
    lines += [
        "",
        "Costs below use the per-model price table in `src/config.py` and are "
        "**estimates**, not invoices. Each seed's cost uses the model that "
        "actually served its calls.",
        "",
        "**Selected primary model: `qwen3.8-flash`** - cheapest and fewest "
        "placeholders in the earlier data: 5 seeds, 118/119 accepted, 1 "
        "placeholder (0.8%), estimated $0.0195 total and $0.0002 per accepted. "
        "Its free quota stopped the 20-seed rerun. The DeepSeek backups were "
        "the only models still available later; the hardened single-model "
        "subset is therefore reported as validation, not as a completed "
        "20-seed primary. This is a provider quota limitation, not a pipeline "
        "change.",
        "",
        "## Full 20-seed dataset (multi-model, pre-hardening)",
        "",
        f"- Seeds: {len(full)}; theory slots: {fm['slots']}; accepted "
        f"**{fm['accepted']}**; placeholders **{fm['placeholders']}** "
        f"({fm['placeholder_rate']:.1%}).",
        f"- Source overlap: **{fm['overlap']}** keys; allowed-deck "
        f"violations: **{fm['violations']}**.",
        f"- Max near-copy: **{fm['max_near']:.3f}**.",
        f"- Calls: {fm['calls']}; tokens: {fm['tokens']}; estimated cost "
        f"**${fm['cost']:.4f}**; per accepted **${fm['per_accepted']:.4f}**.",
        f"- Low-overlap points: {fm['low']}/{fm['points']} "
        f"({fm['low_rate']:.1%}); this run predates point retries.",
        "",
        "Computed marks distribution: "
        + ", ".join(f"{k}: eval {comp.get(k, 0)} / fingerprint "
                    f"{FINGERPRINT.count(k)}" for k in sorted(set(comp))),
        "",
        "## Hardened single-model validation subset",
        "",
        f"- Model: `deepseek-v4-flash-0731`; seeds: {hm['seeds']}.",
        f"- Accepted {hm['accepted']}/{hm['slots']}; placeholders "
        f"{hm['placeholders']} ({hm['placeholder_rate']:.1%}).",
        f"- Max attempts per slot: **{hm['attempt_max']}** (limit 4 = initial "
        f"+ 3 retries). Point retries: **{hm['point_retries']}** calls.",
        f"- Low-overlap points remaining: **{hm['low']}/{hm['points']} "
        f"({hm['low_rate']:.1%})** after up to 2 point retries each.",
        f"- Source overlap: **{hm['overlap']}**; allowed-deck violations: "
        f"**{hm['violations']}**.",
        f"- Part B scenario sampling: {hm['scen_sampled']}/"
        f"{2 * len(hm['seeds'])} Part B groups sampled a scenario "
        f"({hm['scen_sampled'] / max(1, 2 * len(hm['seeds'])):.1%}); "
        f"{hm['scen_slots']} scenario-bearing questions were accepted "
        "(both B groups in seed 6; the other sampled groups ended as "
        "placeholders). Sampling rate used: 7/19 = 36.8% (small-sample "
        "variance).",
        f"- Estimated cost **${hm['cost']:.4f}**; per accepted "
        f"**${hm['per_accepted']:.4f}**.",
        "",
        "## Marking-point hardening",
        "",
        "Threshold: term overlap **0.50**. A low-overlap point triggers up to "
        "**2 point-level regeneration calls**; if still low it is kept and "
        "flagged for human review. The full pre-hardening run has the raw "
        "low-overlap rate; the hardened subset shows the post-retry rate.",
        "",
        "### 10 low-overlap examples (point + quote)",
        "",
    ]
    lines += _md_table(
        ["#", "Seed / slot", "Overlap", "Point", "Quote"],
        [[i, f"{s} / {slot}", f"{ov:.2f}", p, q]
         for i, (s, slot, ov, p, q) in enumerate(low_rows[:10], 1)],
        ["---:", "---", "---:", "---", "---"])
    lines += [
        "",
        "## Top 10 accepted/past question pairs",
        "",
    ]
    lines += _md_table(
        ["#", "Seed / slot", "Ratio", "Generated question",
         "Nearest real past question"],
        [[i, f"{s} / {q['slot']}", f"{ratio:.3f}", q["question"],
          f"{nc.paper} {nc.q}: {nc.text}"]
         for i, (ratio, s, q, nc) in enumerate(top, 1)],
        ["---:", "---", "---:", "---", "---"])
    lines += [
        "",
        "## 0.70 near-copy sensitivity",
        "",
        f"Static audit of the full 0.80 accepted set: **{rejected70}** of "
        f"{fm['accepted']} accepted questions are at or above 0.70. Rejecting "
        f"them without regeneration would leave **{proj_ph}/"
        f"{fm['slots']} ({proj_rate:.1%})** placeholders. The "
        f"0.80 run cost **${fm['cost']:.4f}**; a true 0.70 regeneration run "
        "could not be executed because all model quotas were exhausted. A "
        f"rough regeneration estimate at the full-run average "
        f"(${fm['cost'] / max(1, fm['accepted']):.4f}/accepted) is "
        f"10 x that = **${10 * fm['cost'] / max(1, fm['accepted']):.4f}**, "
        f"for a projected 0.70 total near **${fm['cost'] + 10 * fm['cost'] / max(1, fm['accepted']):.4f}**. "
        "This is an estimate, not a measured 0.70 run. The 10 most similar "
        "pairs above are the candidates that would be regenerated.",
        "",
        "## Topic map and actual mix",
        "",
    ]
    tmap = TOPIC_DECKS
    lines += _md_table(["Topic", "Allowed decks"],
                       [[k, ", ".join(v)] for k, v in tmap.items()],
                       ["---", "---"])
    lines += [
        "",
        "Decks **051** and **052** are allowed for both `attacks/malware` and "
        "`software/OS security`. Actual topic mix is accepted marks by the "
        "planner's slot topic plus the allowed-deck check; majority-deck mix "
        "is retained only as a diagnostic.",
        "",
    ]
    ptot, atot = Counter(), Counter()
    for r in full:
        ptot.update(r["payload"].get("planned_topic_mix", {}))
        for q in r["payload"].get("accepted", []):
            atot[q["topic"]] += q["marks"]
    lines += _md_table(
        ["Topic", "Planned marks", "Actual accepted marks", "Difference"],
        [[t, ptot[t], atot[t], atot[t] - ptot[t]]
         for t in sorted(set(ptot) | set(atot))],
        ["---", "---:", "---:", "---:"])
    lines += [
        "",
        "`classical ciphers` has 0 planned marks but 44 actual marks because "
        "the 2-mark theory slot paired with the computed Vigenere question "
        "shares the computed topic; it sits outside the seven-topic target.",
        "",
        "| Seed | Planned topic marks | Actual accepted topic marks |",
        "|---|---|---|",
    ]
    for r in full:
        p = r["payload"].get("planned_topic_mix", {})
        a = Counter()
        for q in r["payload"].get("accepted", []):
            a[q["topic"]] += q["marks"]
        lines.append(f"| {r['seed']} | {sum(p.values())} | {sum(a.values())} |")
    lines += [
        "",
        "## Attempts",
        "",
        "The old max >4 came from summing draft attempts across (a) and (b) "
        "and across point retries. The pipeline now records the maximum "
        "attempts for any one slot (limit 4: initial + 3 retries) and "
        f"separate point-retry calls. The hardened subset max is "
        f"**{hm['attempt_max']}**; point retries are "
        f"**{hm['point_retries']}** extra calls.",
        "",
        "## Human evaluation sheet",
        "",
        "`outputs/human_eval.xlsx`: 20 random generated questions and 10 "
        "random real past questions, shuffled with no labels; hidden `key` "
        "sheet records generated/real and origin.",
        "",
        "## Appendix",
        "",
        "`outputs/eval_multi_model_appendix.md` groups the earlier multi-model "
        "run by model, including quota-affected seeds.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
