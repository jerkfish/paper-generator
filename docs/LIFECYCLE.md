# Project lifecycle

Current public deployment: **https://uitmpapergen.download** (library-only).

The public site does not run Python and does not generate papers. Generation
happens locally; the public bundle is built from the local cache and uploaded
to R2. The Worker serves the bundle and a small D1-backed gallery.

## 1. Local generation (CSC662 today)

1. **Inputs stay read-only**
   - Original papers: `CSC662/`
   - Working copies: `data/papers/<SUBJECT>/`
   - Lecture decks: `data/lecturedecks/CSC662/` (falls back to
     `CSC662_DECKS_DIR` or `~/Desktop/CSC662` while the folder is empty)
   - Template: `data/reference/CSC662/CSC662 FEBRUARY 2026-raw docx.docx`

2. **Plan the paper**
   - The planner reads the question log/fingerprint and builds 24 slots
     (A1-A10, B1, B2).
   - Realistic mode uses the observed topic distribution; practice mode uses
     requested computed marks N.
   - Computed slots use the subject's generator plugins (Vigenere, ACM,
     columnar, rail fence, OTP, Caesar for CSC662).

3. **Draft and verify theory questions**
   - The theory module retrieves lecture chunks with BM25.
   - The LLM drafts grounded questions and marking points.
   - Verification checks source overlap, entailment, near-copy against the
     35 past papers, topic/deck allow-lists, and style confidence.
   - Unresolved slots remain visible placeholders, not invented answers.

4. **Build paper and scheme**
   - Paper: the subject template, original local-build cover, computed
     questions (including the Vigenere tableau where needed).
   - Scheme: computed working, supported theory points, citations; public
     schemes omit verbatim slide quotes.
   - Word COM exports PDF; scheme table geometry and margins are QA checked in
     Word and LibreOffice.

5. **Cache**
   - Result goes to `outputs/web_cache/CSC662/<config-hash>/`.
   - `meta.json` stores seed, mode, computed marks, year, topic marks,
     accepted/placeholder counts, file paths and a config hash.
   - The same subject + mode + seed + config hash returns instantly with no LLM
     call.

Commands:

```bash
uv run python -m src.app.main
# open http://127.0.0.1:8000/csc662/generate

# rebuild the 20-seed Library without LLM calls
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC662
```

### MAT133 local generation

MAT133 has no lecture decks and no theory module. Its planner is
`src/mat133/planner.py`:

- five questions: inequalities/absolute value; functions/coordinate geometry;
  complex numbers/algebra; systems/coordinate geometry; trigonometry/geometry;
- 15 parts, 64-72 marks, all deterministic from the seed;
- diagrams and LaTeX working come from the 57 generator plugins;
- no API key and no LLM call.

```bash
uv run python -m src.app.prebuild_library --seeds 1-20 --subject MAT133
# local web UI: http://127.0.0.1:8000/mat133/generate
```

## 2. Public bundle

```bash
uv run python -m scripts.build_public_bundle --out outputs/public_bundle
```

The builder:

- reads the private Library cache;
- copies each paper DOCX and exports PDF, keeping the original local-build
  cover and crest;
- rebuilds each scheme with verbatim slide quotes omitted;
- renders the public pages from the app templates;
- writes public-safe subject JSON and the Library manifest;
- adds `?v=<mtime>` to document URLs so browsers do not reuse an older PDF;
- fails on forbidden paths or a scheme missing the quote-omission marker.

The explicit allowlist is generated with:

```bash
uv run python -m scripts.public_bundle --write
# cloudflare/public_bundle_manifest.txt / .json
```

## 3. R2 upload

```bash
# dry run: no network calls
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# upload
uv run --with boto3 python -m scripts.r2_sync \
  --bundle outputs/public_bundle --upload
```

- One `ListObjectsV2` and only changed PUTs.
- Hard budgets: 1 GiB, 5,000 objects, 10,000 Class A/month,
  100,000 Class B/month.
- A local backup is made before each upload.
- State: `outputs/r2_sync_state.json`; quota ledger:
  `outputs/r2_quota_ledger.json`.

## 4. Serving and custom domain

The Worker is in `cloudflare/worker/`.

- R2 binding: `BUCKET` -> `exampapers`
- D1 binding: `DB` -> `papergen`
- Custom domains: `uitmpapergen.download` and
  `www.uitmpapergen.download` (www redirects to the apex)
- Cron: daily 03:00 UTC

Routes:

| Path | Source |
|---|---|
| `/` | `index.html` |
| `/csc662` | `csc662/index.html` |
| `/csc662/library` | `csc662/library/index.html` |
| `/csc662/generate` | static notice; live generation disabled |
| `/gallery` | `gallery/index.html` + D1 API |
| `/paused` | `paused/index.html` |
| `/library/CSC662/...` | R2 objects with download filenames |
| `/api/gallery` | non-expired D1 rows |

Deploy:

```bash
cd cloudflare/worker
bun x wrangler deploy
```

Custom-domain DNS records and certificates are created by Cloudflare when the
`custom_domain = true` routes are deployed. A new subject uses the same
hostname with a different path; no new domain is needed.

## 5. Gallery share and expiry

1. A visitor clicks **Share** on a Library row.
2. `POST /api/gallery/share` accepts only `subject`, `mode` and `seed`.
3. The Worker finds the existing public manifest entry.
4. If an unexpired row for the same subject/mode/seed exists, it returns that
   ID and copies nothing.
5. Otherwise it copies four files (paper/scheme × DOCX/PDF) from
   `library/CSC662/...` to `shared/<32-hex-id>/`, inserts a D1 row with
   `created_at` and `expires_at`, and returns the ID.
