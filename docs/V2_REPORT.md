# Playbook v2 — Phase 2 report

Date: **2026-11-11**
Branch: **ICT450**
Commit: **169fc55** `feat: add shared v2 bank, assembler and gate enforcement`

Scope: shared bank/assembler code, subject contracts, lifecycle v2, gate
enforcement, scaffolds, tests and the CSC429 regression. No subject was
published, uploaded or deployed. No MinerU or LLM call was made.

## 1. What landed

### Shared bank — `src/bank/`

| Module | Responsibility |
|---|---|
| `schema.py` | Status/asset/provenance vocabularies, text normalisation, content hash, question/asset/answer validation |
| `store.py` | File-backed bank at `data/tracking/<code>/bank/`; questions, assets, plans, answers, approvals, corrections, unsure, rejected hashes |
| `validators.py` | Approved-only seed-plan validation: slot count, marks, no in-paper repeat, part and content-hash match, asset provenance, rejected hashes, reference integrity |
| `duplicates.py` | Exact normalised-text duplicate clusters and a canonical id |
| `quality.py` | 0–1 completeness score and high/medium/low band |
| `review.py` | HTML review sheet with original / extracted / recreation columns and decision export |
| `extraction.py` | MinerU wrapper that enforces `papers` and `cloud_processing` permissions, keeps the full ZIP and normalises the dossier |
| `gates.py` | Gate A / Gate B / Gate C checks for `strategy: recycle` subjects |
| `cli.py` | `python -m src.bank.cli status|review|plans <CODE>` |

The bank is file-based and subject-agnostic. No shared module contains a
subject list or a subject-specific branch.

### Assembler — `src/assemble/recycle.py`

- `requirements_from_sections()` turns a format profile into slot requirements.
- `feasibility()` reports distinct seeds, reuse-cap capacity, missing classes
  and `min(20, feasible)` Library size.
- `build_plans()` selects approved questions deterministically, enforces the
  reuse cap across seeds, avoids adjacent-seed reuse and never repeats a
  question inside one seed.
- Rendering helpers extracted from CSC429: `clean_question_text()`,
  `rewrite_references()`, `caption_text()`, `asset_mapping()`,
  `display_width()`, `split_subparts()`.

The DOCX layout itself stays subject-specific (CSC429 keeps its renderer under
`src/subjects/csc429/`); a new recycle subject supplies its format profile and
renderer at V3–V5.

### Subject contract — `src/subjects/registry.py`

`Subject` now exposes and validates these optional `subject.json` fields:

```json
{
  "strategy": "recycle",
  "variants": {"enabled": false},
  "library": {"size_policy": "min(20, feasible)"},
  "answers": {"sources": ["model_unofficial", "solver_verified"]},
  "extraction": {"method": "mineru", "model": "vlm"}
}
```

Defaults keep existing subjects unchanged: `strategy` is `recycle` for type D
and `generate` otherwise; `variants.enabled` is false; the Library policy is
`min(20, feasible)`.

### Lifecycle v2 — `src/subjects/lifecycle.py`

- V0–V8 stage skeleton, `schema_version: 2`, `playbook_version: "2.0"`.
- Gates A/B/C stored separately from stage status.
- A v2 state is detected by its `V0_intake` key, not by the schema number, so
  CSC429's legacy state keeps mapping to stages 0–10 read-only.
- `status_report()` now returns `lifecycle_schema`, `next_gate`, `gates`,
  `bank` and `answers`.

`scripts/lifecycle_status.py` prints the schema, next stage, the gate attached
to that stage, all three gate statuses and bank counts.

### Gate enforcement — `builders`

`src/app/prebuild_library.py` calls `require_seed_gate()` before building any
seed:

- Gate A is required before seed 1;
- Gate B is required for seed 4 and later;
- Gate A is refused if the bank has no approved questions;
- a `recycle` subject with no registered assembler cannot fall through to the
  LLM prebuild path.

The check applies only to `strategy: recycle` subjects. Finished subjects keep
their existing guards and behaviour.

### Scaffolds — `scripts/new_subject.py`

