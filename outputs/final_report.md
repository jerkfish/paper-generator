# Final project summary

## Evaluation

- Primary run: **DeepSeek V4.1 Flash** (`deepseek-flash`) on seeds 1-20.
- Theory slots: **464**; accepted **457**; placeholders **7 (1.5%)**.
- Max near-copy: **0.764** (threshold 0.80); source overlap **0**.
- Estimated cost: **$1.0315** total, **$0.0023** per accepted question
  (official peak cache-miss rates; estimate, not invoice).
- Marking points: 1,251/1,896 passed the stemmed-overlap gate; 645 were
  entailment-checked (yes 327 / partly 287 / no 31); all 31 `no` points were
  regenerated; 103 verbatim-copy points were rejected.
- Full report: `eval_realistic.md`.
- Pre-hardening multi-model appendix: `eval_multi_model_appendix.md`.

## Final paper

- `mock_paper_04.pdf` / `.docx` - 6 pages, 23 sourced theory answers plus one
  6-mark Vigenere question, **0 placeholders**.
- `mock_scheme_04.pdf` / `.docx` - 15 pages, with slide citations, verbatim
  quotes, stem-overlap scores and confidence labels.
- Built from the final hardened realistic run, seed 12.

## Step 8 comparison

- Full report: `step8_comparison.md`.
- One-page summary: `step8_summary.pdf` / `.md`.
- Layout metrics: `step8_layout_metrics.json`.
- Wording/diversity data: `step8_wording.json`.
- Side-by-side pages: `step8_side_by_side.png`,
  `step8_side_by_side_jun2019.png`, `step8_side_by_side_feb2022.png`.

Key Step 8 findings: structure matches all three modern papers (Parts, marks,
100 total, 3 hours, part-heading mark totals); page count 6 matches DEC 2019;
computed share is 6 % vs the clean-modern 4.0-mark average; the main wording
gap is 2-mark stems at 20 words median vs 9 in real papers; header ink is
heavier than the real papers; 36/94 marking points remain low stem-overlap but
were accepted by the entailment check.

## Final pack

- `review_pack_final/` - paper 04, scheme 04, evaluation report, Step 8
  comparison, side-by-side images and the blind human-evaluation workbook.
- `human_eval.xlsx` - rebuilt from the final 20-seed accepted set: 20 generated
  + 10 real questions, shuffled; hidden key sheet.

## Small fixes

- Mark-aware stem limits: 2/5/6-mark p90 = 18/54/43 words. The post-fix
  8-seed sample reduced medians from 19/31/31 to **12/26.5/21**; see
  `stem_length_report.md`.
- `eval_realistic.md` includes placeholder breakdowns by Part A/B, scenario
  and topic, plus the per-topic diversity and unused-slide tables.
- Scheme 04 shows `supported` / `partly supported` / `not supported` beside
  every theory marking point.

## Web UI

- Run: `uv run python -m src.app.main` and open `http://127.0.0.1:8000`.
- One-page FastAPI + HTMX UI: realistic/practice mode, optional seed,
  practice computed marks, background job progress, cost, placeholders,
  cancel, paper/scheme downloads, and a no-LLM Library.
- Prebuild the Library: `uv run python -m src.app.prebuild_library --seeds 1-20`.
- Cost cap: `MOCKGEN_COST_CAP_USD` (default $0.05).
- Public build: `PUBLIC_BUILD=1` strips branding and disables the Library.
- Screenshot and one-run log: `app_screenshot_job.png`,
  `web_run_log.md`.

## Verification

`uv run pytest -q`: **134 passed**.
