# Subject onboarding playbook — v2

Version: **2.0**
Status: **authoritative onboarding procedure**
Supersedes: `docs/archive/SUBJECT_PLAYBOOK_v1.md` (v1 is archived verbatim)

This playbook is the operating procedure for adding or changing a subject. It
implements the **“recycle, don’t invent”** model: every question in a generated
paper is a real past-paper question from an approved question bank. Answers are
attached to those questions, and the paper is laid out in the current format.
Generators are optional variants, never the default.

Read this file, `subjects/<CODE>/subject.json` and
`subjects/<CODE>/lifecycle_state.json` before touching a subject.

The public deployment is library-only. Nothing here authorises an R2 upload, a
Worker deploy, a registry promotion or a change to supplied originals. Those
are Gate C decisions.

## Why v2

The v1 pipeline generated many questions from templates or LLM prompts. That
produced useful papers, but it also made it easy to drift from the real paper:
invented prose, missing past-paper figures, section shapes that did not match
the current exam, and answers with unclear provenance.

v2 separates the concerns:

1. **Question bank** — what real questions exist, with their original marks,
   text, tables and assets.
2. **Format profile** — how the current paper is structured, independent of the
   year a question came from.
3. **Assembler** — a deterministic, seeded selection of approved bank questions
   that fits the current format.

This gives a paper that is wholly traceable to past papers while still being a
new paper: different question mix, current layout, no repeats, checked marks and
renumbered figure/table references.

## Non-negotiable rules

1. **Originals are read-only.** Never edit, rename, move or delete supplied PDFs
   in `CSC662/`, `data/papers/<CODE>/`, `data/reference/<CODE>/` or
   `data/lecturedecks/<CODE>/`. Extraction works from copies under
   `data/papers/<CODE>/`.
2. **Recycle, don’t invent.** Every selected question must come from an approved
   bank record with a source paper, page and content hash. A generator may only
   produce an optional variant when `variants.enabled` is true and the answer
   can be independently verified.
3. **Three human gates only:** **Gate A** (bank approved), **Gate B** (first
   seeds approved), **Gate C** (publish). Do not invent extra per-stage gates.
4. **Never publish without Gate C.** Building a local bundle is not publishing.
   R2 upload and Worker deploy are Gate C only.
5. **Record uncertainty as `unsure`.** A noisy cover, an unreadable table, a
   missing asset, an uncertain mark or an unresolved reference is recorded in
   `lifecycle_state.json`; it is never silently guessed.
6. **Answers carry provenance.** Every answer is labelled `official`,
   `solver_verified`, `model_unofficial` or `human_checked`. The scheme shows the
   provenance.
7. **No secrets in the repository.** Keys come from the environment only. Never
   print, log or commit key values.
8. **Registry-driven only.** Application code reads `subjects/*/subject.json` or
   the generated `subjects.json`. A new hard-coded subject list is a bug.
9. **Evidence or it did not happen.** A stage is complete only when its
   evidence exists and any blocking `unsure` item is closed or explicitly
   accepted.
10. **Git commits are allowed only when the user asks.** Commit as
    `konata1998 <jerkfish123@gmail.com>`; do not push or pull. Commit messages
    must describe the change only and must not add `Co-Authored-By`,
    `Generated with`, or any agent/tool attribution.
11. **Do not change finished subjects for a new onboarding task.** CSC402,
    CSC413, CSC429, CSC662 and MAT133 keep their current generation/Library
    behaviour unless the owner explicitly requests a migration.
12. **New subject, new branch.** Before V0, create `<CODE>` from
    `main`. All subject work happens on that branch. Merge into `main` only
    after the subject is marked complete (V8 close-out and Gate C). Use
    `<CODE>/exp-<topic>` or `<CODE>/backup-<date>` for
    experiments and backups; sub-branches never merge directly into `main`.

## The three layers

### 1. Question bank — era-independent

One record per real question. The bank is the source of truth.

Minimum record:

