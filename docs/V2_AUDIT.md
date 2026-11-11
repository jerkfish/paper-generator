# Playbook v2 — Phase 0 audit

Date: **2026-11-11**
Scope: **read-only audit** of the current subject registry, question sources,
banks, answers, assets, Libraries, QA and lifecycle state.

No subject data, code, cache, public bundle, R2 object or Worker was changed for
this audit.

## Baseline

Recorded before any documentation work:

```text
uv run pytest -q   -> 352 passed, 0 failed, 12 skipped (100.63 s)
cd cloudflare/worker && bun test -> 6 passed, 0 failed
```

The baseline is the comparison point for the Phase 1 docs and the later Phase 2
code refactor.

## Executive summary

| Subject | Type | Question source | Bank / log | Answer source | Assets | Library | Verdict |
|---|---|---|---|---:|---|---:|---|
| CSC402 | B | Generated | 21 papers, 164 OCR entries | Deterministic generators | None | 20 | **Keep as is** |
| CSC413 | B | Generated | 15 papers, 249 OCR entries | Deterministic generators | None | 20 | **Keep as is** |
| CSC429 | D | Recycled | 215 questions, 633 sub-parts, 96 assets | 153 unofficial model answers | 96 source crops; 15 native tables | 20 | **Keep as is; extract shared recycle code** |
| CSC662 | A | Mixed | 38 papers, 891 question rows | Lecture-grounded theory + computed | Diagram flags, no asset bank | 20 | **Keep as is** |
| MAT133 | B | Generated | 41 papers, 978 entries | Exact computed solutions | Generated diagrams | 20 | **Keep as is** |
| ICT450 | C→D | Mixed / generated (v1, unapproved) | 12 papers, 60 entries | Deterministic generators | 40 MinerU assets | 0 | **Restart as Type D; archive v1 in Phase 2b** |
| 38 empty stubs | unset | None | None | None | None | 0 | **Convert to recycle (D) when started** |

Two findings need action:

1. **ICT450 restarts as Type D.** The owner has confirmed that v1 is not
   finished and was not approved. Archive the v1 state, docs, generators,
   question log, seeds, caches and QA; do not finish v1. The lifecycle scaffold
   and the later v1 artifacts are both archived so the archive is complete.
2. **CSC429's documentation is internally inconsistent.** The lifecycle state
   records Stage 9 and publish as complete; `docs/CSC429.md` still says
   “Stage 9 publish pending” in one section.

## 1. CSC402 — Programming I

- **Contract:** Type B, `available`, curriculum order 1.
- **Question production:** generated. 13 deterministic generator IDs; no
  recycled real-question bank.
- **Question log:** `data/tracking/csc402/question_log.json`; 21 unique papers,
  164 entries. Entries are raw OCR/text with part, marks, topic and source
  metadata. They do not contain answers or assets.
- **Answers:** generator-computed; the scheme is project output. No official
  scheme was parsed.
- **Assets:** none.
- **Library:** 20 seeds in `outputs/web_cache/CSC402/`; 100 marks, 22 slots.
- **QA:** 20/20 library prebuild validation; builder QA for paper/scheme page
  counts, marks and forbidden tokens.
- **Gates:** v1 stages 0–8 done and approved. Stage 9 is pending; publication is
  not allowed (`publication.allowed` is effectively unconfirmed).
- **Verdict:** **keep as is.** Do not change the generated behaviour. A recycle
  path is not requested for this finished subject.
- **v2 gap:** no answer-provenance objects and no bank. If the owner later wants
  recycle variants, a separate bank build is required.

## 2. CSC413 — Introduction to Interactive Multimedia

- **Contract:** Type B, `available`, order 2, published.
- **Question production:** generated. Four generators: true/false, matching,
  MCQ and structured.
- **Question log:** `data/tracking/csc413/question_log.json`; 15 unique papers,
  249 OCR/text entries. No answers or assets.
- **Answers:** deterministic generators; the supplied scheme was waived.
- **Assets:** none in the question log or Library.
- **Library:** 20 seeds; 64 questions / 72 slots / 100 marks.
- **QA:** 20/20 seeds validate; builder QA and public-bundle validation pass.
- **Gates:** v1 stages 0–10 are `done`; the lifecycle still carries a blocking
  `unsure` item from the MinerU pilot: the owner has not chosen a default model
  for any remaining MinerU processing. This does not affect the finished
  deterministic Library.
