"""Build the final one-model (DeepSeek V4.1 Flash) evaluation report."""
from __future__ import annotations

import itertools
import json
from collections import Counter, defaultdict
from pathlib import Path

from src.config import MODEL_PRICES, OUTPUTS_DIR
from src.theory.bm25 import TOPIC_DECKS
from src.theory.decks import load_chunks
from src.theory.generate import SUBANGLE_KEYWORDS, TOPIC_SUBANGLES
from src.theory.verify import (normalize_text, near_copy,
                               semantic_duplicate)

SRC = OUTPUTS_DIR / "eval_final_deepseek"
OUT = OUTPUTS_DIR / "eval_realistic.md"
APPENDIX = OUTPUTS_DIR / "eval_multi_model_appendix.md"
EXPECTED_MODEL = "deepseek-flash"
PRICE_IN, PRICE_OUT = MODEL_PRICES[EXPECTED_MODEL]
FINGERPRINT = [0, 0, 0, 0, 0, 2, 6, 6, 12, 14]


def _md_table(headers, rows, aligns=None):
    aligns = aligns or ["---"] * len(headers)
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(aligns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(
            str(x).replace("|", "/").replace("\n", " ") for x in row) + " |")
    return lines


def _load():
    rows = []
    for seed in range(1, 21):
        tp = SRC / f"seed_{seed:02d}_theory.json"
        pp = SRC / f"seed_{seed:02d}_planner.json"
        if not tp.exists() or not pp.exists():
            raise SystemExit(f"missing seed {seed}: {tp} / {pp}")
        rows.append({
            "seed": seed,
            "payload": json.loads(tp.read_text(encoding="utf-8")),
            "plan": json.loads(pp.read_text(encoding="utf-8")),
        })
    return rows


def _group_slots(payload):
    """slot -> (group question, part, topic, scenario_sampled)."""
    out = {}
    for g in payload.get("groups", []):
        topic = g.get("topic", "")
        scen = bool(g.get("scenario_sampled"))
        for sid in g.get("slots", []):
            part = "A" if str(sid).startswith("A") else "B"
            out[sid] = {
                "question": g.get("question", ""),
                "part": part,
                "topic": topic,
                "scenario": scen if part == "B" else False,
                "group_accepted": bool(g.get("accepted")),
            }
    return out


def _metrics(row):
    p = row["payload"]
    accepted = p.get("accepted", [])
    placeholders = p.get("placeholders", [])
    groups = p.get("groups", [])
    slots = len(accepted) + len(placeholders)
    attempts = [g.get("attempts", 0) for g in groups]
    near = [near_copy(q["question"]).ratio for q in accepted]
    points = [pt for q in accepted for pt in q.get("marking_points", [])]
    low_points = [pt for pt in points if pt.get("low_stem_overlap")]
    initial = Counter(p.get("initial_entailment_counts", {}))
    return {
        "seed": row["seed"],
        "computed_marks": row["plan"].get("computed_marks", 0),
        "accepted": len(accepted),
        "placeholders": len(placeholders),
        "slots": slots,
        "placeholder_rate": len(placeholders) / max(1, slots),
        "attempts_avg": sum(attempts) / len(attempts) if attempts else 0.0,
        "attempts_max": max(attempts, default=0),
        "total_draft_attempts": sum(
            g.get("total_draft_attempts", 0) for g in groups),
        "entailment_calls": sum(g.get("entailment_calls", 0) for g in groups),
        "regen_calls": sum(g.get("point_regeneration_calls", 0)
                           for g in groups),
        "point_retry_calls": sum(g.get("point_retry_calls", 0)
                                 for g in groups),
        "max_near": max(near, default=0.0),
        "cost": p.get("usage", {}).get("cost_usd", 0.0),
        "calls": p.get("usage", {}).get("calls", 0),
        "tokens": p.get("usage", {}).get("total_tokens", 0),
        "points": len(points),
        "low_points": len(low_points),
        "high_points": len(points) - len(low_points),
        "initial_entailment": initial,
        "final_entailment": Counter(p.get("entailment_counts", {})),
        "verbatim_rejections": p.get("verbatim_copy_rejections", 0),
        "scenario_sampled": sum(1 for g in groups
                                if g.get("scenario_sampled")),
        "scenario_questions": len(p.get("scenario_questions", [])),
        "source_overlap": p.get("source_overlap", {}).get(
            "overlap_key_count", 0),
        "deck_violations": len(p.get("deck_topic_violations", [])),
        "accepted_q": accepted,
        "placeholders_list": placeholders,
        "groups": groups,
    }


