# CSC429 pure-extraction seeds 1-3

Built outside the lifecycle/stage pipeline after the owner rejected the staged 20-seed set.

## What is here

- `seed_01/`, `seed_02/`, `seed_03/` — paper + scheme DOCX/PDF, `plan.json`, `qa.json`.
- `run_manifest.json` — selections, page counts, answer cost and validation summary.

## Rules applied

- Every question is a real past-paper question.
- Pictures, diagrams and tables are taken from the supplied papers; diagrams are never recreated.
- Captions are native text; `(N marks)` is right-tabbed; the scheme does not print question bodies.
- No question is reused across the three seeds.

## Review notes

- 30 of 33 questions are not in the rejected Stage-8 set.
- The three B1 assembly questions are reused from the rejected set because only five 20-mark B1 questions pass the table-readiness gate; the other B1 candidates depend on fill-in tables that are not recreated from OCR.
- Answer generation: 31 new calls, $0.028619.
- No publication, R2 upload or Worker deployment.
