# CSC429 pure-extraction comparison report

- Test seed: **1**
- Paper: **8 pages**, scheme: **11 pages**
- Questions: **11 real past-paper questions**
- Assets: **7** (3 pictures, 3 diagrams, 1 formula figure)
- Native recreations: 1 instruction table, 3 formula/bit-string questions
- Answer model: DeepSeek Flash, **13 calls**, **$0.010906**
- Pipeline/lifecycle/playbook: not modified
- Visual comparison: `comparisons.pdf`

One test seed. Each question is copied from the named source paper; figures are cropped from the source page; captions are native text; tables are native Word tables.

| Slot | Source | Marks | Content | Asset verification |
|---|---|---:|---|---|
| A1 | CSC429-2019-12 p2 | 5 | picture 946x475px | asset SHA recorded in asset_manifest.json |
| A2 | CSC429-2019-06 p2 | 5 | picture 500x396px | asset SHA recorded in asset_manifest.json |
| A3 | CSC429-2025-02 p2 | 5 | native bit string | native text; no asset |
| A4 | CSC429-2023-07 p2 | 5 | native text | native text; no asset |
| A5 | CSC429-2026-02 p3 | 10 | diagram 1667x816px | asset SHA recorded in asset_manifest.json |
| A6 | CSC429-2024-07 p3 | 10 | native text | native text; no asset |
| A7 | CSC429-2023-02 p5 | 10 | diagram 1270x229px | asset SHA recorded in asset_manifest.json |
| A8 | CSC429-2023-07 p5 | 10 | diagram 1438x1021px | asset SHA recorded in asset_manifest.json |
| A9 | CSC429-2025-02 p4 | 10 | native text | native text; no asset |
| A10 | CSC429-2024-07 p4 | 10 | picture 792x292px | asset SHA recorded in asset_manifest.json |
| B1 | CSC429-2026-02 p6 | 20 | formula 771x196px, native table | asset SHA recorded in asset_manifest.json |

## Source and extraction notes

- A1/A2 use native snippet text plus a captured portrait/photo; the picture is not OCR-dependent.
- A3's 40-bit string is native text, not an image.
- A4/A6 formulas are native text with Unicode subscripts.
- A5/A7/A8/B1 figures are cropped from the source page at 300 dpi; captions are native text below the image. A9 is text-only.
- B1's instruction table is recreated as a native Word table from the source layout.

