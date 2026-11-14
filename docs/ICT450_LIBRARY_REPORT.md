# ICT450 — V6 Library report

Date: **2026-11-11**

The Library cache now carries **paper and scheme files for all 20 seeds**.
V4 is complete: 60/60 approved questions have model_unofficial answers, and
every seed's scheme is registered in `meta.json` / `library_manifest.json`.
The first 15 answers (seeds 1–3) were owner-approved; the others use the same
format and knowledge-base grounding. No public bundle, R2 upload or Worker
deploy was built.

## Size and feasibility

- Library size: **20** (`min(20, feasible)`).
- Approved bank: **60** questions; **56** usable for assembly.
- Reuse cap: **4**; maximum actual reuse: **2**.
- Distinct seeds without reuse: **10**.
- Capacity with the reuse cap: **40** seeds.

### Questions excluded from selection

The four approved questions below are kept in the bank but are not used by
the Library because their extracted marks do not reconcile (no mark was
invented):

- `ICT450-2018-JUN-Q4` — marks do not reconcile.
- `ICT450-2023-FEB-Q1` — subpart label gap, marks do not reconcile.
- `ICT450-2024-JAN-Q2` — marks do not reconcile.
- `ICT450-2025-JUL-Q1` — marks do not reconcile.

## Seeds

| Seed | Q1 concepts | Q2 design theory | Q3 normalization | Q4 SQL | Q5 ERD | Marks | Pages | Attachments |
|---|---|---|---|---|---|---:|---:|---:|
| 1 | ICT450-2018-DEC-Q1 | ICT450-2018-JUN-Q2 | ICT450-2019-DEC-Q4 | ICT450-2019-JUN-Q3 | ICT450-2022-FEB-Q5 | 100 | 6 | 1/1 |
| 2 | ICT450-2023-JUL-Q1 | ICT450-2023-FEB-Q2 | ICT450-2024-JAN-Q3 | ICT450-2024-JUL-Q4 | ICT450-2025-FEB-Q5 | 100 | 6 | 3/3 |
| 3 | ICT450-2026-FEB-Q1 | ICT450-2025-JUL-Q2 | ICT450-2018-DEC-Q4 | ICT450-2019-DEC-Q3 | ICT450-2018-JUN-Q5 | 100 | 6 | 2/2 |
| 4 | ICT450-2019-JUN-Q1 | ICT450-2022-FEB-Q2 | ICT450-2023-FEB-Q3 | ICT450-2023-JUL-Q4 | ICT450-2024-JAN-Q5 | 100 | 6 | 5/5 |
| 5 | ICT450-2024-JUL-Q1 | ICT450-2025-FEB-Q2 | ICT450-2025-JUL-Q3 | ICT450-2026-FEB-Q4 | ICT450-2018-DEC-Q5 | 100 | 6 | 3/3 |
| 6 | ICT450-2018-JUN-Q1 | ICT450-2019-DEC-Q2 | ICT450-2019-JUN-Q4 | ICT450-2022-FEB-Q4 | ICT450-2023-FEB-Q5 | 100 | 6 | 5/5 |
| 7 | ICT450-2024-JAN-Q1 | ICT450-2023-JUL-Q2 | ICT450-2024-JUL-Q3 | ICT450-2025-FEB-Q4 | ICT450-2025-JUL-Q5 | 100 | 6 | 1/1 |
| 8 | ICT450-2019-DEC-Q1 | ICT450-2026-FEB-Q2 | ICT450-2018-JUN-Q3 | ICT450-2018-DEC-Q3 | ICT450-2019-JUN-Q5 | 100 | 6 | 2/2 |
| 9 | ICT450-2022-FEB-Q1 | ICT450-2024-JUL-Q2 | ICT450-2023-JUL-Q3 | ICT450-2023-FEB-Q4 | ICT450-2026-FEB-Q5 | 100 | 6 | 5/5 |
| 10 | ICT450-2025-FEB-Q1 | ICT450-2018-DEC-Q2 | ICT450-2022-FEB-Q3 | ICT450-2024-JAN-Q4 | ICT450-2019-DEC-Q5 | 100 | 6 | 1/1 |
| 11 | ICT450-2018-JUN-Q1 | ICT450-2019-JUN-Q2 | ICT450-2025-FEB-Q3 | ICT450-2025-JUL-Q4 | ICT450-2023-JUL-Q5 | 100 | 6 | 5/5 |
| 12 | ICT450-2024-JAN-Q1 | ICT450-2023-FEB-Q2 | ICT450-2026-FEB-Q3 | ICT450-2024-JUL-Q4 | ICT450-2025-JUL-Q5 | 100 | 6 | 2/2 |
| 13 | ICT450-2018-DEC-Q1 | ICT450-2018-JUN-Q2 | ICT450-2019-DEC-Q4 | ICT450-2019-JUN-Q3 | ICT450-2024-JUL-Q5 | 100 | 6 | 1/1 |
| 14 | ICT450-2022-FEB-Q1 | ICT450-2023-JUL-Q2 | ICT450-2023-FEB-Q3 | ICT450-2024-JAN-Q4 | ICT450-2025-FEB-Q5 | 100 | 6 | 3/3 |
| 15 | ICT450-2026-FEB-Q1 | ICT450-2025-JUL-Q2 | ICT450-2018-DEC-Q4 | ICT450-2019-DEC-Q3 | ICT450-2018-JUN-Q5 | 100 | 6 | 2/2 |
| 16 | ICT450-2019-JUN-Q1 | ICT450-2022-FEB-Q2 | ICT450-2023-JUL-Q3 | ICT450-2023-FEB-Q4 | ICT450-2024-JAN-Q5 | 100 | 6 | 5/5 |
| 17 | ICT450-2024-JUL-Q1 | ICT450-2025-FEB-Q2 | ICT450-2025-JUL-Q3 | ICT450-2026-FEB-Q4 | ICT450-2018-DEC-Q5 | 100 | 6 | 3/3 |
| 18 | ICT450-2019-DEC-Q1 | ICT450-2019-JUN-Q2 | ICT450-2018-JUN-Q3 | ICT450-2022-FEB-Q4 | ICT450-2023-FEB-Q5 | 100 | 6 | 2/2 |
| 19 | ICT450-2023-JUL-Q1 | ICT450-2024-JUL-Q2 | ICT450-2024-JAN-Q3 | ICT450-2025-FEB-Q4 | ICT450-2026-FEB-Q5 | 100 | 6 | 3/3 |
| 20 | ICT450-2025-FEB-Q1 | ICT450-2018-DEC-Q2 | ICT450-2019-JUN-Q4 | ICT450-2025-JUL-Q4 | ICT450-2019-DEC-Q5 | 100 | 6 | 2/2 |