- **Verdict:** **keep as is.** Do not process more papers or change the
  generator behaviour. Resolve the MinerU `unsure` item separately if the owner
  wants further extraction.

## 3. CSC429 — Computer Organization and Architecture

- **Contract:** Type D, `available`, order 3, published.
- **Question production:** recycled. Real past-paper questions are the source of
  truth; generators are disabled (`generators_enabled: []`).
- **Bank:** `data/tracking/csc429/bank/`:
  - 20 unique source papers.
  - 215 questions, 633 sub-parts.
  - 172 `approved`, 26 `needs_fix`, 17 `rejected`.
  - 67 questions carry assets.
  - 96 source-crop assets: 12 diagram, 39 figure, 5 formula, 4 picture,
    36 table.
  - 15 native tables accepted after OCR comparison; 21 table crops retained.
- **Answers:** `bank/answers.json` has 153 cached **unofficial** model answers
  (`official: false`, model-labelled). No official CSC429 scheme was supplied.
- **Library:** 20 seeds, 11 slots / 100 marks. Feasibility records 5 fully
  distinct seeds and 20 seeds at reuse cap K = 4; 172 approved questions.
- **QA:** Gate 1 bank review; Gate 2 seeds 1–3; 20-seed assembly QA; native Word
  list numbering; assets and reference renumbering checks.
- **Gates:** lifecycle is schema v2 and records Gate 1 and Gate 2 as approved;
  Stage 9 and close-out are `done`. `docs/CSC429.md` still has a stale
  “Stage 9 publish pending” line and should be corrected in a later docs pass.
- **Verdict:** **keep as is.** This is the reference implementation for v2.
  Extract its generic bank/assembler/gate/answer/Library pieces into shared
  modules in Phase 2; leave CSC429-specific extraction rules under
  `src/subjects/csc429/`.
- **Reuse map:** see §7.

## 4. CSC662 — Computer Security

- **Contract:** Type A, `available`, order 38, published.
- **Question production:** mixed. LLM theory questions are grounded in lecture
  decks; computed cipher questions use seven deterministic generators.
- **Question source:** `data/tracking/mock_paper_planner.xlsx`:
  - 38 registered papers in the Papers sheet.
  - 891 question rows across 35 papers.
  - 87 rows flagged `Has diagram`.
- **Answers:** theory answers carry slide citations, marking points and
  entailment/source-overlap checks; computed answers are deterministic. No
  official scheme was parsed.
- **Assets:** diagram flags exist in the workbook, but there is no extracted
  asset bank or source-crop store. The current theory pipeline is text-first.
- **Library:** 20 accepted seeds in `outputs/web_cache/CSC662/`; extra ad-hoc
  cache entries exist but are not part of the 20-seed Library.
- **QA:** builder and scheme QA; near-copy and entailment checks; public-scheme
  quote marker.
- **Gates:** v1 stages 0–9 are done; Stage 10 is `in_progress` because
  historical LLM cost per stage is not reconstructed.
- **Verdict:** **keep as is.** Do not change the LLM theory or computed
  behaviour. v2 recycle is not the default for this existing type-A subject.

## 5. MAT133 — Pre-Calculus

- **Contract:** Type B, `available`, order 44, published.
- **Question production:** generated. 57 deterministic computed generators.
- **Question log:** `data/tracking/mat133/question_log.json`; 41 papers,
  978 entries. The log records patterns, givens, solution blueprints and marks;
  it is not a recycled real-question bank.
- **Answers:** exact computed solutions; the official 2024 answer scheme was
  parsed for format/marking conventions, not used as a source of recycled
  questions.
- **Assets:** generated diagrams/plots where a generator needs one; no
  past-paper asset bank.
- **Library:** 20 seeds; 5 questions / 15 parts / 64–72 marks.
- **QA:** 20-seed generator coverage, DOCX/XML builder checks, right-margin
  overflow checks, public-bundle validation.
- **Gates:** v1 stages 0–10 done; no blockers.
- **Verdict:** **keep as is.** Do not change the deterministic behaviour.

## 6. ICT450 — Database Design and Development

