# Marking-scheme table fit fix

## Usable width

Body section (last section): page width **11,910 twips** minus left margin
**1,280** and right margin **1,320** = **9,310 twips**.

The cover section is 9,390 twips; scheme tables use the body section.

## Geometry applied to every table

- `tblW` = 9,310 dxa; `tblInd` = 0; `tblLayout` = fixed.
- `tblGrid` columns sum to exactly 9,310.
- Every `tcW` equals its column width.
- Columns (Chunk folded into Source as a second line):

| Column | Share | Twips |
|---|---:|---:|
| No. | 6% | 559 |
| Point | 30% | 2,793 |
| Evidence quote | 27% | 2,514 |
| Source + chunk ID | 16% | 1,490 |
| Verdict | 12% | 1,117 |
| Overlap | 9% | 837 |

- Table body font: **8 pt**.
- Chunk IDs get a zero-width space after every `::` and `-`, so long
  identifiers wrap instead of widening the table.
- Header row repeats on every page (`tblHeader`); every row has `cantSplit`.

## Automated checks

`src/assemble/table_fit.py` checks every `gridCol` sum against the body usable
width. `src/assemble/scheme_qa.py` exports the scheme with Word COM and
LibreOffice headless, renders each PDF at 200 dpi, and scans pixels to the right
of the right margin. It raises `SchemeQAError` on failure, so
`build_docx_scheme_04` and the Library prebuild fail the build.

```text
usable_width_twips=9310; tables=23; grid_sums=[9310]
scheme QA passed: grid widths and Word/LibreOffice margins
```

The pixel scan uses a 6 px tolerance at 200 dpi (0.03 in) for the cover's
decorative frame and antialiasing; the table grid check is exact.

## Regeneration

- `outputs/mock_scheme_04.docx` / `.pdf` regenerated.
- Every prebuilt Library scheme is regenerated from stored plan/theory JSON
  with `uv run python -m src.app.prebuild_library --seeds 1-20 --schemes-only`
  (no LLM calls).
- All **20/20** Library schemes pass the Word + LibreOffice QA
  (`outputs/library_scheme_qa.log`); every grid sum is exactly 9,310 twips.

## Visual check

- `outputs/scheme_page3.png` - page 3 (normal table).
- `outputs/scheme_page5.png` - page 5 (long access-control table; header row
  repeats and rows do not split).
