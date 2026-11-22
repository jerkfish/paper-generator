# CSC404 publication report

Published: **2026-11-22**  
Gate C: **approved by owner**

## Result

- Public bundle built at `outputs/public_bundle` with `--subject CSC404`.
- **20 CSC404 seeds** published: 20 papers and 20 schemes, DOCX and PDF,
  **v2 only**. Unreferenced v1 files were removed before upload; a v1 seed
  URL returns 404.
- R2: **778 objects / 200.86 MiB**; the publication run uploaded **91
  changed** objects and skipped 687 unchanged. A final metadata refresh
  uploaded 2 shared index files. Sync state: `outputs/r2_sync_state.json`;
  quota ledger: `outputs/r2_quota_ledger.json`.
- Worker `papergen` deployed as version
  `82c99cdb-d45c-4366-9308-3f5f0183498a`.
- Live site: **https://uitmpapergen.download**
- Subject page: **https://uitmpapergen.download/csc404**
- Library: **https://uitmpapergen.download/csc404/library**

## Scope note

Gate C built and uploaded only CSC404 documents. Shared site index files
(`subjects.json`, `library/manifest.json`, `paused/index.html`,
`static/gallery-shell.html`) and `subjects/CSC404/subject.json` were
refreshed; no other subject's papers or schemes were rebuilt or uploaded.

## Live checks

| Route | Result |
|---|---|
| `/` | 200 |
| `/csc404` | 200 |
| `/csc404/library` | 200 |
| `/library/CSC404/manifest.json` | 200; 20 papers, v2 only |
| CSC404 seeds 01–20 paper PDFs | 200 |
| CSC404 seed 01/10/20 scheme PDFs | 200 |
| CSC404 v1 seed 01 paper PDF | 404 (legacy not public) |

## Evidence

- `outputs/review/csc404_v2/gate_c_approval.json`
- `outputs/review/csc404_v2/library/Gate_C_report.md`
- `outputs/public_bundle/library/CSC404/manifest.json`
- `outputs/r2_sync_state.json`
- `outputs/r2_quota_ledger.json`
- `outputs/web_cache/CSC404/manifest.json`

## Provenance

No official CSC404 marking scheme was supplied. All answers and schemes are
`model_unofficial` and are not lecturer-marked. The public deployment is
library-only; generation remains local.
