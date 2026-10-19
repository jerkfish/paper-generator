# Step 8 - mock paper vs three clean modern CSC662 papers

Generated 2026-10-19. Mock: `outputs/mock_paper_01.pdf` (4 pages). Comparison
papers: `CSC662 JUNE 2019.PDF` (7 pages), `CSC662 DECEMBER 2019.PDF` (6 pages),
`CSC662 FEBRUARY 2022.pdf` (14 pages). The mock and scheme were exported with
Microsoft Word COM (Office16 `WINWORD.EXE`), not LibreOffice.

Method: pages were rendered at 200 dpi. Header/footer/body "region scores" are
the fraction of ink pixels (grey < 160) in the header band (top 12 %), footer
band (bottom 12 %) and body (12-88 %), median over pages 2..N. Text metrics use
PyMuPDF word/span boxes for the text PDFs; JUN 2019 is a scan, so its text
counts come from the cached WinRT OCR (`data/tracking/ocr_cache/CSC662-2019-06.txt`)
and its region scores from the rendered images. These are layout scores, not
content similarity: the body text is different by design.

## 1. Structure

| Feature | Mock | JUN 2019 | DEC 2019 | FEB 2022 | Difference |
|---|---|---|---|---|---|
| Parts | Part A (10 questions), Part B (2 questions) | same | same | same | none |
| Marks per Part A question | a) 2, b) 6 | a) 2, b) 6 | a) 2, b) 6 | a) 2, b) 6 | none |
| Marks per Part B question | a) 5, b) 5 | a) 5, b) 5 | a) 5, b) 5 | a) 5, b) 5 | none |
| Part A / Part B marks | 80 / 20 | 80 / 20 | 80 / 20 | 80 / 20 | none |
| Total | 100 | 100 (sum of parts; cover total unsure) | 100 (sum; cover total unsure) | 100 (printed) | none in the numbers |
| Duration | 3 HOURS | 3 HOURS | 3 HOURS | 3 HOURS | none |
| Part headings | `PART A`, `PART B` | `PART A (80 MARKS)`, `PART B (20 MARKS)` | same | same | **diff**: mock omits the mark totals |
| Cover title | `FINAL EXAMINATION` | `FINAL EXAMINATION` | `FINAL EXAMINATION` | `FINAL TEST` | **diff vs FEB 2022** |
| Instructions | 5 standard items | 5 standard items | 5 standard items | 3 items + Name/Student ID/Group + marks grid | **diff vs FEB 2022** |
| Printed pages | 4 | 7 | 6 | 14 | **diff**: mock is much denser |
| Computed marks in paper | 6 slots / 28 marks | 6 (Q4b) | 6 (Q4b) | 0 | **diff**: mock is a practice paper |
| Placeholder marks | 18 slots / 72 marks | 0 | 0 | 0 | **diff**: theory module not built |

The paper skeleton (Parts, question counts, 2+6 and 5+5 marks, 100 marks,
3 hours) matches all three modern papers exactly. The differences are the
part-heading labels, the cover/instruction variant, the page count, and the
computed/placeholder mix.

## 2. Layout, pages 2 onward

| Metric | Mock | JUN 2019 | DEC 2019 | FEB 2022 |
|---|---|---|---|---|
| Page count | 4 | 7 | 6 | 14 |
| Header present (body pages) | 3/3 | 6/6 (OCR) | 5/5 | 13/13 |
| Footer present (body pages) | 3/3 | 6/6 (OCR) | 5/5 | 13/13 |
| Header ink fraction, median | 0.0101 | 0.0038 | 0.0116 | 0.0125 |
| Footer ink fraction, median | 0.0070 | 0.0102 | 0.0105 | 0.0166 |
| Body ink fraction, median | 0.0236 | 0.0368 | 0.0459 | 0.0184 |
| Question heading size / weight | 10.7 pt, regular | OCR only | 9.7-10.0 pt, regular | 11.0 pt, bold |
| Question heading left x / page width | 0.1233 | OCR only | 0.1357 | 0.1210 |
| a)/b) labels counted | 24 | 24 (OCR) | 24 | 25 |
| `(N marks)` labels counted | 24 | 24 (OCR) | 24 | 24 |
| Mark-label right edge / page width | 0.8791 | OCR only | 0.8684 | 0.8793 |
| Median question-heading gap | 154.2 pt | n/a | 203.3 pt | one question per page |
| Question headings per body page | 4/4/4 | 2-3 (OCR) | 3/3/3/1/2 | 1 per page |

