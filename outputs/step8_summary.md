# Step 8 summary - mock CSC662 paper vs 3 clean modern papers

**Scope.** `mock_paper_01.pdf` (4 pages) vs JUN 2019 (7), DEC 2019 (6), FEB 2022 (14). Word COM export; 200 dpi renders; header/footer/body ink scores plus text-box measurements. Full report: `step8_comparison.md`.

**Structure - matches.** Part A 10 x (2 + 6) = 80; Part B 2 x (5 + 5) = 20; total 100; 3 HOURS. The three papers use the same counts and marks. A/B numbering, 2/6/5/5 labels and mark totals all match.

**Structure - differences.** Mock part headings are `PART A` / `PART B`; all three papers print `PART A (80 MARKS)` / `PART B (20 MARKS)`. Mock cover is the FEB 2026 template (`FINAL EXAMINATION`, 5 instructions); FEB 2022 uses `FINAL TEST`, 3 instructions and a Name/ID/Group + marks grid. Page count 4 vs 6/7/14 because the mock packs 4 questions/page and the theory slots are short placeholders.

**Layout.** Header and footer on every body page in all four papers. Mock question headings: 10.7 pt regular at x/page = 0.123; DEC 9.7-10.0 regular at 0.136; FEB 11.0 bold at 0.121. Mark labels are separate right-aligned lines with right edge at 0.879/0.868/0.879 of page width - mock matches FEB. Header/footer/body ink medians: mock 0.0101/0.0070/0.0236; DEC 0.0116/0.0105/0.0459; FEB 0.0125/0.0166/0.0184; JUN scan 0.0038/0.0102/0.0368. Mock is denser than FEB, lighter than DEC; footer is lighter than DEC/FEB.

**Computed share.** Mock: 6 computed slots / 28 marks (28 %), 18 placeholders / 72 marks. Clean modern fingerprint: 40 machine-verifiable marks over 10 papers = 4.0 marks/paper; the three comparison papers have 6, 6 and 0. Mock is a **practice-mode paper**, 7x the modern computed share. A realistic paper would have ~2-5 computed marks (one 6-mark cipher/ACM question, sometimes none) and 94-98 theory marks.

**Wording / difficulty.** Caesar is close to OCT 2006 Q2a (0.80 similarity) but 24-25 letters with shift 7 for 2 marks; real modern Caesar is 11 letters for 6 marks and asks for the key. Playfair is close to DEC 2016 Q8 (0.63) but 12-13 pairs for 6 marks vs 5 pairs; I/J merge + X padding unverified. ACM asks matrix+ACL+CL+diagram for 6 marks; older course splits the three views into 3+3+3 = 9 marks, modern asks matrix only for 6. Columnar is a 3x4 grid, 12 letters, pad X for 6 marks; real questions use 30 letters, pad D/z and say "Show the steps"; 3x4 convention unverified. Caesar and Playfair each appear twice in the mock; real papers vary the cipher.

**Marking scheme.** `mock_scheme_01.pdf`, 5 pages, same header/footer as the paper: full working for all 6 computed slots, ACM matrix/ACL/CL + rendered diagram, confidence labels (`computed` / `convention unverified` / `placeholder`), suggested splits, and an 18-row placeholder table. No official CSC662 schemes exist; every mark split is inferred from the printed 2/6 and 5/5 labels.

**Weakness list (specific).** 72 marks are placeholders; computed share 7x modern; repeated cipher types; Caesar 24-25 letters for 2 marks; Playfair 12-13 pairs for 6 marks; ACM four outputs for 6 marks; columnar 12 vs 30 letters and unverified 3x4/pad-X convention; part headings omit mark totals; cover differs from FEB 2022; 4 pages vs 6/7/14; headings regular vs FEB bold; footer ink lighter; no official scheme.

**Artifacts.** `mock_paper_01.pdf`, `mock_scheme_01.pdf`, `step8_comparison.md`, `step8_layout_metrics.json`, `step8_side_by_side.png` (+ JUN/FEB versions), `review_pack/`.