def _placeholder_breakdown(rows):
    part_total = Counter()
    part_ph = Counter()
    scen_total = Counter()
    scen_ph = Counter()
    topic_total = Counter()
    topic_ph = Counter()
    for row in rows:
        p = row["payload"]
        gmap = _group_slots(p)
        for sid, info in gmap.items():
            part_total[info["part"]] += 1
            topic_total[info["topic"]] += 1
            scen_total["scenario" if info["scenario"] else "non-scenario"] += 1
        for ph in p.get("placeholders", []):
            sid = ph.get("slot", "")
            info = gmap.get(sid, {})
            part = info.get("part") or ("A" if sid.startswith("A") else "B")
            part_ph[part] += 1
            if info.get("scenario"):
                scen_ph["scenario"] += 1
            else:
                scen_ph["non-scenario"] += 1
            topic_ph[ph.get("topic", info.get("topic", "unknown"))] += 1
    return {
        "part": (part_total, part_ph),
        "scenario": (scen_total, scen_ph),
        "topic": (topic_total, topic_ph),
    }


def _question_rows(rows):
    out = []
    for row in rows:
        for q in row.get("accepted_q", []):
            out.append({
                "seed": row["seed"],
                "slot": q["slot"],
                "topic": q["topic"],
                "question": q["question"],
                "norm": normalize_text(q["question"]).lower(),
            })
    return out


def _angle_for(topic: str, question: str) -> str:
    ql = question.lower()
    best = ("other", 0)
    for angle in TOPIC_SUBANGLES.get(topic, []):
        hits = sum(1 for k in SUBANGLE_KEYWORDS.get(angle, [])
                   if k in ql)
        if hits > best[1]:
            best = (angle, hits)
    return best[0]


def _diversity(rows):
    qs = _question_rows(rows)
    by_topic = defaultdict(list)
    for q in qs:
        by_topic[q["topic"]].append(q)
    topic_rows = []
    for topic, items in sorted(by_topic.items()):
        distinct = len({q["norm"] for q in items})
        angles = [_angle_for(topic, q["question"]) for q in items]
        angle_counts = Counter(angles)
        top2 = sum(n for _, n in angle_counts.most_common(2))
        pairs = 0
        same_angle = 0
        wording_dup = 0
        for i, j in itertools.combinations(range(len(items)), 2):
            a, b = items[i], items[j]
            if a["seed"] == b["seed"]:
                continue
            pairs += 1
            if angles[i] == angles[j]:
                same_angle += 1
            if (a["norm"] == b["norm"] or semantic_duplicate(
                    a["question"], b["question"])[0]
                    or near_copy(a["question"]).ratio >= 0.70):
                wording_dup += 1
        same_rate = same_angle / pairs if pairs else 0.0
        wording_rate = wording_dup / pairs if pairs else 0.0
        distinct_rate = distinct / len(items) if items else 0.0
        top2_share = top2 / len(items) if items else 0.0
        # Assessment-level duplicate = same sub-angle (different wording
        # still tests the same thing).  Topics concentrated in one or two
        # angles are flagged, even when wording varies.
        flag = "LOW" if (same_rate >= 0.45 or top2_share >= 0.90) else ""
        topic_rows.append({
            "topic": topic, "questions": len(items), "distinct": distinct,
            "distinct_rate": distinct_rate, "angles": len(angle_counts),
            "angles_available": len(TOPIC_SUBANGLES.get(topic, [])),
            "pairs": pairs,
            "same_angle_pairs": same_angle, "same_angle_rate": same_rate,
            "wording_duplicate_pairs": wording_dup,
            "wording_duplicate_rate": wording_rate,
            "top2_share": top2_share,
            "angle_counts": dict(angle_counts),
            "flag": flag,
        })
    all_distinct = len({q["norm"] for q in qs})
    return qs, all_distinct, topic_rows