What matches: header on every body page (ref code left/right layout, page
number, `CONFIDENTIAL`), footer on every body page, left-aligned `QUESTION N`
headings, a)/b) numbering, `(N marks)` on a separate right-aligned line, and
the right margin of the mark labels (mock 87.9 %, FEB 87.9 %, DEC 86.8 %).

What differs: the mock is set denser than all three (4 questions per page vs
1-3), which is why it is 4 pages instead of 6-14. Its question headings are
regular 10.7 pt (DEC is regular 9.7-10.0; FEB 2022 is bold 11 pt). Its footer
ink is lighter than DEC/FEB (smaller or thinner footer text), and its header
ink is below DEC/FEB but above the scanned JUN 2019. The mock has no
`PART A (80 MARKS)` / `PART B (20 MARKS)` labels.

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
  marks (FEB 2022) of machine-verifiable work.
- Across the wider modern set in the Questions sheet (13 papers, 2018+), the
  total is 48 machine-verifiable marks, mean **3.7 marks/paper** (range 0-14).
- The mock carries **28 computed marks (6 slots)** and **72 placeholder marks
  (18 slots)**, i.e. **28 % computed, 7x the clean-modern average**.

Plainly: `mock_paper_01` is a **practice-mode paper**. It concentrates the
machine-verifiable types (Caesar/Playfair/columnar/ACM) so they can be drilled
and checked. A realistic CSC662 paper would normally have about 2-5 computed
marks - often one 6-mark cipher or access-control question, sometimes none -
and the remaining 94-98 marks in theory, scenario and short-objective
questions. Those 72 placeholder marks are the missing realistic part.

## 4. Wording: generated computed stems vs the closest real stems

Similarity was measured with `SequenceMatcher` on normalised text (marks
removed, punctuation stripped). "Closest" means closest available, not
necessarily the same cipher.

| Slot | Generated stem (abridged) | Closest modern | Closest older |
|---|---|---|---|
| Q2a/Q4a | `Using Caesar Cipher technique, decrypt the following ciphertext. KLCP... / AYHP... (2 marks)` | DEC 2019 Q5b, 6 marks: `The message below was encrypted using a Caesar cipher. OWWL UWZVQVO. Identify the key and decrypt the message.` | OCT 2006 Q2a, 3 marks: `Using Caesar Cipher technique, decrypt the following ciphertext. wuhdwblpsrvvleoh` (similarity 0.80) |
| Q2b/Q4b | `Encrypt the message below using Playfair encryption with the key REDFOX. REVIEW ACCESS PERMISSIONS / CONTAINER SECURITY CHECKS (6 marks)` | No modern Playfair stem exists. Closest modern compute stems are DEC 2019 Q4b (OTP, 6 marks) and 2018-01 Q14 (Vigenere, 3 marks) - different ciphers. | DEC 2016 Q8, 6 marks: `Encrypt the message "LESS IS MORE" using Playfair encryption. The key = REDFOX.` (similarity 0.63; extraction noise around the marks) |
| Q3b | `Assume a computer system with the accounts: Ali, Yati, Umi, Root. Ali can read, write X-1; ... Based on the scenario above, write the ACM, ACL, CL, and draw the diagram. (6 marks)` | 2018-06 Q7, 6 marks: `Given the situation: A computer system has four (4) accounts: Adam, Suzy, Maryam and Root. Four rights ... Draw an Access Control Matrix based on the above UNIX access control list (ACL).` | 2015-06 Q7a-c, 3+3+3 = 9 marks: `Write a access control matrix (ACM).` / `Write a set of access control lists (ACL).` / `Write a set of capability lists (CL).` |
| Q5b | `Decrypt the following ciphertext using columnar transposition with a 3 x 4 grid (3 rows, 4 columns). LNIOATGUXIDX (6 marks)` | 2018-01 Q10, 6 marks: `Decrypt the following cipher-text using columnar transposition once with character 'D' as a padding character. AEICC RTTOS YSMES DPCUD UUBDT RJD. Show the steps in your answer.` | 2011-04 Q7, 8 marks: same wording with padding character `z`; 30 letters. |

Specific differences:

- **Phrasing.** The generated stems are short imperatives (`Using ...`,
  `Encrypt ...`, `Decrypt ...`). Real stems often set a situation first
  (`Given the situation: ...`, `The message below was ...`) and sometimes ask
  for an extra step (`Identify the key`, `Show your work`, `Show the steps`).
  The Caesar template is a near-exact copy of the 2006 stem (0.80); the other
  generated stems are original.
- **Punctuation and quoting.** Real Playfair uses a quoted message
  (`"LESS IS MORE"`); the mock uses an unquoted line. Real keys appear as
  `key = REDFOX`; the mock says `with the key REDFOX`. The mock has no
  `Show your work` phrase in the paper (the scheme shows it).
- **Key and message format.** The mock uses uppercase, unspaced ciphertext
  (25/24/12 letters), a keyword or numeric key in the sentence, and no
  padding character in the paper. Real modern ciphertexts are often grouped
  in 5-letter blocks and state the padding character (`D`/`z`); real Caesar
  questions may give a lowercase message and ask for the key.
- **Mark placement.** The mock puts `(N marks)` on a separate right-aligned
  line. DEC 2019, FEB 2022 and JUN 2019 (OCR) do the same; the older 2006/2016
  rows show the mark text inline at the end in the extraction, so the mock
  matches the clean modern layout, not the older inline style.
- **Repeated types.** The mock uses Caesar twice (Q2a/Q4a) and Playfair twice
  (Q2b/Q4b). None of the three modern papers repeats the same cipher in one
  paper; JUN 2019 combines substitution + columnar, DEC 2019 OTP + Caesar,
  FEB 2022 has no cipher-compute question.

## 5. Difficulty cues

"Steps" for the mock are the explicit operations printed in the scheme
(per-letter mappings, Playfair pairs, columnar columns/rows, ACM views). Real
papers do not print their working, so their step counts are inferred from the
requested output and the letter count. Marks are the printed marks.

| Slot | Generated: length / key / steps | Marks | Closest real: length / key / steps | Marks | Marks per step (mock vs real) |
|---|---|---|---|---|---|
| Q2a | 25 letters; shift 7; 25 letter mappings | 2 | DEC 2019: 11 letters; key to identify; ~11 mappings + key trial | 6 | 0.08 vs ~0.5 |
| Q4a | 24 letters; shift 7; 24 mappings | 2 | OCT 2006: 15 letters; no key; ~15 mappings | 3 | 0.08 vs 0.20 |
| Q2b | 23 letters; key REDFOX (6); 13 pairs | 6 | DEC 2016: 10 letters; key REDFOX; 5 pairs | 6 | 0.46 vs 1.20 per pair |
| Q4b | 23 letters; key REDFOX (6); 12 pairs | 6 | same as Q2b | 6 | 0.50 vs 1.20 per pair |
| Q3b | 4 users x 3 objects; 12 matrix cells + 4 ACL + 4 CL + diagram | 6 | 2018-06: 4 accounts, 4 rights, UNIX ACL -> matrix only; 2015-06: ACM+ACL+CL in three 3-mark parts | 6 / 9 | 0.29 per element vs ~0.5 per matrix cell / 3 per view |
| Q5b | 10 letters -> 12 cells; 4 columns x 3 rows; 4 columns + 3 rows + key order | 6 | 2018-01: 30 letters; pad D; 6 marks. 2011-04: 30 letters; pad z; 8 marks | 6 / 8 | 0.75 per grid step; 0.50 per letter vs 0.20-0.27 per letter |

What the cues mean:

- The 2-mark Caesar slots are **long** (24-25 letters) for 2 marks; the real
  modern Caesar question is 11 letters for 6 marks and asks for the key. The
  mock gives the shift, so the work is a 25-step substitution for 2 marks.
- The 6-mark Playfair slots are **long** (12-13 pairs) compared with the real
  10-letter/5-pair Playfair question. The mock's 6 marks are spread thinly
  across pairs.
- The 6-mark ACM slot is **compressed**: it asks for matrix + ACL + CL +
  diagram, while the older course question gives three 3-mark parts for the
  same three views (9 marks) and the modern question asks matrix only (6
  marks). The 2/2/1/1 split in the scheme is a proposal, not an official
  allocation.
- The 6-mark columnar slot is **shorter** than the real questions (12 vs 30
  letters) but adds an explicit 3x4 grid and padding step. It is a convention
  check, not a difficulty match.

## 6. Marking scheme

