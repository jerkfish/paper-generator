# R2 quota plan (Phase 1 preparation)

Goal: stay inside the Cloudflare R2 free tier and never reach a paid overage.

## Free-tier limits and internal budgets

| Resource | Free tier | Internal hard cap | Headroom |
|---|---:|---:|---:|
| Storage | 10 GB-month | **1 GiB** | 90% |
| Class A operations | 1,000,000/month | **10,000/month** | 99% |
| Class B operations | 10,000,000/month | **100,000/month** | 99% |
| Object count | (storage-bound) | **5,000 objects** | large |

The sync tool (`scripts/r2_sync.py`) refuses to run when a bundle would exceed
the storage/object caps, or when the monthly ledger would exceed the Class A/B
caps. It checks before any network call and exits non-zero.

## Measured bundle

The built public bundle is 80 files (paper/scheme × DOCX/PDF) plus the static
pages and metadata. Measured on 2026-10-21 in `outputs/public_bundle`:

- 80 document files plus pages/metadata: **95 files, 15.3 MB**.
- That is about **0.15% of 10 GB** and **96 Class A operations**
  (95 object PUTs + 1 LIST) on the first sync.

A public-bundle build will replace the private cache files; sizes are similar
because the content is the same.

## Operation model

- One `ListObjectsV2` per sync is **1 Class A operation**, regardless of the
  number of objects returned (paginated results may add more; 80 objects fit
  in one page).
- Only changed files are uploaded. An unchanged re-sync costs **1 Class A**
  and **0 Class B** operations.
- The sync never issues `HeadObject`/`GetObject`; remote state is compared
  from the single listing plus a local SHA-256 state file.
- User downloads are Class B operations. The 100,000/month internal cap still
  allows about 25,000 full paper+scheme downloads per month; the Worker rate
  limit is the second guard.

## Configuration

The account ID, endpoint and bucket are read from the environment:

```text
R2_ACCOUNT_ID=<account id>
R2_BUCKET=exampapers
# optional, overrides the derived endpoint:
R2_ENDPOINT=https://<account id>.r2.cloudflarestorage.com
R2_ACCESS_KEY_ID=...
R2_SECRET_ACCESS_KEY=...
```

Access keys are only read from the environment. They are never written to the
repository, the bundle, or logs.

## Dry run and upload

```bash
# Plan only: no network calls, no credentials.
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# Upload (requires R2 keys and the optional boto3 package):
uv run --with boto3 python -m scripts.r2_sync \
  --bundle outputs/public_bundle --upload
```

Before an upload the tool copies the bundle to
`outputs/public_bundle_backups/<UTC timestamp>/`.

Runtime state (not tracked, no secrets):

- `outputs/r2_sync_state.json` - object key, size, SHA-256 and last ETag.
- `outputs/r2_quota_ledger.json` - month, Class A/B counts, object/byte totals.

## Backup plan when a limit is reached

The guard aborts **before** the operation that would cross a cap. Recovery
does not depend on R2:

1. **Stop uploads.** The tool exits non-zero and prints the quota error. No
   retry, no automatic escalation to a paid plan.
2. **Serve the static site without R2.** The public HTML/CSS/HTMX pages are
   pure static files and can be hosted on Cloudflare Pages (separate free
   product) or any static host. The Library download links can point at the
   local FastAPI app or a local archive while R2 is paused.
3. **Shrink the bundle, in this order:**
   - PDF-only bundle: drops the DOCX files, roughly halves the storage.
   - 10-seed bundle: halves the remaining storage; keep 20 seeds locally.
   - Static pages + metadata only: all documents served from the local app.
4. **Restore from local backup.** Every upload is preceded by a local bundle
   copy. To rebuild the bucket, fix the quota condition, then re-run the sync;
   the state file makes unchanged objects free to skip.
5. **Wait for the monthly reset.** Class A/B counters reset on the first day
   of the UTC month. The ledger detects the month change automatically.
6. **If storage itself is exhausted** (not expected with a 1 GiB cap): delete
   old `shared/` gallery objects via the Phase 2 lifecycle rule, delete stale
   bundle versions, or reduce the seed count. Do not upgrade the plan without
   an explicit decision.

Monitoring: check the Cloudflare dashboard R2 usage before the first upload
and after each sync. The internal ledger is the primary guard; dashboard
alerts are the backstop.
