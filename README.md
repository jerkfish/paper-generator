# CSC662 mock paper generator

Local study tool for CSC662 Computer Security. It plans a realistic or practice
paper, drafts grounded theory questions from the lecture decks, verifies the
marking points, and exports a Word/PDF paper and marking scheme.

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

The page has two tabs:

- **Generate** - realistic or practice mode, optional seed, computed marks N
  (practice only). Generation runs as a background job with progress by
  question (A1 ... B2), cost so far, placeholders and a Cancel button.
- **Library** - 20 prebuilt realistic papers from the accepted sets. These
  are served from cache instantly and make no LLM call.

## API key

Only live generation needs a key. Put it in `.env` (gitignored):

```text
DEEPSEEK_API_KEY=...
```

The default model is `deepseek-flash` (DeepSeek-V4.1-Flash-1017). With no key,
the Library still works; the Generate tab explains that live generation is
unavailable.

## Library

The Library is prebuilt in `outputs/web_cache/`. To rebuild it from the stored
20-seed planner/theory JSON (no LLM calls):

```bash
uv run python -m src.app.prebuild_library --seeds 1-20
# schemes only, reusing the cached paper DOCX:
uv run python -m src.app.prebuild_library --seeds 1-20 --schemes-only
```

## Cost cap and cache

- Per-run cap: `MOCKGEN_COST_CAP_USD` (default **$0.05**). The generator
  checks the running token cost after every LLM call and aborts with status
  `cost_capped`.
- Cache key: mode + seed + computed marks + model + thresholds +
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

- `PUBLIC_BUILD=1` strips university branding, omits verbatim slide quotes from
  public schemes, disables the private Library and refuses to serve files under
  `data/reference/`, `CSC662/` or `data/papers/`.
- The proposed public-bundle allowlist is generated with:

  ```bash
  uv run python -m scripts.public_bundle --write
  # cloudflare/public_bundle_manifest.txt
  ```

## Public build

```text
PUBLIC_BUILD=1
```

This replaces the university name, crest and reference code with generic
branding and disables the Library (which is built from real course material).
Live generation still works with an API key.

## Data required at runtime

- `data/tracking/mock_paper_planner.xlsx` - question/fingerprint source.
- `data/tracking/theory/deck_chunks.json` - cached lecture chunks.
- `data/phrases.json` - offline phrase bank for computed questions.
- `data/reference/CSC662 FEBRUARY 2026-raw docx.docx` - paper/scheme template.
- `outputs/computed_questions.json`, `outputs/acm_questions.json`.
- `outputs/web_cache/` - prebuilt Library.
- `outputs/eval_final_deepseek/seed_*_planner.json` and
  `seed_*_theory.json` - source data for rebuilding the Library.
- Lecture decks at `CSC662_DECKS_DIR` (default `~/Desktop/CSC662`).

## Design review

The multi-subject / Cloudflare page design and the proposed public-bundle
allowlist are in `design/DESIGN.md` and `design/PUBLIC_BUNDLE_PROPOSAL.md`.
The static page mockups are in `design/mockups/` (open `index.html`).

## Tests

```bash
uv run pytest -q
```

Covers the planner/verifier, app job lifecycle, cancel, cost-cap abort, cache
hit, Library without a key, public branding, scheme table geometry, the
secret-leak scan, public-path guards, and the public bundle allowlist.
