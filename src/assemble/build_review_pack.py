"""Build outputs/review_pack/ for a classmate or lecturer.

Contains the paper and scheme PDFs, a one-page checklist, full working for
the generated Playfair and columnar answers, and the Step 8 summary/report.
"""
from __future__ import annotations

import html
import shutil
from pathlib import Path

from src.assemble.build_docx_paper import build_slots
from src.assemble.mock_paper import html_to_pdf
from src.assemble.scheme_working import (
    columnar_decrypt_working,
    playfair_working,
)

PACK = Path("outputs/review_pack")

CHECKLIST_MD = """# CSC662 mock paper - review checklist (one page)

Paper: `mock_paper_01.pdf` (4 pages). Scheme: `mock_scheme_01.pdf` (5 pages).
Computed: 6 slots / 28 marks. Placeholders: 18 slots / 72 marks.
**Theory questions are placeholders** - the theory module has not been built.
Do not treat the 72 placeholder marks as a complete exam.

## 1. Does the layout look like a real CSC662 paper?

- [ ] Yes  [ ] No  Comments:
- Parts/marks: Part A 10 x (2+6) = 80; Part B 2 x (5+5) = 20; total 100; 3 hours. Matches JUN/DEC 2019 and FEB 2022.
- Header/footer on every body page: yes - CONFIDENTIAL, page number, `CS/MOCK OCT 2026/CSC662`, copyright.
- a)/b) numbering and right-aligned `(N marks)`: yes.
- Part headings with mark totals: **no** - mock says `PART A` / `PART B`; the modern papers say `PART A (80 MARKS)` / `PART B (20 MARKS)`.
- Cover: mock uses `FINAL EXAMINATION` + 5 instructions (FEB 2026 template); FEB 2022 uses `FINAL TEST` + 3 instructions + Name/Student ID/Group + marks grid. The mock has no name grid.
- Density: 4 pages, 4 questions/page; modern papers are 6/7/14 pages, FEB 2022 gives each question a page. The mock has less answer space.
- Headings: mock 10.7 pt regular; FEB 2022 11 pt bold; DEC 2019 ~10 pt regular.

## 2. Do the computed questions look like ones this course would set?

- Caesar/Playfair/columnar/ACM are course types; lengths and marks are the concern.
- Caesar Q2a/Q4a: 24-25 letters, shift 7, 2 marks. Real modern Caesar: 11 letters, 6 marks, identify key; older: 15 letters, 3 marks.
- Playfair Q2b/Q4b: 12-13 pairs, key REDFOX, 6 marks. Real Playfair: 10 letters, 5 pairs, 6 marks.
- ACM Q3b: matrix + ACL + CL + diagram, 6 marks. Older course: 3+3+3 = 9 marks for the three views; modern: matrix only, 6 marks.
- Columnar Q5b: 3x4 grid, 12 letters, 6 marks. Real columnar: 30 letters, pad D/z, "Show the steps"; 6/8 marks.
- [ ] The computed questions look like course questions  [ ] Too long / too short  [ ] Marks too tight / too generous

## 3. Conventions to confirm

- Playfair: [ ] I/J merge  [ ] separate J  [ ] X padding  [ ] other padding: ______
- Columnar 3x4: [ ] 3 rows x 4 columns  [ ] 4 rows x 3 columns; fill [ ] rows [ ] columns; read [ ] rows [ ] columns; pad [ ] X [ ] Z [ ] none
- Vigenere: [ ] standard 26x26 tabula recta  [ ] A=0  [ ] key repeats from the start  [ ] other: ______

## 4. Generated Playfair and columnar answers to check

| Slot | Key | Plaintext | Ciphertext / answer | Convention used |
|---|---|---|---|---|
| Q2b | REDFOX | REVIEW ACCESS PERMISSIONS | `EDEPDVBGAFNCTQDEHKNCPLRTNC` | I/J merge, X padding, 13 pairs |
| Q4b | REDFOX | CONTAINER SECURITY CHECKS | `GFPNIPPRFNFARXMPFLIRBLNC` | I/J merge, X padding, 12 pairs |
| Q5b | 4 (3x4) | LOGIN AUDIT | ct `LNIOATGUXIDX`; answer `LOGINAUDIT` | 3 rows x 4 cols, fill rows, read columns, pad X |

Full working: `generated_answers.pdf`. Please check the grid orientation, fill/read order and padding.

## 5. Comments

________________________________________________________________________________
________________________________________________________________________________
________________________________________________________________________________
"""

