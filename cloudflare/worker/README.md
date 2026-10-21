# Papergen Worker (library-only)

Serves the static public bundle from R2, adds a D1-backed public gallery, and
copies PUBLIC_BUILD library files into `shared/<id>/` when someone shares a
paper. There is no Python runtime and no LLM call in this deployment.

## Current deployment

- Worker: https://uitmpapergen.download
- `www.uitmpapergen.download` redirects to the apex
- workers.dev fallback: https://papergen.jerkfish123.workers.dev
- D1: `papergen` (`9d99c331-d8ba-495e-9a8d-35e295bb882c`), schema applied.
- R2: `exampapers`, 96-file public bundle plus shared gallery objects.
- Lifecycle: read-only check works; adding the rule needs
  `Workers R2 Storage Write` on the API token (or the dashboard).

## Prerequisites

- The public bundle is already in the `exampapers` bucket.
- Wrangler is available through `bun x wrangler`; log in once:

```bash
cd cloudflare/worker
bun x wrangler login
```

## Create D1 and apply the schema

```bash
bun x wrangler d1 create papergen
# Copy the database_id into wrangler.toml, replacing the all-zero UUID.

bun run db:migrate        # remote
bun run db:migrate:local  # optional local dev database
```

The schema is in `migrations/0001_gallery.sql`.

## R2 lifecycle rule

Expire shared files seven days after upload. The bucket-scoped **Object Read &
Write** S3 token used by the uploader cannot edit lifecycle configuration:
R2 returns `AccessDenied` for `PutBucketLifecycleConfiguration`. Either add the
rule in the dashboard (R2 -> exampapers -> Settings -> Object lifecycle rules:
prefix `shared/`, delete after 7 days) or use a temporary admin token:

```bash
bun x wrangler r2 bucket lifecycle add exampapers expire-shared-7d shared/ --expire-days 7
```

The Worker also deletes expired objects during its daily Cron trigger, so the
gallery still expires correctly if the lifecycle rule has not been added; the
rule is the backstop. Show or add the rule through the Cloudflare API:

```bash
uv run python -m scripts.r2_lifecycle --show
uv run python -m scripts.r2_lifecycle --apply
```

`--show` currently works and reports only the default multipart-abort rule.
`--apply` needs **Account -> Workers R2 Storage Write** on
`CLOUDFLARE_API_TOKEN`; without it Cloudflare returns `Authentication error`.
The dashboard path is R2 -> exampapers -> Settings -> Object lifecycle rules
(prefix `shared/`, delete after 7 days).

## Deploy

```bash
bun run deploy
```

`workers_dev = true` keeps the `*.workers.dev` fallback. The custom domains in
`wrangler.toml` are `uitmpapergen.download` and
`www.uitmpapergen.download`; the Worker redirects `www` to the apex.

## Routes

| Route | Behaviour |
|---|---|
| `/` | `index.html` from R2 |
| `/csc662` | subject page |
| `/csc662/library` | sortable/filterable Library |
| `/csc662/generate` | static notice (live generation disabled) |
| `/gallery` | public gallery page |
| `/paused` | paused notice |
| `/assets/*`, `/library/*` | static bundle objects |
| `GET /api/gallery` | non-expired D1 entries |
| `POST /api/gallery/share` | copy one Library paper/scheme into `shared/` |
| `GET /api/gallery/:id/(paper|scheme).(pdf|docx)` | shared download |
| Cron `0 3 * * *` | delete expired D1 rows and R2 objects |

## Share rules

- The request body may contain only `subject`, `mode` and `seed`.
- Subject must be `CSC662`; mode must be `realistic`; seed must be 1–20.
- No user text, filenames or URLs are accepted.
- An existing unexpired row for the same subject/mode/seed is reused, so
  repeat shares cost no R2 operations.
- `MAX_GALLERY_ENTRIES` caps active entries at 100; older entries expire
  automatically. Each share copies four files (paper/scheme × DOCX/PDF).
- Shared files live under `shared/<32-hex-id>/`; IDs are unguessable.
- No IP addresses are stored in D1. Per-IP rate limiting belongs to Phase 3.

## Tests

```bash
bun test
```

Covers static routing, traversal rejection, Content-Disposition, content types
and share validation.

## Quota notes

- Static serving: one R2 Class B GET per page/document request.
- Share: four R2 GETs (Class B) and four PUTs (Class A), plus D1 reads/writes.
- Purge: R2 DELETEs and D1 deletes for expired rows.
- The R2 free-tier budgets and local ledger are documented in
  `cloudflare/R2_QUOTA_PLAN.md`. Worker requests do not consume R2 Class A
  operations for static pages.