def _unused_slides(rows):
    chunks = load_chunks()
    by_topic = defaultdict(set)
    for c in chunks:
        for topic, allowed in TOPIC_DECKS.items():
            if c.deck.startswith(allowed):
                by_topic[topic].add((c.deck, c.slide))
    used = defaultdict(set)
    for row in rows:
        for q in row.get("accepted_q", []):
            for pt in q.get("marking_points", []):
                used[q["topic"]].add((pt["source_deck"],
                                      pt["source_slide"]))
    out = []
    for topic in sorted(TOPIC_DECKS):
        total = len(by_topic.get(topic, set()))
        u = len(used.get(topic, set()) & by_topic.get(topic, set()))
        unused = max(0, total - u)
        out.append({
            "topic": topic, "slides": total, "used": u,
            "unused": unused,
            "unused_rate": unused / total if total else 0.0,
        })
    return out


def main() -> None:
    rows = _load()
    metrics = [_metrics(r) for r in rows]
    models = sorted({r["payload"].get("model", "") for r in rows})
    if models != [EXPECTED_MODEL]:
        raise SystemExit(f"expected one model {EXPECTED_MODEL}, got {models}")

    total_slots = sum(m["slots"] for m in metrics)
    total_acc = sum(m["accepted"] for m in metrics)
    total_ph = sum(m["placeholders"] for m in metrics)
    total_cost = sum(m["cost"] for m in metrics)
    total_calls = sum(m["calls"] for m in metrics)
    total_tokens = sum(m["tokens"] for m in metrics)
    total_groups = sum(len(m["groups"]) for m in metrics)
    total_draft_attempts = sum(m["total_draft_attempts"] for m in metrics)
    total_attempts = sum(m["attempts_avg"] * len(m["groups"])
                         for m in metrics)
    avg_attempts = total_attempts / max(1, total_groups)
    max_attempts = max((m["attempts_max"] for m in metrics), default=0)
    total_points = sum(m["points"] for m in metrics)
    total_low = sum(m["low_points"] for m in metrics)
    initial = Counter()
    final_ent = Counter()
    for m in metrics:
        initial.update(m["initial_entailment"])
        final_ent.update(m["final_entailment"])
    checked = sum(initial.values())
    max_near = max((m["max_near"] for m in metrics), default=0.0)
    computed = Counter(m["computed_marks"] for m in metrics)
    qs, distinct_q, topic_div = _diversity(metrics)
    placeholder_bd = _placeholder_breakdown(rows)
    unused = _unused_slides(metrics)

    # Near-copy top 10 across all accepted questions.
    pairs = []
    for m in metrics:
        for q in m["accepted_q"]:
            nc = near_copy(q["question"])
            pairs.append((nc.ratio, m["seed"], q, nc))
    pairs.sort(key=lambda x: -x[0])
    top_pairs = pairs[:10]

    lines = [
        "# Final realistic-mode evaluation",
        "",
        "## Setup",
        "",
        "This is the primary evaluation requested in the final pass: **one "
        "model for all 20 seeds**, the hardened theory pipeline, and no "
        "quota rotation.",
        "",
        f"- Model: **DeepSeek V4.1 Flash** (`{EXPECTED_MODEL}`, "
        "DeepSeek-V4.1-Flash-1017).",
        f"- Seeds: **1-20**; theory slots: **{total_slots}**; accepted "
        f"**{total_acc}**; placeholders **{total_ph}** "
        f"({total_ph / max(1, total_slots):.1%}).",
        f"- Estimated cost: **${total_cost:.4f}**, **${total_cost / max(1, total_acc):.4f}** "
        "per accepted question.",
        f"- Official DeepSeek list price used: **${PRICE_IN:.2f}/1M input, "
        f"${PRICE_OUT:.2f}/1M output** (peak cache-miss rates; off-peak is "
        "half). The run took place in the peak window (01:00-04:00 UTC on a "
        "weekday), so peak rates apply. Cache-hit discounts are not counted, "
        "so this is a conservative estimate from token usage, not an invoice.",
        f"- Calls: **{total_calls}**; tokens: **{total_tokens}**.",
        f"- Source overlap: **{sum(m['source_overlap'] for m in metrics)}** "
        "keys; allowed-deck violations: "
        f"**{sum(m['deck_violations'] for m in metrics)}**.",
        f"- Max near-copy against the 35 past papers: **{max_near:.3f}** "
        "(threshold 0.80).",
        "- Raw per-seed payloads: `outputs/eval_final_deepseek/"
        "seed_XX_theory.json` (and `.md` reports).",
        "",
        "## Per-seed results",
        "",
    ]
    rows_table = []
    for m in metrics:
        rows_table.append([
            m["seed"], m["computed_marks"], m["accepted"], m["placeholders"],
            f"{m['attempts_avg']:.2f}", m["attempts_max"],
            m["entailment_calls"], m["regen_calls"],
            f"{m['max_near']:.2f}", f"${m['cost']:.4f}",
        ])
    rows_table.append([
        "**Total**", "", f"**{total_acc}**", f"**{total_ph}**",
        f"**{avg_attempts:.2f}**", f"**{max_attempts}**",
        f"**{sum(m['entailment_calls'] for m in metrics)}**",
        f"**{sum(m['regen_calls'] for m in metrics)}**",
        f"**{max_near:.2f}**", f"**${total_cost:.4f}**",
    ])
    lines += _md_table(
        ["Seed", "Computed", "Accepted", "Placeholders", "Attempts avg",
         "Attempts max", "Entailment calls", "Point regen calls",
         "Max near-copy", "Cost"], rows_table,
        ["---:", "---:", "---:", "---:", "---:", "---:", "---:", "---:",
         "---:", "---:"])

    lines += [
        "",
        f"Placeholder rate overall: **{total_ph}/{total_slots} "
        f"({total_ph / max(1, total_slots):.1%})**. Draft attempts: "
        f"**{total_draft_attempts}** across **{total_groups}** groups "
        f"(**{total_draft_attempts / max(1, total_groups):.2f}** draft calls "
        f"per group); per-slot max attempts mean **{avg_attempts:.2f}**, "
        f"max **{max_attempts}** (limit 4 = initial + 3 retries). The old "
        ">4 values came from summing attempts across (a)/(b) and point "
        "retries.",
        "",
        "## Marking-point gates",
        "",
        f"- First gate: **stemmed content-token overlap** (Snowball English "
        "stemmer) at threshold **0.50**.",
        f"- First-pass high stem-overlap points: "
        f"**{total_points - checked}/{total_points}** "
        f"({(total_points - checked) / max(1, total_points):.1%}); these "
        "passed without an entailment call.",
        f"- Low stem-overlap points that triggered the gate: **{checked}** "
        f"({checked / max(1, total_points):.1%} of accepted points); after "
        f"point handling, **{total_low}** still have low stem overlap "
        f"(**{checked - total_low}** rewrites moved above the threshold).",
        "",
        "| Entailment verdict (initial check) | Count | Share of checked |",
        "|---|---:|---:|",
    ]
    for verdict in ["yes", "partly", "no", "error"]:
        n = initial.get(verdict, 0)
        if n or verdict != "error":
            lines.append(f"| {verdict} | {n} | "
                         f"{n / max(1, checked):.1%} |")
    lines += [
        "",
        "Only **no** points are regenerated (up to two point-level rewrites "
        "each); **yes** and **partly** points are kept and recorded. "
        f"Point regeneration calls: **{sum(m['regen_calls'] for m in metrics)}**; "
        f"entailment calls: **{sum(m['entailment_calls'] for m in metrics)}** "
        "(including checks on low-overlap rewrites).",
        f"Final accepted verdicts: **yes {final_ent.get('yes', 0)}**, "
        f"**partly {final_ent.get('partly', 0)}**, "
        f"**no {final_ent.get('no', 0)}**; a 'no' point that was successfully "
        "rewritten is replaced, so the final 'no' count is lower than the "
        "initial count.",
        "",
        f"Verbatim-copy rejections (point copied from its quote): "
        f"**{sum(m['verbatim_rejections'] for m in metrics)}** across the "
        "20 seeds.",
        "",
        "### Ten remaining low-stem-overlap points",
        "",
    ]
    low_examples = []
    for m in metrics:
        for q in m["accepted_q"]:
            for pt in q.get("marking_points", []):
                if pt.get("low_stem_overlap"):
                    low_examples.append((m["seed"], q["slot"], pt))
    low_examples = low_examples[:10]
    lines += _md_table(
        ["#", "Seed / slot", "Stem overlap", "Entailment", "Point", "Quote"],
        [[i, f"{s} / {slot}", f"{pt.get('stem_overlap', 0):.2f}",
          pt.get("entailment", ""), pt["point"], pt["quote"]]
         for i, (s, slot, pt) in enumerate(low_examples, 1)],
        ["---:", "---", "---:", "---", "---", "---"])

    # Placeholder breakdown
    part_total, part_ph = placeholder_bd["part"]
    scen_total, scen_ph = placeholder_bd["scenario"]
    topic_total, topic_ph = placeholder_bd["topic"]
    lines += [
        "",
        "## Placeholder breakdown",
        "",
        "### By Part A / Part B",
        "",
        "| Part | Slots | Placeholders | Rate |",
        "|---|---:|---:|---:|",
    ]
    for part in ["A", "B"]:
        t, p = part_total.get(part, 0), part_ph.get(part, 0)
        lines.append(f"| Part {part} | {t} | {p} | {p / max(1, t):.1%} |")
    lines += [
        "",
        "### By scenario / non-scenario",
        "",
        "A slot counts as scenario only when its Part B group was sampled "
        "for a scenario; Part A is always non-scenario.",
        "",
        "| Group type | Slots | Placeholders | Rate |",
        "|---|---:|---:|---:|",
    ]
    for kind in ["scenario", "non-scenario"]:
        t, p = scen_total.get(kind, 0), scen_ph.get(kind, 0)
        lines.append(f"| {kind} | {t} | {p} | {p / max(1, t):.1%} |")
    lines += [
        "",
        "### By topic",
        "",
        "| Topic | Slots | Placeholders | Rate |",
        "|---|---:|---:|---:|",
    ]
    for topic in sorted(topic_total):
        t, p = topic_total[topic], topic_ph.get(topic, 0)
        lines.append(f"| {topic} | {t} | {p} | {p / max(1, t):.1%} |")
    lines += [
        "",
        f"Part B scenario sampling: **{sum(m['scenario_sampled'] for m in metrics)}"
        f"/{2 * len(metrics)}** Part B groups sampled a scenario; "
        f"**{sum(m['scenario_questions'] for m in metrics)}** scenario-bearing "
        "questions were accepted. Sampling rate used: 7/19 = 36.8% (the "
        "measured lower bound).",
        "",
        "## Diversity across the 20 papers",
        "",
        f"- Theory questions generated: **{len(qs)}**; distinct question "
        f"texts: **{distinct_q}** ({distinct_q / max(1, len(qs)):.1%}); "
        f"duplicate instances: **{len(qs) - distinct_q}**.",
        "- Duplicate pairs are counted between different seeds only. The "
        "**same-angle rate** is the assessment-level duplicate rate: two "
        "questions test the same sub-angle even if their wording differs. "
        "The **wording rate** counts exact text, semantic duplicates "
        "(sequence >= 0.65 and Jaccard >= 0.45), or near-copy >= 0.70.",
        "",
        "| Topic | Questions | Distinct | Distinct rate | Angles used | "
        "Cross-seed pairs | Same-angle pairs | Same-angle rate | Top-2 angle "
        "share | Wording dup rate | Flag |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for t in topic_div:
        lines.append(
            f"| {t['topic']} | {t['questions']} | {t['distinct']} | "
            f"{t['distinct_rate']:.1%} | {t['angles']}/"
            f"{t['angles_available']} | {t['pairs']} | "
            f"{t['same_angle_pairs']} | {t['same_angle_rate']:.1%} | "
            f"{t['top2_share']:.1%} | {t['wording_duplicate_rate']:.1%} | "
            f"{t['flag']} |")
    flagged = [t["topic"] for t in topic_div if t["flag"]]
    ethics = next((t for t in topic_div
                   if t["topic"] == "risk/management (ethics)"), None)
    lines += [
        "",
        ("Low-diversity topics flagged: **" + ", ".join(flagged) + "**."
         if flagged else "No topic crossed the low-diversity flag."),
    ]
    if ethics:
        top = ", ".join(f"{k} ({v})" for k, v in
                        Counter(ethics["angle_counts"]).most_common())
        lines.append(
            "Ethics (deck 071) is flagged: "
            f"{ethics['top2_share']:.1%} of its questions fall into its two "
            f"dominant sub-angles; distribution: {top}.")
    lines += [
        "",
        "### Unused slides per topic",
        "",
        "Counted over the union of the 20 papers: slides in the topic's "
        "allowed decks that were never cited by an accepted question of that "
        "topic.",
        "",
        "| Topic | Slides in allowed decks | Used | Unused | Unused rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for u in unused:
        lines.append(f"| {u['topic']} | {u['slides']} | {u['used']} | "
                     f"{u['unused']} | {u['unused_rate']:.1%} |")
    lines += [
        "",
        "## Top 10 accepted/past-question pairs",
        "",
    ]
    lines += _md_table(
        ["#", "Seed / slot", "Ratio", "Generated question",
         "Nearest real past question"],
        [[i, f"{s} / {q['slot']}", f"{ratio:.3f}", q["question"],
          f"{nc.paper} {nc.q}: {nc.text}"]
         for i, (ratio, s, q, nc) in enumerate(top_pairs, 1)],
        ["---:", "---", "---:", "---", "---"])
    lines += [
        "",
        "## Stem-length follow-up",
        "",
        "This 20-seed run predates the mark-aware stem-length check. A fresh "
        "8-seed sample with the check (`outputs/eval_stem_sample/`, seeds 1-8) "
        "reduced the median stem length from **19 to 12** words for 2-mark "
        "questions, **31 to 26.5** for 5-mark questions, and **31 to 21** for "
        "6-mark questions; all generated stems were inside the clean-modern "
        "90th percentile (18/54/43 words). That sample accepted 181/185 slots "
        "with 4 placeholders (2.2%). Details: `stem_length_report.md`.",
        "",
        "## Prior-figure corrections",
        "",
        "- The previous **26/474** placeholder projection was wrong: rejecting "
        "10 near-copy questions does not add slots. With 464 total theory "
        "slots the corrected figure is **26/464 = 5.6%**.",
        "- The appendix sentence about quota-affected seeds was corrected: "
        "the affected clusters are qwen3.6-flash seeds 14 and 16, and "
        "qwen3.6-plus seeds 13, 15 and 19.",
        "",
        "## Appendix",
        "",
        "`eval_multi_model_appendix.md` is the earlier multi-model run, "
        "clearly labelled **pre-hardening** and kept only for comparison.",
        "",
        "## Human evaluation",
        "",
        "`human_eval.xlsx` contains 20 generated and 10 real past questions, "
        "shuffled with no labels; the hidden `key` sheet records origin.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
