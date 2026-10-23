# Mock Paper Generator

Local study tool for two subjects:

- **CSC662 Computer Security** - plans realistic or practice papers, drafts
  grounded theory questions from lecture decks, verifies marking points and
  exports Word/PDF papers and marking schemes.
- **MAT133 Pre-Calculus** - deterministic, paper-derived computed generators.
  No lecture decks, no LLM calls and no API key.

There are two environments:

- **Local generator** - runs on this machine, can call the LLM for CSC662, and
  keeps lecture decks and past papers private.
- **Public site** - a library-only deployment that serves pre-generated
  public papers/schemes through Cloudflare. It runs no Python and makes no LLM
  calls.

## Current deployment

| Item | Value |
|---|---|
| Public site | **https://uitmpapergen.download** |
| `www` | `https://www.uitmpapergen.download` -> 301 -> apex |
| Fallback | https://papergen.jerkfish123.workers.dev |
| Worker | `cloudflare/worker/` |
| D1 database | `papergen` (`9d99c331-d8ba-495e-9a8d-35e295bb882c`) |
| R2 bucket | `exampapers` |
| Public bundle | 181 files, 52,389,765 bytes / 49.96 MiB (CSC662 + MAT133) |
| R2 bucket contents | 189 objects, 53,822,593 bytes / 51.33 MiB (bundle + 8 shared files) |
| R2 quota used | 427 / 10,000 internal Class A, 0 Class B (October 2026) |
| Worker | Deployed with CSC662 and MAT133 routes (version `597dd1ca`) |
| Subjects | CSC662 and MAT133 available; CSC580/CSC645 coming soon |
| Contact | auzair1990@gmail.com |
| Repository | https://github.com/jerkfish/paper-generator |

## Run the local web UI

```bash
uv sync
uv run python -m src.app.main
# open http://127.0.0.1:8000
```

Or:

```bash
uv run uvicorn src.app.main:app --host 127.0.0.1 --port 8000
```

## Local routes

| Route | Purpose |
|---|---|
| `/` | Subject table: CSC662 and MAT133 available; CSC580/CSC645 coming soon |
| `/csc662` | CSC662 hub: generate, Library, gallery |
| `/csc662/library` | Filterable table of the 20 prebuilt CSC662 papers |
| `/csc662/generate` | Generate a CSC662 paper as a background job (LLM) |
| `/mat133` | MAT133 hub: deterministic generate and Library |
| `/mat133/library` | Filterable table of the 20 prebuilt MAT133 papers |
| `/mat133/generate` | Generate a MAT133 paper from a seed (no key, no cost) |
| `/gallery` | Gallery page; the API is supplied by the deployed Worker |
| `/paused` | Daily-cap fallback notice |

The Library is subject-aware. CSC662 keeps the **Computed marks** column
(practice-mode `N`), numeric **Placeholders** and its placeholder filter.
MAT133 has no practice mode and no placeholders, so the same position becomes
**Total marks** (64-72), the placeholder column shows **—**, and the marks
filter operates on total marks. Click any column title to sort
ascending/descending; the next click reverses the direction. Filtering and
sorting are a small vanilla-JS enhancement, so the static public bundle
behaves the same way.

The job page shows one row per question and per-part slot status, updated from
real job events. There is no fake timer, animation or typewriter. MAT133 jobs
are deterministic and finish without an API key.

## Public routes

The public deployment is **library-only**. The Generate page is a static
notice; no API key or Python process exists there.

| Route | Purpose |
|---|---|
| `/` | Subject table |
| `/csc662` | CSC662 hub |
| `/csc662/library` | Sortable/filterable CSC662 Library with Share buttons |
| `/csc662/generate` | Static "live generation disabled" page |
| `/mat133` | MAT133 hub |
| `/mat133/library` | Sortable/filterable MAT133 Library with Share buttons |
| `/mat133/generate` | Static "live generation disabled" page |
| `/gallery` | D1-backed shared-paper gallery |
| `/paused` | Paused notice |
| `/library/<SUBJECT>/...` | R2 papers and schemes |

