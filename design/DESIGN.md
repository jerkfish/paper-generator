# Mock Paper Generator - page design (v2)

Status: **design only**. No Phase 0-4 implementation has started.

Direction: grounded, document-like, early-2000s web. Default browser
typography, table-based lists, visible 1px borders, blue underlined links,
small text, no cards, no shadows, no gradients, no large icons. The stylesheet
is deliberately tiny.

## Mockups

Open `design/mockups/index.html` directly, or:

```bash
uv run python -m http.server 8090 --directory design/mockups
# http://127.0.0.1:8090
```

| Mockup | Final route | Purpose |
|---|---|---|
| `index.html` | `/` | Subject table |
| `subject-csc662.html` | `/csc662` | Subject hub with three paths |
| `library.html` | `/csc662/library` | Filter input + details table list |
| `generate.html` | `/csc662/generate` | Form + real-event job status table |
| `gallery.html` | `/gallery` | Public table list, expiry, takedown |
| `paused.html` | `/paused` | Daily-cap fallback |

Screenshots: `design/mockups/*.png` and `*-top.png` (desktop), `*-mobile.png`
(390 px).

## Rules

- No icons, logos or decorative images in the interface.
- No card grid. Library is a details table.
- No animation or typewriter. Generation progress is a table updated from
  real job events. No fake timer.
- Mobile: the table scrolls horizontally if needed; no separate mobile app
  shell. Font stays readable at 11-12 px.
- `prefers-reduced-motion` is respected trivially because there is no motion.
- Keep keyboard access: real form controls, labels, links and table headers.
- Content is a centred 980 px column with 92% width and side gutters.
- Every page ends with contact and Git-repository placeholders; replace them with the real details before deployment.

## Pages

### Home

Text title, nav line, short purpose statement, then two tables:

1. **Subjects** - code, title, status, papers, open link. CSC662 available;
   CSC580/CSC645 coming soon with no data.
2. **Purpose** - Generate / Library / Gallery, whether a key is needed and the
   cost.

### Subject page

Breadcrumb, heading, status line, then:

- **Paths** table: Generate, Library, Gallery, with a link and a plain
  description.
- **Subject data** table: registry path, computed generator plugins, clean
  modern paper count, evaluation stats, public-build note.

### Library

Filter form above the table:

```text
Text: [__________]  Computed marks: [any v]  Placeholders: [any v]  [Apply] [Reset]
```

Details table columns:

```text
Seed | Mode | Computed marks | Topic mix (marks) | Placeholders | Paper | Scheme
```

- Paper and Scheme cells: DOCX / PDF links.
- Topic mix is a compact text string: `ATK 24 AUT 16 ACC 18 ...`.
- No thumbnails in the default v2 table. A "Preview page 1" link may be added
  later without changing the table.
- Filtering is HTMX in the live app; the mockup shows the controls only.

### Generate

- Form in a `fieldset`: mode, optional seed, practice-only computed N,
  Turnstile slot, Generate/Cancel.
- Job status tables:
  - counters: cost, attempts, accepted/24, placeholders, elapsed;
  - textual pipeline: `Retrieve > Draft > Verify > Accept`;
  - ASCII progress bar;
  - one row per question, columns a/b/note;
  - last accepted question + source + entailment;
  - download links only on completion.
- Job table updates from actual events. No pulse, no typewriter.

Event contract:

```text
plan_ready      -> outline rows created
slot_started    -> row shows active/waiting
stage_changed   -> pipeline text
draft_rejected  -> log line with reason and attempt count
slot_accepted   -> a/b cell accepted; question/source row
slot_placeholder-> placeholder cell
cost_update     -> cost/attempt counters
job_done        -> downloads and final summary
```

### Gallery

- Table: Subject, Seed, Mode, Computed, Created, Expires, ID, Paper, Scheme.
- Notice: study aid, not official; slide-supported theory; auto-delete after
  7 days; no accounts; no user text; no IP logging beyond rate limiting.
- Expired rows are filtered by `created_at` immediately; Cron purges later.
- Takedown contact section.

### Paused

Plain notice: daily cap reached, live generation resumes at 00:00 UTC, browse
the Library. No API key is used.

## Filenames

```text
{SUBJECT} Seed {SEED} {YEAR}.docx / .pdf
{SUBJECT} Seed {SEED} {YEAR} - Marking Scheme.docx / .pdf
```

Practice adds ` (practice N)` before the extension. Content-Disposition uses
an ASCII `filename` plus RFC 5987 `filename*`. YEAR is UTC generation year.

## Subject registry sketch

```text
subjects/CSC662/subject.json
subjects/CSC580/subject.json   status: coming_soon
subjects/CSC645/subject.json   status: coming_soon
```

Fields: `code`, `title`, `status`, `header_text`, `template_path`,
`fingerprint`, `deck_map`, `topic_deck_allowlist`,
`enabled_computed_generators`.

Computed generators are subject plugins; another subject needs its own.
Routes, cache key and Library folders are subject-scoped.

## Public bundle

The proposed allowlist is in `design/PUBLIC_BUNDLE_PROPOSAL.md`. It contains
only public pages, CSS, HTMX, public subject metadata, a Library manifest and
PUBLIC_BUILD papers/schemes. No thumbnails are required for the v2 table.

## Open decisions

1. Title: plain **Mock Paper Generator** vs a named product.
2. Subject stubs: CSC580 Software Engineering and CSC645 Data Security.
3. Library: text filter plus computed/placeholder selects; confirm whether a
   mode filter is also needed.
4. Gallery: text table only, no thumbnails.
5. Generation: plain job table, no animation (v2 recommendation).