Every seed has five distinct source papers and six pages: the cover and
instructions page plus one page per question. All 20 seeds pass QA with
no missing attachments, no forbidden tokens and no page overflow.

All 20 seeds now carry V4 marking schemes in the cache, ranging from 6 to 9
pages. The first three were owner-approved; the rest use the same
model_unofficial format. The machine-readable `library_manifest.md` includes a
Scheme column and `docs/ICT450_SCHEMES_REPORT.md` lists every seed.

## Reuse

- Questions used: **56**.
- Maximum uses: **2** of cap **4**.
- Within cap: **true**.

## Evidence

- `outputs/web_cache/ICT450/library_manifest.json` — seed metadata, files,
  marks, pages, source papers and QA status.
- `outputs/web_cache/ICT450/library_manifest.md` — human-readable table.
- `outputs/web_cache/ICT450/reuse_report.json` — per-question use counts.
- `outputs/web_cache/ICT450/<key>/` — per-seed `paper.docx`, `paper.pdf`,
  `plan.json`, `qa.json` and `meta.json`.

## Gate C

Gate C was **approved on 2026-11-14**. The public bundle was validated, uploaded
to R2 and the Worker was deployed. See `docs/ICT450_PUBLICATION_REPORT.md`.
LLM cost: **$0.00**.
