# Subject onboarding playbook

This is the operating procedure for adding or changing a subject. It is
written from the CSC662, MAT133 and CSC402 work, and it is the authority for
the lifecycle state machine in `src/subjects/lifecycle.py`.

Read this file and `subjects/<CODE>/lifecycle_state.json` **before** touching a
subject. If the lifecycle file is missing, run stage 0 first; do not infer
progress from the presence of a cache folder.

The public deployment is library-only. Nothing in this playbook authorises an
upload, a Worker deploy, a registry promotion, or a change to the original
papers. Those are separate [HUMAN] decisions.

## Non-negotiable rules

1. **Originals are read-only.** Never edit, rename, move or delete
   `CSC662/`, `data/papers/<CODE>/` source files, `data/reference/<CODE>/`,
   `data/lecturedecks/<CODE>/` or the supplied PDFs. Stage 1 operates only on
   working copies under `data/papers/<CODE>/`; the shared code refuses paths
   outside `data/papers/` (`src/subjects/preprocess.py`).
2. **Flag uncertainty as `unsure`.** A noisy OCR cover, an unconfirmed
   permission, a guessed month, an unmatched question or an unvalidated
   generator is recorded in `lifecycle_state.json`, not silently resolved.
   CSC402's `CSC402 (21)` OCR cover is the reference example: the month was
   manually mapped to JULY 2025 and the mapping was recorded in
   `docs/CSC402.md`.
3. **Stop at [HUMAN] gates.** Every stage has one. Do not advance the state
   file past an unapproved gate. Stage 9 is always a hard stop before upload
   or deploy.
4. **Log LLM cost per stage.** Write the actual `usage.cost_usd` from the
   provider response into `lifecycle_state.json` (`llm_cost.by_stage` and
   `total_usd`). Never estimate silently. A cached run costs $0. MAT133 and
   every type-B subject cost $0 by design.
5. **Run the gates at every stage.**
   ```bash
   uv run python -m src.app.safety --check
   uv run pytest -q
   cd cloudflare/worker && bun test
   ```
   The secret scan is also run by the app at startup
   (`src/app/safety.py`, `src/app/main.py`).
6. **A hard-coded subject list is a bug.** Application code reads the registry
   (`src/subjects/registry.py`) or the generated `subjects.json`
   (`scripts/build_public_bundle.py`). The Worker has no `SUBJECTS`,
   `SUBJECT_ROUTES` or subject-specific `PAGE_MAP`
   (`cloudflare/worker/src/index.js`). Subject-specific code belongs only under
   `src/subjects/<code>/`; shared stage modules stay under `src/subjects/`.
7. **Record permissions before publish.** `subject.json` has a `permissions`
   block for `papers`, `scheme`, `slides` and `publication`. Each entry has
   `allowed`, `basis`, `confirmed_by`, `confirmed_on` and `notes`. An
   unconfirmed permission is `allowed: false` with `basis: "unsure"`.
8. **No secrets in the repo.** Read keys from the environment only. The
   placeholder key handling in `src/config.py` is fail-closed for public
   builds.
9. **Do not touch production in a scaffolding task.** Building a local bundle
   is not publishing; R2 upload and Worker deploy are stage 9 only.

## Subject types

| Type | Meaning | Reference | Planner | Prebuild | Public scheme |
|---|---|---|---|---|---|
| **A** | Slides + LLM theory | CSC662 (`subjects/CSC662/subject.json`) | LLM theory, lecture retrieval | LLM seed set + cached rebuild | Rebuilt with the quote-omission marker |
| **B** | Deterministic computed | MAT133 (`subjects/MAT133/subject.json`) | Deterministic, paper-derived | Subject plugin, no LLM | Copied from cache; no quote marker |
| **C** | Hybrid | New scaffolds default here | Deterministic and/or LLM theory | Subject plugin or LLM seed set | Rebuilt if it uses slide quotes; otherwise copied |
| **D** | Asset-first assembly | CSC429 (`subjects/CSC429/subject.json`) | Approved real-paper questions only; generators disabled | Approved seed set + deterministic assembler | Copied from cache; no quote marker |

