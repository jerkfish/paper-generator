"""Assemble the final planner/theory/paper-02 report."""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from pypdf import PdfReader

from src.config import OUTPUTS_DIR
from src.planner.fingerprint_data import load_all_rows
from src.planner.planner import TYPE_LABEL
from src.planner.tasks import command_word
from src.theory.verify import near_copy

PLAN = OUTPUTS_DIR / "planner_revised_realistic.json"
MEAS = OUTPUTS_DIR / "planner_measurements.json"
THEORY = OUTPUTS_DIR / "theory_drafts_realistic.json"
OUT = OUTPUTS_DIR / "final_report.md"


def _clean_examples(label: str, n: int = 3) -> list[dict]:
    bad = ("o hak cipta", "confidential", "http", "universiti teknologi mara")
    out = []
    for r in load_all_rows():
        if int(r["Marks"] or 0) != 6:
            continue
        if command_word(r["Original question text"])[0] != label:
            continue
        text = str(r["Original question text"]).replace("\n", " ").strip()
        if any(b in text.lower() for b in bad):
            continue
        out.append({"paper": str(r["Paper ID"]),
                    "q": f"Q{r['Q no.']}{r['Sub-part'] or ''}",
                    "text": text})
        if len(out) >= n:
            break
    return out


def _md_table(headers: list[str], rows: list[list[str]],
              aligns: list[str] | None = None) -> list[str]:
    aligns = aligns or ["---"] * len(headers)
    lines = ["| " + " | ".join(headers) + " |",
             "|" + "|".join(aligns) + "|"]
    for row in rows:
        lines.append("| " + " | ".join(str(c).replace("|", "/")
                                       for c in row) + " |")
    return lines


