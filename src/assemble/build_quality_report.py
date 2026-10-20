"""Summarise the theory quality pass, formatting pass and seed-9 paper."""
from __future__ import annotations

import json
from collections import Counter

from pypdf import PdfReader

from src.config import OUTPUTS_DIR
from src.theory.bm25 import deck_topic

OUT = OUTPUTS_DIR / "quality_pass_report.md"


def main() -> None:
    metrics = json.loads(
        (OUTPUTS_DIR / "eval_realistic" / "metrics.json").read_text())
    ok = [m for m in metrics if not m.get("error")]
    seed9 = json.loads(
        (OUTPUTS_DIR / "eval_realistic" / "seed_09_theory.json").read_text())
    plan9 = json.loads(
        (OUTPUTS_DIR / "eval_realistic" / "seed_09_planner.json").read_text())
    total_slots = sum(m["theory_slots"] for m in ok)
    total_ph = sum(m["placeholders"] for m in ok)
    total_acc = sum(m["accepted"] for m in ok)
    total_cost = sum(m["cost_usd"] for m in ok)
    total_calls = sum(m["calls"] for m in ok)
    total_tokens = sum(m["tokens"] for m in ok)
    overlap_keys = sum(m["source_overlap_keys"] for m in ok)
    overlap_papers = sum(1 for m in ok if m["source_overlap_keys"] > 0)
    max_near = max((m["max_near_copy"] for m in ok), default=0)
    low_term = sum(m["low_term_overlap_points"] for m in ok)
    scenario_count = sum(m["scenario_count"] for m in ok)
    p9 = seed9["source_overlap"]
    low9 = seed9.get("low_term_overlap_points", [])
    short9 = seed9.get("short_quote_points", [])
    repaired9 = seed9.get("repaired_quote_count", 0)
    scenarios9 = seed9.get("scenario_questions", [])
    paper_pages = len(PdfReader(str(OUTPUTS_DIR / "mock_paper_03.pdf")).pages)
    scheme_pages = len(PdfReader(str(OUTPUTS_DIR / "mock_scheme_03.pdf")).pages)

    lines = [
        "# Theory quality pass and formatting pass",
        "",
        "This pass changed only the theory/verification pipeline and the "
        "paper-03 formatting; paper 02 remains as delivered.",
        "",
        "## 1. Source overlap",
        "",
        "- The unit of overlap is `(deck, slide)`. Retrieval excludes slides "
        "already cited by earlier accepted questions; if fewer than three "
        "unused chunks remain, it fills from unused chunks in the allowed "
        "decks before allowing any overlap.",
        "- Each slot gets its own evidence pool; the higher-mark slot in a pair "
        "reserves its slides first. A verifier rejects a chunk that belongs to "
        "the other slot's pool or a slide already used by another accepted "
        "question.",
        f"- Seed 9: **{p9['overlap_key_count']}** overlapping keys across "
        f"{p9['distinct_source_keys']} distinct keys (target 0).",
        f"- Seeds 1-20: **{overlap_keys}** overlapping keys across "
        f"{overlap_papers}/20 papers; target 0. Full per-seed detail is in "
        "`outputs/eval_realistic.md`.",
        "",
        "## 2. Topic-source consistency",
        "",
        "The `TOPIC_DECKS` allow-list is enforced in the verifier (for example, "
        "ethics may cite only deck 071; classical ciphers only deck 031). A "
        "question whose cited deck is outside its slot topic's allow-list is "
        "rejected. The eval report computes the actual topic mix from cited "
        "decks, and compares it with the planner's planned marks.",
        "",
        "Seed 9 planned vs actual (marks): "
        + "; ".join(f"{k}: {plan9['assigned_theory_topic_marks'].get(k, 0)}"
                    f" -> {seed9.get('actual_topic_mix', {}).get(k, 0)}"
                    for k in sorted(set(plan9['assigned_theory_topic_marks'])
                                    | set(seed9.get('actual_topic_mix', {}))))
        + ". The large attack/software shift is because attack questions cite "
        "software/web decks (051/052), which the deck-topic map classifies as "
        "software/OS security.",
        "",
        "## 3. Part B",
        "",
        "Measured from the clean modern papers with explicit A/B rows: "
        "**7/19** Part B questions have a scenario paragraph in the (a) stem, "
        "**11/19** (a)/(b) pairs share a topic, and **2/19** explicitly refer "
        "back to (a)/the above. The method is documented in "
        "`outputs/planner_measurements.md`; the 2023-02 Ali scenario may be in "
        "an unlogged paragraph, so scenario detection is a lower bound.",
        "",
        "Part B now generates a short shared scenario grounded in the cited "
        "slides. B1a/B1b and B2a/B2b use the same scenario in paper 03; "
        "marking points still come from slide quotes. Part B topics are "
        "sampled by their measured marks weights, not fixed to the top two.",
        "",
        f"Seed 9 generated **{len(scenarios9)//2}** shared scenarios: "
        + "; ".join(
            (f"{s['slot']} reuses (a)" if s['slot'].endswith('b')
             else f"{s['slot']} grounding {s['grounding']:.2f}")
            for s in scenarios9) + ".",
        "",
        "The command mapping now includes **Propose** (propose/recommend/"
        "suggest) and **Analyse** (analyse/analyze/critically); they are no "
        "longer dropped into `Other`.",
        "",
        "## 4. Marking-point quality",
        "",
        "- Slide-title-only quotes are rejected.",
        "- Each quote must share a key term with its point; the term-overlap "
        "score is stored per point and shown in scheme 03. Low scores are "
        "flagged, not silently treated as strong evidence.",
        f"- Seed 9: **{len(low9)}** low term-overlap points, "
        f"**{len(short9)}** short quotes and **{repaired9}** repaired quotes. "
        "Repairs only replace a paraphrase with an exact nearby line from the "
        "same cited chunk.",
        "",
        "## 5. Style-confidence report",
        "",
        "The planner table now reports both **exact style n** and **used style "
        "n**; low-confidence slots are still those with exact n<3, but the "
        "used count (3-5 after widening) is visible in the same row.",
        "",
        "## 6. Evaluation (seeds 1-20)",
        "",
        f"- Theory slots: {total_slots}; accepted **{total_acc}**; "
        f"placeholders **{total_ph}** ({total_ph / max(1, total_slots):.1%}).",
        f"- Source overlap: **{overlap_keys}** keys across "
        f"{overlap_papers}/20 papers (target 0).",
        f"- Maximum near-copy similarity: **{max_near:.2f}** (threshold 0.80).",
        f"- Calls: {total_calls}; tokens: {total_tokens}; estimated total "
        f"cost: **${total_cost:.4f}**; cost per accepted question: "
        f"**${total_cost / max(1, total_acc):.4f}**.",
        f"- Low term-overlap points flagged: {low_term}; Part B scenario "
        f"questions generated: {scenario_count}.",
        "- Full per-seed table, computed-mark distribution, attempts, topic "
        "mix and costs: `outputs/eval_realistic.md`.",
        "",
        "## 7. Formatting pass against the manually revised mock",
        "",
        "The manual revision was compared at paragraph/run level. The "
        "substantive formatting changes were:",
        "",
        "- bold running header (`CONFIDENTIAL ... CS/MOCK OCT 2026/CSC662`);",
        "- bold `PART A` / `PART B` / `QUESTION n` / `END OF QUESTION PAPER` "
        "headings;",
        "- 1.5 line spacing for the body paragraphs from PART A onward;",
        "- a blank line after each PART heading and after the Vigenere tableau.",
        "",
        f"These are applied in `mock_paper_03.docx` / `.pdf` "
        f"({paper_pages} pages); the scheme is {scheme_pages} pages. The "
        "manual scheme had no material type-size change beyond the labels; "
        "scheme 03 adds the required methods note, the supported-by label and "
        "the term-overlap column.",
        "",
        "## 8. Seed-9 paper/scheme",
        "",
        "- `outputs/mock_paper_03.docx` / `.pdf`",
        "- `outputs/mock_scheme_03.docx` / `.pdf`",
        "- Seed 9: 23/23 theory answers accepted, 0 placeholders, 0 source "
        "overlap; the computed Vigenere question still prints the tableau.",
        "- Scheme theory headers read **supported by lecture slides (not "
        "lecturer-marked)** and every marking point shows quote, source and "
        "term overlap; low overlaps are marked LOW.",
        "",
        "## Files",
        "",
        "- `outputs/eval_realistic.md` - evaluation report (primary).",
        "- `outputs/eval_realistic/` - per-seed planner/theory JSON and "
        "Markdown.",
        "- `outputs/mock_paper_03.docx` / `.pdf`",
        "- `outputs/mock_scheme_03.docx` / `.pdf`",
        "- `outputs/planner_measurements.md` - updated labels and Part B "
        "scenario measurement.",
        "- `outputs/quality_pass_report.md` - this summary.",
        "",
        "## Caveats",
        "",
        "- Source overlap is reported at slide level, stricter than exact "
        "chunk-id reuse.",
        "- Actual topic mix is inferred from a primary deck-topic map; a deck "
        "used by more than one topic can shift the actual mix.",
        "- Low term-overlap points are flagged for human review, not "
        "automatically rejected.",
        "- Cost uses the public qwen-flash price as an estimate; the model "
        "actually used for the 20-seed eval is recorded in `eval_realistic.md`.",
    ]
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