### Type D — asset-first assembly (additive)

Type D is an additive type for subjects whose source of truth is a set of real
past papers. It does not change Types A, B or C. It maps the stage numbers to
the asset-first pipeline:

| Playbook stage | Type D operation |
|---|---|
| 0 intake | P0 reset and lock: archive old state/assets/seeds, write `rejected_registry.json`, confirm source papers and templates. |
| 1 preprocess | P1 extract: segment questions/sub-parts and marks, native text, source crops for every picture/figure/diagram/table, labels and references, topic tags. |
| 2 scheme/slides | Not used as source of truth. Reference answers are unofficial and are produced at the answers stage. |
| 3 template | P0/P6: use the owner-approved paper and scheme templates, including crest and cover box offsets. |
| 4 taxonomy/log | P1: write the per-question/per-asset bank under `data/tracking/<CODE>/bank/`. |
| 5 fingerprint/planner | P4: derive paper structure and a deterministic seed plan from **approved** questions only. |
| 6 generators | Disabled. `generators_enabled: []`, `parametric_variants: false`; only the owner may switch them on. |
| 7 builders/QA | P6: assemble seeds 1-3, enforce approval/asset/reference/rejected-registry gates, export via Word COM and run QA. |
| 8 library prebuild | P7/P8: build remaining approved seeds and manifest. |
| 9 publish | Separate [HUMAN] stage; never part of P0-P8. |

Type D data contracts:

- `bank/questions/<QID>.json` — id, source paper/pages, marks and sub-part
  marks, native text blocks, native tables, `refs`, `assets[]`, topic tags,
  status, content hash, notes.
- `bank/assets/<AID>.png` and `<AID>.json` — 300 dpi source crop, kind,
  caption/label, page, bbox, treatment, compare result and human verdict.
- `bank/corrections.json` and `bank/approvals.json` — keyed by QID and content
  hash; re-extraction must not overwrite them.

Hard gate: the seed builder must refuse to run unless every selected question
is `approved`, every asset belongs to its question, and the required gate is
recorded as approved in `lifecycle_state.json`. The word “continue” is not an
approval.

The type is a promise encoded in `capabilities`:

```json
{
  "type": "C",
  "capabilities": {
    "generation": "hybrid",
    "prebuild": "plugin",
    "public_documents": "rebuild_scheme",
    "needs_llm": true,
    "uses_slides": true,
    "practice_mode": true,
    "placeholders": true,
    "public_scheme_requires_quote_marker": true
  },
  "plugins": {
    "plan": "src.subjects.csc402.plugin:plan",
    "prebuild": "src.subjects.csc402.plugin:build_seed"
  }
}
```

`src/subjects/registry.py` derives safe defaults, and
`src/subjects/plugins.py` loads the dotted entry points. No branch in
`src/app/jobs.py` names a subject.

### What changes by type

| Stage | Type A | Type B | Type C |
|---|---|---|---|
| 1 preprocess | Papers + cover OCR | Papers + OCR | Papers + OCR |
| 2 scheme/slides | Scheme **and** slides required | Scheme required; slides `not_applicable` | Scheme required; slides if the hybrid uses theory |
| 4 taxonomy/log | Theory topics from slides and papers | Paper-derived topics and marks | Union of both |
| 5 planner | LLM/theory planner plugin | Deterministic planner plugin | Hybrid planner plugin |
| 6 generators | Computed cipher/generic plugins + theory module | All questions deterministic | Selected deterministic generators + theory where configured |
| 7 QA | Structure, citations, placeholders | Deterministic answer/DOCX/PDF validation | Both checks |
| 8 prebuild | Needs accepted LLM seed set; rebuild is free | Plugin builds 20 seeds at $0 | Plugin or LLM seed set, depending on `prebuild` |
| 9 bundle | `rebuild_scheme`; marker required | `copy_cached`; no marker | `rebuild_scheme` by default |

## Lifecycle state schema

`subjects/<CODE>/lifecycle_state.json` is written by
`scripts/new_subject.py` and read by `scripts/lifecycle_status.py`:

```json
{
  "schema_version": 1,
  "subject": "TEST000",
  "type": "C",
  "updated": "2026-11-04T00:00:00Z",
  "stages": {
    "0_intake": {
      "status": "pending",
      "evidence": ["subjects/TEST000/subject.json"],
      "llm_cost_usd": 0.0,
      "blockers": [],
      "human_approval": {"required": true, "approved": false, "by": "", "on": "", "note": ""},
      "notes": ""
    }
  },
  "unsure": [
    {"stage": "0_intake", "item": "Confirm the course title.", "blocking": true, "opened": "2026-11-04"}
  ],
  "llm_cost": {"currency": "USD", "total_usd": 0.0, "by_stage": {}}
}
```

Statuses are `pending`, `in_progress`, `blocked`, `done`, `skipped` and
`not_applicable`. A stage is not complete if its evidence path is missing, its
required human approval is absent, or a blocking `unsure` item remains.

## Stages 0–10

Each stage has a human checkpoint. The [HUMAN] gate is deliberate: it is the
only place a person can reject a plausible but wrong result.

### Stage 0 — Intake and permissions [HUMAN]

**Purpose.** Confirm what is being onboarded, its code, title, curriculum
order, type and legal/usage basis.

**Inputs.** The subject code and title from the curriculum; the owner's
instruction; existing `subjects/*/subject.json` for ordering.

**Outputs.**
- `subjects/<CODE>/subject.json` with `status: "coming_soon"`, `type`,
  `capabilities`, `plugins` and `permissions`.
- `subjects/<CODE>/lifecycle_state.json`.
- `src/subjects/<code>/` package, `data/papers/<CODE>/`,
  `data/tracking/<code>/`, `docs/<CODE>.md`.

**Commands.**
```bash
uv run python -m scripts.new_subject <CODE> --type A|B|C --dry-run
uv run python -m scripts.new_subject <CODE> --type A|B|C --title "Subject title"
uv run python -m scripts.lifecycle_status <CODE>
```

**Definition of Done.**
- `subject.json` parses through `load_subjects()`.
- `lifecycle_status <CODE>` prints `0_intake` as the next stage.
- The four permissions are present. None is `allowed: true` unless the owner
  recorded the basis.
- `status` is still `coming_soon`.
- No file outside the scaffold paths exists.

**Evidence.** `subjects/<CODE>/subject.json`,
`subjects/<CODE>/lifecycle_state.json`, and the dry-run output captured in the
job log.

**References.** `scripts/new_subject.py`, `src/subjects/registry.py`,
`src/subjects/lifecycle.py`, `docs/LIFECYCLE.md` §7.

### Stage 1 — Paper preprocessing [HUMAN]

**Purpose.** Turn the working-copy folder into a reliable, deduplicated paper
register and text corpus without touching originals.

**Inputs.** `data/papers/<CODE>/*.pdf` (working copies only).

**Outputs.**
- `data/tracking/<code>/papers_register.json` — one row per file: source,
  SHA-256, pages, cover source (`text`/`ocr`), parsed month/year, confidence,
  duplicate link.
- `papers_summary.json` — total, unique, duplicate groups, month/year found,
  low-confidence list.
- `cover_text.json` — cover text/OCR cache keyed by hash.
- `paper_text/*.txt` and `paper_text/index.json` when `--corpus` is used.
- Renamed working copies only when `--apply-rename` is explicitly passed.

**Commands.**
```bash
# scan and register; no rename, no OCR if --no-ocr is supplied
uv run python -m src.subjects.preprocess --subject <CODE> --register

# add the full-text/OCR corpus
uv run python -m src.subjects.preprocess --subject <CODE> --register --corpus

# after the human approves the register, rename working copies by cover
uv run python -m src.subjects.preprocess --subject <CODE> --register --apply-rename
```

**Definition of Done.**
- Summary counts reconcile: `unique + duplicate copies = total`.
- Every unique paper has a non-empty text entry or an explicit `unsure` item.
- Duplicate pairs are byte-identical SHA-256 groups and are listed, not
  deleted.
- Low-confidence covers are in `unsure`; no month/year is invented.
- Original folders are unchanged.

