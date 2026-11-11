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
| `approved` | 37 |
| `needs_fix` | 23 |
| `extracted` after the owner review | 0 |
| Assets | 40 |
| Assets: use original | 7 |
| Assets: use recreation, pending review | 32 |
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

The owner reviewed the bank on **2026-11-11**:

- 37 questions approved, 23 needs-fix.
- 7 assets use the original crop; 32 assets request an HTML recreation.
- 25 questions need a second look (23 needs-fix plus 2 approved questions with
  recreation assets).

A print pack with only those 25 questions is at
`outputs/review/ICT450/needs_fix.pdf` (and `needs_fix.html`). It shows the
original crop beside the HTML recreation, with a printed
use / keep / needs-more-work line for each asset. Five assets had no MinerU
table HTML and were transcribed into HTML from the source crop: the AB Bistro
receipt, the database-design flowchart, the Sasa eStore invoice, Table 3 of
2025-JUL, and Table 4 of 2025-JUL.

## Gate A

Status: **awaiting owner review of the 32 recreations**.

The 37 approved questions are accepted. The 23 needs-fix questions remain
unapproved until their recreation sheet is reviewed. Gate A is not approved;
seeds, answers and templates remain blocked.