CHECKLIST_HTML = """<!doctype html><html><head><meta charset="utf-8"><style>
@page { size: A4; margin: 1.0cm 1.15cm; }
body { font-family: Arial, sans-serif; font-size: 8.0pt; line-height: 1.22; color:#111; }
h1 { font-size: 13pt; margin: 0 0 3pt 0; text-align:center; }
h2 { font-size: 9.2pt; margin: 6pt 0 2pt 0; border-bottom:1px solid #999; }
p { margin: 2pt 0; }
ul { margin: 2pt 0 2pt 13pt; padding:0; }
li { margin: 1.2pt 0; }
table { border-collapse: collapse; width:100%; font-size:7.6pt; margin:2pt 0; }
td, th { border:1px solid #999; padding:1.4pt 2.5pt; vertical-align:top; }
th { background:#eee; }
.box { border:1.5px solid #333; padding:4pt 6pt; margin:3pt 0; }
.small { font-size:7.4pt; }
</style></head><body>
<h1>CSC662 mock paper - review checklist</h1>
<p><b>Paper:</b> mock_paper_01.pdf (4 pages). <b>Scheme:</b> mock_scheme_01.pdf (5 pages).
<b>Computed:</b> 6 slots / 28 marks. <b>Placeholders:</b> 18 slots / 72 marks.</p>
<div class="box"><b>THEORY QUESTIONS ARE PLACEHOLDERS.</b> The theory module has not been built.
Do not treat the 72 placeholder marks as a complete exam. The paper is a practice-mode paper
with 28 computed marks (7x the clean-modern average of ~4 marks/paper).</div>

<h2>1. Does the layout look like a real CSC662 paper?</h2>
<p>[ ] Yes&nbsp;&nbsp;[ ] No&nbsp;&nbsp;Comments:</p>
<ul>
<li>Parts/marks: Part A 10 x (2+6) = 80; Part B 2 x (5+5) = 20; total 100; 3 hours. Matches JUN/DEC 2019 and FEB 2022.</li>
<li>Header/footer on every body page: yes - CONFIDENTIAL, page number, CS/MOCK OCT 2026/CSC662, copyright.</li>
<li>a)/b) numbering and right-aligned (N marks): yes.</li>
<li><b>Part headings with mark totals: no</b> - mock says PART A / PART B; modern papers say PART A (80 MARKS) / PART B (20 MARKS).</li>
<li><b>Cover:</b> mock uses FINAL EXAMINATION + 5 instructions (FEB 2026 template); FEB 2022 uses FINAL TEST + 3 instructions + Name/ID/Group + marks grid. No name grid in the mock.</li>
<li><b>Density:</b> 4 pages, 4 questions/page; modern papers 6/7/14 pages, FEB 2022 one question/page. Less answer space.</li>
<li>Headings: mock 10.7 pt regular; FEB 2022 11 pt bold; DEC 2019 ~10 pt regular.</li>
</ul>

<h2>2. Do the computed questions look like ones this course would set?</h2>
<ul>
<li>Caesar/Playfair/columnar/ACM are course types; lengths and marks are the concern.</li>
<li><b>Caesar Q2a/Q4a:</b> 24-25 letters, shift 7, 2 marks. Real modern Caesar: 11 letters, 6 marks, identify key; older: 15 letters, 3 marks.</li>
<li><b>Playfair Q2b/Q4b:</b> 12-13 pairs, key REDFOX, 6 marks. Real Playfair: 10 letters, 5 pairs, 6 marks.</li>
<li><b>ACM Q3b:</b> matrix + ACL + CL + diagram, 6 marks. Older course: 3+3+3 = 9 marks for the three views; modern: matrix only, 6 marks.</li>
<li><b>Columnar Q5b:</b> 3x4 grid, 12 letters, 6 marks. Real columnar: 30 letters, pad D/z, "Show the steps"; 6/8 marks.</li>
<li>[ ] The computed questions look like course questions&nbsp;&nbsp;[ ] Too long / too short&nbsp;&nbsp;[ ] Marks too tight / too generous</li>
</ul>

<h2>3. Conventions to confirm</h2>
<ul>
<li><b>Playfair:</b> [ ] I/J merge&nbsp;&nbsp;[ ] separate J&nbsp;&nbsp;[ ] X padding&nbsp;&nbsp;[ ] other padding: __________</li>
<li><b>Columnar 3x4:</b> [ ] 3 rows x 4 columns&nbsp;&nbsp;[ ] 4 rows x 3 columns;
fill [ ] rows [ ] columns; read [ ] rows [ ] columns; pad [ ] X [ ] Z [ ] none</li>
<li><b>Vigenere:</b> [ ] standard 26x26 tabula recta&nbsp;&nbsp;[ ] A=0&nbsp;&nbsp;[ ] key repeats from the start&nbsp;&nbsp;[ ] other: __________</li>
</ul>

<h2>4. Generated Playfair and columnar answers to check</h2>
<table>
<tr><th>Slot</th><th>Key</th><th>Plaintext</th><th>Ciphertext / answer</th><th>Convention used</th></tr>
<tr><td>Q2b</td><td>REDFOX</td><td>REVIEW ACCESS PERMISSIONS</td><td>EDEPDVBGAFNCTQDEHKNCPLRTNC</td><td>I/J merge, X padding, 13 pairs</td></tr>
<tr><td>Q4b</td><td>REDFOX</td><td>CONTAINER SECURITY CHECKS</td><td>GFPNIPPRFNFARXMPFLIRBLNC</td><td>I/J merge, X padding, 12 pairs</td></tr>
<tr><td>Q5b</td><td>4 (3x4)</td><td>LOGIN AUDIT</td><td>ct LNIOATGUXIDX; answer LOGINAUDIT</td><td>3 rows x 4 cols, fill rows, read columns, pad X</td></tr>
</table>
<p class="small">Full working: generated_answers.pdf. Please check the grid orientation, fill/read order and padding.</p>

<h2>5. Comments</h2>
<p>______________________________________________________________________________________</p>
<p>______________________________________________________________________________________</p>
<p>______________________________________________________________________________________</p>
</body></html>"""

