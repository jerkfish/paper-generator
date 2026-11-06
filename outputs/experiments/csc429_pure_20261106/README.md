# CSC429 pure-extraction experiment — test seed 1

This is an isolated experiment. It does **not** modify the production
pipeline, the stopped CSC429 lifecycle, `AGENTS.md`, or
`docs/SUBJECT_PLAYBOOK.md`.

## Strategy

Take the supplied past papers and extract the question in its purest form:

1. **Question with a picture** — A1, A2, A10
2. **Question with a diagram** — A5, A7, A8
3. **Question with a table/formula** — A3, A4, B1 (plus text-only A6, A9)

Rules used:

- If the question can be recreated accurately, it is native Word text:
  A3's 40-bit string, A4/A6 formulas, A9 text, and B1's instruction table.
- If the question refers to a picture/diagram, the original region is cropped
  from the source page at 300 dpi. The caption is native text below the crop,
  not baked into the image.
- A1/A2 use native snippet text plus the original portrait/photo crop, so the
  question text stays searchable and the picture remains original.
- B1's formula is captured because its OCR is ambiguous; its instruction table
  is recreated natively.
- Every asset has its source page, PDF bounding box, SHA-256 and OCR text in
  `asset_manifest.json`.

## Outputs

- `seed_01/paper.docx` / `seed_01/paper.pdf` — 8 pages
- `seed_01/scheme.docx` / `seed_01/scheme.pdf` — 11 pages
- `comparison_report.md` — slot-by-slot extraction record
- `comparisons.pdf` — source crop vs generated paper page, plus B1 table
- `asset_manifest.json` — crop provenance and OCR
- `questions.json` — curated question bank for this seed
- `answers.json` — reference answers and marking points
- `run_manifest.json` — page counts and cost

## Refinements in this revision

- Figure widths are set per question instead of one full-width default:
  A1 8 cm, A2 7 cm, A5 12 cm, A7 full width (16.2 cm), A8 10 cm, A10 7 cm, B1 10 cm.
- `(N marks)` is right-tabbed to the right margin in both paper and scheme.
- The scheme no longer prints the question body; it keeps the question number,
  source page, reference answer and marking points only.

## Review checklist

1. Open `seed_01/paper.pdf` and check A1/A2 portrait snapshots, A5 nested
   interrupts, A7 SISD, A8 NUMA, A10 USB icon, and B1 formula/table.
2. Open `comparisons.pdf` for the direct source-vs-generated comparison.
3. Check A3's bit string and B1's native instruction table against the source.
4. Review `answers.json` and the scheme. Answers are **reference answers**,
   not official UTM marking schemes.
5. Check pagination: no figure caption should be separated from its figure.

## Cost and scope

- Questions: 11, all from the supplied papers.
- Asset-bearing questions: 7 (3 pictures, 3 diagrams, 1 formula figure).
- Native table: 1. Native formula/bit-string questions: 3.
- Answer generation: DeepSeek Flash, 13 calls, **$0.010906** actual estimated
  cost.
- No publication, upload or deployment was performed.