The Worker maps both `/csc662...` and `/mat133...`. A share request carries the
subject code, and the Worker reads that subject's
`library/<SUBJECT>/manifest.json`.

## Subject registry

The app discovers subjects by scanning `subjects/*/subject.json`:

```text
subjects/CSC662/subject.json   status: available
subjects/MAT133/subject.json   status: available (57 deterministic generators)
subjects/CSC580/subject.json   status: coming_soon
subjects/CSC645/subject.json   status: coming_soon
```

Each record contains the code, title, status, header text, template path,
fingerprint metadata, deck map, topic-deck allow-list and enabled computed
generators. `status: coming_soon` subjects appear on the home page but have no
papers or Library cache.

Computed generators are subject plugins: the CSC662 types (Vigenere, ACM,
columnar, rail fence, OTP, Caesar) live in `src/generators/`. MAT133 has its
own deterministic plugins in `src/mat133/generators/`. Another subject needs
its own planner, deck map and generator plugin before it can become
`available`. Routes, cache keys and Library folders are subject-scoped.

## MAT133 Pre-Calculus

MAT133 is paper-derived: there are no lecture decks. The 41 past papers were
ingested into a taxonomy and question log, and 57 computed generators cover
every subtopic. See `docs/MAT133_TAXONOMY.md` and `docs/MAT133.md`.

The MAT133 planner (`src/mat133/planner.py`) builds five questions from the
same structure observed in the past papers:

1. inequalities and absolute value;
2. functions and coordinate geometry;
3. complex numbers and algebra;
4. systems and coordinate geometry;
5. trigonometry and geometry.

Each seed deterministically selects the generators and parameters. A paper
has 15 parts, 64-72 marks and a full `NO | SOLUTION | MARK` marking scheme.
Across seeds 1-20, all 57 generators are exercised. MAT133 Library metadata
exports `total_marks`, `has_practice_mode: false` and
`has_placeholders: false`; the public manifests carry the same fields.

```bash
# rebuild the paper text/OCR cache and the question log (cached LLM calls free)
uv run python -m scripts.build_mat133_corpus
uv run python -m scripts.build_mat133_question_log --workers 4

# build the 20-seed deterministic MAT133 Library (Word COM for PDF)
uv run python -m src.app.prebuild_library --seeds 1-20 --subject MAT133

# generate, build and validate all three generator groups
uv run python -m scripts.validate_mat133_generators --group 1
uv run python -m scripts.validate_mat133_generators --group 2
uv run python -m scripts.validate_mat133_generators --group 3
```

The MAT133 builder (`src/mat133/build_docx.py`) never clones CSC662 sample
blocks: it starts from the MAT133 cover and appends a clean question paper and
a marking scheme in the original `NO | SOLUTION | MARK` table layout. Scheme
working is line-by-line mathematics with red `M1`/`A1`/`B1` codes; explanatory
prose and numbered steps are not rendered. The marker cover uses
`INSTRUCTIONS TO MARKERS` with only the two scheme notes.

Public MAT133 schemes have no lecture quotes, so they do not need the CSC662
quote-omission marker. The bundle validator applies that marker only to
CSC662.

## Download names

Downloads carry both an ASCII `filename` and an RFC 5987 `filename*` header:

```text
CSC662 Seed 07 2026.pdf
MAT133 Seed 07 2026.pdf
MAT133 Seed 07 2026 - Marking Scheme.docx
CSC662 Seed 07 2026 (practice 14).pdf
```

`YEAR` is the UTC year of generation (the cached Library uses the year stored
when it was prebuilt). Practice mode adds ` (practice N)` where `N` is the
requested computed marks. Seeds are zero-padded to two digits: seed 7 is
`Seed 07`, seed 12345 remains `Seed 12345`.

