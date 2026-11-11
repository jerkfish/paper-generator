# ICT450 — Phase 4 pilot report (V1–V2)

Date: **2026-11-11**
Branch: **ICT450**
Scope: V0 permissions re-check, V1 MinerU dossier, V2 database-aware bank.
**Stopped at Gate A.** No answers, templates or seeds were built.

## Papers

| Item | Count |
|---|---:|
| Working PDFs | 13 |
| Unique papers | 12 |
| Duplicate copies | 1 (SHA-256 identical) |
| MinerU dossiers | 12 |
| Extraction failures | 0 |

All 12 unique papers were extracted with MinerU Cloud v4, model `vlm`. The
full result ZIP, content lists, layout, `full.md`, page renders and a
per-paper `review/EXTRACTION_REPORT.md` are kept. Seven working copies had no
text layer and were extracted by OCR; five of those six unique provisional
months were confirmed from the MinerU cover. `ICT450-2019-JUN` has no readable
month on the cover, so its paper id remains provisional and is recorded as
`unsure`.

## Bank

| Item | Count |
|---|---:|
| Questions | 60 |
| `approved` | 55 |
| `needs_fix` | 5 |
| `extracted` after the owner review | 0 |
| Assets | 40 |
| Assets: use original | 7 |
| Assets: use recreation, approved | 26 |
| Updated recreations pending review | 5 |
| Tables | 25 |
| Figures | 10 |
| Diagrams | 1 |
| Pictures | 1 |
| Page-crop fallbacks | 3 |
| Native tables accepted | 3 |
| Table/figure crops | 34 |
| Exact-text hashes | 60 |
| Questions that ask for SQL | 11 |
| Unresolved references | 2 |
| Duplicate clusters (exact) | 0 |
| Near-duplicate pairs (review aid) | 1 |

Every question has a source paper, file, page, content hash and an
`exact_text_hash`. SQL/code and relational-schema text keeps its line breaks
and indentation; only MinerU Markdown escapes such as `TEAM\_ID` were undone
to `TEAM_ID`. No SQL was rewritten.

A native table is accepted only when the PDF text layer and MinerU HTML agree
on every row's token sequence and cell count. Three typed tables met that
test; the other 34 tables/figures kept the source crop. Two unlinked wide
`TERDUKA` watermark images were skipped as decorative and listed in the gate
report.

## Needs-fix and unsure items

- 4 questions have visible marks below the paper's modal 20 (`2018-JUN-Q4`,
  `2023-FEB-Q1`, `2024-JAN-Q2`, `2025-JUL-Q1`); a sub-part may be missing.
  `2023-FEB-Q1` also has a nested-label gap (`c)` followed by `ii)`).
- 2 questions reference tables that MinerU did not emit as assets
  (`2025-JUL-Q3` Table 1, `2025-JUL-Q4` Table 4); page crops are kept and the
  references are reported as unresolved.
- `ICT450-2019-JUN` month is unverified.
- One potential repeat: `ICT450-2018-DEC-Q4` ~ `ICT450-2019-DEC-Q4`
  (Jaccard 0.71). It is reported, not merged.

## MinerU quota and cost

| Item | Value |
|---|---:|
| Documents uploaded | 12 |
| Daily limit | 5000 |
| MinerU cost | $0.00 |
| LLM cost | $0.00 |

## Owner review import

The owner reviewed the bank in two rounds on **2026-11-11**:

- First round: 37 questions approved, 23 needs-fix; 7 assets use the original
  crop and 32 requested an HTML recreation.
- Second round: 20 more questions approved; 5 remain. The owner supplied
  replacement HTML for the five remaining recreations:
  `2018-DEC-A37`, `2019-DEC-A40`, `2023-JUL-A06`, `2024-JAN-A12`, and the
  combined `2024-JUL-A14` (A14 + A15 are one figure).

The final review sheet with only those 5 questions is at
`outputs/review/ICT450/needs_fix.html` (printed copy: `needs_fix.pdf`).
Each asset has working use recreation / keep original / needs more work
buttons and a notes field; **Export decisions JSON** downloads a `fix_review`
file that can be applied back to the bank.

## Gate A

Status: **approved by the owner on 2026-11-11**.

All 60 questions are approved. The final export marked
`2024-JAN-Q3/A12` as needs_fix and carried the wrong invoice HTML in the
`2024-JUL-Q2/A14` notes; the owner’s message approved all five, so the
normalised decisions accept the existing A12 recreation, keep the combined
A14+A15 recreation, and record both corrections in
`review_decisions_round3_normalized.json`.

## V3 — format profile and scaling

- `format_profile.json`: A4, 16.56 cm content width, five questions × 20 marks,
  3 hours, QUESTION n / a), b), c) / i), ii) numbering.
- `asset_scaling.json` and `asset_scaling.md`: 38 approved assets checked.
  - 21 native tables at full 16.56 cm width, maximum 7 columns.
  - 17 images sized between 11.18 and 16.56 cm wide; maximum height 18.0 cm.
  - **0 warnings**; every asset fits the 16.56 × 24.32 cm content box.
- `review/scaling_check.pdf`: one page per asset with the A4 content box and
  the asset at its final size.

**V3 is still open.** The paper template at
`data/reference/ICT450/ICT450 TEMPLATE.docx` is a CSC662 cover
(`CS/FEB 2026/CSC662`, PART A 10 questions, PART B 2 questions), and the
standard cover copy is the same CSC662 file. It cannot be used for ICT450
documents. V4 also has no official ICT450 scheme or answer source. No paper or
scheme document has been generated.