```json
{
  "id": "CSC429-2019-06-A2",
  "source_paper": "CSC429-2019-06",
  "source_file": "CSC429 (7).pdf",
  "pages": [2, 3],
  "part": "A",
  "question_no": 2,
  "slot_hint": "A2",
  "marks": 10,
  "subpart_marks": [
    {"label": "a", "marks": 4},
    {"label": "b", "marks": 6}
  ],
  "native_text": "...",
  "native_tables": [],
  "assets": ["A-...-D1"],
  "refs": ["Figure 1", "Table 1"],
  "topic_tags": ["Von Neumann architecture"],
  "duplicate_cluster": "cluster-...",
  "status": "approved",
  "quality_score": 0.92,
  "content_hash": "sha256:...",
  "answers": ["ANS-..."]
}
```

Statuses:

| Status | Meaning |
|---|---|
| `extracted` | Machine-extracted, not reviewed |
| `needs_fix` | Known issue: OCR, missing mark, bad asset, unresolved reference |
| `approved` | Human-reviewed and approved for assembly |
| `rejected` | Never selectable; retained for audit |

The bank also stores corrections and approvals keyed by question id and content
hash. Re-extraction must not overwrite them.

### 2. Format profile — per era, current by default

The format profile describes how a paper is laid out, independent of the year a
question came from.

```json
{
  "era": "current",
  "source_papers": ["newest representative papers"],
  "sections": [
    {"key": "A", "questions": 10, "marks_per_slot": [5, 10]},
    {"key": "B", "questions": 1, "marks_per_slot": [20]}
  ],
  "total_marks": 100,
  "duration": "3 HOURS",
  "numbering": "QUESTION 1..n; a) b) c); i. ii.",
  "cover_template": "data/reference/<CODE>/...",
  "scheme_template": "data/reference/standard/UTM_STANDARD_MARKING_SCHEME.docx"
}
```

“Current” means the newest papers that define the format the subject uses now.
Older eras remain available for comparison but are not the default.

### 3. Assembler — seeded and deterministic

The assembler fills the current format profile from **approved** bank questions.

Hard rules:

- Marks must match the slot. A tolerance is allowed only with the owner’s
  written approval recorded in the format profile.
- A question is not tied to the section it originally appeared in. It may fill
  any compatible slot if marks and topic coverage fit.
- No question repeats inside one paper, by bank id, content hash or duplicate
  cluster.
- A configurable reuse cap applies across papers in one Library.
- Topic coverage follows the format profile’s quotas or weights.
- Figure and Table references are renumbered per paper and checked against the
  assets actually inserted.
- `rejected` and `needs_fix` records are never selected.
- The assembler reports **“N distinct papers possible”** and the maximum
  feasible Library size.

The implementation target is `src/assemble/recycle.py` plus shared bank
validators under `src/bank/` (Phase 2). CSC429 is the reference implementation.

## Subject types

Type **D** is the default for every new subject. Types A/B/C remain valid for
existing subjects and for optional variants where a solver can verify answers.

| Type | Meaning | Default strategy | Existing example |
|---|---|---|---|
| **A** | Slides + LLM theory | Generate + verify | CSC662 |
| **B** | Deterministic computed | Generate | CSC402, CSC413, MAT133 |
| **C** | Hybrid | Generate and/or recycle | ICT450 |
| **D** | Asset-first recycle | Recycle approved real questions | CSC429 |

A subject contract records:

```json
{
  "strategy": "recycle",
  "variants": {"enabled": false},
  "library": {"size_policy": "min(20, feasible)"},
  "answers": {"sources": ["model_unofficial", "solver_verified"]},
  "extraction": {"method": "mineru", "fallback": ["legacy_ocr", "page_crop"]}
}
```

Type D sets `generators_enabled: []` and `parametric_variants: false`. Only the
owner may enable variants.

## Marks, era and format rules

- Bank marks are the marks printed in the source paper. If a mark is
  unreadable, record `unsure`; do not guess.
- Sub-part marks must sum to the question total. A mismatch is `needs_fix`
  unless the owner records a written correction.