## Local generation

Only CSC662 live generation needs an API key. Put it in `.env` (gitignored):

```text
DEEPSEEK_API_KEY=...
```

The default model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017). With no key,
the CSC662 Library still works; the Generate page explains that live
generation is unavailable. MAT133 never needs a key.

The CSC662 pipeline is:

1. Planner builds 24 slots (A1-A10, B1, B2).
2. Theory module retrieves lecture chunks with BM25, drafts questions and
   marking points, then verifies source overlap, entailment, near-copy against
   past papers, topic/deck allow-lists and style confidence.
3. Paper builder creates the original local-build cover and computed questions.
4. Scheme builder adds working, citations and quote-free public marking points.
5. Word COM exports PDF; scheme table geometry and margins are QA checked in
   Word and LibreOffice.
6. Result is cached under `outputs/web_cache/CSC662/<config-hash>/`.

The MAT133 pipeline is:

1. Planner selects five deterministic question groups from the 57 generators.
2. Generators produce question text, exact answers, LaTeX working and diagrams.
3. The MAT133 builder writes paper and scheme DOCX/PDF.
4. Result is cached under `outputs/web_cache/MAT133/<config-hash>/`.

## Library

The Library is prebuilt per subject in `outputs/web_cache/<SUBJECT>/`. CSC662
is built from the stored 20-seed planner/theory JSON (no LLM calls); MAT133 is
built directly from deterministic generators.

```bash
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC662
# schemes only, reusing the cached paper DOCX:
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC662 --schemes-only

uv run python -m src.app.prebuild_library --seeds 1-20 --subject MAT133
```

Caches created before Phase 1 lived in flat `outputs/web_cache/<hash>/`
folders. They remain readable; to copy them into the subject folder and add
the subject/year/topic fields:

```bash
uv run python -m scripts.migrate_cache_subjects
# --move removes the old flat folders after a successful copy
```

## Cost cap and cache

- CSC662 per-run cap: `MOCKGEN_COST_CAP_USD` (default **$0.05**). The
  generator checks running token cost after every LLM call and aborts with
  `cost_capped`.
- MAT133 cost: **$0**. It makes no LLM calls.
- Cache key: subject + mode + seed + computed marks + model + thresholds +
  `PUBLIC_BUILD`. A cache hit returns instantly with **$0** run cost.

## PDF export and scheme QA

PDF export uses Microsoft Word COM. If Word is unavailable, a CSC662 job
completes with DOCX links and says PDF export is unavailable. MAT133 prebuild
treats a missing PDF as a build error because the public bundle needs both
formats.

Scheme tables are checked after export: the grid must fit the body usable
width, and rendered pages are scanned for ink beyond the right margin in both
Word and LibreOffice headless. A failure raises `SchemeQAError` and fails the
CSC662 build. MAT133 prebuild also rejects right-margin overflow, missing
cover, missing part labels or missing marks.

## Safety and public build

- Secrets are read only from the environment / Wrangler secrets. `.env` is
  gitignored; `.env.example` contains names and non-secret public values.
- The FastAPI app runs a startup secret scan. It fails if an environment
  secret value appears in a tracked text file.
- Run the check manually:

  ```bash
  uv run python -m src.app.safety --check
  ```

- `PUBLIC_BUILD=1` keeps the original local-build cover, omits verbatim slide
  quotes from CSC662 public schemes, disables the private Library in the live
  FastAPI app and refuses to serve files under `data/reference/`, `CSC662/`,
  `MAT133/` or `data/papers/`.
- Set `MOCKGEN_PUBLIC_STRIP_BRANDING=1` only if you intentionally want the old
  generic-branding cover. The default is **0** (original cover retained).
- Public document URLs include `?v=<mtime>`, so a rebuilt PDF is not hidden by
  a browser cache.