**Owner decision (2026-11-11): ICT450 is not finished and was not approved. It
restarts under v2 as Type D (recycle). Do not finish v1.** This audit only
inventories what exists so the v1 archive is complete.

- **Contract today:** `subjects/ICT450/subject.json` is a minimal scaffold;
  `type` is unset and the registry infers C. Status is `coming_soon`.
  Permissions are absent/unsure.
- **Lifecycle today:** `subjects/ICT450/lifecycle_state.json` is schema v1,
  created 2026-11-04, with every stage `pending` and five blocking `unsure`
  items. It says the next stage is `0_intake`. It does not record the later v1
  work.
- **V1 work artifacts on disk:** `docs/ICT450.md` and
  `data/tracking/ict450/` contain work that is not reflected in the state file:
  - 13 supplied PDFs, 12 unique papers; paper register and working copies.
  - 60 logged questions across 8 topics; taxonomy and question log built from
    the type-C planner/generators.
  - 7 deterministic output generators; seeds 1–20 validated.
  - MinerU VLM extraction for 12 papers; 10 figures, 29 tables, 1 equation.
  - Stage 7 sample builds under `data/tracking/ict450/build_sample*`, including
    DOCX/PDF/QA output.
  - No `outputs/web_cache/ICT450/` Library.
- **Answers:** deterministic generator answers; no official scheme.
- **Assets:** MinerU source crops and table HTML; the v1 builder rendered four
  native tables and two figures in its sample.
- **Library:** 0 seeds.
- **QA:** the v1 report claims Stage 1–7 sample QA with 0 problems; this is not
  represented in lifecycle state and is not approved.
- **Gates:** state says stage 0; docs claim Stage 7 revision 3 awaiting visual
  approval. This mismatch is an **archive inventory task**, not a decision
  point: the decision is restart.
- **Verdict:** **restart as Type D (recycle).** Archive all v1 work in Phase 2b;
  do not finish, extend or publish v1. Keep the paper register, read-only
  working copies, cover/template files and crest assets only as unverified
  reuse inputs after owner confirmation.

## 7. CSC429 code — reusable versus subject-specific

CSC429 already contains most of the v2 recycle pipeline, but it is bound to
CSC429 paths, an 11-slot/100-mark format and Gate 1/2 names.

| CSC429 module | Reusable capability | Proposed shared home |
|---|---|---|
| `pure_bank.py` | Bank schema, segmentation, asset linking, duplicate clusters, quality/review flags | `src/bank/` |
| `pure_pool.py` | Approved-only pool, topic/class counts, feasibility, reuse cap, deterministic seed plans | `src/assemble/recycle.py` |
| `pure_assembly.py` | Seed assembler, native numbering, figure/table insertion, Figure/Table reference renumbering, QA | `src/assemble/recycle.py` |
| `pure_gate.py`, `pure_guard.py` | Gate approval checks, approved-only selection, asset/question provenance, content-hash checks | `src/bank/validators.py`, `src/assemble/recycle.py` |
| `pure_review.py`, `pure_approvals.py`, `pure_compare.py` | Review sheet, approval/correction import, table OCR comparison | `src/bank/` |
| `pure_answers.py`, `answers.py`, `pure_usage.py` | Answer provenance/caching, solver/model separation, per-stage cost ledger | `src/bank/answers.py`, shared usage ledger |
| `pure_library.py` | Library manifest, seed metadata, cache publishing | shared Library helper |
| `pure_config.py` | Subject-scoped extraction/assembly defaults and environment names | `src/bank/config.py` |
| `capture.py`, `layout.py`, `assets.py`, `questions.py`, `tables.py`, `corrections.py`, `stage1.py` | Extraction/normalization pipeline | `src/subjects/parsers/` + `src/ingest/`; subject rules stay under the subject |
| `seed_pilot.py`, `build_docx.py`, `planner.py`, `taxonomy.py`, `generators.py` | Older CSC429-specific/archived patterns; native numbering and figure sizing are reusable patterns | Keep under CSC429; do not make them the shared assembler |

Hard-coded v2 blockers inside the reusable pieces:

- 11 slots and 100 marks in `pure_guard.py` and `pure_assembly.py`.
- 4 five-mark, 6 ten-mark and 1 twenty-mark slot rules in `pure_pool.py`.
- `CSC429` subject/path constants in every `pure_*` module.
- Gate names `GATE 1` / `GATE 2` instead of Gate A / Gate B / Gate C.
- `CSC429_COST_CAP_USD` in `pure_config.py` and `pure_usage.py`.
- CSC429-specific prompt and topic rules in `pure_answers.py`/`pure_bank.py`.