- The format profile’s total marks must equal the sum of its slots.
- Current-format papers are selected from the newest representative papers,
  not from an average of all eras.
- A question may move across sections; its original section is provenance, not
  a placement constraint.
- No “fill to 20” rule: Library size is `min(20, feasible with the reuse cap)`.
  Never invent questions to reach 20.
- A tolerance on marks is a written owner decision, not an assembler default.

## Answers and provenance

Every answer is an object:

```json
{
  "answer_id": "ANS-CSC429-2019-06-A2",
  "question_id": "CSC429-2019-06-A2",
  "subparts": [
    {"label": "a", "answer": "...", "marks": 4},
    {"label": "b", "answer": "...", "marks": 6}
  ],
  "marking_points": ["1 mark: ..."],
  "provenance": "model_unofficial",
  "confidence": "medium",
  "source": "model: deepseek-flash; cached 2026-11-08",
  "assumptions": "Diagram labels read from the page crop.",
  "reviewed_by": "",
  "reviewed_on": ""
}
```

| Provenance | When it is allowed |
|---|---|
| `official` | Parsed from a published scheme, only when the subject’s `permissions.scheme` allows it |
| `solver_verified` | Computed by code and independently checked; store the solver id and verification result |
| `model_unofficial` | Drafted by an AI model; labelled unofficial; needs the model name and confidence |
| `human_checked` | Reviewed or corrected by a person; record reviewer and date |

Numeric answers are verified by code where possible. The scheme shows the
provenance; it never presents a model answer as an official marking scheme.

## Assets

| Kind | Rule |
|---|---|
| `picture` | Original crop |
| `table` | Native table only when it matches the original; otherwise the crop |
| `figure` / `diagram` | Original crop unless it is simple **and** verified **and** approved |
| `equation` | LaTeX if verified, otherwise the crop |

Each asset record includes:

```json
{
  "id": "A-CSC429-2019-06-D1",
  "question_id": "CSC429-2019-06-A2",
  "kind": "diagram",
  "path": "data/tracking/csc429/bank/assets/A-CSC429-2019-06-D1.png",
  "source_paper": "CSC429-2019-06",
  "source_page": 2,
  "bbox": [x0, y0, x1, y1],
  "dpi": 300,
  "sha256": "...",
  "caption": "Figure 1: ...",
  "caption_bbox": [x0, y0, x1, y1],
  "treatment": "original_crop",
  "verdict": "approved"
}
```

No picture, figure or diagram is redrawn. A native table is accepted only after
a second comparison pass agrees with the extracted cell text. Assets belong to
their source question and cannot be borrowed by another question.

## Extraction

Use MinerU first for a figure-heavy subject; keep the full result ZIP and the
full extraction dossier for each paper.

V1 dossier requirements:

- source SHA-256 and page count;
- parser and model (`mineru/pipeline`, `mineru/vlm`, `legacy_ocr`, `page_crop`);
- cache path and task id;
- every page and block: text, image, table, equation, header/footer, page
  number, with block id and bbox;
- every Figure/Table reference and whether it resolved;
- every asset crop and every fallback page crop;
- raw Markdown and a block-provenance table;
- pipeline/vlm differences when both models were run.

MinerU is additive. If a referenced asset is missing, crop from the 300 dpi page
render. Respect `permissions.cloud_processing` before any upload. Never discard a
model’s asset because the other model has cleaner text.

## Three human gates

| Gate | When | What the owner approves |
|---|---|---|
| **Gate A** | After V2 bank build | Question statuses, marks, assets and reference links, duplicate clusters, review sheet, unresolved `unsure` items |
| **Gate B** | After V5 seeds 1–3 | Layout, question selection, marks fit, answer provenance, figures/tables, QA output |
| **Gate C** | Before publish | Public bundle, publication permission, R2 upload and Worker deploy |

Gate approvals are recorded in `lifecycle_state.json`. A gate is not approved by
a chat message alone; the approval must name the owner, date, evidence paths and
any conditions. “Continue” is not an approval.

## Branching

