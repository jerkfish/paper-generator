# CSC662 mock paper - review checklist (one page)

Paper: `mock_paper_01.pdf` (5 pages). Scheme: `mock_scheme_01.pdf` (5 pages).
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
- Density: 5 pages, 4 questions/page on pages 2-4 (Part B Q2 tail on p5); modern papers are 6/7/14 pages, FEB 2022 gives each question a page. The mock has less answer space.
- Headings: mock 10.7 pt regular; FEB 2022 11 pt bold; DEC 2019 ~10 pt regular.

## 2. Do the computed questions look like ones this course would set?

- Caesar/Playfair/columnar/ACM are course types; lengths and marks are the concern.
- Caesar Q2a/Q4a: 24-25 letters, shift 7, 2 marks. Real modern Caesar: 11 letters, 6 marks, identify key; older: 15 letters, 3 marks.
- Playfair Q2b/Q4b: 12-13 pairs, key REDFOX, 6 marks. Real Playfair: 10 letters, 5 pairs, 6 marks.
- ACM Q3b: matrix + ACL + CL + diagram, 6 marks. Older course: 3+3+3 = 9 marks for the three views; modern: matrix only, 6 marks.
- Columnar Q5b: 3x4 grid, 12 letters, 6 marks. The 3x4 fill-rows/read-columns/pad-X convention is **verified** against lecture slides 20-21/24. Real columnar: 30 letters, pad D/z, "Show the steps"; 6/8 marks.
- [ ] The computed questions look like course questions  [ ] Too long / too short  [ ] Marks too tight / too generous

## 3. Conventions to confirm

- Playfair (no lecture slide): [ ] I/J merge  [ ] separate J  [ ] X padding  [ ] other padding: ______
- Columnar 3x4 (slides 20-21/24: 3 rows x 4 columns, fill rows, read columns, pad X): [ ] confirmed  [ ] different: rows ___ cols ___; fill [ ] rows [ ] columns; read [ ] rows [ ] columns; pad [ ] X [ ] Z [ ] none
- Vigenere (slide 15: standard tableau, A=0, key repeats): [ ] confirmed  [ ] other: ______
- OTP (slide 17 is inconsistent: 25-letter I/J-merged vs 26-letter): [ ] 25-letter  [ ] 26-letter  [ ] ask lecturer

## 4. Generated Playfair and columnar answers to check

| Slot | Key | Plaintext | Ciphertext / answer | Convention used |
|---|---|---|---|---|
| Q2b | REDFOX | REVIEW ACCESS PERMISSIONS | `EDEPDVBGAFNCTQDEHKNCPLRTNC` | I/J merge, X padding, 13 pairs |
| Q4b | REDFOX | CONTAINER SECURITY CHECKS | `GFPNIPPRFNFARXMPFLIRBLNC` | I/J merge, X padding, 12 pairs |
| Q5b | 4 (3x4) | LOGIN AUDIT | ct `LNIOATGUXIDX`; answer `LOGINAUDIT` | 3 rows x 4 cols, fill rows, read columns, pad X |

Full working: `generated_answers.pdf`. The 3x4 columnar convention is verified against lecture slides 20-21/24; Playfair has no lecture slide. See `slide_convention_report.md`.

## 5. Comments

________________________________________________________________________________
________________________________________________________________________________
________________________________________________________________________________
