# Step 8 - final mock paper vs three clean modern CSC662 papers

Generated 2026-10-20. Mock: `outputs/mock_paper_04.pdf` (6 pages), built from
the final hardened realistic run, seed 12 (DeepSeek V4.1 Flash). Comparison
papers: `CSC662 JUNE 2019.PDF` (7 pages), `CSC662 DECEMBER 2019.PDF` (6 pages),
`CSC662 FEBRUARY 2022.pdf` (14 pages). The paper and scheme were exported with
Microsoft Word COM (Office16 `WINWORD.EXE`), not LibreOffice.

Method: pages were rendered at 200 dpi. Header/footer/body "region scores" are
the fraction of ink pixels (grey < 160) in the header band (top 12 %), footer
band (bottom 12 %) and body (12-88 %), median over pages 2..N. Text metrics use
PyMuPDF word/span boxes for the text PDFs; JUN 2019 is a scan, so its text
counts come from the cached WinRT OCR (`data/tracking/ocr_cache/CSC662-2019-06.txt`)
and its region scores from the rendered images. These are layout scores, not
content similarity: the body text is different by design. The earlier
paper-01 comparison is archived in `step8_comparison_paper01.md`.

The paper is complete: **23 sourced theory answers plus one computed Vigenere
question, 0 placeholders**. Every theory marking point cites a slide and carries
a verbatim quote; the scheme labels them `supported by lecture slides (not
lecturer-marked)`.

## 1. Structure

| Feature | Mock 04 | JUN 2019 | DEC 2019 | FEB 2022 | Difference |
|---|---|---|---|---|---|
| Parts | Part A (10 questions), Part B (2 questions) | same | same | same | none |
| Marks per Part A question | a) 2, b) 6 | a) 2, b) 6 | a) 2, b) 6 | a) 2, b) 6 | none |
| Marks per Part B question | a) 5, b) 5 | a) 5, b) 5 | a) 5, b) 5 | a) 5, b) 5 | none |
| Part A / Part B marks | 80 / 20 | 80 / 20 | 80 / 20 | 80 / 20 | none |
| Total | 100 | 100 | 100 | 100 (printed) | none |
| Duration | 3 HOURS | 3 HOURS | 3 HOURS | 3 HOURS | none |
| Part headings | `PART A (80 MARKS)`, `PART B (20 MARKS)` | same | same | same | none |
| Cover title | `FINAL EXAMINATION` | `FINAL EXAMINATION` | `FINAL EXAMINATION` | `FINAL TEST` | **diff vs FEB 2022** |
| Instructions | 5 standard items | 5 standard items | 5 standard items | 3 items + Name/Student ID/Group + marks grid | **diff vs FEB 2022** |
| Printed pages | 6 | 7 | 6 | 14 | matches DEC; **diff vs JUN/FEB** |
| Computed marks in paper | 6 (1 Vigenere slot) | 6 (Q4b) | 6 (Q4b) | 0 | matches JUN/DEC; **diff vs FEB** |
| Theory slots | 23 sourced answers, 94 marks | 94 marks of theory | 94 marks of theory | 100 marks of theory | structurally complete |

The paper skeleton (Parts, question counts, 2+6 and 5+5 marks, 100 marks,
3 hours) matches all three modern papers exactly. The paper now prints the
part-heading mark totals, which the earlier paper-01 mock omitted.

## 2. Layout, pages 2 onward

| Metric | Mock 04 | JUN 2019 | DEC 2019 | FEB 2022 |
|---|---|---|---|---|
| Page count | 6 | 7 | 6 | 14 |
| Header present (body pages) | 5/5 | 6/6 (OCR) | 5/5 | 13/13 |
| Footer present (body pages) | 5/5 | 6/6 (OCR) | 5/5 | 13/13 |
| Header ink fraction, median | 0.02395 | 0.00382 | 0.01161 | 0.01252 |
| Footer ink fraction, median | 0.00701 | 0.01015 | 0.01050 | 0.01657 |
| Body ink fraction, median | 0.04278 | 0.03682 | 0.04586 | 0.01837 |
| Question heading size / weight | 10.7 pt, bold (12/12) | OCR only | 9.7-10.0 pt, regular | 11.0 pt, bold |
| Question heading left x / page width | 0.1233 | OCR only | 0.1357 | 0.1210 |
| a)/b) labels counted | 24 | 24 (OCR) | 24 | 25 |
| `(N marks)` labels counted | 24 | 24 (OCR) | 24 | 24 |
| Mark-label right edge / page width | 0.8791 | OCR only | 0.8684 | 0.8793 |
| Median question-heading gap | 165.9 pt | n/a | 203.3 pt | one question per page |

