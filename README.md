# Mock Paper Generator

Local study tool for CSC662 Computer Security. It plans a realistic or
practice paper, drafts grounded theory questions from the lecture decks,
verifies the marking points, and exports a Word/PDF paper and marking scheme.

Everything runs on this machine. There are no accounts, payments or uploads;
lecture slides and past papers never leave the machine.

## Run the web UI

```bash
uv sync
uv run python -m src.app.main
# open http://127.0.0.1:8000
```

Or:

```bash
uv run uvicorn src.app.main:app --host 127.0.0.1 --port 8000
```

## Pages

| Route | Purpose |
|---|---|
| `/` | Subject table: CSC662 available, CSC580/CSC645 coming soon |
| `/csc662` | Subject hub: generate, Library, gallery |
| `/csc662/library` | Filterable table of the 20 prebuilt papers |
| `/csc662/generate` | Generate a new paper as a background job |
| `/gallery` | Public shared papers (no entries enabled locally) |
| `/paused` | Daily-cap fallback notice |

The Library filters by text, computed marks, topic and placeholder count.
Click any column title to sort ascending/descending; the next click reverses
the direction. The filtering and sorting are a small vanilla-JS enhancement,
so the static public bundle works the same way. The job page shows one row per
question and per-part slot status, updated from real job events. There is no
fake timer, animation or typewriter; the plain table is the v2 design fallback.

## Subject registry

The app discovers subjects by scanning `subjects/*/subject.json`:

```text
subjects/CSC662/subject.json   status: available
subjects/CSC580/subject.json   status: coming_soon
subjects/CSC645/subject.json   status: coming_soon
```

Each record contains the code, title, status, header text, template path,
fingerprint metadata, deck map, topic-deck allow-list and enabled computed
generators. `status: coming_soon` subjects appear on the home page but have
no papers, cache folder or generators.

Computed generators are subject plugins: the CSC662 types (Vigenere, ACM,
columnar, rail fence, OTP, Caesar) live in `src/generators/`. Another subject
needs its own planner and generator plugin before its status can become
`available`. Routes, cache keys and Library folders are subject-scoped.

## Download names

Downloads carry both an ASCII `filename` and an RFC 5987 `filename*` header:

```text
CSC662 Seed 07 2026.pdf
CSC662 Seed 07 2026 - Marking Scheme.docx
CSC662 Seed 07 2026 (practice 14).pdf
```

`YEAR` is the UTC year of generation (the cached Library uses the year stored
when it was prebuilt). Practice mode adds ` (practice N)` where `N` is the
requested computed marks. Seeds are zero-padded to two digits, so seed 7 is
`Seed 07` and seed 12345 remains `Seed 12345`.

## API key

Only live generation needs a key. Put it in `.env` (gitignored):

```text
DEEPSEEK_API_KEY=...
```

The default model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017). With no key,
the Library still works; the Generate page explains that live generation is
unavailable.

## Library

The Library is prebuilt per subject in `outputs/web_cache/CSC662/`. To rebuild
it from the stored 20-seed planner/theory JSON (no LLM calls):

```bash
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC662
# schemes only, reusing the cached paper DOCX:
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC662 --schemes-only
```

Caches created before Phase 1 lived in flat `outputs/web_cache/<hash>/`
folders. They remain readable; to copy them into the subject folder and add
the subject/year/topic fields:

```bash
uv run python -m scripts.migrate_cache_subjects
# --move removes the old flat folders after a successful copy
```

## Cost cap and cache

- Per-run cap: `MOCKGEN_COST_CAP_USD` (default **$0.05**). The generator
  checks the running token cost after every LLM call and aborts with status
  `cost_capped`.
- Cache key: subject + mode + seed + computed marks + model + thresholds +
  `PUBLIC_BUILD`. A cache hit returns instantly with **$0** run cost.

## PDF export and scheme QA

PDF export uses Microsoft Word COM. If Word is unavailable, the job completes
with DOCX links and says PDF export is unavailable.

Scheme tables are checked after export: the grid must fit the body usable
width, and rendered pages are scanned for ink beyond the right margin in both
Word and LibreOffice headless. A failure raises `SchemeQAError` and fails the
build. LibreOffice is required for the full QA; install it separately if
`soffice` is not on PATH.

## Phase 0 safety

- Secrets are read only from the environment / Wrangler secrets. `.env` is
  gitignored; `.env.example` contains names only.
- The FastAPI app runs a startup secret scan. It fails if an environment
  secret value appears in a tracked text file (`.env`, `.git`, `.venv`,
  `outputs` and `data` are excluded).
- Run the same check manually:

  ```bash
  uv run python -m src.app.safety --check
  ```

- `PUBLIC_BUILD=1` keeps the original local-build cover, omits verbatim slide
  quotes from public schemes, disables the private Library and refuses to serve
  files under `data/reference/`, `CSC662/` or `data/papers/`.
  Set `MOCKGEN_PUBLIC_STRIP_BRANDING=1` only if you intentionally want the old
  generic-branding cover.
- The proposed public-bundle allowlist is generated with:

  ```bash
  uv run python -m scripts.public_bundle --write
  # cloudflare/public_bundle_manifest.txt
  ```

## Public build

```text
PUBLIC_BUILD=1
```