**Evidence.** `papers_summary.json`, `paper_text/index.json`, and the
human-approved duplicate list. CSC402's equivalent is
`data/tracking/csc402/papers_summary.json` (24 files, 21 unique, 3 duplicate
pairs) and `docs/CSC402.md`.

**References.** `src/subjects/preprocess.py`, `src/ingest/ocr.py`,
`scripts/register_mat133_papers.py` (the subject-specific predecessor),
`scripts/build_mat133_corpus.py`.

### Stage 2 — Scheme and slides [HUMAN]

**Purpose.** Confirm what answer/scheme material and lecture material exist,
who may use them, and which one is authoritative.

**Inputs.** `data/reference/<CODE>/` (official scheme/template) and, for type
A/C, `data/lecturedecks/<CODE>/`.

**Outputs.**
- `permissions.scheme` and `permissions.slides` in `subject.json`.
- A slide/deck inventory or BM25 deck map when applicable.
- `data/tracking/<code>/scheme_parse*.json` when a scheme is parsed.
- `unsure` entries for missing, incomplete or unreadable material.

**Commands.**
```bash
# Existing MAT133 scheme parser (subject-specific example)
uv run python -m src.subjects.templates --subject MAT133 --check
uv run python -m src.subjects.preprocess --subject MAT133 --register --corpus
```
For a new subject, add the parser under `src/subjects/<code>/` and record the
command in that subject's `docs/<CODE>.md`.

**Definition of Done.**
- `permissions.scheme.allowed` and `permissions.slides.allowed` are recorded
  with a basis. Type B may set slides to `not_applicable`.
- The scheme is either parsed into a traceable artifact or explicitly marked
  `unsure`.
- No lecture/scheme file is copied into the public bundle.
- CSC662's public schemes still contain the quote-omission marker; MAT133's
  deterministic schemes do not need it.

**Evidence.** `data/reference/<CODE>/...`, `data/tracking/<code>/`,
`data/tracking/mat133/scheme_fingerprint.json`,
`data/lecturedecks/CSC662/`.

**References.** `docs/MAT133.md` (scheme parse and 57 generators),
`src/theory/bm25.py`, `scripts/build_mat133_question_log.py`,
`src/assemble/build_docx_scheme_04.py` (`quote_for_scheme`).

### Stage 3 — Template and cover [HUMAN]

**Purpose.** Approve the DOCX template, cover, crest/header/footer and
pagination before any body generation.

**Inputs.** A supplied template DOCX under `data/reference/<CODE>/`, or the
standard CSC662/MAT133 cover as the reference.

**Outputs.**
- `subject.json.template_path` pointing at the approved template.
- `data/tracking/<code>/template_check.json` from the structural check.

**Commands.**
```bash
uv run python -m src.subjects.templates --subject <CODE> --check
uv run python -m src.subjects.templates --subject <CODE> --install /path/to/template.docx --apply
```

**Definition of Done.**
- `template_check.json` reports `xml_valid: true`, at least one section,
  non-empty cover text, and a header or footer.
- `subject.json.template_path` exists.
- The human has seen the rendered cover and page-2 transition.
- The original template file is unchanged.

**Evidence.** `template_check.json`, the approved DOCX path, and a rendered
cover sample. The MAT133 cover-pagination caveat is documented in
`docs/DEPLOY_LIVE.md`.

**References.** `src/subjects/templates.py`, `src/mat133/build_docx.py`,
`src/assemble/build_docx_paper.py`.

### Stage 4 — Taxonomy and question log [HUMAN]

**Purpose.** Derive the paper's topic taxonomy, marks distribution and
question metadata from the past papers, with every question traceable to a
source.

**Inputs.** The stage-1 corpus, the stage-2 scheme, and the subject's
paper-derived conventions.

**Outputs.**
- `data/tracking/<code>/taxonomy.json`.
- `data/tracking/<code>/question_log.json` (and schema if applicable).
- `subject.json.fingerprint`, `deck_map`, `topic_deck_allowlist` as needed.

**Commands.**
```bash
# MAT133 reference implementation
uv run python scripts/build_mat133_question_log.py
uv run python -m pytest -q tests/test_mat133_taxonomy.py

# New subject: add src/subjects/<code>/taxonomy.py and run
uv run python -m src.subjects.<code>.taxonomy
```

