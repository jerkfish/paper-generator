# MAT133 publication report — Gate C

Date: 2026-11-16 (MYT)
Subject: MAT133 (Type D recycle, playbook v2.0)
Decision: **Gate C approved and executed**

## Approval

- Approver: project owner
- Instruction: “okay deploy this to live, gate C pass”
- Recorded before the R2 upload and Worker deployment.
- Lifecycle: `subjects/MAT133/lifecycle_state.json` gate `C` is `approved`.

## Public bundle

- Path: `outputs/public_bundle/`
- Subjects: every publication-approved available subject, plus the
  `coming_soon` stubs; generated `subjects.json` drives the Worker routes.
- MAT133: 20 seeds; each seed exposes v1 and v2 paper/scheme DOCX and PDF.
- Bundle allowlist: **558 entries, 0 forbidden/missing**.
- Builder validation: **0 problems**.
- R2 bucket: `exampapers`; **642 objects, 178,823,300 bytes (170.54 MiB)**.
- Upload: **138 changed / 504 unchanged**; Class A for this run: **139**.
- Quota ledger: **807 / 10,000 Class A** for 2026-11; within the 1 GiB,
  5,000-object and Class A budgets.

## Worker deployment

- Worker: `papergen`
- Version: `399b5696-9d80-4764-bd28-17c2465b56b5`
- Domain: https://uitmpapergen.download
- `www.uitmpapergen.download` redirects to the apex.
- Fallback: https://papergen.jerkfish123.workers.dev
- Bindings: R2 `exampapers`, D1 `papergen`, gallery TTL 7 days.
- Worker tests: **6 passed, 0 failed**.

## Live verification

| Check | Result |
|---|---|
| `/` | 200 |
| `/mat133` | 200 |
| `/mat133/library` | 200, v1 and v2 links present |
| `/mat133/generate` | 200, live generation disabled in the static bundle |
| `/library/MAT133/manifest.json` | 200 |
| MAT133 paper/scheme URLs (20 seeds × v1/v2 × DOCX/PDF) | **160 / 160 return 200** |
| `/ict450`, `/csc402`, `/csc413`, `/csc429`, `/csc662` | 200 |

## Local gates

- `uv run pytest -q`: **431 passed, 0 failed, 12 skipped**.
- `uv run python -m src.app.safety --check`: **OK, 382 text files**.
- `bun test` in `cloudflare/worker`: **6 passed**.
- `uv run python -m scripts.r2_sync --bundle outputs/public_bundle`: dry run
  within quota before upload.

## Scope and caveats

- The public deployment remains **library-only**. On-demand generation for
  MAT133 seeds 21–64 and ICT450 seeds 21–40 runs only in the local FastAPI
  app; the static Worker has no Python runtime and no LLM key.
- All model answers remain `model_unofficial`.
- Seeds 1–3 received individual owner review; seeds 4–20 passed automated QA.
- Piecewise `cases` equations use a readable plain-text fallback.
- Some recycled figures retain their source captions.
- No original file under `CSC662/` or any supplied source was modified.
