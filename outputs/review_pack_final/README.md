# CSC662 mock paper - final review pack

Final paper and evidence package. Built from the hardened realistic run,
seed 12 (DeepSeek V4.1 Flash).

## Paper

- `mock_paper_04.pdf` / `.docx` - 6 pages, 100 marks, 23 sourced theory
  answers plus one 6-mark Vigenere question, **0 placeholders**.
- `mock_scheme_04.pdf` / `.docx` - 16 pages. Every theory marking point has a
  verbatim slide quote and `deck, slide` citation; points carry the
  `supported by lecture slides (not lecturer-marked)` label, stem-overlap
  scores and low-overlap flags.

## Evaluation

- `eval_realistic.md` - final 20-seed, one-model evaluation
  (DeepSeek V4.1 Flash): 457/464 accepted, 7 placeholders (1.5%),
  max near-copy 0.764, estimated cost $1.0315 total / $0.0023 per accepted.
- `eval_multi_model_appendix.md` - earlier multi-model run, clearly labelled
  **pre-hardening**; kept for comparison only.

## Step 8 comparison

- `step8_comparison.md` - full comparison of paper 04 against JUN 2019,
  DEC 2019 and FEB 2022.
- `step8_summary.pdf` / `.md` - one-page summary.
- `step8_layout_metrics.json` - raw 200 dpi layout measurements.
- `step8_wording.json` - generated/real word counts, command mix and
  nearest-past-question data.
- `step8_side_by_side.png`, `step8_side_by_side_jun2019.png`,
  `step8_side_by_side_feb2022.png` - question-page comparisons.

## Human evaluation

- `human_eval.xlsx` - 20 random generated questions and 10 random real past
  questions, shuffled with no labels. The hidden `key` sheet records
  generated/real, origin and model.

## Headline caveats

- The paper is a study aid; theory answers are slide-supported, not
  lecturer-marked.
- 2-mark stems are longer than real papers (20 vs 9 words median); see
  `step8_comparison.md` for the full weakness list.
- The running header is bolder/heavier than the real papers.
- No official CSC662 marking schemes exist; all suggested mark splits are
  inferred.