- **New subject:** create `<CODE>` from `main` before V0. Put every
  subject-specific change — docs, `subject.json`, lifecycle state, bank,
  extraction artifacts that are tracked, subject code and tests — on that
  branch.
- **Merge to main:** only after the subject is complete. Completion means V8
  close-out is done, Gate C is recorded, evidence exists and
  `lifecycle_status <CODE>` has no open stage.
- **Sub-branches:** use `<CODE>/exp-<topic>` for experiments or
  `<CODE>/backup-<date>` for backups. They branch from the subject
  branch, never from `main`, and merge back into the subject branch after
  validation. A sub-branch never merges directly into `main`.
- **No subject-specific commits on `main`.** Shared documentation or shared
  infrastructure fixes may go on `main` when they are not part of a subject’s
  in-progress work.

## Stages V0–V8

The v2 stages replace the v1 stages `0_intake`…`10_close_out`. V1 lifecycle
states remain valid and are mapped in the compatibility table below.

### V0 — Intake and permissions

**Purpose.** Confirm the subject identity, type, curriculum order and the legal
basis for using papers, scheme, slides and cloud processing. Create the
subject branch before any subject file is written.

**Inputs.** Subject code/title, owner instruction, existing registry order and
a clean `main` branch.

**Outputs.**

- `subjects/<CODE>/subject.json` with `status: "coming_soon"`, `type`,
  `strategy`, `variants`, `library`, `answers`, `extraction`, `capabilities`,
  `plugins` and `permissions`.
- `subjects/<CODE>/lifecycle_state.json` with `schema_version: 2`,
  `playbook_version: "2.0"` and the V0–V8 stage skeleton.
- `src/subjects/<code>/`, `data/papers/<CODE>/`, `data/tracking/<code>/`,
  `docs/<CODE>.md`.

**Definition of Done.**

- `subject.json` loads through `load_subjects()`.
- All four permissions are present. None is `allowed: true` without a recorded
  basis.
- `status` is still `coming_soon`.
- The work is on `<CODE>`, not on `main`.
- No original file is modified.
- The owner has supplied or confirmed the paper/scheme/slide inputs.

**Evidence.** `subject.json`, `lifecycle_state.json`, the intake inventory and
the permission records.

### V1 — Extract (MinerU-first dossier per paper)

**Purpose.** Turn working copies into a reliable, deduplicated, page-indexed
dossier with every text block, figure, table, equation and reference.

**Inputs.** `data/papers/<CODE>/*.pdf` (working copies only); optional
`permissions.cloud_processing`.

**Outputs.**

- `data/tracking/<code>/papers_register.json` — file, SHA-256, pages, cover
  source, duplicate group.
- `papers_summary.json` — unique/duplicate reconciliation.
- `data/tracking/<code>/mineru/<paper_id>/<model>_<options>/` — full ZIP tree,
  content lists, layout, images and manifest.
- `EXTRACTION_REPORT.md` per paper — the full page/block/asset dossier.
- Legacy OCR/page-render fallback records.
- `parser_provenance[]` in the lifecycle state.

**Definition of Done.**

- `unique + duplicate copies = total` reconciles.
- Every unique paper has a dossier or an explicit `unsure` item.
- Every referenced Figure/Table is resolved to an asset or a recorded fallback.
- Every fallback is listed with its page and reason.
- Originals are unchanged.

**Evidence.** `papers_summary.json`, the MinerU manifests, the per-paper
`EXTRACTION_REPORT.md`, and the fallback list.

### V2 — Bank build, then Gate A

**Purpose.** Segment real questions, link their assets, tag topics, cluster
duplicates and produce a review sheet.

**Inputs.** V1 dossiers and the source page renders.

**Outputs.**

- `data/tracking/<code>/bank/questions/<QID>.json`.
- `data/tracking/<code>/bank/assets/<AID>.png` and `<AID>.json`.
- `bank/index.json`, `bank/unsure.json`, `bank/corrections.json`,
  `bank/approvals.json`.
- `bank/review/` — the human review sheet.
- Duplicate clusters and feasibility sketch.
- `bank` counts in the lifecycle state.

