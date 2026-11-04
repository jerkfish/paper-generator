# Project lifecycle

Last updated: **2026-11-04**

Public site: **https://uitmpapergen.download** (library-only).

Generation runs locally. The public site has no Python process, no API key and
no live generation; it serves a prebuilt bundle from R2 through a Cloudflare
Worker. The Worker also provides a small D1-backed gallery.

Stage definitions, evidence rules and [HUMAN] gates live in
`docs/SUBJECT_PLAYBOOK.md`. Per-subject progress lives in
`subjects/<CODE>/lifecycle_state.json`; query it with:

```bash
uv run python -m scripts.lifecycle_status <CODE>
```

## Current state

| Subject | Type | Local generation | Public |
|---|---|---|---|
| **CSC402** Programming I | B | Deterministic plugin; 20-seed private Library | **Not published**; stage 9 pending |
| **CSC413** Introduction to Interactive Multimedia | B | TRUE/FALSE, matching, MCQ and structured generators; 20-seed Library | **Not published**; stage 8 in progress |
| **CSC662** Computer Security | A | LLM theory plus deterministic computed generators; 20-seed Library | Published |
| **MAT133** Pre-Calculus | B | Deterministic paper-derived generators; 20-seed Library | Published |

- The registry has 44 subjects: 4 `available` and 40 `coming_soon` curriculum
  stubs.
- CSC413 stages 0-7 are complete; stage 8 built the 20-seed private Library
  and awaits [HUMAN] approval. Its publication permission is `allowed: true`,
  but stage 9 remains a hard stop and nothing has been uploaded or deployed.
- CSC402 stages 0-8 are approved and complete. Stage 9 (publication) is a hard
  stop; no CSC402 papers, downloads or Library route are published. The public
  bundle only carries the `coming_soon` registry stub.
- CSC402's publication permission is `allowed: false` in
  `subjects/CSC402/subject.json`. Do not change it without an explicit owner
  instruction.
- The public navigation's Generate link is disabled in
  `src/app/templates/base.html`. Keep it disabled while the public site is
  library-only.
- Public bundle and R2 snapshot: 221 files / 221 objects, 52,424,641 bytes
  (50.00 MiB), including 44 subject registry files.
- Public subjects are CSC662 and MAT133, with 20 Library papers each. The
  Generate routes are static notices; the live gallery is D1-backed.

## 1. Local generation

```bash
uv sync
uv run python -m src.app.main
# open http://127.0.0.1:8000
```

Local routes are subject-scoped: `/<code>`, `/<code>/library` and
`/<code>/generate`. **CSC402** routes exist only locally.

Generation behaviour comes from the registry, not from a subject allow-list:

- **Type A (CSC662)** — the planner reads the fingerprint/question log and
  builds 24 slots (A1-A10, B1, B2). Realistic mode uses the observed topic
  distribution; practice mode uses requested computed marks. Theory questions
  are drafted from lecture decks, verified (source overlap, entailment,
  near-copy, topic/deck allow-lists) and may remain visible placeholders.
  Computed slots use the CSC662 generator plugins.
- **Type B (CSC402, MAT133)** — no lecture decks, no LLM and no placeholders.
  A subject plugin builds every slot deterministically from the seed.
  CSC402 uses the modern 100-mark format: 10 MCQs (10 marks), 5 structured
  questions (60 marks) and 2 complete programs (30 marks); 17 questions and
  22 slots. MAT133 uses five questions / 15 parts / 64-72 marks.
- Subject-specific code lives under `src/subjects/<code>/`. MAT133's adapter
  reuses the existing implementation in `src/mat133/`.

Cache:

- Results go to `outputs/web_cache/<CODE>/<config-hash>/`.
- `meta.json` records seed, mode, marks, counts, files and validation.
- Re-running the same subject + mode + seed + config is instant and costs $0.
- If a rebuild had to use a new folder (for example, a locked PDF), the newest
  valid cache meta wins.

Prebuild the Library:

```bash
uv run python -m src.app.prebuild_library --seeds 1-20 --subject <CODE>
# add --force to rebuild existing seeds
```

## 2. Public bundle

The public bundle is built from the private Library cache. The registry drives
the subject list, routes and document strategy.

| Capability | Subjects | Behaviour |
|---|---|---|
| `rebuild_scheme` | Type A (CSC662) | Copy/re-export the paper; rebuild the public scheme with verbatim slide quotes omitted; require the quote-omission marker |
| `copy_cached` | Type B (CSC402, MAT133) | Copy the already-public-safe paper and scheme from the Library cache |

```bash
# Publish only the currently approved subjects.
uv run python -m scripts.build_public_bundle \
  --out outputs/public_bundle --subject CSC662 --subject MAT133

# Pages/manifests only; no Word/LibreOffice export.
uv run python -m scripts.build_public_bundle --out outputs/public_bundle \
  --subject CSC662 --subject MAT133 --pages-only
```