- The public-bundle allowlist is generated with:

  ```bash
  uv run python -m scripts.public_bundle --write
  # cloudflare/public_bundle_manifest.txt / .json
  ```

## Build the public bundle

```bash
# all available subjects (CSC662 + MAT133)
uv run python -m scripts.build_public_bundle --out outputs/public_bundle

# one subject only
uv run python -m scripts.build_public_bundle --subject MAT133

# resume after an interruption; existing complete seed files are skipped
uv run python -m scripts.build_public_bundle --out outputs/public_bundle

# pages/manifests only (fast; no Word/LibreOffice)
uv run python -m scripts.build_public_bundle --out outputs/public_bundle --pages-only
```

The builder keeps each paper's original local-build cover, rebuilds CSC662
schemes with verbatim slide quotes omitted, copies the already-public-safe
MAT133 deterministic files, renders the public pages and writes:

```text
index.html
csc662/index.html
csc662/library/index.html
csc662/generate/index.html
mat133/index.html
mat133/library/index.html
mat133/generate/index.html
gallery/index.html
paused/index.html
assets/style.css, htmx.min.js, library.js, gallery.js
subjects/<CODE>/subject.json
library/manifest.json
library/CSC662/manifest.json
library/MAT133/manifest.json
library/<SUBJECT>/papers/*.docx, *.pdf
library/<SUBJECT>/schemes/*.docx, *.pdf
static/gallery-shell.html
```

The builder fails on a forbidden path, a missing manifest file, or a CSC662
scheme without the quote-omission marker.

## Publish to R2

```bash
# dry run: no credentials, no network calls
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# upload (requires R2_ACCESS_KEY_ID / R2_SECRET_ACCESS_KEY)
uv run --with boto3 python -m scripts.r2_sync \
  --bundle outputs/public_bundle --upload

# verify the bucket
uv run --with boto3 python -m scripts.r2_sync --check
```

- One bucket listing per sync; only changed files are uploaded.
- A local backup is made before each upload.
- Hard budgets: 1 GiB, 5,000 objects, 10,000 Class A/month and 100,000
  Class B/month. The tool aborts before crossing a cap.
- Runtime state: `outputs/r2_sync_state.json`; quota ledger:
  `outputs/r2_quota_ledger.json`.
- R2 configuration: `R2_ACCOUNT_ID`, `R2_BUCKET` (default `exampapers`),
  optional `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`.
- Free-tier compliance and backup plan: `cloudflare/R2_QUOTA_PLAN.md`.
- Minimal credential scopes: `cloudflare/TOKEN_SCOPES.md`.

## Cloudflare Worker and gallery

The library-only Worker lives in `cloudflare/worker/`. It serves the static
bundle from R2, exposes a D1-backed gallery and copies PUBLIC_BUILD files into
`shared/<id>/` when someone shares a Library paper. There is no Python runtime
and no LLM call. The Worker supports CSC662 and MAT133 routes and subjects.

Current Worker state:

- Custom domains: `uitmpapergen.download` and `www.uitmpapergen.download`
- D1 schema applied (`migrations/0001_gallery.sql`)
- Gallery capped at 100 active entries, 7-day expiry
- Daily Cron at 03:00 UTC deletes expired rows and R2 objects
- R2 lifecycle rule for `shared/` is **not installed** yet; see below

Deploy or redeploy:

```bash
cd cloudflare/worker
bun test
bun run deploy
```

Initial setup (already done for this account):

```bash
bun x wrangler d1 create papergen
# put the returned database_id into wrangler.toml
bun run db:migrate
```

Deployment needs a Cloudflare API token with Workers Scripts Write, D1 Write
and Workers R2 Storage Read (or `wrangler login`). Add Workers R2 Storage Write
for lifecycle management and Zone Workers Routes Write + Zone Read only for a
custom domain. `Workers Routes:Edit` is not a valid permission name.

### R2 lifecycle status

Show the current rules:

```bash
uv run python -m scripts.r2_lifecycle --show
```