**Definition of Done.**

- Every question has source paper, pages, marks, sub-part marks and content
  hash.
- Every picture/figure/diagram/table/equation is linked to its question and
  source page.
- Every question status is `extracted`, `needs_fix`, `approved` or `rejected`.
- Duplicate clusters are recorded; same question across years is not silently
  duplicated.
- Open `unsure` items are listed for Gate A.
- The review sheet renders the source asset and the extracted native content.

**Gate A.** The owner reviews the bank and records approval. The assembler
refuses to run while Gate A is not approved.

**Evidence.** Bank index, review index, Gate A report, approvals/corrections,
and the owner’s recorded approval.

### V3 — Format profile and templates

**Purpose.** Define the current paper format and approve the cover/scheme
templates before assembly.

**Inputs.** Newest representative papers, the subject template, the standard
marking-scheme template.

**Outputs.**

- `data/tracking/<code>/format_profile.json`.
- `subject.json.template_path` and `scheme_template_path`.
- `data/tracking/<code>/template_check.json`.

**Definition of Done.**

- Sections, questions per section, marks per slot, total marks, duration and
  numbering style are explicit.
- Marks sum to the printed total, or the mismatch is a recorded owner decision.
- `template_check.json` reports `xml_valid: true`, a non-empty cover, and a
  header or footer.
- The owner has seen the rendered cover and page-2 transition.
- The original template is unchanged.

**Evidence.** `format_profile.json`, `template_check.json`, rendered cover and
the approved template paths.

### V4 — Answers

**Purpose.** Attach an answer object to every selectable question and record its
provenance.

**Inputs.** Published scheme (only when permitted), solver code, model drafting,
human review.

**Outputs.**

- `bank/answers.json` — answer objects by question id.
- `bank/answers_report.json` — counts by provenance and unresolved items.
- `answers` provenance counts in the lifecycle state.

**Definition of Done.**

- Every approved question has at least one answer object.
- Every answer has provenance, confidence and source.
- Numeric answers are independently verified by code where possible.
- Official-scheme parsing is used only when `permissions.scheme` allows it.
- Model answers are labelled unofficial and carry assumptions.
- A sample of answers has been reviewed for correctness and presentation.

**Evidence.** `answers.json`, `answers_report.json`, solver verification output,
and the answer sample review.

### V5 — Assemble seeds 1–3 and QA, then Gate B

**Purpose.** Assemble the first three seeds from approved bank questions and
prove that the format, marks, assets and answers work together.

**Inputs.** Approved bank + format profile + answers.

**Outputs.**

- The subject Library cache folders for seeds 1–3
  (`outputs/web_cache/<CODE>/`), or a configured temporary build folder during
  review.
- Paper and scheme DOCX/PDF.
- `plan.json`, `qa.json`, `meta.json`.
- Feasibility report: distinct papers possible and reuse-cap use.

**Definition of Done.**

- Each seed has the exact format-profile slot count and total marks.
- No question repeats inside a seed.
- Rejected/needs_fix questions are absent.
- Figure/Table references are renumbered and resolve to inserted assets.
- Answers and marking points reconcile with question marks.
- DOCX/PDF QA is clean: XML valid, headings, marks, no forbidden tokens, no
  right-margin overflow.
- The three seeds use distinct source papers where feasible.

**Gate B.** The owner reviews seeds 1–3 and records approval. Seeds 4+ are
blocked until Gate B is approved.

**Evidence.** Seed plans, QA files, rendered PDFs, feasibility report and the
recorded Gate B approval.

### V6 — Remaining seeds and feasibility-sized Library

**Purpose.** Build the rest of the Library to `min(20, feasible)` without live
LLM spend or invented questions.

**Inputs.** Gate B-approved assembler and bank.

**Outputs.**

- Library cache `outputs/web_cache/<CODE>/`.
- A manifest with seed count, marks, topics, file paths and source-question
  counts.
- A reuse-cap report.

**Definition of Done.**