The builder writes the public pages, assets, per-subject JSON, Library
manifests and the generated `subjects.json` used by the Worker. It fails on
forbidden paths, private-path leaks, missing manifest files or a missing
required scheme marker.

**Subject selection:** with no `--subject`, the builder includes every
`available` subject whose `permissions.publication.allowed` is true, plus the
`coming_soon` stubs. Always pass explicit `--subject` values for a partial
rebuild.

## 3. R2 upload

```bash
# Dry run: no network calls.
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# Upload changed objects only.
uv run --with boto3 python -m scripts.r2_sync \
  --bundle outputs/public_bundle --upload
```

- Hard budgets: 1 GiB, 5,000 objects, 10,000 Class A/month and
  100,000 Class B/month.
- A local backup is made before each upload.
- State: `outputs/r2_sync_state.json`; quota ledger:
  `outputs/r2_quota_ledger.json`.
- Do not upload without explicit publication approval for every subject in
  the bundle.

## 4. Worker, routes and gallery

The Worker is in `cloudflare/worker/`.

- R2 binding: `BUCKET` -> `exampapers`
- D1 binding: `DB` -> `papergen`
- Custom domains: `uitmpapergen.download` and
  `www.uitmpapergen.download` (www redirects to the apex)
- Cron: daily 03:00 UTC

Subject routes are generated from `subjects.json`; the Worker has no
hard-coded subject list.

| Path | Source |
|---|---|
| `/` | `index.html` |
| `/<code>` | `<code>/index.html` |
| `/<code>/library` | `<code>/library/index.html` |
| `/<code>/generate` | static notice; live generation disabled |
| `/gallery` | `gallery/index.html` + D1 API |
| `/paused` | `paused/index.html` |
| `/library/<CODE>/...` | R2 objects with download filenames |
| `/api/gallery` | non-expired D1 rows |

Deploy only when publication is approved:

```bash
cd cloudflare/worker
bun x wrangler deploy
```

Gallery sharing:

1. A visitor clicks **Share** on a Library row.
2. `POST /api/gallery/share` accepts only `subject`, `mode: realistic` and
   seed 1-20.
3. The Worker finds the existing public manifest entry.
4. An unexpired row for the same subject/mode/seed is reused.
5. Otherwise four files (paper/scheme x DOCX/PDF) are copied from
   `library/<CODE>/...` to `shared/<32-hex-id>/`, a D1 row is inserted with
   `created_at`/`expires_at`, and the ID is returned.
6. `/gallery` lists only `expires_at > now`.
7. The daily Cron deletes expired D1 rows and R2 objects.
8. The R2 lifecycle rule for the `shared/` prefix is the storage backstop. It
   is not installed because the API token lacks `Workers R2 Storage Write`.

The gallery is capped at 100 active entries and shares expire after 7 days
(`GALLERY_TTL_DAYS`). Each share costs four R2 PUTs and four GETs plus D1
operations.

## 5. Updating the public site

1. Rebuild changed documents in the local Library.
2. Rebuild the bundle with explicit `--subject` values.
3. Run the R2 dry-run, then `--upload`; only changed objects are sent.
4. Document URLs carry `?v=<mtime>`, so a rebuilt PDF is not hidden by a
   browser cache.
5. Content-only changes do not require redeploying the Worker.

## 6. Adding a subject

Use `docs/SUBJECT_PLAYBOOK.md` as the authority. In short:

```bash
uv run python -m scripts.new_subject <CODE> --type A|B|C --dry-run
uv run python -m scripts.new_subject <CODE> --type A|B|C --title "Title"
uv run python -m scripts.lifecycle_status <CODE>
```

- Complete stages 0-10 in order. Every stage has a [HUMAN] gate; record the
  approval and evidence before marking it `done`.
- Record `permissions.papers`, `scheme`, `slides` and `publication` before
  stage 9.
- Stage 9 is a hard stop before public-bundle rebuild, R2 upload and Worker
  deploy.
- Subject-specific code belongs only under `src/subjects/<code>/`. Shared
  preprocessing is in `src/subjects/preprocess.py`, `templates.py` and
  `forbidden.py`.
- The app, bundle builder and Worker read the registry or generated
  `subjects.json`. Adding a hard-coded subject list is a bug.
- Being `available` locally is not the same as being published.

## 7. Live container mode

Status: **scaffolded, not deployed.** The library-only deployment remains
$0/month; live generation requires Cloudflare Workers Paid ($5/month) and
Docker to build the image. Full instructions and pricing are in
`docs/DEPLOY_LIVE.md`.