What matches: header and footer on every body page; the ref-code/page-number/
`CONFIDENTIAL` header layout; left-aligned `QUESTION N` headings; a)/b)
numbering; separate right-aligned `(N marks)` lines; the mark-label right edge
(mock 87.9 %, FEB 87.9 %, DEC 86.8 %); and the page count/density of DEC 2019.
The body ink fraction (0.0428) is close to DEC (0.0459), so the final paper is
no longer the very dense 5-page practice paper.

What differs: the mock header is much heavier (0.0240 vs 0.0116-0.0125), because
the running header is bold; the footer is lighter than DEC/FEB (0.0070 vs
0.0105/0.0166). Question headings are 10.7 pt bold: between DEC's regular
9.7-10.0 pt and FEB's 11 pt bold. FEB 2022 gives each question a page and runs
to 14 pages; the mock packs questions more tightly and has less answer space.

Side-by-side question pages (same 200 dpi renders, resized for display):

- `outputs/step8_side_by_side.png` - mock page 2 vs DEC 2019 page 2.
- `outputs/step8_side_by_side_jun2019.png` - mock page 2 vs JUN 2019 page 2.
- `outputs/step8_side_by_side_feb2022.png` - mock page 2 vs FEB 2022 page 2.

## 3. Computed share

From the fingerprint (`outputs/fingerprint_report.md`, clean modern view: 10
papers, 995 marks):

- Modern machine-verifiable marks: 34 classical-cipher + 6 access-control
  construction = **40 marks over 10 papers = 4.0 marks/paper**.
- The three comparison papers carry 6 marks each (JUN 2019, DEC 2019) and 0
  marks (FEB 2022).
- Mock 04 carries **6 computed marks (1 Vigenere slot) = 6 % of the paper**
  and **94 theory marks** across 23 sourced questions.

The final paper is realistic, not practice mode: 6 % is within the observed
modern range (0-14 marks) and close to the 4.0-mark average. It supersedes the
paper-01 practice paper (28 computed marks / 28 %). A single Vigenere question
also avoids the earlier paper's repeated Caesar and Playfair types.

## 4. Theory content vs the real papers

Content metrics use the 23 accepted theory questions; the real comparison is
the 10 clean modern papers (259 question/sub-part rows).

| Marks | Mock 04: median words (range) | Clean modern real: median words (p90) |
|---:|---|---|
| 2 | 20 (18-30) | 9 (18) |
| 5 | 31.5 (24-36) | 26 (43) |
| 6 | 31 (28-45) | 18 (44) |
| All theory | 29 (18-45) | 12 overall |

Command mix:

| Command | Mock 04 | Clean modern real |
|---|---:|---:|
| Explain | 11 | 91 |
| State | 6 | 47 |
| Describe | 2 | 22 |
| Discuss | 2 | 17 |
| List | 2 | 15 |
| Compare | 0 | 8 |
| Propose | 0 | 11 |
| Analyse | 0 | 8 |
| Justify | 0 | 1 |

The generated 2-mark stems are the main wording gap: 20 words median against 9
in the real clean papers. The 6-mark stems are also longer (31 vs 18), because
the generator spells out multiple sub-requirements in the stem. The 5-mark
stems are close to the real median. The command mix is narrower than the real
corpus because this seed happened to draw only Explain/State/Describe/Discuss/
List; Compare, Propose and Analyse exist in the planner and appear in other
seeds.

Quality and grounding:

- **23/23** theory questions accepted; **0** placeholders; **94** marking
  points, all with a verbatim quote and slide citation.
- Source overlap: **0** shared `(deck, slide)` keys across 48 distinct keys.
- Maximum near-copy against the 35 past papers: **0.614** (threshold 0.80).
- Low stem-overlap points: **36/94 (38.3%)**; initial entailment verdicts
  **yes 22, partly 12, no 2**; both `no` points were regenerated; final
  accepted verdicts **yes 23, partly 13, no 0**.
- Verbatim-copy rejections: **6** points across the seed's retries.
- Part B: **2/2** groups have a shared scenario (B1 password policy, B2 trusted
  computing), with slide grounding 0.391. This seed over-represents the
  measured 7/19 = 36.8% scenario rate; other seeds sample it.

Five closest generated/past pairs (no pair reaches the 0.80 rejection
threshold):