- Seed count equals `min(20, feasible with reuse cap)`.
- No seed repeats a question inside itself.
- Reuse across seeds stays within the configured cap.
- Every seed passes automated QA.
- No human gate is required unless QA fails; a QA failure reopens the affected
  seed and must be reported.
- Cached builds cost $0.

**Evidence.** Library manifest, feasibility report, QA summary and seed metadata.

### V7 — Publish, Gate C hard stop

**Purpose.** Build the public-safe bundle, verify permissions, then upload and
deploy only with explicit approval.

**Inputs.** Approved Library, `permissions.publication.allowed`, public bundle.

**Outputs.**

- `outputs/public_bundle/` with pages, manifests and documents.
- Generated `subjects.json`.
- R2 objects and Worker deployment, only after approval.

**Definition of Done.**

- Bundle validation reports no forbidden path and no missing manifest.
- Publication permission is recorded for every included subject.
- The R2 dry run is clean and within quota.
- The public route, Library manifest and downloads work.
- Gate C is recorded before any upload or deploy.

**Gate C.** Hard stop. No upload, deploy or registry promotion before the owner
records Gate C approval.

**Evidence.** Bundle validation, R2 ledger, Worker deployment record, public
route checks and the Gate C approval.

### V8 — Close-out

**Purpose.** Make the subject reproducible for the next person or agent.

**Outputs.**

- `lifecycle_state.json` with V0–V8 statuses, gate records, evidence, bank
  counts, answer-provenance counts and actual cost per stage.
- `docs/<CODE>.md` with commands, deviations and caveats.
- A clean final gate run.

**Definition of Done.**

- `lifecycle_status <CODE>` shows no next stage or only the final sign-off.
- Every evidence path exists.
- Gate A/B/C records are present where the stage required them.
- Blocking `unsure` items are closed or explicitly accepted.
- Secret scan and test suites pass.
- No behaviour change was made outside the subject’s contract.

**Evidence.** Strict status output, final test/safety results and the updated
`docs/<CODE>.md`.

## Lifecycle state v2

A v2 state file looks like this:

```json
{
  "schema_version": 2,
  "playbook_version": "2.0",
  "subject": "CSC429",
  "type": "D",
  "strategy": "recycle",
  "stages": {
    "V0_intake": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                   "blockers": [], "human_approval": {"required": false,
                   "approved": true, "by": "owner", "on": "2026-11-08",
                   "note": "Inputs and permissions recorded."}, "notes": ""},
    "V1_extract": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                   "blockers": [], "notes": ""},
    "V2_bank": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                "blockers": [], "notes": ""},
    "V3_format": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                  "blockers": [], "notes": ""},
    "V4_answers": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                   "blockers": [], "notes": ""},
    "V5_seeds_1_3": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                     "blockers": [], "notes": ""},
    "V6_library": {"status": "done", "evidence": [], "llm_cost_usd": 0.0,
                   "blockers": [], "notes": ""},
    "V7_publish": {"status": "pending", "evidence": [], "llm_cost_usd": 0.0,
                   "blockers": [], "notes": ""},
    "V8_close_out": {"status": "pending", "evidence": [], "llm_cost_usd": 0.0,
                     "blockers": [], "notes": ""}
  },
  "gates": {
    "A": {"status": "approved", "by": "owner", "on": "2026-11-08",
          "evidence": ["data/tracking/csc429/bank/gate1_report.md"]},
    "B": {"status": "approved", "by": "owner", "on": "2026-11-08",
          "evidence": ["outputs/.../GATE2_REPORT.md"]},
    "C": {"status": "pending", "by": "", "on": "", "evidence": []}
  },
  "bank": {
    "questions": 215, "approved": 172, "needs_fix": 26, "rejected": 17,
    "assets": 96, "duplicate_clusters": 0
  },
  "answers": {
    "official": 0, "solver_verified": 0, "model_unofficial": 153,
    "human_checked": 0
  },
  "parser_provenance": [],
  "llm_cost": {"currency": "USD", "total_usd": 0.0, "by_stage": {}}
}
```

Fields:

- `playbook_version` must be `"2.0"` for a converted state.
- `gates` records A/B/C separately from stage status.
- `bank` records question/asset counts and statuses.
- `answers` records provenance counts.
- `parser_provenance` records per-paper parser, model, pages, task id, cache and
  report path for `mineru`, `legacy_ocr` or `page_crop`.
- `llm_cost.by_stage` records actual cost per stage; deterministic and cached
  runs record `0.0` with a reason.
- A v1 state remains valid. Do not rewrite it just to change the schema; map it
  read-only and record v2 fields when the subject is migrated.

## v1 → v2 compatibility map

| v1 stage | v2 equivalent |
|---|---|
| `0_intake` | V0 intake and permissions |
| `1_preprocess` | V1 extract |
| Stage 1a MinerU | V1 extract |
| `2_scheme_slides` | V4 answer-source inventory (scheme) and V0/V1 slide inputs |
| `3_template` | V3 format profile and templates |
| `4_taxonomy_question_log` | V2 bank build (taxonomy and question metadata) |
| `5_fingerprint_planner` | V3 format profile + V5 assembler plan |
| `6_generators` | Optional variants only; not the default |
| `7_builders_qa` | V5 seeds 1–3 + QA |
| `8_library_prebuild` | V6 remaining seeds and Library |
| `9_publish` | V7 publish, Gate C |
| `10_close_out` | V8 close-out |

`scripts/lifecycle_status.py` must read both schemas and show the next gate
(`A`, `B` or `C`) for a v2 state. A v1 state continues to show its v1 next
stage until the subject is migrated.

## Gate checklist

- [ ] Every selected question is `approved` and traceable to a source paper.
- [ ] Marks reconcile, or a written owner tolerance is recorded.
- [ ] No question repeats inside a paper; the reuse cap is respected.
- [ ] Rejected and `needs_fix` records were not selected.
- [ ] Figure/Table references were renumbered and resolve to inserted assets.
- [ ] Every answer has provenance and, where applicable, a solver verification.
- [ ] Library size is `min(20, feasible)`; no question was invented to fill it.
- [ ] Gate A/B/C approval is recorded before the action it governs.
- [ ] `uv run python -m src.app.safety --check` passes.
- [ ] `uv run pytest -q` passes.
- [ ] `cd cloudflare/worker && bun test` passes.
- [ ] `uv run python -m scripts.lifecycle_status <CODE>` shows the stage and
      gate you claim.
- [ ] Any commit uses `konata1998 <jerkfish123@gmail.com>` and contains no
      agent/tool attribution.

## Adding a subject: the short version

```bash
# V0: scaffold a recycle subject (after Phase 2 code lands)
uv run python -m scripts.new_subject <CODE> --type D --title "Subject title"

# V1: register and extract working copies
uv run python -m src.subjects.preprocess --subject <CODE> --register --corpus

# V2: build the bank and review sheet, then stop for Gate A
# V3: write the current format profile and approve templates
# V4: attach answers with provenance
# V5: assemble seeds 1-3, run QA, then stop for Gate B
uv run python -m src.app.prebuild_library --seeds 1-3 --subject <CODE>

# V6: build the feasible Library
uv run python -m src.app.prebuild_library --seeds 1-20 --subject <CODE>

# V7: Gate C only, after explicit publication approval
uv run python -m scripts.build_public_bundle --out outputs/public_bundle --subject <CODE>
```

The shared bank, assembler and gate entry points now live in `src/bank/` and
`src/assemble/recycle.py`. Use:

```bash
# bank counts, quality, duplicates and feasibility (read-only)
uv run python -m src.bank.cli status <CODE>

# generate the HTML review sheet
uv run python -m src.bank.cli review <CODE>

# build approved-only seed plans after Gate A (and Gate B for seeds 4+)
uv run python -m src.bank.cli plans <CODE> --sections sections.json --seeds 1-3
```

CSC429 remains the reference implementation. Its subject-specific DOCX
renderer stays under `src/subjects/csc429/`; the shared helpers were extracted
without changing its output.