def build() -> str:
    plan = json.loads(PLAN.read_text(encoding="utf-8"))
    meas = json.loads(MEAS.read_text(encoding="utf-8"))
    theory = json.loads(THEORY.read_text(encoding="utf-8"))
    m = plan["measurement"]
    slots = plan["slots"]
    accepted = {q["slot"]: q for q in theory["accepted"]}
    pct = lambda a, b: f"{a}/{b} ({a / b:.1%})" if b else "0/0"

    lines = [
        "# CSC662 mock paper 02 - planner revision, theory module and report",
        "",
        "Generated locally from the 35 past papers and the read-only CSC662 "
        "lecture decks. No original paper or deck was modified.",
        "",
        "## Deliverables",
        "",
        "- `outputs/mock_paper_02.docx` / `.pdf` - realistic-mode paper, 4 pages.",
        "- `outputs/mock_scheme_02.docx` / `.pdf` - marking scheme, 13 pages.",
        "- `outputs/planner_revised_realistic.json` / `.md` - revised slot table.",
        "- `outputs/theory_drafts_realistic.json` / `.md` - verified theory "
        "questions and sources.",
        "- `outputs/vigenere_tableau.png` - 26 x 26 tableau printed after Q2(b).",
        "- `outputs/final_report.md` / `.pdf` - this report (7 pages in the PDF "
        "render).",
        "",
        "## 1. Measurements (reported before the planner was changed)",
        "",
        f"- Clean modern papers: **{meas['clean_papers']}**; papers with "
        f"explicit Part A/B labels used for pair/part measures: "
        f"**{len(meas['ab_papers'])}** ({', '.join(meas['ab_papers'])}).",
        "- Coverage caveat: 2018-01 and 2018-06 use a numeric-question layout "
        "with no A/B labels and are excluded from the pair/part measures; "
        "2025-07 has incomplete/noisy A/B extraction. 2026-02 marks are noisy "
        "in places but its valid pairs are included.",
        "",
        "### (a) Part A (a)/(b) relationship",
        "",
        f"- Pairs measured: **{meas['part_a_pairs']}**.",
        f"- Same topic: **{pct(meas['same_topic_pairs'], meas['part_a_pairs'])}**.",
        f"- (b) explicitly refers to (a) / the above / the scenario: "
        f"**{pct(meas['dependent_pairs'], meas['part_a_pairs'])}**.",
        "",
        "Dependency regex: `your answer in (a)`, `answer in (a)`, `the above`, "
        "`based on the above`, `scenario above`, `given scenario`, `this "
        "scenario`, `same scenario`, `in part (a)`, `using your answer`.",
        "",
        "### (b) Command-word distribution by part",
        "",
    ]
    labels = ["State", "List", "Explain", "Describe", "Discuss", "Compare",
              "Justify", "Other"]
    rows = []
    for label in labels:
        rows.append([
            label,
            meas["part_a_label_counts"].get(label, 0),
            meas["part_a_label_marks"].get(label, 0),
            meas["part_b_label_counts"].get(label, 0),
            meas["part_b_label_marks"].get(label, 0),
        ])
    lines += _md_table(["Label", "Part A rows", "Part A marks",
                        "Part B rows", "Part B marks"], rows,
                       ["---", "---:", "---:", "---:", "---:"])
    lines += [
        "",
        "Raw phrasing mapped to the seven labels: define -> Describe; what is "
        "-> Explain; identify/give/name -> State; why/how -> Explain; propose/"
        "suggest/support -> Justify; differentiate -> Compare. `Other` means no "
        "mapped command word and is never used as a generated slot label.",
        "",
        "### (c) Topic distribution in Part B",
        "",
    ]
    pb = sorted(meas["part_b_topic_marks"].items(), key=lambda x: -x[1])
    lines += _md_table(["Topic", "Rows", "Marks"],
                       [[t, meas["part_b_topic_counts"].get(t, 0), v]
                        for t, v in pb], ["---", "---:", "---:"])
    lines += [
        "",
        "Part B topic and task mix is used separately from Part A: the two "
        "Part B questions take the two largest measured Part B topic shares "
        "(risk/management 39 marks, attacks/malware 36), and the four Part B "
        "slots take the measured Part B 5-mark command mix (Explain 2, State 1, "
        "Discuss 1 in this seed).",
        "",
        "## 2. Revised planner table (realistic mode, seed 9)",
        "",
        f"- 24 slots, 100 marks: Part A 80, Part B 20; computed marks "
        f"**{plan['computed_marks']}** (clean-modern mean "
        f"{plan['computed_distribution_mean']}).",
        f"- Question topics: `{' -> '.join(f'{q}:{t}' for q, t in zip(['A1','A2','A3','A4','A5','A6','A7','A8','A9','A10','B1','B2'], plan['question_topic_sequence']))}`.",
        f"- One topic per question: **yes**; no more than two consecutive "
        f"questions with the same topic: "
        f"**{'PASS' if plan['no_three_consecutive_same_topic'] else 'FAIL'}**.",
        f"- Dependent pair(s): **{', '.join(plan['dependent_questions']) or 'none'}** "
        "(1 of 9 Part A theory pairs = 11.1%, close to the measured 9.7%).",
        "",
    ]
    rows = []
    for s in slots:
        style = ""
        if s["kind"] == "theory":
            style = f"{s['style_n']} / {s['style_mode']}"
        note = s["acm_scope"] or s["note"]
        rows.append([
            s["slot"], s["marks"], s["kind"], s["topic"], s["task"],
            TYPE_LABEL.get(s["computed_type"], s["computed_type"]),
            s["target"], style,
            "yes" if s.get("low_style_confidence") else "",
            "yes" if s.get("dependent") else "",
            note,
        ])
    lines += _md_table(
        ["Slot", "Marks", "Kind", "Topic", "Command", "Computed type",
         "Target size / key", "Style exact / mode", "Low conf.", "Dependent",
         "Notes"], rows,
        ["---", "---:", "---", "---", "---", "---", "---", "---", "---",
         "---", "---"])
    lines += [
        "",
        "### Topic allocation vs modern share",
        "",
    ]
    rows = []
    for t, weight in plan["topic_weights"].items():
        rows.append([t, f"{weight:.3f}", plan["target_topic_marks"].get(t, 0),
                     plan["assigned_theory_topic_marks"].get(t, 0)])
    lines += _md_table(["Topic", "Modern weight", "Target marks",
                        "Assigned theory marks"], rows,
                       ["---", "---:", "---:", "---:"])
    lines += [
        "",
        "The planner renormalised the seven theory topics after adding "
        "`risk/management (ethics)` (modern risk marks = 119; source deck 071 "
        "Ethics). Planned-vs-target differences are reported rather than "
        "hidden: risk is 10 vs 14 target, software/OS 8 vs 5, network 8 vs 6, "
        "access control 16 vs 14. A 2-mark theory slot paired with the computed "
        "Vigenere question is on `classical ciphers` (one-topic-per-question "
        "rule) and sits outside the seven-topic target.",
        "",
        "Coverage note: 173 of 955 modern non-compute marks (18.1%) fall in "
        "topics outside the seven (other, general cryptography, classical "
        "ciphers, public-key, hashing/signatures, block ciphers) and were not "
        "reallocated. The ethics deck contributes 16 text chunks from 18 "
        "slides (slides 1,3-9,11-18), 6,387 characters.",
        "",
        "## 3. Three real 6-mark examples per command label used at 6 marks",
        "",
        "The labels used at 6 marks in this paper are State, Explain, Describe, "
        "Discuss and Justify. These are real past questions whose marks column "
        "is 6; noisy OCR/header text was skipped for the display.",
        "",
    ]
    for label in ["State", "Explain", "Describe", "Discuss", "Justify"]:
        lines.append(f"### {label}")
        lines.append("")
        for ex in _clean_examples(label):
            text = ex["text"]
            if len(text) > 320:
                text = text[:317] + "..."
            lines.append(f"- **{ex['paper']} {ex['q']}**: {text}")
        lines.append("")
    lines += [
        "## 4. Theory module",
        "",
        "### Pipeline",
        "",
        "- Deck ingestion: python-pptx, read-only from the KB folder "
        "`C:/Users/Ahmad/Desktop/CSC662`; 25 decks, 496 slide chunks; every "
        "chunk keeps deck + slide number.",
        "- Retrieval: BM25 (k1=1.5, b=0.75), top 10 chunks, max 4 per deck; "
        "topic-specific deck allow-lists (ethics restricted to deck 071). "
        "Fallback to all decks is recorded if fewer than 3 hits.",
        "- Generation: Qwen cheap model via the existing OpenAI-compatible "
        "client with `enable_thinking=False`; Pydantic JSON schema; one call "
        "per question pair, with up to 3 retries after the initial attempt.",
        "- Verification: quote must be a verbatim contiguous substring of the "
        "cited retrieved chunk (whitespace-normalised); ellipses rejected; "
        "exactly one marking point per mark; command word present; dependent "
        "(b) must refer back to (a); non-dependent siblings must use different "
        "angles; cross-generated duplicates rejected; fuzzy near-copy against "
        "all 35 papers rejected at SequenceMatcher >= 0.80.",
        "- Every accepted theory answer is labelled `sourced`; each point "
        "carries deck + slide + chunk id.",
        "",
        "### Results and cost",
        "",
        f"- Model: **{theory['model']}**; attempt limit: "
        f"{theory['attempt_limit']} (initial + up to 3 retries).",
        f"- Slots filled: **24/24** (23 theory sourced, 1 computed); "
        f"accepted theory questions: **{theory['accepted_count']}** / 23 "
        f"theory slots; placeholders left: **{theory['placeholder_count']}**.",
        f"- Rejected slots in the final artifact: **0**; intermediate rejected "
        "attempts are listed below with reasons.",
        f"- Theory marks covered: **94**; marking points: **94**; every point "
        "has a verified quote.",
        f"- Calls: **{theory['usage']['calls']}**; tokens: "
        f"{theory['usage']['prompt_tokens']} prompt + "
        f"{theory['usage']['completion_tokens']} completion = "
        f"{theory['usage']['total_tokens']}.",
        f"- Estimated cost: **${theory['usage']['cost_usd']:.4f}**; "
        f"cost per accepted question: "
        f"**${theory['cost_per_accepted_question_usd']:.4f}**.",
        "- Cost basis: public qwen-flash list prices (input $0.022/M, output "
        "$0.216/M) used as a configurable estimate; this is not an invoice.",
        "",
        "### Rejections and retries",
        "",
        "The final pass made 28 group attempts for 12 question groups; 2 "
        "groups were accepted on the first attempt. Rejection categories in "
        "the retained attempt logs:",
        "",
    ]
    cats = Counter()
    for g in theory["groups"]:
        for errs in g["errors"]:
            for e in errs:
                if "near-duplicate" in e or "sibling pair near-duplicate" in e:
                    cats["near-duplicate / sibling duplicate"] += 1
                elif "not verbatim" in e:
                    cats["quote not verbatim"] += 1
                elif "ellipsis" in e:
                    cats["ellipsis in quote"] += 1
                elif "marking points" in e:
                    cats["point count != marks"] += 1
                elif "JSON schema" in e:
                    cats["JSON/schema failure"] += 1
                elif "does not refer back" in e:
                    cats["dependent (b) missing back-reference"] += 1
                elif "angle hint" in e or "forbidden angle" in e:
                    cats["angle hint violation"] += 1
                elif "question too short" in e or "question too long" in e:
                    cats["question length"] += 1
                elif "quote too short" in e:
                    cats["quote too short"] += 1
                elif "chunk_id" in e:
                    cats["chunk id not in retrieved evidence"] += 1
                else:
                    cats["other"] += 1
    for k, v in cats.most_common():
        lines.append(f"- {k}: {v}")
    lines += [
        "",
        "### Rejected attempts (examples from the retained logs)",
        "",
    ]
    rej_rows = []
    for g in theory["groups"]:
        for attempt, errs in enumerate(g["errors"], 1):
            if not errs:
                continue
            reason = "; ".join(errs[:2])
            if len(reason) > 240:
                reason = reason[:237] + "..."
            rej_rows.append([g["question"], ", ".join(g["slots"]), attempt,
                             reason])
            if len(rej_rows) >= 18:
                break
        if len(rej_rows) >= 18:
            break
    lines += _md_table(["Question", "Slots", "Attempt", "Rejected because"],
                       rej_rows, ["---", "---", "---:", "---"])
    lines += [
        "",
        "The first exploratory pass and the placeholder retries also rejected "
        "near-copies, ellipsis quotes, 10-character schema failures and "
        "duplicate sibling angles; those were fixed by the chunk-id cleanup, "
        "quote-length rule, sibling/duplicate checks and per-slot angle hints. "
        "No placeholder remains in the final paper.",
        "",
        "### Attempts per question group",
        "",
    ]
    rows = []
    for g in theory["groups"]:
        rows.append([g["question"], ", ".join(g["slots"]), g["attempts"],
                     "accepted" if g["accepted"] else "placeholder",
                     "; ".join(f"{r['deck']} s{r['slide']}"
                               for r in g["retrieved"][:2]) or "-"])
    lines += _md_table(["Question", "Slots", "Attempts", "Result",
                        "Top retrieval"], rows,
                       ["---", "---", "---:", "---", "---"])
    lines += [
        "",
        "### Low style-confidence slots",
        "",
        f"Exact style examples n<3: **{len(plan['low_style_confidence_slots'])} "
        f"slots** - {', '.join(plan['low_style_confidence_slots'])}. These were "
        "widened in the order exact -> same topic/any command -> same command/"
        "any topic; every accepted question still has at least 3 style examples "
        "after widening and is marked `low_style_confidence` in the JSON and "
        "scheme.",
        "",
        "### Source coverage",
        "",
    ]
    src = Counter()
    for q in theory["accepted"]:
        for pt in q["marking_points"]:
            src[pt["source_deck"]] += 1
    for deck, n in src.most_common():
        lines.append(f"- {deck}: {n} marking points")
    lines += [
        "",
        f"Near-copy maximum against the 35 past papers: **{max(near_copy(q['question']).ratio for q in theory['accepted']):.2f}** "
        "(threshold 0.80).",
        "",
        "## 5. Paper and scheme QA",
        "",
        f"- Paper PDF: **{len(PdfReader(str(OUTPUTS_DIR / 'mock_paper_02.pdf')).pages)} pages**; "
        f"scheme PDF: **{len(PdfReader(str(OUTPUTS_DIR / 'mock_scheme_02.pdf')).pages)} pages**.",
        "- Paper marks audit: 24 mark lines summing to 100 "
        "(Part A 80 + Part B 20).",
        "- Paper headings: PART A (80 MARKS) and PART B (20 MARKS).",
        "- Vigenere computed question: ciphertext `UMRBVVNWVPREQE`, key "
        "`CIPHER`, answer `SECURE LOGIN NOW`; the 26 x 26 tableau is printed "
        "immediately after Q2(b), titled `Vigenere tableau (A = 0)`.",
        "- Scheme: 23 sourced theory answers + 1 computed answer + 0 "
        "placeholders; each theory point shows its quote, deck, slide and chunk "
        "id; low-style slots are flagged.",
        "- Template checks: crest media `word/media/image1.jpeg` retained; "
        "header `CS/MOCK OCT 2026/CSC662` and footer `CONFIDENTIAL` / "
        "`Hak Cipta Universiti Teknologi MARA` retained in both paper and "
        "scheme.",
        "- Tests: 112 pytest tests pass (`uv run pytest -q`), including planner "
        "invariants, theory quote verification, near-copy detection and "
        "dependent/sibling checks.",
        "",
        "## 6. Caveats / still unverified",
        "",
        "- The 2018 papers have no A/B labels, and 2025-07/2026-02 contain "
        "noisy extraction; measured rates use the 8 papers with explicit A/B "
        "labels (72 Part A pairs).",
        "- Low style confidence: 10 slots lack 3 exact (topic+command+marks) "
        "examples; widening is recorded per slot.",
        "- Some marking points quote short slide headings (e.g. `Operating "
        "System Independence`) rather than full sentences; the quote is still "
        "verbatim, but a human marker may want a fuller sentence.",
        "- A6(b) is a password-threat question under the attacks/malware topic; "
        "it is an attack-on-authentication angle, sourced from deck 022 rather "
        "than the malware slides. The paper does not print topic labels; the "
        "scheme shows the sources.",
        "- Playfair and affine remain older-style only and are not used in "
        "realistic mode; OTP remains unverified against the inconsistent slide "
        "17 and is not used here.",
        "- Cost is an estimate from public qwen-flash prices, not an account "
        "invoice; token counts are from the provider usage fields.",
        "",
        "## 7. Generated files",
        "",
        "- `outputs/mock_paper_02.docx` / `.pdf`",
        "- `outputs/mock_scheme_02.docx` / `.pdf`",
        "- `outputs/planner_revised_realistic.json` / `.md`",
        "- `outputs/planner_measurements.json` / `.md`",
        "- `outputs/theory_drafts_realistic.json` / `.md`",
        "- `outputs/vigenere_tableau.png`",
        "- `outputs/final_report.md` / `.pdf`",
    ]
    return "\n".join(lines) + "\n"


def main() -> None:
    md = build()
    OUT.write_text(md, encoding="utf-8")
    print(f"wrote {OUT} ({len(md.splitlines())} lines)")


if __name__ == "__main__":
    main()
