# CSC662 mock exam paper generator

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

Or with uvicorn:

```bash
uv run uvicorn src.app.main:app --host 127.0.0.1 --port 8000
```

The page has two tabs:

- **Generate** - realistic or practice mode, optional seed, computed marks N
  (practice only). Generation runs as a background job; the page polls and
  shows progress by question (A1 ... B2), cost so far, and placeholders. A
  Cancel button stops the job at the next safe point.
- **Library** - prebuilt realistic papers from the 20-seed accepted sets. These
  are served from cache instantly and make no LLM call.

## API key

Only live generation needs a key. Put it in `.env` (gitignored):

```text
DEEPSEEK_API_KEY=...
```

The code reads `DEEPSEEK_API_KEY` from the environment; it is never printed or
written into a report. The default model is `deepseek-flash`
(DeepSeek-V4.1-Flash-1017); override with `MOCKGEN_MODEL` if needed.

With no key, the Generate tab explains that live generation is unavailable and
the Library still works.

## Library demo (no key, no cost)

Build the cache from the final 20-seed accepted sets:

```bash
uv run python -m src.app.prebuild_library --seeds 1-20
```

This writes `outputs/web_cache/<hash>/` with `paper.docx`, `paper.pdf`,
`scheme.docx`, `scheme.pdf` and `meta.json`. The Library links to those files.
Re-running the command is a no-op unless `--force` is passed.

## Cost cap and cache

- Per-run cap: `MOCKGEN_COST_CAP_USD` (default **$0.05**). The generator checks
  the running token cost after every LLM call and aborts with status
  `cost_capped`.
- Cache key: mode + seed + computed marks (practice) + model + thresholds +
  PUBLIC_BUILD. A cache hit returns instantly with **$0** run cost.
- Job progress includes cost so far and the final summary includes the
  estimated cost based on the model's configured price table.

## PDF export and scheme QA

PDF export uses Microsoft Word COM on this machine. If Word is unavailable,
the job still completes and serves the DOCX files; the page says PDF export is
unavailable. It never fails the job for a missing PDF backend.

Marking-scheme tables are checked after export: every table grid must fit the
body usable width exactly, and rendered pages are scanned for ink beyond the
right margin in both Word and LibreOffice (headless). The build fails with a
`SchemeQAError` if either check fails. LibreOffice is required for the full
scheme QA; install it separately if `soffice` is not on PATH.

## Public build

```text
PUBLIC_BUILD=1
```

When true:

- the university name, crest and reference code are replaced with generic
  branding in generated DOCX/PDF files;
- the Library is disabled (it is built from real course material);
- live generation still works with an API key.

## Tests

```bash
uv run pytest -q
```

Covers the planner/verifier, app job lifecycle, cost-cap abort, cache hit, and
Library access without an API key.

## Pipeline notes

- Theory stems are checked against the clean-modern 90th percentile by mark
  value (2/5/6 marks); see `outputs/stem_length_report.md`.
- Marking points use stemmed overlap as the first gate, then an LLM
  yes/partly/no entailment check. Only `no` triggers regeneration.
- Near-copy, source-overlap and allowed-deck checks remain in place.
- Scheme tables show the entailment verdict beside each marking point.