- `--type` now defaults to **D** (recycle).
- Type D writes a schema-v2 lifecycle at V0, `strategy: recycle`,
  `variants.enabled: false`, the Library policy, answer sources and MinerU
  extraction metadata.
- Type D scaffolds `data/tracking/<code>/bank/{questions,assets,plans,review,inbox}`
  with a bank README and empty `approvals.json`.
- Explicit A/B/C scaffolding keeps the v1 lifecycle for compatibility.

## 2. CSC429 regression

Baseline captured before the refactor in
`data/tracking/csc429/regression_baseline.json`. Seeds 1–3 were rebuilt after
the refactor with `python -m src.subjects.csc429.pure_assembly --seeds 1-3`.

| Check | Seed 1 | Seed 2 | Seed 3 |
|---|---|---|---|
| Paper DOCX paragraph text | identical | identical | identical |
| Scheme DOCX paragraph text | identical | identical | identical |
| QA (excluding `word_version`) | identical | identical | identical |
| QA problems | none | none | none |
| Asset SHA-256 map | identical | identical | identical |
| Plan hash (canonical JSON) | identical | identical | identical |
| Binary DOCX/PDF hash | differs | differs | differs |

The binary hash difference is expected: Word COM rewrites the DOCX package and
PDF metadata on every build. It is not a content change. The tracked outputs
were restored to their pre-refactor files, so the branch contains no artifact
churn.

## 3. Test and gate results

```text
uv run pytest -q                          -> 377 passed, 0 failed, 12 skipped
cd cloudflare/worker && bun test          -> 6 passed, 0 failed
uv run python -m src.app.safety --check   -> secret scan ok: 339 text files
uv run python -m scripts.lifecycle_status ICT450
  -> schema v2 / recycle, V0_intake in progress, Gates A/B/C pending
uv run python -m scripts.lifecycle_status CSC429
  -> legacy v1 stages complete, no blockers
```

New test file: `tests/test_v2_bank.py` (17 tests). It covers:

- Type D scaffold defaults, bank folders and v2 lifecycle;
- v1 state read-only mapping even when the file says `schema_version: 2`;
- approved-only selection, marks fit, part/content-hash checks, in-seed
  repeats, unresolved references, asset verdict/source-paper checks;
- feasibility, reuse cap and non-repeating plans;
- duplicate clustering and canonical choice;
- Gate A, Gate B and the approved-question precondition;
- bank status counts and the HTML review sheet.

## 4. Cost

| Item | Cost |
|---|---:|
| LLM calls | $0.00 |
| MinerU calls | $0.00 |
| Deterministic builds | $0.00 |
| **Phase 2 total** | **$0.00** |

## 5. Limitations recorded for later phases

1. The shared module selects and validates questions; it does not render a
   subject DOCX. V3 must record the format profile and V5 must supply the
   subject renderer.
2. `src/bank/extraction.py` has not been exercised against the live MinerU API
   in Phase 2. Phase 4 will run it on ICT450 after the V0 permission re-check.
3. Database subjects need exact SQL/code text and native tables only on an
   exact cell/count match. Those rules are enforced by the subject bank build
   in Phase 4, not by the generic schema.
4. Gate enforcement covers `strategy: recycle` v2 subjects. CSC429 keeps its
   existing `pure_gate` guard; no finished subject was migrated.
5. The public bundle, R2 and the Worker were not touched.

## 6. Next step — STOP 2

Phase 3 ends here. Phase 4 (ICT450 pilot) needs explicit approval of this
report. When approved it will:

1. re-check the ICT450 permissions at V0;
2. build a MinerU dossier per paper (full ZIP + fallback crops) at V1;
3. build the database-aware bank at V2, with SQL/code preservation, exact
   native-table matching, diagram crops, reference resolution, duplicate
   clusters and quality scores;
4. report papers, questions, assets, unresolved references, low-quality items,
   MinerU quota, cost and unsure items;
5. **stop at Gate A**. No answers, templates, seeds or publication in Phase 4.

ICT450 remains at **V0** with Gates A/B/C pending and `publication.allowed`
false.