**Definition of Done.**
- Every taxonomy topic has a stable key and a short label.
- Every logged question has paper ID, question/part, marks, topic and a
  verbatim source reference; drops are listed as `unsure`.
- The marks sums reconcile with the paper totals, or the mismatch is recorded.
- The human has reviewed the taxonomy, especially merged/split topics.

**Evidence.** `data/tracking/mat133/taxonomy.json`,
`data/tracking/mat133/question_log.json`, and the matching tests.

**References.** `scripts/build_mat133_question_log.py`,
`src/mat133/planner.py` (`TOPIC_SHORT`, `TOPIC_TITLES`),
`data/tracking/mat133/question_log.schema.json`.

### Stage 5 — Fingerprint and planner [HUMAN]

**Purpose.** Turn the taxonomy and marks distribution into a repeatable plan
for a whole paper.

**Inputs.** The stage-4 taxonomy/question log, the paper fingerprint, and the
subject's planner plugin.

**Outputs.**
- A planner plugin (for example `src/subjects/<code>/plugin.py::plan` or a
  deterministic planner module).
- `outputs/eval_final_deepseek/seed_<NN>_planner.json` for type A/C, or the
  deterministic plan generated by the plugin.
- `subject.json.fingerprint` with the source papers, era and slot structure.

**Commands.**
```bash
# Reference planner tests
uv run python -m pytest -q tests/test_planner.py tests/test_planner_revision.py

# MAT133 deterministic planner
uv run python -m pytest -q tests/test_mat133_planner.py

# Every stage gate
uv run python -m scripts.lifecycle_status <CODE>
```

**Definition of Done.**
- The same seed produces the same slots and topic/marks assignment.
- Slot marks sum to the expected paper total.
- Every slot resolves through a plugin or a recorded deterministic rule.
- The planner is approved by a human, including its topic sequence and any
  low-confidence style slots.

**Evidence.** Planner JSON/plugin tests, `lifecycle_state.json` stage 5.
CSC662's 24-slot plan is in `outputs/eval_final_deepseek/seed_01_planner.json`;
MAT133's five-question, 15-part plan is in `src/mat133/planner.py`.

**References.** `src/planner/planner.py`, `src/subjects/csc662/plugin.py`,
`src/mat133/planner.py`, `src/subjects/plugins.py`.

### Stage 6 — Generators [HUMAN]

**Purpose.** Implement the question types the planner can emit, with
deterministic answers or grounded theory answers.

**Inputs.** The stage-5 slot kinds, the stage-4 taxonomy, the scheme/slides.

**Outputs.**
- Generator modules under `src/subjects/<code>/` for type B/C; shared cipher
  generators remain in `src/generators/`.
- `subject.json.enabled_computed_generators` and generator labels.
- Generator validation artifacts: per-type or per-seed pass/fail.

**Commands.**
```bash
# MAT133 reference: 57 generators, all used across seeds 1-20
uv run python scripts/validate_mat133_generators.py
uv run python -m pytest -q tests/test_mat133_generators.py

# CSC662 computed generator tests
uv run python -m pytest -q tests/test_ciphers.py tests/test_acm.py tests/test_computed_type1.py
```

**Definition of Done.**
- Every enabled generator has a registered implementation and a label.
- Deterministic answers are independently recomputed in tests.
- Unsupported types fail closed; they never invent an answer.
- A 20-seed run covers every enabled generator or the gap is recorded as
  `unsure`.
- The human has sampled outputs for correctness and presentation.

**Evidence.** `tests/test_mat133_generators.py` (57/57 coverage),
`docs/MAT133.md`, and the subject's generator validation log.

**References.** `src/generators/`, `src/mat133/generators/`,
`scripts/validate_mat133_generators.py`.

### Stage 7 — Builders and QA [HUMAN]

**Purpose.** Assemble a paper and marking scheme that are structurally valid,
downloadable and visually acceptable.

**Inputs.** The planner, theory/generator output, and the approved template.

