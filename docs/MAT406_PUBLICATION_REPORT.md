# MAT406 publication report

Published: **2026-11-22**  
Gate C: **approved by owner**

## Result

- Public bundle built at `outputs/public_bundle`.
- 12 MAT406 seeds published: 12 papers and 12 schemes (DOCX and PDF), all
  **v2**. v1 documents are legacy and are not referenced by the current
  production manifest.
- R2: **742 objects / 195.45 MiB** including legacy v1 MAT406 objects; the
  v2-only local bundle is **694 objects / 183.02 MiB**. This run uploaded
  **113 changed** objects and skipped **629 unchanged**.
- Worker `papergen` deployed as version
  `31d985ce-7b4c-4f7d-99ff-a9abf4b87f5c`.
- Live site: **https://uitmpapergen.download**
- Subject page: **https://uitmpapergen.download/mat406**
- Library: **https://uitmpapergen.download/mat406/library**

## Scope note

Gate C built only MAT406 documents. The first bundle pass also rewrote the
shared site metadata for every public subject (the seven `subject.json`
files), which is why R2 showed activity for other subjects. Their paper and
scheme documents were not rebuilt or re-uploaded. The bundle builder is now
scoped so future `--subject` runs only write that subject's `subject.json`.

## Live checks

| Route | Result |
|---|---|
| `/` | 200 |
| `/mat406` | 200 |
| `/mat406/library` | 200 |
| `/library/MAT406/manifest.json` | 200 |
| MAT406 seed 01 paper PDF | 200 |
| MAT406 seed 01 scheme PDF | 200 |
| `/mat133` and MAT133 manifest | 200 |

## Evidence

- `data/tracking/mat406/v2/gate_c_approval.json`
- `data/tracking/mat406/v2/GATE_C_REPORT.md`
- `outputs/public_bundle/library/MAT406/manifest.json`
- `outputs/r2_sync_state.json`
- `outputs/r2_quota_ledger.json`
- `outputs/web_cache/MAT406/manifest.json`

## Provenance

No official MAT406 marking scheme was supplied. All answers and schemes are
`model_unofficial` and are not lecturer-marked. The public deployment is
library-only; generation remains local.