There are **no official CSC662 marking schemes** in the material; the real
papers print only the mark labels (and sometimes `Show your work` / `Show the
steps`). The mark allocation is therefore inferred from the printed 2+6 and
5+5 splits, not from an official scheme.

The regenerated `mock_scheme_01.pdf` (5 pages) uses the same Word template,
header and footer as the paper and contains:

- Full working for all six computed slots: Caesar (per-letter modular
  arithmetic), Playfair (5x5 grid + every padded pair + row/column/rectangle
  rule), ACM (matrix table, ACL and capability lists, rendered diagram), and
  columnar (3x4 grid, column split, rows, padding removal).
- Confidence labels: `computed`, `convention unverified`, `placeholder`.
- Suggested mark allocation per computed slot.
- A table of the 18 placeholder slots (72 marks), explicitly marked
  `placeholder`.

Comparison with the real allocation style: the real papers show only the
question and the marks; the mock scheme is much more detailed. For a 2-mark
Caesar question a real scheme would likely award method + answer (1+1), not
25 per-letter lines; the mock scheme says this in its "Suggested marks" line.
The Playfair and columnar working is the part a lecturer is most likely to
want to check (I/J merge, X padding, grid orientation, fill/read order).

## 7. Weakness list

Specific, not an overall rating:

1. **72 of 100 marks are placeholders** (18 slots). The paper is not a
   complete exam until the theory module is built.
2. **Computed share is 28 % vs 4.0 marks/paper in the clean modern view.**
   The mock is practice mode, not a realistic paper.
3. **Cipher types repeat**: Caesar twice (Q2a/Q4a) and Playfair twice
   (Q2b/Q4b). Real papers vary the cipher within a paper.
4. **Caesar slots are long for 2 marks**: 24-25 letters with the shift given;
   the real modern Caesar is 11 letters and asks for the key.
5. **Playfair slots are long for 6 marks**: 12-13 pairs vs 5 pairs in the
   real Playfair question; the I/J-merge and X-padding convention is
   unverified.
6. **ACM slot asks four outputs for 6 marks**: matrix + ACL + CL + diagram.
   The older course question splits the three views into 3+3+3 = 9 marks; the
   modern one asks matrix only for 6. The 6-mark allocation is likely tight.
7. **Columnar slot is short (12 letters vs 30) and uses a 3x4 numeric grid
   with pad X**; real questions state pad `D`/`z` and ask `Show the steps`.
   The 3x4 fill/read convention is unverified.
8. **Part headings omit the mark totals**: all three modern papers print
   `PART A (80 MARKS)` / `PART B (20 MARKS)`; the mock prints `PART A` /
   `PART B`.
9. **Cover/instruction variant**: the mock follows the FEB 2026 template
   (`FINAL EXAMINATION`, 5 instructions); FEB 2022 uses `FINAL TEST`, 3
   instructions and a Name/Student ID/Group + marks grid. JUN/DEC 2019 match
   the mock's 5-instruction style.
10. **Page density/page count**: 4 pages vs 6/7/14; the mock packs 4
    questions per page, FEB 2022 gives each question a page. The mock has
    much less answer space.
11. **Question-heading weight differs**: mock 10.7 pt regular; FEB 2022 is
    11 pt bold. DEC 2019 is regular 9.7-10.0, so the mock is between DEC and
    FEB.
12. **Footer ink is lighter** than DEC/FEB (0.0070 vs 0.0105/0.0166); the
    footer text may be smaller or closer to the page edge.
13. **No official scheme exists**, so every suggested mark split in the
    scheme (including 2/2/1/1 for the ACM and 1/1/2/2/1 for columnar) is
    inferred.
14. The scheme's Q2b working runs from page 2 to page 3; the page break cuts
    through the pair list. This is cosmetic, but a lecturer may prefer each
    computed slot to start on a fresh page.

## 8. Files

- `outputs/mock_paper_01.pdf`, `outputs/mock_paper_01.docx` - 4-page paper.
- `outputs/mock_scheme_01.pdf`, `outputs/mock_scheme_01.docx` - 5-page scheme.
- `outputs/step8_layout_metrics.json` - raw layout metrics.
- `outputs/step8_wording.json` - generated/closest-stem data.
- `outputs/step8_side_by_side.png` - mock vs DEC 2019 page 2.
- `outputs/step8_side_by_side_jun2019.png`, `outputs/step8_side_by_side_feb2022.png`.
- `outputs/step8_summary.md` / `outputs/step8_summary.pdf` - one-page summary.