**Outputs.**
- `paper.docx`, `paper.pdf`, `scheme.docx`, `scheme.pdf` in the cache.
- QA reports for XML validity, headings, part labels, marks, cover, page-2
  body start, right-margin overflow and forbidden tokens.
- Public schemes with quote omission where required.

**Commands.**
```bash
# one accepted seed through the shared prebuild path
uv run python -m src.app.prebuild_library --seeds 1 --subject <CODE> --force

# local visual check
uv run python -m src.app.main
# open http://127.0.0.1:8000/<route>/library

# every stage gate
uv run python -m src.app.safety --check
uv run pytest -q
```

**Definition of Done.**
- Both DOCX files open and pass structural checks.
- PDFs exist or the DOCX fallback is recorded; the job does not pretend PDF
  export succeeded.
- No forbidden token or private path is present
  (`src/subjects/forbidden.py`).
- The human has opened the rendered paper and scheme and approved cover,
  tables and marks.
- Public scheme marker is present when
  `public_scheme_requires_quote_marker` is true.

**Evidence.** Cache `meta.json`, QA logs, and the human's visual approval.
MAT133's validation is `src/mat133/library.py::_validate`; CSC662's public
marker is checked by `scripts/build_public_bundle.py::_check_scheme`.

**Standard marking-scheme template.** Use
`data/reference/standard/UTM_STANDARD_MARKING_SCHEME.docx` for the scheme
cover and notes until the owner changes it. Patch the course/title/code/date
fields and append the answer key/worked answers; do not create a new scheme
cover.

**References.** `src/assemble/generic_build.py`,
`src/mat133/build_docx.py`, `src/assemble/pdf_export.py`,
`src/subjects/forbidden.py`.

### Stage 8 — Library prebuild [HUMAN]

**Purpose.** Produce the fixed seed set that the private Library and public
bundle use, without accidental live LLM spend.

**Inputs.** The approved builder, 20 accepted seeds, and (for type A/C) stored
planner/theory JSON.

**Outputs.**
- `outputs/web_cache/<CODE>/<config-hash>/` with `meta.json`, DOCX/PDF and
  progress records.
- For a type-B subject, the plugin's deterministic output and validation.
- A 20-seed coverage report.

**Commands.**
```bash
uv run python -m src.app.prebuild_library --seeds 1-20 --subject <CODE>
uv run python -m scripts.lifecycle_status <CODE>
```

**Definition of Done.**
- 20 seeds exist and are loadable by `library_items(<CODE>)`.
- Every `meta.json` has subject, seed, mode, year, marks/topic data and file
  paths; cached files exist.
- A type-B run costs $0 and makes no LLM call.
- A type-A/C run reuses accepted theory and records LLM cost in the lifecycle.
- The human has accepted the 20-seed set and any placeholders.

**Evidence.** `outputs/web_cache/MAT133/` (20 seeds),
`outputs/web_cache/CSC662/`, and `meta.json` records. CSC662 has 20 accepted
seeds under `outputs/eval_final_deepseek/`.

**References.** `src/app/prebuild_library.py`,
`src/subjects/mat133/plugin.py`, `src/mat133/library.py`,
`src/app/jobs.py` (`cache_path`).

### Stage 9 — Publish [HUMAN — hard stop]

**Purpose.** Build the public-safe bundle, verify it, then upload and deploy
only with explicit permission.

**Inputs.** Approved caches, `subject.json.permissions.publication.allowed`,
the generated public pages and documents.

**Outputs.**
- `outputs/public_bundle/` including per-subject pages, `library/<CODE>/`,
  subject JSON, and the generated `subjects.json`.
- `cloudflare/public_bundle_manifest.txt/.json` when the allowlist is written.
- R2 objects, Worker deployment, and an updated public URL.

