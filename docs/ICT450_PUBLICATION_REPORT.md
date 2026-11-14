# ICT450 — publication report (Gate C)

Date: **2026-11-14**

## Gate C approval

The owner granted Gate C with the instruction:

> “v4 approved, publication permission true, can start gate C”

Recorded as:

- Gate C: **approved** by owner on 2026-11-14.
- `subjects/ICT450/subject.json` → `status: available`,
  `permissions.publication.allowed: true`.
- Publication basis: owner approval recorded in the subject contract.

## Public bundle

- Output: `outputs/public_bundle/`
- Validation: **0 problems** (no forbidden paths, no private markers, no
  missing manifest files).
- Bundle objects: **562**; size **149.74 MiB** of the 1 GiB internal budget.
- ICT450: **20 seeds**, **40 paper files** (DOCX + PDF) and **40 scheme files**
  (DOCX + PDF).
- Public pages: `/ict450`, `/ict450/library`, `/ict450/generate`.
- Local backup: `outputs/public_bundle_backups/20261114T063636Z/`.

## R2 upload

- Bucket: `exampapers`.
- Uploaded this run: **151 changed / 411 unchanged** objects.
- Class A this run: **152**; monthly ledger: **668 / 10,000**.
- Class B: **0 / 100,000**.
- Stored: **562 objects**, **157,012,467 bytes** (149.74 MiB) of the 1 GiB
  budget.
- Ledger: `outputs/r2_quota_ledger.json`.
- Sync state: `outputs/r2_sync_state.json`.

## Worker deployment

- Worker: `papergen`
- Version ID: `78c22e17-c81e-48e2-9cab-d92463264833`
- Custom domain: `https://uitmpapergen.download`
- Workers.dev fallback: `https://papergen.jerkfish123.workers.dev`
- Bindings: D1 `papergen`, R2 `exampapers`, gallery TTL 7 days.

## Public route checks

| Check | Result |
|---|---|
| `https://uitmpapergen.download/` | 200 HTML |
| `https://uitmpapergen.download/ict450` | 200 HTML |
| `https://uitmpapergen.download/ict450/library` | 200 HTML, 20 scheme links |
| `/library/ICT450/manifest.json` | 200 JSON, count **20** |
| Seed 01 paper PDF | 200 `application/pdf` (361,061 bytes) |
| Seed 01 scheme PDF | 200 `application/pdf` (313,457 bytes) |
| Seed 20 paper PDF | 200 (321,329 bytes) |
| Seed 20 scheme PDF | 200 (330,780 bytes) |

## Status and caveats

- V4 is complete: 60/60 approved questions answered, all `model_unofficial`.
  The first 15 answers and seed 1–3 schemes were owner-approved; the remaining
  schemes were generated in the same format and have passed automated QA but
  were not individually owner-reviewed.
- All 20 schemes are attached to the Library cache and published.
- Four flagged questions are answered but excluded from Library seeds because
  their extracted marks do not reconcile (`2018-JUN-Q4`, `2023-FEB-Q1`,
  `2024-JAN-Q2`, `2025-JUL-Q1`). The non-blocking `unsure` items remain
  recorded and accepted.
- No secret values are included in this report or the public bundle.