This keeps the original local-build cover (university name, crest and reference
code) and disables the Library in the live FastAPI app. Public schemes still
omit verbatim slide quotes. Live generation still works with an API key.
The static public bundle uses the same rule.

## Public bundle

Build the static/public bundle from the private Library cache:

```bash
uv run python -m scripts.build_public_bundle --out outputs/public_bundle
# resume after an interruption; existing complete seed files are skipped
uv run python -m scripts.build_public_bundle --out outputs/public_bundle
# pages/manifests only (fast; no Word/LibreOffice)
uv run python -m scripts.build_public_bundle --out outputs/public_bundle --pages-only
```

The builder keeps each paper's original local-build cover, rebuilds each
scheme with verbatim slide quotes omitted, renders the pages from the app
templates, and writes:

```text
index.html
csc662/index.html
csc662/library/index.html
csc662/generate/index.html
gallery/index.html
paused/index.html
assets/style.css, htmx.min.js, library.js
subjects/<CODE>/subject.json
library/manifest.json
library/CSC662/manifest.json
library/CSC662/papers/*.docx, *.pdf
library/CSC662/schemes/*.docx, *.pdf
```

The builder fails if it finds a scheme without the quote-omission marker or a
forbidden path. The public-bundle allowlist is in
`cloudflare/public_bundle_manifest.txt`.

## Cloudflare/R2 preparation

The public bundle uses per-subject folders
(`library/CSC662/papers/`, `library/CSC662/schemes/`) and public-safe subject
metadata. The built bundle is **96 files / 18.36 MB** and has been uploaded to R2. R2 access keys are read from `.env`.

Free-tier compliance and the backup plan are documented in
`cloudflare/R2_QUOTA_PLAN.md`; the minimal credential scopes are in
`cloudflare/TOKEN_SCOPES.md`. The sync tool budgets 1 GiB storage, 10,000
Class A operations/month and 100,000 Class B operations/month, and aborts
before crossing a cap:

```bash
# dry run: no credentials, no network calls
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# upload (requires R2_ACCESS_KEY_ID/R2_SECRET_ACCESS_KEY):
uv run --with boto3 python -m scripts.r2_sync \
  --bundle outputs/public_bundle --upload
```

R2 configuration is read from the environment: `R2_ACCOUNT_ID`, `R2_BUCKET`
(default `exampapers`), optional `R2_ENDPOINT`, `R2_ACCESS_KEY_ID`, and
`R2_SECRET_ACCESS_KEY`. The bucket name is not a secret; access keys are.

The built bundle has been uploaded to R2: **96 objects, 16,011,605 bytes**.

## Cloudflare Worker and gallery

The library-only Worker is deployed at
**https://uitmpapergen.download** (and `www` redirects to the apex).
It lives in `cloudflare/worker/`,
serves the static bundle from R2, exposes a D1-backed gallery, and copies
PUBLIC_BUILD library files into `shared/<id>/` on share. There is no Python
runtime and no LLM call.

```bash
cd cloudflare/worker
bun test
bun x wrangler d1 create papergen
# put the returned database_id into wrangler.toml
bun run db:migrate
bun x wrangler r2 bucket lifecycle add exampapers expire-shared-7d shared/ --expire-days 7
bun run deploy
```

The Worker config is `cloudflare/worker/wrangler.toml`; deployment requires a
Cloudflare API token with Workers Scripts Write, D1 Write and Workers R2
Storage Read (or `wrangler login`). Add Workers R2 Storage Write for lifecycle
management and Zone Workers Routes Write + Zone Read only for a custom domain. The gallery is capped at 100
active entries and entries expire after 7 days. See
`cloudflare/worker/README.md`.

## Data required at runtime

- `data/tracking/mock_paper_planner.xlsx` - question/fingerprint source.
- `data/tracking/theory/deck_chunks.json` - cached lecture chunks.
- `data/phrases.json` - offline phrase bank for computed questions.
- `data/reference/CSC662 FEBRUARY 2026-raw docx.docx` - paper/scheme template.
- `outputs/computed_questions.json`, `outputs/acm_questions.json`.
- `outputs/web_cache/CSC662/` - prebuilt Library (legacy flat folders still
  work).
- `outputs/eval_final_deepseek/seed_*_planner.json` and
  `seed_*_theory.json` - source data for rebuilding the Library.
- Lecture decks at `CSC662_DECKS_DIR` (default `~/Desktop/CSC662`).

## Lifecycle

See `docs/LIFECYCLE.md` for the local generation, public bundle, R2 upload,
Worker serving, gallery and new-subject onboarding flow.

## Design review

The multi-subject / Cloudflare page design and the proposed public-bundle
allowlist are in `design/DESIGN.md` and `design/PUBLIC_BUNDLE_PROPOSAL.md`.
The static page mockups are in `design/mockups/` (open `index.html`).

## Tests

```bash
uv run pytest -q
```

Covers the planner/verifier, app job lifecycle, cancel, cost-cap abort, cache
hit, Library without a key, public branding, scheme table geometry, subject
discovery, download names, subject-scoped routes, sortable Library headers,
public-bundle rendering/validation, the secret-leak scan, public-path guards,
the public bundle allowlist, and the R2 quota guard.