**Commands.**
```bash
# 1. local bundle only; no network
uv run python -m scripts.build_public_bundle --out outputs/public_bundle --subject <CODE> --seeds 1-20

# 2. allowlist dry run
uv run python -m scripts.public_bundle

# 3. R2 dry run (no writes)
uv run python -m scripts.r2_sync --bundle outputs/public_bundle

# 4. [HUMAN] upload
uv run --with boto3 python -m scripts.r2_sync --bundle outputs/public_bundle --upload

# 5. [HUMAN] Worker deploy
cd cloudflare/worker 
bun x wrangler deploy

# 6. verify the generated subject route, not a hand-edited route
curl -I https://uitmpapergen.download/<route>
curl -I https://uitmpapergen.download/library/<CODE>/manifest.json
```

**Definition of Done.**
- `validate()` reports no forbidden path, no missing manifest file, and no
  missing quote marker where required.
- `subjects.json` contains the subject and its route; the Worker resolves the
  route from it, with no Worker subject list edit.
- R2 object count/bytes are within the quota plan
  (`cloudflare/R2_QUOTA_PLAN.md`); the dry run is clean before upload.
- `permissions.papers`, `scheme`, `slides` and `publication` are recorded.
- The human has explicitly approved the upload and deploy.
- The public route, Library manifest, downloads and gallery share work.

**Evidence.** `outputs/public_bundle/subjects.json`,
`cloudflare/public_bundle_manifest.json`, R2 sync ledger, deployment URL, and
the permission record.

**References.** `scripts/build_public_bundle.py`, `scripts/public_bundle.py`,
`scripts/r2_sync.py`, `cloudflare/worker/src/index.js`,
`cloudflare/R2_QUOTA_PLAN.md`, `docs/DEPLOY_LIVE.md`.

### Stage 10 — Close-out [HUMAN]

**Purpose.** Make the subject's state reproducible for the next person or
agent and record the true cost and unresolved questions.

**Inputs.** All prior evidence, the lifecycle state, and the test/gate output.

**Outputs.**
- `subjects/<CODE>/lifecycle_state.json` with every stage `done`, evidence
  paths, human approvals and `llm_cost.by_stage`.
- `docs/<CODE>.md` updated with commands, deviations and known caveats.
- A clean final gate run.

**Commands.**
```bash
uv run python -m scripts.lifecycle_status <CODE> --strict
uv run python -m src.app.safety --check
uv run pytest -q
cd cloudflare/worker && bun test
```

**Definition of Done.**
- `lifecycle_status <CODE>` reports no next stage or only the final human
  sign-off.
- Every completed stage's evidence path exists and every required approval is
  recorded.
- All blocking `unsure` items are closed or explicitly accepted by the human.
- Secret scan and test suites pass.
- `docs/<CODE>.md` explains anything a newcomer would otherwise re-derive.

**Evidence.** The strict status output, the gate logs, and the final
`lifecycle_state.json`.

**References.** `scripts/lifecycle_status.py`, `docs/LIFECYCLE.md`,
`README.md`.

## Adding a subject: the short version

```bash
# 1. scaffold; still coming_soon, no onboarding
uv run python -m scripts.new_subject CSC402 --type C --title "Programming I" --dry-run
uv run python -m scripts.new_subject CSC402 --type C --title "Programming I"

# 2. stage 0 human checkpoint, then stage 1
uv run python -m src.subjects.preprocess --subject CSC402 --register --corpus

# 3. stage 2-7 subject-specific plugins and approvals
# 4. stage 8
uv run python -m src.app.prebuild_library --seeds 1-20 --subject CSC402

# 5. stage 9 only after publication permission
uv run python -m scripts.build_public_bundle --out outputs/public_bundle --subject CSC402
```

CSC402 is deliberately still `coming_soon`: only stage 1 is done, and its
permissions/type are not yet human-confirmed. Use it as the worked example of
"prepared corpus, not onboarded."

## Gate checklist for every stage

- [ ] Working only under `data/papers/<CODE>/`, never an original.
- [ ] New uncertainty is in `lifecycle_state.json` as `unsure`.
- [ ] `uv run python -m src.app.safety --check` passes.
- [ ] `uv run pytest -q` passes.
- [ ] `cd cloudflare/worker && bun test` passes.
- [ ] No new hard-coded subject list; Worker reads `subjects.json`.
- [ ] LLM cost for this stage is recorded (or `$0` with the reason).
- [ ] The stage's [HUMAN] approval is recorded before status moves to `done`.
