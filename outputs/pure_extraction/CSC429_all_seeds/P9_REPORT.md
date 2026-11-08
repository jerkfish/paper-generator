# CSC429 — P9 close-out

Status: **complete** — local Library only; Stage 9 publish remains a separate hard stop.

## Summary

- Seeds: **20**
- Approved questions: **172**
- Needs fix (excluded): **26**
- Rejected (excluded): **17**
- Assets: **96**
- Format: **QUESTION 1..11 + native Word lists**
- QA failures: **0**
- Cost: **$0.139464** of $5.00
- Tests: **341 passed, 12 skipped (legacy Type C retired)**

## Playbook changes made

- Added Type D (asset-first assembly) as an additive subject type; A/B/C unchanged.
- Added Type D stages P0-P9 mapping to the existing stage numbers.
- Added `bank/questions`, `bank/assets`, `bank/corrections`, `bank/approvals` contracts.
- Added approved-only, asset-ownership, reference-integrity, rejected-registry and gate guards.
- Added native Word list numbering and sequential QUESTION 1..11 formatting.
- Added local HTML review sheets and decision import.
- Added Type D local Library manifest/metadata without publication.

## Open items

- 26 needs_fix questions and 17 rejected questions are outside the pool.
- 5 numeric answers are flagged for human checking.

## Local public bundle

Built locally at `outputs/public_bundle` with `--local-only`; validation problems: **0**. No R2 upload and no Worker deployment. Publication permission remains **false**.

## Publish

Stage 9 full publish/upload/deploy was not performed and requires explicit approval.