6. `/gallery` lists only `expires_at > now`.
7. The daily Cron deletes expired D1 rows and R2 objects.
8. The R2 `shared/` lifecycle rule (prefix `shared/`, 7 days) is the storage
   backstop. It is currently not installed because the API token lacks
   `Workers R2 Storage Write`.

The active gallery is capped at 100 entries. Each share costs four R2 PUTs and
four GETs plus D1 operations.

## 6. Updating the public site

1. Rebuild changed documents/pages locally.
2. Run the bundle builder (`--pages-only` if documents are unchanged).
3. Run the R2 dry-run, then `--upload`; only changed objects are sent.
4. Document links carry `?v=<mtime>`, so the new PDF is fetched instead of a
   browser-cached old copy.
5. The Worker and custom domain do not need redeploying for content-only
   changes.

## 7. Adding a different subject

Use `docs/SUBJECT_PLAYBOOK.md` as the authority. The short version:

1. Read `docs/SUBJECT_PLAYBOOK.md` and the subject's
   `subjects/<CODE>/lifecycle_state.json`.
2. Scaffold without onboarding:
   ```bash
   uv run python -m scripts.new_subject <CODE> --type A|B|C --dry-run
   uv run python -m scripts.new_subject <CODE> --type A|B|C --title "Title"
   uv run python -m scripts.lifecycle_status <CODE>
   ```
   This creates `subject.json` with `status: "coming_soon"`, capabilities,
   permissions, plugins, a lifecycle state, the working folders and a subject
   plugin package under `src/subjects/<code>/`.
3. Complete stages 0-10 in order. Each stage has a [HUMAN] checkpoint; stop
   and record the approval before moving the lifecycle status to `done`.
4. Subject-specific code belongs only under `src/subjects/<code>/`. Shared
   rename/dedupe/OCR/register/template/forbidden-token code is in
   `src/subjects/preprocess.py`, `templates.py` and `forbidden.py`.
5. The app, bundle builder and Worker read the registry or generated
   `subjects.json`. There is no subject allow-list to edit in
   `src/app/jobs.py`, `scripts/build_public_bundle.py` or
   `cloudflare/worker/src/index.js`.
6. Record `permissions.papers`, `scheme`, `slides` and `publication` before
   stage 9. Stage 9 is a hard stop before R2 upload and Worker deploy.

A subject that only exists as `subject.json` still needs a planner/prebuild,
builders, a Library cache and explicit publication permission before it can
publish. Being `available` is not the same as being published.

### MAT133 status (published)

MAT133 completed the full lifecycle:

- `data/papers/MAT133/` — 41 papers, renamed and registered.
- `data/reference/MAT133/` — standard cover/template and answer scheme.
- `data/tracking/mat133/taxonomy.json` and `question_log.json` — paper-derived
  taxonomy and question log.
- `src/mat133/` — template body builder, 57 deterministic generators and the
  five-question planner.
- `outputs/web_cache/MAT133/` — 20-seed Library; all 57 generators are used
  across seeds 1-20; every seed passes DOCX/PDF validation.
- `outputs/public_bundle/mat133/` and `library/MAT133/` — public pages and 80
  documents.
- Worker routes and gallery share validation accept MAT133.
- `subjects/MAT133/subject.json` is `available`.

## 8. What is live now

- Public bundle: 221 files, 52,424,641 bytes / 50.00 MiB, original local-build
  covers; CSC662 schemes are quote-free; 44 subject registry files.
- R2: 221 objects, 52,424,641 bytes; the previous 8 shared gallery files have
  expired (7-day gallery TTL).
- Library metadata: CSC662 exposes computed marks and numeric placeholders;
  MAT133 exposes total marks (64-72), `has_practice_mode: false` and
  `has_placeholders: false`.
- Public subjects: CSC662 and MAT133, 20 Library papers each; 42 curriculum
  stubs are listed as `coming_soon`.
- D1: gallery schema applied; user-shared entries exist.
- Custom domain: apex and www, HTTPS, www -> apex redirect.
- Public site is library-only; the Generate page is a static notice.
- Worker routes: `/csc662...` and `/mat133...`, plus subject-aware gallery
  sharing.
- Footer contact: auzair1990@gmail.com
- Footer repository: https://github.com/jerkfish/paper-generator

## 9. Live container mode (Phase 4.2)

Status: **scaffolded, not deployed.**

- `Dockerfile` builds a Linux image with Python 3.12, uv, LibreOffice Writer
  and Graphviz.
- `src/assemble/pdf_export.py` uses Word COM on Windows and LibreOffice
  headless when `MOCKGEN_PDF_ENGINE=libreoffice` or on a non-Windows host.
- `cloudflare/container-worker/` defines the `papergen-live` Worker, a
  Durable Object container lifecycle, `/health` readiness, and the optional
  `live.uitmpapergen.download` route.
- The container runs with `PUBLIC_BUILD=1`, `MOCKGEN_MODEL=gemini-3.5-flash`
  and the `GEMINI_API_KEY` Worker secret. The repo only contains the
  placeholder `REPLACE_WITH_GEMINI_API_KEY`; the Worker refuses to start the
  container until the real secret is set. `PUBLIC_BUILD=1` also selects
  Gemini and fails closed rather than falling back to DeepSeek when the key is
  missing or a placeholder.
- Cloudflare Containers requires **Workers Paid ($5/month)**; there is no free
  tier. The library-only deployment remains $0.
- Docker is required to build the image. This machine has no Docker, so the
  image and deployment were not executed locally.
- LibreOffice currently renders the MAT133 cover one page longer than Word;
  live mode should serve DOCX only or document that difference until the cover
  is tuned.

Full instructions and pricing are in `docs/DEPLOY_LIVE.md`.
