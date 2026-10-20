# Theory quality pass and formatting pass

This pass changed only the theory/verification pipeline and the paper-03 formatting; paper 02 remains as delivered.

## 1. Source overlap

- The unit of overlap is `(deck, slide)`. Retrieval excludes slides already cited by earlier accepted questions; if fewer than three unused chunks remain, it fills from unused chunks in the allowed decks before allowing any overlap.
- Each slot gets its own evidence pool; the higher-mark slot in a pair reserves its slides first. A verifier rejects a chunk that belongs to the other slot's pool or a slide already used by another accepted question.
- Seed 9: **0** overlapping keys across 44 distinct keys (target 0).
- Seeds 1-20: **0** overlapping keys across 0/20 papers; target 0. Full per-seed detail is in `outputs/eval_realistic.md`.

## 2. Topic-source consistency

The `TOPIC_DECKS` allow-list is enforced in the verifier (for example, ethics may cite only deck 071; classical ciphers only deck 031). A question whose cited deck is outside its slot topic's allow-list is rejected. The eval report computes the actual topic mix from cited decks, and compares it with the planner's planned marks.

Seed 9 planned vs actual (marks): access control models: 8 -> 8; attacks/malware: 24 -> 2; authentication/biometrics: 18 -> 18; classical ciphers: 0 -> 2; network security: 8 -> 10; risk/management (ethics): 16 -> 16; software/OS security: 8 -> 28; trusted computing/blockchain: 10 -> 10. The large attack/software shift is because attack questions cite software/web decks (051/052), which the deck-topic map classifies as software/OS security.

## 3. Part B

Measured from the clean modern papers with explicit A/B rows: **7/19** Part B questions have a scenario paragraph in the (a) stem, **11/19** (a)/(b) pairs share a topic, and **2/19** explicitly refer back to (a)/the above. The method is documented in `outputs/planner_measurements.md`; the 2023-02 Ali scenario may be in an unlogged paragraph, so scenario detection is a lower bound.

Part B now generates a short shared scenario grounded in the cited slides. B1a/B1b and B2a/B2b use the same scenario in paper 03; marking points still come from slide quotes. Part B topics are sampled by their measured marks weights, not fixed to the top two.

Seed 9 generated **2** shared scenarios: B1a grounding 0.54; B1b reuses (a); B2a grounding 0.32; B2b reuses (a).

The command mapping now includes **Propose** (propose/recommend/suggest) and **Analyse** (analyse/analyze/critically); they are no longer dropped into `Other`.

## 4. Marking-point quality

- Slide-title-only quotes are rejected.
- Each quote must share a key term with its point; the term-overlap score is stored per point and shown in scheme 03. Low scores are flagged, not silently treated as strong evidence.
- Seed 9: **30** low term-overlap points, **15** short quotes and **0** repaired quotes. Repairs only replace a paraphrase with an exact nearby line from the same cited chunk.

## 5. Style-confidence report

The planner table now reports both **exact style n** and **used style n**; low-confidence slots are still those with exact n<3, but the used count (3-5 after widening) is visible in the same row.

## 6. Evaluation (seeds 1-20)

- Theory slots: 464; accepted **448**; placeholders **16** (3.4%).
- Source overlap: **0** keys across 0/20 papers (target 0).
- Maximum near-copy similarity: **0.78** (threshold 0.80).
- Calls: 564; tokens: 2115646; estimated total cost: **$0.0892**; cost per accepted question: **$0.0002**.
- Low term-overlap points flagged: 694; Part B scenario questions generated: 70.
- Full per-seed table, computed-mark distribution, attempts, topic mix and costs: `outputs/eval_realistic.md`.

## 7. Formatting pass against the manually revised mock

The manual revision was compared at paragraph/run level. The substantive formatting changes were:

- bold running header (`CONFIDENTIAL ... CS/MOCK OCT 2026/CSC662`);
- bold `PART A` / `PART B` / `QUESTION n` / `END OF QUESTION PAPER` headings;
- 1.5 line spacing for the body paragraphs from PART A onward;
- a blank line after each PART heading and after the Vigenere tableau.

These are applied in `mock_paper_03.docx` / `.pdf` (5 pages); the scheme is 16 pages. The manual scheme had no material type-size change beyond the labels; scheme 03 adds the required methods note, the supported-by label and the term-overlap column.

## 8. Seed-9 paper/scheme

- `outputs/mock_paper_03.docx` / `.pdf`
- `outputs/mock_scheme_03.docx` / `.pdf`
- Seed 9: 23/23 theory answers accepted, 0 placeholders, 0 source overlap; the computed Vigenere question still prints the tableau.
- Scheme theory headers read **supported by lecture slides (not lecturer-marked)** and every marking point shows quote, source and term overlap; low overlaps are marked LOW.

## Files

- `outputs/eval_realistic.md` - evaluation report (primary).
- `outputs/eval_realistic/` - per-seed planner/theory JSON and Markdown.
- `outputs/mock_paper_03.docx` / `.pdf`
- `outputs/mock_scheme_03.docx` / `.pdf`
- `outputs/planner_measurements.md` - updated labels and Part B scenario measurement.
- `outputs/quality_pass_report.md` - this summary.

## Caveats

- Source overlap is reported at slide level, stricter than exact chunk-id reuse.
- Actual topic mix is inferred from a primary deck-topic map; a deck used by more than one topic can shift the actual mix.
- Low term-overlap points are flagged for human review, not automatically rejected.
- Cost uses the public qwen-flash price as an estimate; the model actually used for the 20-seed eval is recorded in `eval_realistic.md`.