Only the default multipart-abort rule is present. Applying the `shared/`
7-day rule currently fails because the token lacks Workers R2 Storage Write:

```bash
uv run python -m scripts.r2_lifecycle --apply
# Cloudflare API permission denied
```

Add that permission, or set the rule in the dashboard:
R2 -> `exampapers` -> Settings -> Object lifecycle rules -> prefix `shared/`,
delete after 7 days. The daily Cron already removes expired objects, so the
lifecycle rule is the storage backstop.

## Data required at runtime

- `data/tracking/mock_paper_planner.xlsx` - CSC662 question/fingerprint source.
- `data/tracking/theory/deck_chunks.json` - cached CSC662 lecture chunks.
- `data/phrases.json` - offline phrase bank for computed questions.
- `data/reference/CSC662/CSC662 FEBRUARY 2026-raw docx.docx` - CSC662
  paper/scheme template.
- `data/reference/MAT133/MAT133 TEMPLATE.docx` - MAT133 cover/template.
- `outputs/computed_questions.json`, `outputs/acm_questions.json`.
- `outputs/web_cache/CSC662/` - prebuilt CSC662 Library.
- `outputs/web_cache/MAT133/` - prebuilt MAT133 Library (20 deterministic seeds).
- `outputs/eval_final_deepseek/seed_*_planner.json` and
  `seed_*_theory.json` - source data for rebuilding the CSC662 Library.
- `data/tracking/mat133/taxonomy.json`,
  `question_log.json` and `question_log.schema.json` - MAT133 paper-derived
  taxonomy and question log.
- `data/tracking/mat133/paper_text/` and `question_log/raw/` - cached OCR/text
  and per-paper extraction (reruns cost $0).

Per-subject input folders:

```text
data/papers/<SUBJECT>/         past-paper working copies
data/reference/<SUBJECT>/      templates, crest and cover assets
data/lecturedecks/<SUBJECT>/   lecture decks, if the subject uses them
```

The 38 CSC662 papers were moved to `data/papers/CSC662/`. The CSC662 template
is at `data/reference/CSC662/`. MAT133 papers are in `data/papers/MAT133/`;
its template and answer scheme are in `data/reference/MAT133/`; it has no
lecture decks. CSC580 and CSC645 have empty reference folders ready for future
subjects; their paper folders can be created when papers are added. The CSC662
lecture folder exists at `data/lecturedecks/CSC662/`; when it is empty the
loader uses the external `CSC662_DECKS_DIR`/Desktop fallback, so no 52 MB of
slides need to be copied into the repository.

## Lifecycle

See `docs/LIFECYCLE.md` for the complete flow: local generation, public bundle,
R2 upload, Worker serving, gallery share/expiry and adding a new subject.
MAT133 setup, scheme parse, cover template, taxonomy, question log, builder,
planner, 20-seed Library and generator validation are in `docs/MAT133.md`; the
taxonomy/report is in `docs/MAT133_TAXONOMY.md`.

## Design review

The multi-subject / Cloudflare page design and the public-bundle allowlist are
in `design/DESIGN.md` and `design/PUBLIC_BUNDLE_PROPOSAL.md`. Static page
mockups are in `design/mockups/`.

## Tests

```bash
uv run pytest -q        # 243 Python tests
cd cloudflare/worker
bun test                # 5 Worker tests
```

Coverage includes the planner/verifier, job lifecycle, cancel, cost-cap abort,
cache hit, Library without a key, scheme table geometry, subject discovery,
download names, subject-scoped routes, sortable/filterable Library,
subject-aware marks/placeholder columns, public bundle rendering/validation,
secret scan, public-path guards, bundle allowlist,
R2 quota guard, MAT133 taxonomy/question-log integrity, all 57 MAT133
generators, the MAT133 deterministic planner, the 20-seed generator coverage
and the MAT133 DOCX/XML builder.