ANSWERS_CSS = """@page { size: A4; margin: 1.4cm 1.5cm; }
body { font-family: Arial, sans-serif; font-size: 9.2pt; line-height: 1.3; }
h1 { font-size: 15pt; text-align:center; }
h2 { font-size: 11.5pt; margin-top: 14pt; }
pre { font-family: 'Courier New', monospace; font-size: 8.2pt; white-space: pre-wrap;
      background:#f4f4f4; padding:6px; border:1px solid #ddd; }
.note { font-size: 8.6pt; color:#333; border-left:3px solid #666; padding-left:7px; }"""


def main() -> None:
    PACK.mkdir(parents=True, exist_ok=True)
    for src in ("outputs/mock_paper_01.pdf", "outputs/mock_scheme_01.pdf"):
        shutil.copy2(src, PACK / Path(src).name)
    for src in ("outputs/step8_summary.pdf", "outputs/step8_comparison.md",
                "outputs/step8_side_by_side.png"):
        shutil.copy2(src, PACK / Path(src).name)

    slots = build_slots()
    q2b, q4b, q5b = slots["Q2b"], slots["Q4b"], slots["Q5b"]
    w2b = playfair_working(q2b["plaintext"], q2b["key"])
    w4b = playfair_working(q4b["plaintext"], q4b["key"])
    w5b = columnar_decrypt_working(q5b["ciphertext"], q5b["key"],
                                   rows=q5b["rows"])

    (PACK / "checklist.md").write_text(CHECKLIST_MD, encoding="utf-8")
    answers_md = f"""# Generated Playfair and columnar answers (convention check)

These are the generated answers used in the mock paper and scheme.
Playfair uses I/J merge and X padding; columnar uses a 3 rows x 4 columns
grid, fill rows left-to-right, read columns left-to-right, pad X. These are
the conventions to confirm against the course slides.

## Q2(b) - Playfair encrypt (6 marks)

Question: {q2b['question']}

```
{w2b}
```

## Q4(b) - Playfair encrypt (6 marks)

Question: {q4b['question']}

```
{w4b}
```

## Q5(b) - columnar decrypt, 3x4 grid (6 marks)

Question: {q5b['question']}

```
{w5b}
```
"""
    (PACK / "generated_answers.md").write_text(answers_md, encoding="utf-8")

    checklist_pages = html_to_pdf(CHECKLIST_HTML, str(PACK / "checklist.pdf"))
    print("checklist.pdf pages:", checklist_pages)

    answers_html = (
        "<!doctype html><html><head><meta charset='utf-8'><style>"
        + ANSWERS_CSS +
        "</style></head><body>"
        "<h1>Generated Playfair and columnar answers (convention check)</h1>"
        "<p class='note'>These are the generated answers used in the mock paper "
        "and scheme. Playfair uses I/J merge and X padding; columnar uses a 3 "
        "rows x 4 columns grid, fill rows left-to-right, read columns "
        "left-to-right, pad X. These are the conventions to confirm against "
        "the course slides.</p>"
    )
    for title, q, w in (
            ("Q2(b) - Playfair encrypt (6 marks)", q2b, w2b),
            ("Q4(b) - Playfair encrypt (6 marks)", q4b, w4b),
            ("Q5(b) - columnar decrypt, 3x4 grid (6 marks)", q5b, w5b)):
        answers_html += (
            f"<h2>{html.escape(title)}</h2>"
            f"<p><b>Question:</b></p><pre>{html.escape(q['question'])}</pre>"
            f"<pre>{html.escape(w)}</pre>"
        )
    answers_html += "</body></html>"
    answers_pages = html_to_pdf(answers_html,
                                str(PACK / "generated_answers.pdf"))
    print("generated_answers.pdf pages:", answers_pages)
    print("pack contents:", sorted(p.name for p in PACK.iterdir()))


if __name__ == "__main__":
    main()