| Slot | Ratio | Generated stem (abridged) | Closest real stem |
|---|---:|---|---|
| A1a | 0.614 | List TWO (2) differences between morals and laws as described in the lecture on ethics and computer security. | CSC662-2018-06 Q15a: Differentiate between Morals, Ethics and Laws in computer security. |
| A9a | 0.512 | State two ways in which an intrusion detection system contributes to detecting and defending against attacks on a system. | CSC662-2018-06 Q14a: How do intrusion detection system (IDS) and intrusion detection and prevention systems (IDPS) differ between one another? |
| A8a | 0.511 | State the two stages of the biometric authentication process and, for each stage, name the activities it involves. | CSC662-2015-12 Q5a: State the importance of the password for authentication mechanism. |
| A5b | 0.505 | Refer to your answer in (a). Based on the scenario in (a), explain how the organization can strengthen its preventive network security mechanisms... | CSC662-2025-02 QA6b: Explain 3 preventive network security mechanisms, including a firewall, a proxy server, and network segmentation... |
| B1a | 0.471 | Explain five password security controls that the administrator can apply to protect the accounts on this server, and state how passwords should be stored. | CSC662-2026-02 QA1a: State TWO (2) security goals that must be prioritized to protect the cloud-based system. |

The A1a ethics stem is the closest (0.614): the topic and the "morals vs laws"
angle recur in the real corpus, but the generated stem adds the lecture-scope
phrase and remains below the rejection threshold. This is the main residual
diversity risk in the paper, matching the ethics flag in `eval_realistic.md`.

## 5. Marking scheme

There are **no official CSC662 marking schemes** in the material; the real
papers print only mark labels (and sometimes `Show your work` / `Show the
steps`). The mark allocation is therefore inferred from the printed 2+6 and
5+5 splits, not from an official scheme.

`mock_scheme_04.pdf` (16 pages) uses the same Word template, header and footer as
the paper and contains:

- full working for the computed Vigenere slot, including the 26 x 26 tableau
  printed in the question paper;
- every accepted theory answer, with each marking point's verbatim quote and
  `deck, slide` citation;
- the **supported by lecture slides (not lecturer-marked)** confidence label;
- stemmed overlap scores, low-overlap flags, and a note on any point that
  remained low after entailment review.

This scheme is much more detailed than a real CSC662 scheme, which is expected
for a study artifact: it exposes the evidence chain that the real papers do not
print.

## 6. Weakness list

Specific, not an overall rating:

1. **2-mark stems are too long**: 20 words median vs 9 in the clean modern
   papers. Several ask for a context plus two points, where real papers often
   use a single short `State/List TWO ...` stem.
2. **6-mark stems are longer than real**: 31 vs 18 words median; the extra
   clauses make the required answer structure explicit but reduce the
   "exam-like" terseness.
3. **Command mix is narrow in this paper**: no Compare, Propose, Analyse or
   Justify questions; the wider planner supports them and other seeds use
   them.
4. **Header is heavy**: header ink 0.0240 vs 0.0116-0.0125 in DEC/FEB, because
   the running header is bold; it may look darker than the real papers.
5. **Footer is lighter**: 0.0070 vs 0.0105 (DEC) and 0.0166 (FEB); the footer
   text may be smaller or thinner.
6. **Body density/page count**: 6 pages matches DEC, but the paper is much
   denser than FEB 2022 (14 pages, one question per page); there is less
   answer space.
7. **Low-overlap points remain**: 36/94 marking points (38.3%) are below the
   stemmed-overlap threshold, although the entailment check accepted them as
   yes/partly. They are flagged for human review, not silently treated as
   strong evidence.
8. **Scenario over-representation**: both Part B groups in this seed have a
   scenario, versus the measured 7/19 = 36.8%; other seeds sample fewer.
9. **No official marking scheme**: every suggested split in scheme 04 is
   inferred; the 16-page scheme is far more detailed than any real CSC662
   scheme.
10. **Confidence label**: theory answers are slide-supported, not
    lecturer-marked; this is a study aid, not an official answer key.
11. **Computed share is 6%**, 1.5x the clean-modern 4.0-mark average (though
    within the observed 0-14 range).
12. **Cover/instruction variant**: matches JUN/DEC 2019 (`FINAL EXAMINATION`,
    5 instructions) but differs from FEB 2022 (`FINAL TEST`, 3 instructions
    and a name/marks grid).

## 7. Files

- `outputs/mock_paper_04.pdf`, `outputs/mock_paper_04.docx` - 6-page paper.
- `outputs/mock_scheme_04.pdf`, `outputs/mock_scheme_04.docx` - 16-page scheme.
- `outputs/step8_layout_metrics.json` - raw layout metrics for paper 04.
- `outputs/step8_wording.json` - generated/real word counts, command mix and
  nearest-past-question data.
- `outputs/step8_side_by_side.png` - mock page 2 vs DEC 2019 page 2.
- `outputs/step8_side_by_side_jun2019.png`,
  `outputs/step8_side_by_side_feb2022.png`.
- `outputs/step8_summary.md` / `outputs/step8_summary.pdf` - one-page summary.
- `outputs/step8_comparison_paper01.md` - archived paper-01 comparison.