## 8. Hard-coded subject lists and v1 assumptions

### Registry-driven code that is clean

The application and Worker route/registry path does **not** contain a
subject allow-list. `src/app/`, `src/subjects/registry.py`,
`src/subjects/plugins.py`, `src/subjects/preprocess.py`,
`src/subjects/templates.py`, `src/subjects/forbidden.py`,
`scripts/new_subject.py`, `scripts/lifecycle_status.py` and
`cloudflare/worker/src/` read `subjects/*/subject.json` or generated
`subjects.json`.

### Legacy modules that still name a subject

| File | Finding |
|---|---|
| `src/config.py` | CSC662 aliases (`PAPERS_DIR`, `LECTURE_DECKS_DIR`, `CREST_PATH`) kept for v1 compatibility |
| `src/assemble/build_docx_paper.py`, `build_docx_paper_04.py`, `build_docx_scheme.py`, `build_docx_scheme_04.py` | CSC662 cover tokens, course values and scheme text |
| `src/assemble/generic_build.py` | CSC662 token replacements |
| `src/theory/decks.py`, `src/theory/generate.py` | CSC662 default deck fallback and CSC662 prompt text |
| `src/planner/planner.py` | CSC662-specific calibration/comment text |
| `src/fingerprint/types.py` | CSC662 topic × task labelling |
| `scripts/migrate_cache_subjects.py` | Defaults to CSC662 |
| `scripts/build_mat133_corpus.py`, `build_mat133_question_log.py`, `register_mat133_papers.py`, `validate_mat133_generators.py` | MAT133-specific scripts; acceptable for a finished subject but not a shared pattern |
| `cloudflare/worker/test/worker.test.js` | Test fixtures use CSC662/MAT133; not a production subject list |

Generated `cloudflare/public_bundle_manifest.json` and `.txt` contain subject
paths because they are generated artifacts; they are not source lists.

### v1-only assumptions to change in Phase 2

| Area | v1 assumption |
|---|---|
| `scripts/new_subject.py` | Accepts only A/B/C, defaults C, scaffolds plugin-only subjects, no bank folders, no `strategy`, `variants`, `library.size_policy` or `answers.sources` |
| `src/subjects/lifecycle.py` | `SCHEMA_VERSION = 1`; stages `0_intake`…`10_close_out`; no Gate A/B/C, bank counts, answer-provenance counts or `playbook_version` |
| `scripts/lifecycle_status.py` | Prints v1 stages and the next stage, not the next gate (A/B/C) or v2 stage names |
| `src/subjects/registry.py` | Types A–D are valid, but `strategy`, `variants`, `library.size_policy` and `answers.sources` are not modeled or published |
| `src/app/prebuild_library.py` | Defaults to seeds 1–20; no Gate A/B enforcement; no feasibility-sized Library |
| `scripts/build_public_bundle.py` | Defaults to seeds 1–20; no Gate C enforcement beyond publication permission |
| `src/subjects/csc429/pure_*` | CSC429 paths, 11 slots / 100 marks, reuse-cap constants, Gate 1/2 names |

## 9. Coming-soon stubs

These 39 entries are `coming_soon`. All have no papers, bank, answers, assets,
Library or QA. Type is unset; the registry currently infers C. Under v2 the
default for a new subject is **D recycle**.

