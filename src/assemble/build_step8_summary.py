"""Generate the one-page Step 8 summary PDF (compact HTML -> Edge PDF)."""
from __future__ import annotations

from src.assemble.mock_paper import html_to_pdf

HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 1.0cm 1.1cm; }
body { font-family: Arial, sans-serif; font-size: 8.1pt; line-height: 1.2; color:#111; }
h1 { font-size: 13.5pt; margin: 0 0 3pt 0; text-align:center; }
h2 { font-size: 9.1pt; margin: 6pt 0 2pt 0; border-bottom:1px solid #999; padding-bottom:1pt; }
p { margin: 2pt 0; }
ul { margin: 2pt 0 2pt 13pt; padding:0; }
li { margin: 1pt 0; }
table { border-collapse: collapse; width:100%; font-size:7.6pt; margin:2pt 0; }
td, th { border:1px solid #999; padding:1.3pt 2.5pt; vertical-align:top; }
th { background:#eee; }
.small { font-size:7.4pt; color:#333; }
</style></head><body>
<h1>Step 8 summary - mock CSC662 paper vs 3 clean modern papers</h1>
<p class="small"><b>Scope.</b> mock_paper_01.pdf (5 pages) vs JUN 2019 (7), DEC 2019 (6), FEB 2022 (14). Word COM export; 200 dpi renders. Full report: step8_comparison.md. Slide check: slide_convention_report.md.</p>

<h2>Structure</h2>
<table>
<tr><th>Feature</th><th>Mock</th><th>JUN 2019</th><th>DEC 2019</th><th>FEB 2022</th></tr>
<tr><td>Part A / B</td><td>10 x (2+6) = 80 / 2 x (5+5) = 20</td><td>same</td><td>same</td><td>same</td></tr>
<tr><td>Total / duration</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td><td>100 / 3 HOURS</td></tr>
<tr><td>Part headings</td><td>PART A / PART B</td><td>PART A (80 MARKS) / PART B (20 MARKS)</td><td>same</td><td>same</td></tr>
<tr><td>Cover</td><td>FINAL EXAMINATION, 5 instructions</td><td>same style</td><td>same style</td><td>FINAL TEST, 3 instructions + name/marks grid</td></tr>
<tr><td>Printed pages</td><td>5</td><td>7</td><td>6</td><td>14</td></tr>
<tr><td>Computed / placeholder marks</td><td>28 / 72</td><td>6 / 0</td><td>6 / 0</td><td>0 / 0</td></tr>
</table>
<p><b>Matches:</b> parts, question counts, 2/6/5/5 marks, 100 total, 3 hours, a/b numbering, header/footer on every body page, right-aligned mark labels. <b>Differences:</b> mock part headings omit mark totals; cover differs from FEB 2022; page count/density; computed share.</p>

<h2>Layout (pages 2+)</h2>
<table>
<tr><th></th><th>Mock</th><th>JUN 2019</th><th>DEC 2019</th><th>FEB 2022</th></tr>
<tr><td>Header / footer present</td><td>4/4 / 4/4</td><td>6/6 / 6/6</td><td>5/5 / 5/5</td><td>13/13 / 13/13</td></tr>
<tr><td>Header / footer / body ink (median)</td><td>0.0116 / 0.0072 / 0.0270</td><td>0.0038 / 0.0102 / 0.0368</td><td>0.0116 / 0.0105 / 0.0459</td><td>0.0125 / 0.0166 / 0.0184</td></tr>
<tr><td>Question heading</td><td>10.7 pt regular, x=0.123</td><td>OCR only</td><td>9.7-10.0 regular, x=0.136</td><td>11.0 bold, x=0.121</td></tr>
<tr><td>a/b labels / marks labels</td><td>24 / 24</td><td>24 / 24 (OCR)</td><td>24 / 24</td><td>25 / 24</td></tr>
<tr><td>Mark right edge / page width</td><td>0.879</td><td>OCR only</td><td>0.868</td><td>0.879</td></tr>
</table>
<p>Mock is denser than all three (4 questions/page on pages 2-4; Part B Q2 spills onto p5; FEB 2022 gives each question a page), footer ink is lighter than DEC/FEB, and FEB 2022 uses bold headings. Side-by-side question pages: step8_side_by_side.png (DEC), _jun2019.png, _feb2022.png.</p>

<h2>Computed share</h2>
<p>Clean modern fingerprint: <b>40 machine-verifiable marks over 10 papers = 4.0 marks/paper</b> (34 classical cipher + 6 ACM construction). The three clean papers carry 6, 6 and 0. The mock carries <b>28 marks (6 slots)</b> and <b>72 placeholder marks (18 slots)</b> - 7x the modern computed share. <b>Mock is a practice-mode paper.</b> A realistic paper would have about 2-5 computed marks (one 6-mark cipher/ACM question, sometimes none) and 94-98 theory marks; the 72 placeholders are the missing realistic part.</p>

<h2>Wording and slide verification</h2>
<p>Stems now state the key/method: Caesar shift 7 with direction; Playfair 5 x 5 grid, I/J merge, X filler; columnar 3 x 4 matrix, put ciphertext into columns/read rows, filler X.</p>
<ul>
<li><b>Caesar (Q2a/Q4a):</b> 24-25 letters, shift 7, 2 marks; real modern Caesar is 11 letters, 6 marks, asks for the key; older 15 letters, 3 marks.</li>
<li><b>Playfair (Q2b/Q4b):</b> 12-13 pairs, key REDFOX, 6 marks vs real 10 letters/5 pairs; <b>no lecture slide</b>; I/J + X unverified.</li>
<li><b>ACM (Q3b):</b> matrix+ACL+CL+diagram for 6 marks; older three views 3+3+3 = 9 marks; modern matrix only, 6 marks.</li>
<li><b>Columnar (Q5b):</b> 3 x 4, 12 letters, pad X, 6 marks; <b>matches lecture slides 20-21 and 24</b>; real questions use 30 letters, pad D/z and "Show the steps".</li>
<li><b>Other slide checks:</b> Caesar (5/6/9), Vigenere (15), rail fence (25/26) match. <b>Playfair/affine: no slide.</b> <b>OTP slide 17 is internally inconsistent</b> (I/J-merged plaintext indices, 26-letter ciphertext, Q for 15); OTP remains unverified.</li>
</ul>

<h2>Marking scheme</h2>
<p>mock_scheme_01.pdf, 5 pages, same header/footer as the paper: working for all 6 computed slots (Caesar arithmetic, Playfair grid+pairs, ACM matrix/ACL/CL + rendered diagram, 3x4 columnar grid), confidence labels (computed / convention unverified / placeholder), suggested mark splits, and an 18-row placeholder table. No official CSC662 schemes exist; all splits are inferred from the printed 2/6 and 5/5 labels. Columnar and Caesar now carry slide evidence; Playfair remains unverified.</p>

<h2>Weakness list (specific)</h2>
<ul>
<li>72 marks are placeholders; the theory module is not built.</li>
<li>Computed share 28 % vs 4.0 marks/paper modern average (practice mode).</li>
<li>Caesar twice and Playfair twice; real papers vary cipher types.</li>
<li>Caesar 24-25 letters for 2 marks; Playfair 12-13 pairs for 6 marks and no slide.</li>
<li>ACM four outputs for 6 marks; older three-view question is 9 marks.</li>
<li>Columnar 12 vs 30 letters; 3x4 convention verified, but real questions use pad D/z.</li>
<li>OTP slide inconsistent; Playfair/affine have no slide; single transposition is paper-only.</li>
<li>Part headings omit "(80 MARKS)/(20 MARKS)"; cover differs from FEB 2022.</li>
<li>5 pages vs 6/7/14; less answer space; headings regular vs FEB bold; footer ink lighter.</li>
<li>No official marking scheme; suggested splits are inferred.</li>
</ul>
</body></html>"""


def main() -> None:
    pages = html_to_pdf(HTML, "outputs/step8_summary.pdf")
    print("step8_summary.pdf pages:", pages)


if __name__ == "__main__":
    main()
