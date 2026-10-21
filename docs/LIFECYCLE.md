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

## 7. Adding a different subject (for example CSC580)

The registry supports multiple subjects. CSC662 and MAT133 are the two working
examples:

- CSC662 uses the lecture-deck theory pipeline.
- MAT133 uses deterministic paper-derived generators and needs no LLM.

A new subject needs all of these:

### Data and registry

1. Add `subjects/CSC580/subject.json` with `status: "available"`, title,
   header text, template path, fingerprint, deck map, topic-deck allow-list
   and enabled computed generators.
2. Add the subject papers under `data/papers/<SUBJECT>/`, the template under
   `data/reference/<SUBJECT>/` and, if the subject uses slides, the decks under
   `data/lecturedecks/<SUBJECT>/`. No paper folder needs to exist until the
   subject's papers are added.
3. Build the subject's question log/fingerprint from its past papers. The
   CSC662 planner inputs in `data/tracking/mock_paper_planner.xlsx` and
   `outputs/eval_final_deepseek/` are CSC662-specific; MAT133 has its own
   `src/mat133/planner.py`.
4. For a theory-based subject, add its BM25 topic map and topic-to-deck
   allow-list (`src/theory/bm25.py` currently contains CSC662's).
5. Add computed-generator plugins if the subject has computed questions.
6. Add the subject to the small subject allow-lists:
   - the `{DEFAULT_SUBJECT, "MAT133", ...}` check in `src/app/jobs.py`
   - the available-subject loop in `scripts/build_public_bundle.py`
     (already automatic)
   - `SUBJECTS`, `SUBJECT_ROUTES` and `PAGE_MAP` in
     `cloudflare/worker/src/index.js`
7. Add routes/pages under the subject code. The app routes are already
   `/{code}/...`; the Worker needs matching static maps.

### Generate and curate

1. Run realistic/practice generation with the subject's planner and theory
   module, or its deterministic generators.
2. Verify sources, entailment, near-copy, style confidence, or deterministic
   answer validation for a generator-only subject.
3. Human-review the 20-seed set; keep placeholders visible.
4. Build paper/scheme DOCX/PDF and run scheme QA.

### Publish

1. Build the subject's public bundle with
   `scripts.build_public_bundle.py` (all available subjects by default).
2. Update the allowlist and run the R2 dry-run/upload.
3. Add the subject to the Worker route map and D1 share validation.
4. Deploy the Worker (the custom domain is shared).
5. Verify `/csc580`, `/csc580/library`, downloads and gallery sharing.

Adding only a `subjects/CSC580/subject.json` makes the subject appear on the
home page, but it still needs a planner/prebuild, bundle mapping and Worker
routes before it can publish.

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

- Public bundle: 181 files, 52,384,519 bytes / 49.96 MiB, original local-build
  covers; CSC662 schemes are quote-free.
- R2: 189 objects (bundle + 8 shared gallery files), 53,817,347 bytes.
- Public subjects: CSC662 and MAT133, 20 Library papers each.
- D1: gallery schema applied; user-shared entries exist.
- Custom domain: apex and www, HTTPS, www -> apex redirect.
- Public site is library-only; the Generate page is a static notice.
- Worker routes: `/csc662...` and `/mat133...`, plus subject-aware gallery
  sharing.
- Footer contact: auzair1990@gmail.com
- Footer repository: https://github.com/jerkfish/paper-generator