| Code | Title | Order | Type | Highlight no past papers | Verdict |
|---|---|---:|---|---|---|
| CTU552 | Philosophy and Current Issues | 4 | unset | yes | Convert to recycle (D) when started |
| HBU111 | National Kesatria I | 5 | unset | yes | Convert to recycle (D) when started |
| ICT450 | Database Design and Development | 6 | unset (restart as D) | no | **Restart as Type D; archive v1 in Phase 2b; see §6** |
| MAT406 | Foundation Mathematics | 7 | unset | no | Convert to recycle (D) when started |
| CSC404 | Programming II | 8 | unset | no | Convert to recycle (D) when started |
| CTU554 | Values and Civilization II | 9 | unset | no | Convert to recycle (D) when started |
| HBU121 | National Kesatria II | 10 | unset | no | Convert to recycle (D) when started |
| ICT502 | Database Engineering | 11 | unset | no | Convert to recycle (D) when started |
| ITT400 | Introduction to Data Communication and Networking | 12 | unset | no | Convert to recycle (D) when started |
| MAT421 | Calculus I | 13 | unset | no | Convert to recycle (D) when started |
| STA416 | Applied Probability and Statistics | 14 | unset | no | Convert to recycle (D) when started |
| CSC435 | Object-Oriented Programming | 15 | unset | no | Convert to recycle (D) when started |
| CSC510 | Discrete Structures | 16 | unset | no | Convert to recycle (D) when started |
| CSC520 | Principles of Operating Systems | 17 | unset | no | Convert to recycle (D) when started |
| CSC583 | Artificial Intelligence Algorithms | 18 | unset | no | Convert to recycle (D) when started |
| HBU131 | National Kesatria III | 19 | unset | no | Convert to recycle (D) when started |
| LCC401 | English for Mediating Texts | 20 | unset | no | Convert to recycle (D) when started |
| MAT423 | Linear Algebra I | 21 | unset | no | Convert to recycle (D) when started |
| TMC401 | Introductory Mandarin (Level I) | 22 | unset | no | Convert to recycle (D) when started |
| CSC508 | Data Structures | 23 | unset | no | Convert to recycle (D) when started |
| CSC569 | Principles of Compilers | 24 | unset | no | Convert to recycle (D) when started |
| CSC575 | Software Project Management | 25 | unset | no | Convert to recycle (D) when started |
| CSC577 | Software Engineering - Theories and Principles | 26 | unset | no | Convert to recycle (D) when started |
| CSC584 | Enterprise Programming | 27 | unset | no | Convert to recycle (D) when started |
| LCC500 | English for Workplace Communication | 28 | unset | no | Convert to recycle (D) when started |
| TMC451 | Introductory Mandarin (Level II) | 29 | unset | no | Convert to recycle (D) when started |
| CSC580 | Parallel Processing | 30 | unset | no | Convert to recycle (D) when started |
| CSC645 | Algorithm Analysis and Design | 31 | unset | no | Convert to recycle (D) when started |
| CSC649 | Special Topics in Computer Science | 32 | unset | no | Convert to recycle (D) when started |
| CSP600 | Project Formulation | 33 | unset | no | Convert to recycle (D) when started |
| ENT600 | Technology Entrepreneurship | 34 | unset | no | Convert to recycle (D) when started |
| STA404 | Statistics for Business and Social Sciences | 35 | unset | no | Convert to recycle (D) when started |
| TMC501 | Introductory Mandarin (Level III) | 36 | unset | no | Convert to recycle (D) when started |
| CSC562 | Information Retrieval and Searching Algorithms | 37 | unset | no | Convert to recycle (D) when started |
| CSC683 | Game Design and Development | 39 | unset | no | Convert to recycle (D) when started |
| CSP650 | Project | 40 | unset | no | Convert to recycle (D) when started |
| EET699 | English Exit Test | 41 | unset | no | Convert to recycle (D) when started |
| ICT652 | Ethical, Social, and Professional Issues in ICT | 42 | unset | no | Convert to recycle (D) when started |
| CST688 | Computing Science Industrial Training | 43 | unset | no | Convert to recycle (D) when started |

## 10. Migration risks and open decisions

1. **ICT450 restart is decided (blocking for v1 work).** Type D recycle is the
   target. Phase 2b archives all v1 artifacts; Phase 4 pilots the new bank and
   stops at Gate A. Do not build answers, templates or seeds for v1.
2. **CSC429 docs inconsistency (non-blocking).** Correct the stale
   “Stage 9 pending” line in a later docs pass; do not reopen the lifecycle.
3. **CSC413 MinerU `unsure` (non-blocking for v2).** The deterministic Library
   is published; the owner still has not chosen a default MinerU model.
4. **CSC662 historical LLM cost (non-blocking).** Stage 10 remains in progress
   until historical cost is reconstructed.
5. **CSC402 publication permission (non-blocking).** Keep stage 9 pending; do
   not publish.
6. **Answer provenance backfill.** Existing subjects do not consistently record
   `official | solver_verified | model_unofficial | human_checked`. The v2 bank
   must require it for new questions.
