"""Generate the one-page Step 8 summary PDF (compact HTML -> Edge PDF)."""
from __future__ import annotations

from src.assemble.mock_paper import html_to_pdf

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 1.0cm 1.1cm; }
body { font-family: Arial, sans-serif; font-size: 7.9pt; line-height: 1.16; color:#111; }
h1 { font-size: 13.2pt; margin: 0 0 3pt 0; text-align:center; }
h2 { font-size: 8.9pt; margin: 5pt 0 1pt 0; border-bottom:1px solid #999; padding-bottom:1pt; }
p { margin: 1.5pt 0; }
ul { margin: 1.5pt 0 1.5pt 13pt; padding:0; }
li { margin: 0.7pt 0; }
table { border-collapse: collapse; width:100%; font-size:7.3pt; margin:1.5pt 0; }
td, th { border:1px solid #999; padding:1.1pt 2.3pt; vertical-align:top; }
th { background:#eee; }
.small { font-size:7.2pt; color:#333; }
</style></head><body>
<h1>Step 8 summary - final mock CSC662 paper vs 3 clean modern papers</h1>
<p class="small"><b>Scope.</b> mock_paper_04.pdf (6 pages), built from the final hardened realistic run seed 12 (DeepSeek V4.1 Flash), vs JUN 2019 (7), DEC 2019 (6), FEB 2022 (14). Word COM export; 200 dpi renders. Full report: step8_comparison.md. Paper-01 version archived as step8_comparison_paper01.md.</p>

<h2>Structure</h2>
<table>
<tr><th>Feature</th><th>Mock 04</th><th>JUN 2019</th><th>DEC 2019</th><th>FEB 2022</th></tr>
<tr><td>Part A / B</td><td>10 x (2+6) = 80 / 2 x (5+5) = 20</td><td>same</td><td>same</td><td>same</td></tr>
<tr><td>Total / duration</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td></tr>
<tr><td>Part headings</td><td>PART A (80 MARKS) / PART B (20 MARKS)</td><td>same</td><td>same</td><td>same</td></tr>
<tr><td>Cover</td><td>FINAL EXAMINATION, 5 instructions</td><td>same style</td><td>same style</td><td>FINAL TEST, 3 instructions + name/marks grid</td></tr>
<tr><td>Printed pages</td><td>6</td><td>7</td><td>6</td><td>14</td></tr>
<tr><td>Computed / theory marks</td><td>6 / 94, 0 placeholders</td><td>6 / 94</td><td>6 / 94</td><td>0 / 100</td></tr>
</table>
<p><b>Matches:</b> parts, question counts, 2/6/5/5 marks, 100 total, 3 hours, a/b numbering, part mark totals, header/footer on every body page, right-aligned mark labels. <b>Differences:</b> 6 vs 7/14 pages (matches DEC); cover differs from FEB 2022; computed share differs from FEB.</p>

<h2>Layout (pages 2+)</h2>
<table>
<tr><th></th><th>Mock 04</th><th>JUN 2019</th><th>DEC 2019</th><th>FEB 2022</th></tr>
<tr><td>Header / footer present</td><td>5/5 / 5/5</td><td>6/6 / 6/6</td><td>5/5 / 5/5</td><td>13/13 / 13/13</td></tr>
<tr><td>Header / footer / body ink (median)</td><td>0.0240 / 0.0070 / 0.0428</td><td>0.0038 / 0.0102 / 0.0368</td><td>0.0116 / 0.0105 / 0.0459</td><td>0.0125 / 0.0166 / 0.0184</td></tr>
<tr><td>Question heading</td><td>10.7 pt bold, x=0.123</td><td>OCR only</td><td>9.7-10.0 regular, x=0.136</td><td>11.0 bold, x=0.121</td></tr>
<tr><td>a/b labels / marks labels</td><td>24 / 24</td><td>24 / 24 (OCR)</td><td>24 / 24</td><td>25 / 24</td></tr>
<tr><td>Mark right edge / page width</td><td>0.879</td><td>OCR only</td><td>0.868</td><td>0.879</td></tr>
</table>
<p>Body ink is now close to DEC (0.0428 vs 0.0459), so the 6-page paper matches DEC density. Header ink is heavier than all three real papers (bold header); footer ink is lighter. FEB 2022 gives each question a page; the mock is tighter and has less answer space.</p>

<h2>Computed share</h2>
<p>Mock: <b>6 computed marks (1 Vigenere slot) = 6 %</b>, 94 theory marks across 23 sourced questions. Clean modern fingerprint: <b>40 machine-verifiable marks over 10 papers = 4.0 marks/paper</b>; the three comparison papers carry 6, 6 and 0. The paper is realistic, not practice mode, and supersedes paper 01's 28 computed marks / 28 %. Only one cipher type, so no repeated Caesar/Playfair slots.</p>

<h2>Theory content and wording</h2>
<p>23/23 theory questions accepted; 94 marking points; 0 placeholders; source overlap 0; max near-copy <b>0.614</b> (threshold 0.80). Low stem-overlap: <b>36/94 (38.3%)</b>; entailment initial yes 22 / partly 12 / no 2, both no points regenerated; final yes 23 / partly 13 / no 0. Verbatim-copy rejections: 6. Both Part B groups have a shared scenario (grounding 0.391), versus the measured 7/19 = 36.8 % rate.</p>
<table>
<tr><th>Marks</th><th>Mock median words (range)</th><th>Clean modern median (p90)</th></tr>
<tr><td>2</td><td>20 (18-30)</td><td>9 (18)</td></tr>
<tr><td>5</td><td>31.5 (24-36)</td><td>26 (43)</td></tr>
<tr><td>6</td><td>31 (28-45)</td><td>18 (44)</td></tr>
</table>
<p>Generated 2-mark stems are the main wording gap (20 vs 9 words); 6-mark stems are also longer (31 vs 18). Command mix this seed: Explain 11, State 6, Describe 2, Discuss 2, List 2; no Compare/Propose/Analyse/Justify. Closest past pair: A1a ethics vs CSC662-2018-06 Q15a = 0.614. The stems are grounded and non-copied, but wordier and more scaffolded than real questions.</p>

<h2>Marking scheme</h2>
<p>mock_scheme_04.pdf, 15 pages, same header/footer as the paper: computed Vigenere working + 26 x 26 tableau, every theory point with verbatim quote and slide citation, <i>supported by lecture slides (not lecturer-marked)</i> label, stem-overlap scores, low-overlap flags and supported/partly-supported entailment verdicts. No official CSC662 schemes exist; this is far more detailed than a real scheme.</p>

<h2>Weakness list (specific)</h2>
<ul>
<li>2-mark stems too long: 20 vs 9 words median; 6-mark 31 vs 18.</li>
<li>Command mix narrow in this seed: no Compare/Propose/Analyse/Justify.</li>
<li>Header ink 0.024 vs 0.012 real (bold running header); footer lighter (0.007 vs 0.010-0.017).</li>
<li>Body density close to DEC but much denser than FEB; 6 vs 14 pages, less answer space.</li>
<li>36/94 marking points (38.3%) remain low stem-overlap; accepted by entailment but flagged for review.</li>
<li>Both Part B groups have scenarios (over-represents the 36.8 % measured rate).</li>
<li>No official marking scheme; 15-page scheme is far more detailed than real.</li>
<li>Theory answers are slide-supported, not lecturer-marked.</li>
<li>Computed share 6 % vs 4.0-mark modern average (within range but 1.5x).</li>
<li>Cover matches JUN/DEC but differs from FEB 2022.</li>
</ul>
</body></html>"""


def main() -> None:
    pages = html_to_pdf(HTML, "outputs/step8_summary.pdf")
    print("step8_summary.pdf pages:", pages)


if __name__ == "__main__":
    main()
