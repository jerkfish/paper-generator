# MAT133 v2 — Gate B review

Status: **v2 seeds 1–3 built; Gate B is pending owner approval.**
Date: 2026-11-14
Subject: MAT133 Pre-Calculus (Type B, deterministic)
Playbook: v2.0

## What this migration changes

- The **contract** moves to playbook v2: `strategy: generate`,
  `variants.enabled: true`, `library.size_policy: min(20, feasible)`,
  `answers.sources: [solver_verified]` and a v2 `documents` block.
- The **v1 lifecycle is preserved verbatim** as
  `subjects/MAT133/lifecycle_state_v1.json`
  (SHA-256 `8933c0929f693f3e984ba47bd62dbbffb11fe78564562ef9e1f7367796c12d5a`).
- The **v1 documents are untouched**. v1 files remain `paper.*` and
  `scheme.*` under each seed cache and stay visible in the Library as v1.
- **v2 documents** are added beside them:
  - paper: the approved MAT133 template, rebuilt deterministically; its PDF
    text is byte-for-byte equal to the v1 paper text for these seeds;
  - scheme: the standard UTM marking-scheme cover required by `AGENTS.md`,
    followed by the same `NO | SOLUTION | MARK` table.
- The Library shows **Docs v1 / Scheme v1 / Docs v2 / Scheme v2** for MAT133.
  Other subjects keep their existing Paper/Scheme columns.
- **Nothing is published.** `documents.public_versions` is `[1]`, so the
  public bundle continues to expose only v1 until Gate C.

## v2 seeds 1–3

| Seed | Parts | Total marks | v2 paper pages | v2 scheme pages | QA problems |
|---:|---:|---:|---:|---:|---|
| 1 | 15 | 68 | 7 | 6 | 0 |
| 2 | 15 | 67 | 6 | 5 | 0 |
| 3 | 15 | 70 | 7 | 6 | 0 |

Review files:

- `outputs/review/mat133_v2/seeds/seed_01_paper_v2.pdf`
- `outputs/review/mat133_v2/seeds/seed_01_scheme_v2.pdf`
- `outputs/review/mat133_v2/seeds/seed_02_paper_v2.pdf`
- `outputs/review/mat133_v2/seeds/seed_02_scheme_v2.pdf`
- `outputs/review/mat133_v2/seeds/seed_03_paper_v2.pdf`
- `outputs/review/mat133_v2/seeds/seed_03_scheme_v2.pdf`

Covers:

- `outputs/review/mat133_v2/paper_v2_cover_p1.png`
- `outputs/review/mat133_v2/scheme_v2_cover_p1.png`

## Automated QA

For every seed, both DOCX and PDF checks pass:

- valid `word/document.xml` and crest present;
- 5 `QUESTION` headings and 15 scheme part labels;
- page 1 has the cover and `MAT133`; the body starts on page 2;
- all marks present; no forbidden legacy tokens;
- no right-margin overflow;
- v2 paper PDF text equals the v1 paper PDF text (cover month is preserved
  from the v1 cache timestamp, October 2026).

Evidence:

- `data/tracking/mat133/v2/format_profile.json`
- `data/tracking/mat133/v2/template_check.json`
- `data/tracking/mat133/v2/answers/seed_01.json`
- `data/tracking/mat133/v2/answers/seed_02.json`
- `data/tracking/mat133/v2/answers/seed_03.json`
- `outputs/web_cache/MAT133/<seed-cache>/meta.json` → `document_versions."2"`

## Lifecycle position

- **Gate A — not applicable.** MAT133 is Type B and has no recycled question
  bank. The v1 taxonomy and question log were owner-approved on 2026-11-04;
  the v2 state maps that approval read-only and records the basis.
- **Gate B — pending.** v2 seeds 1–3 are ready for owner review.
- **Gate C — pending.** No v2 upload, Worker deploy or public change.

V6 seeds 4–20 are blocked until Gate B. The v1 Library remains fully available
in the meantime.

## Owner review questions

1. Is the standard UTM marking-scheme cover acceptable for MAT133 v2 schemes,
   or should MAT133 keep its v1 marker-style cover for v2 as well?
2. Are the v2 paper/scheme layouts and the four-column Library table
   (Docs v1 / Scheme v1 / Docs v2 / Scheme v2) correct?
3. On approval, should v2 be built for seeds 4–20 and then held at Gate C
   (no publication), or should the v2 Library stop at seeds 1–3?

No LLM calls were made. Cost for V5: **$0.00**.