7. **Assets.** Only CSC429 and ICT450 have source assets. CSC662's diagram
   flags and MAT133's generated diagrams are not a past-paper asset bank.
8. **Reuse cap.** Only CSC429 has a measured feasibility report. Converting
   CSC402/CSC413/CSC662/MAT133 to recycle would require a bank build and a new
   feasibility calculation; it is not a drop-in change.

## Phase 1 post-doc check

After the v2 playbook, AGENTS.md and README updates:

```text
uv run pytest -q   -> 352 passed, 0 failed, 12 skipped (74.46 s)
cd cloudflare/worker && bun test -> 6 passed, 0 failed
src.app.safety --check -> secret scan ok (325 text files)
```

The baseline is unchanged. No code, subject data, cache, public bundle, R2
object or Worker deployment was modified.

## 11. Amended execution plan — ICT450 restart

The owner amended the plan on 2026-11-11. ICT450 is **not finished and was not
approved**. It restarts under v2 as **Type D (recycle)**. The audit above only
inventories the v1 material so the archive is complete.

### Phase 2b — archive ICT450 v1 (after Phase 1 approval, before the pilot)

0. **Branch first.** Create `ICT450` from `main`. Keep the archive,
   reset, rejected registry and all later ICT450 work on that branch; merge
   into `main` only after ICT450 is complete (V8 + Gate C). Use
   `ICT450/exp-<topic>` or `ICT450/backup-<date>` for
   experiments/backups and merge those back into `ICT450`, never
   directly into `main`.
1. **Move, do not delete.** Move all ICT450 v1 work to:
   - `docs/archive/ict450_v1/`
   - `data/tracking/ict450_v1/`

   This includes the type-C planner and generators, taxonomy and question log
   built from them, all built seeds, caches, QA output, the v1
   `lifecycle_state.json` and `docs/ICT450.md`.
2. **Write a manifest** of every moved path and its SHA-256. The manifest is the
   evidence that the archive is complete.
3. **Write a rejected registry** containing the v1 seed ids and file hashes.
   New ICT450 outputs must never contain or read anything in the rejected
   registry. Add a regression test for this.
4. **Keep, but mark unverified.** Retain the paper register, read-only working
   copies, cover/template files and crest assets. Mark them:
   `unverified, reuse only after owner confirmation`. List each item with its
   source path.
5. **Reset the contract.** Set `subjects/ICT450/subject.json` to:
   - `type: "D"`
   - `strategy: "recycle"`
   - `variants.enabled: false`
   - `extraction.method: "mineru"`
   - `permissions.publication.allowed: false` until the owner grants it.
6. **Reset the lifecycle.** Create a schema-v2
   `subjects/ICT450/lifecycle_state.json` at **V0** with the v2 stage skeleton,
   gate records and bank/answer counts empty.

### Phase 4 — ICT450 pilot (after Phase 3 report approval; stop at Gate A)

**V0 — permissions.**

- Re-check `papers`, `scheme` and `slides` permissions before any upload.
- List what is allowed, what is not, and the basis.

**V1 — MinerU dossier.**

- Run MinerU cloud extraction for every ICT450 paper.
- Keep the full result ZIP for every paper.
- Keep fallback page-render crops.
- Record parser/model provenance, task ids, page counts and cache paths.

**V2 — question bank.**

Database-subject handling:

- **SQL and code in boxes:** keep as exact text blocks. Preserve indentation and
  line breaks. Never “fix” the SQL or code.
- **Relational tables and schemas:** use a native Word table only when the cell
  text and cell counts match the original; otherwise keep the crop.
- **ER diagrams, flowcharts and other diagrams:** crop from the original and
  record the caption and every figure/table reference.
- **Linking:** link each figure or table to its question by caption and
  position; report every unresolved reference.
- **Duplicates:** cluster the same question across years.
- **Quality:** score each question.
- **Review sheet:** keep the CSC429 workflow unchanged — original | extracted |
  recreation, with “use original” or “use recreation”.

**Pilot report.**

Report:

- papers processed;
- questions found;
- assets by type;
- unresolved references;
- low-quality questions;
- MinerU quota and cost;
- the `unsure` list with file paths and page numbers.

**Stop at Gate A.** Do not build answers, templates or seeds yet.
