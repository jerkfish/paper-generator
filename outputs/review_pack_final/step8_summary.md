# Step 8 summary - final mock CSC662 paper vs 3 clean modern papers

**Scope.** `mock_paper_04.pdf` (6 pages) vs JUN 2019 (7), DEC 2019 (6), FEB 2022 (14). Built from final hardened realistic run, seed 12 (DeepSeek V4.1 Flash); scheme 04 is 16 pages. Word COM export; 200 dpi renders; header/footer/body ink plus text-box measurements. Full report: `step8_comparison.md`. Earlier paper-01 version archived as `step8_comparison_paper01.md`.

**Structure - matches.** Part A 10 x (2 + 6) = 80; Part B 2 x (5 + 5) = 20; total 100; 3 HOURS. `PART A (80 MARKS)` / `PART B (20 MARKS)`, a/b numbering, 2/6/5/5 labels and mark totals all match the three papers. 23 sourced theory answers + 1 computed Vigenere; **0 placeholders**.

**Structure - differences.** Printed pages 6 vs 7/6/14 (matches DEC 2019). Cover is `FINAL EXAMINATION`, 5 instructions (matches JUN/DEC); FEB 2022 uses `FINAL TEST`, 3 instructions and a Name/ID/Group + marks grid. Computed marks 6 vs 6/6/0 (matches JUN/DEC). FEB 2022 gives one question per page and runs to 14 pages.

**Layout.** Header/footer on every body page (5/5). Header ink 0.02395 vs 0.01161 DEC / 0.01252 FEB - the bold running header is heavier. Footer ink 0.00701 vs 0.01050 DEC / 0.01657 FEB. Body ink 0.04278 vs 0.04586 DEC and 0.01837 FEB - density now close to DEC. Headings 10.7 pt bold (12/12), between DEC 9.7-10.0 regular and FEB 11.0 bold; heading x 0.1233 vs 0.1357 DEC / 0.1210 FEB. Mark-label right edge 0.8791 vs 0.8684 DEC / 0.8793 FEB. 24 a/b labels and 24 mark labels.

**Computed share.** Mock: 6 computed marks / 100 = 6 %; clean modern fingerprint 4.0 marks/paper (40/10), comparison papers 6/6/0. The paper is realistic, not practice mode, and supersedes paper 01's 28 computed marks / 28 %. Only one Vigenere question; no repeated cipher types.

**Theory content.** 23/23 questions accepted, 94 points, 0 placeholders. Source overlap 0; max near-copy 0.614 (threshold 0.80). 36/94 points (38.3%) are low stem-overlap; entailment initial yes 22 / partly 12 / no 2, both `no` points regenerated; final yes 23 / partly 13 / no 0. 6 verbatim-copy rejections. Both Part B groups have a shared scenario (grounding 0.391), versus the measured 7/19 = 36.8% rate.

**Wording / difficulty.** Generated 2-mark stems are **20 words median vs 9** in clean modern papers; 6-mark **31 vs 18**; 5-mark 31.5 vs 26. Commands: Explain 11, State 6, Describe 2, Discuss 2, List 2; no Compare/Propose/Analyse/Justify in this seed. The stems are grounded and non-copied, but wordier and more scaffolded than real questions. Closest pair A1a ethics vs CSC662-2018-06 Q15a = 0.614.

**Marking scheme.** `mock_scheme_04.pdf`, 16 pages, same header/footer as the paper: computed Vigenere working + tableau, every theory point with verbatim quote and slide citation, `supported by lecture slides (not lecturer-marked)` label, stem-overlap scores and low-overlap flags. No official CSC662 schemes exist; the scheme is much more detailed than a real one.

**Weakness list (specific).** 2-mark stems too long; 6-mark stems long; command mix narrow in this seed; header ink too heavy; footer light; body denser than FEB / less answer space; 36/94 low-overlap points flagged; scenario over-represented in this seed; no official scheme; slide-supported not lecturer-marked; computed share 1.5x modern average; cover differs from FEB 2022.

**Artifacts.** `mock_paper_04.pdf`, `mock_scheme_04.pdf`, `step8_comparison.md`, `step8_layout_metrics.json`, `step8_wording.json`, `step8_side_by_side.png` (+ JUN/FEB versions), `step8_summary.pdf`.
