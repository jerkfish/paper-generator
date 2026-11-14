"""V3 scaling check for approved ICT450 assets.

The paper template is A4 with a 16.56 cm content width.  Every approved
diagram, figure, table and recreation is measured and given a display size
that preserves its aspect ratio, fits the page and stays readable.  Native
tables render at full content width.

Run:
    uv run python -m src.subjects.ict450.scaling
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from PIL import Image

from src import config
from src.bank.store import BankStore, save_json
from src.subjects.ict450.papers import SUBJECT
from src.subjects.ict450.review import (MANUAL_RECREATIONS, print_pdf,
                                        trim_png)

TRACKING = config.TRACKING_DIR / "ict450" / "v2"
BANK = TRACKING / "bank"
REVIEW = BANK / "review"
FORMAT = TRACKING / "format_profile.json"
SCALING_JSON = BANK / "asset_scaling.json"
SCALING_MD = BANK / "asset_scaling.md"
SCALING_HTML = REVIEW / "scaling_check.html"
SCALING_PDF = REVIEW / "scaling_check.pdf"
MANUAL_DIR = REVIEW / "manual_recreations"

CONTENT_WIDTH_CM = 16.56
CONTENT_HEIGHT_CM = 24.32
MAX_ASSET_HEIGHT_CM = 18.0
MIN_ASSET_WIDTH_CM = 6.0
DPI = 300.0


def format_profile() -> dict:
    return {
        "schema_version": 2,
        "subject": SUBJECT,
        "paper": {
            "size": "A4",
            "width_cm": 21.01,
            "height_cm": 29.72,
            "content_width_cm": CONTENT_WIDTH_CM,
            "content_height_cm": CONTENT_HEIGHT_CM,
            "margins_cm": {"left": 2.15, "right": 2.29,
                           "top": 2.40, "bottom": 3.00},
        },
        "duration": "3 hours",
        "sections": [{"key": "Q", "questions": 5, "marks_per_slot": 20}],
        "total_marks": 100,
        "numbering": {
            "question": "QUESTION n",
            "subparts": "a), b), c)",
            "nested": "i), ii)",
        },
        "assets": {
            "min_width_cm": MIN_ASSET_WIDTH_CM,
            "max_width_cm": CONTENT_WIDTH_CM,
            "max_height_cm": MAX_ASSET_HEIGHT_CM,
            "source_dpi": DPI,
        },
        "templates": {
            "paper": "data/reference/ICT450/ICT450 TEMPLATE.docx",
            "scheme": "data/reference/standard/"
                      "UTM_STANDARD_MARKING_SCHEME.docx",
            "status": "unverified_owner_confirmation_pending",
        },
        "marks_basis": (
            "Five questions, 20 marks each. Eight of twelve papers extract "
            "exactly 100; four had a missing mark line and the owner approved "
            "the question records after review."),
        "source": "12 ICT450 papers, V1 dossiers and the approved bank",
    }


def _png_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def _fit(width_cm: float, height_cm: float) -> tuple[float, float, str, bool]:
    """Fit an asset into the content box, preserving its aspect ratio."""
    scaled_w, scaled_h = width_cm, height_cm
    capped = "none"
    if scaled_w > CONTENT_WIDTH_CM:
        factor = CONTENT_WIDTH_CM / scaled_w
        scaled_w, scaled_h = scaled_w * factor, scaled_h * factor
        capped = "width"
    if scaled_h > MAX_ASSET_HEIGHT_CM:
        factor = MAX_ASSET_HEIGHT_CM / scaled_h
        scaled_w, scaled_h = scaled_w * factor, scaled_h * factor
        capped = "height" if capped == "none" else "width+height"
    upscaled = False
    if scaled_w < MIN_ASSET_WIDTH_CM:
        factor = MIN_ASSET_WIDTH_CM / scaled_w
        if scaled_h * factor <= MAX_ASSET_HEIGHT_CM:
            scaled_w, scaled_h = scaled_w * factor, scaled_h * factor
            upscaled = True
    return (round(scaled_w, 2), round(scaled_h, 2), capped, upscaled)


def _native_columns(asset: dict) -> int:
    from src.subjects.ict450.bank_build import html_rows
    rows = html_rows(asset.get("mineru_table_html") or "")
    return max((len(row) for row in rows), default=0)


def render_manual_png(asset: dict) -> Path | None:
    fragment = MANUAL_RECREATIONS.get(str(asset.get("id")))
    if not fragment:
        return None
    target = MANUAL_DIR / f"{asset['id']}.png"
    if target.is_file():
        return target
    MANUAL_DIR.mkdir(parents=True, exist_ok=True)
    document = f"""<!doctype html><html><head><meta charset="utf-8">
<style>
body {{ font-family: Arial, sans-serif; margin: 0; padding: 8px; }}
table.rec-table {{ border-collapse: collapse; width: 100%; font-size: 11pt; }}
table.rec-table td, table.rec-table th {{ border: 1px solid #000;
  padding: 4px; vertical-align: top; }}
table.rec-table.small {{ font-size: 9pt; }}
.center {{ text-align: center; }}
.schema {{ border: 1px solid #000; padding: 8mm; font-family: "Courier New",
  monospace; font-size: 11pt; }}
</style></head><body>{fragment}</body></html>"""
    source = MANUAL_DIR / f"{asset['id']}.html"
    source.write_text(document, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1000, "height": 900},
                                device_scale_factor=2)
        page.goto(source.resolve().as_uri())
        page.wait_for_timeout(200)
        page.screenshot(path=str(target), full_page=True)
        browser.close()
    trim_png(target)
    return target


def compute() -> dict:
    store = BankStore(BANK)
    rows = []
    for asset in store.assets():
        if asset.get("merged_into") or asset.get("superseded_by"):
            continue
        if asset.get("status") is not None and asset.get("status") != "approved":
            continue
        if asset.get("verdict") not in {None, "approved"}:
            continue
        aid = str(asset["id"])
        treatment = str(asset.get("selected_treatment") or "crop")
        record = {
            "id": aid,
            "source_paper": asset.get("source_paper"),
            "kind": asset.get("kind"),
            "label": asset.get("label"),
            "treatment": treatment,
        }
        if treatment == "native_table":
            columns = _native_columns(asset)
            record.update({
                "mode": "native_table",
                "display_width_cm": CONTENT_WIDTH_CM,
                "display_height_cm": None,
                "columns": columns,
                "status": "ok",
                "warnings": ([f"{columns} columns may be cramped at "
                              f"{CONTENT_WIDTH_CM} cm"] if columns > 8 else []),
            })
            rows.append(record)
            continue
        image_path = None
        if asset.get("owner_recreation_file"):
            image_path = REVIEW / "owner_recreations" / Path(
                str(asset["owner_recreation_file"])).with_suffix(".png")
        elif treatment == "html_recreation":
            image_path = render_manual_png(asset)
        elif asset.get("crop_path"):
            image_path = Path(str(asset["crop_path"]))
        if image_path is None or not image_path.is_file():
            record.update({"mode": "missing", "status": "warning",
                           "warnings": ["no image source"]})
            rows.append(record)
            continue
        width_px, height_px = _png_size(image_path)
        natural_w = width_px / DPI * 2.54
        natural_h = height_px / DPI * 2.54
        if asset.get("owner_recreation_file") or treatment == "html_recreation":
            start_w = CONTENT_WIDTH_CM
            start_h = start_w * height_px / width_px
        else:
            start_w, start_h = natural_w, natural_h
        display_w, display_h, capped, upscaled = _fit(start_w, start_h)
        warnings = []
        if display_w < MIN_ASSET_WIDTH_CM:
            warnings.append("display width below the readable minimum")
        if display_w < 8.0:
            warnings.append("small on the page")
        record.update({
            "mode": "image",
            "source": str(image_path),
            "width_px": width_px,
            "height_px": height_px,
            "natural_cm": [round(natural_w, 2), round(natural_h, 2)],
            "display_width_cm": display_w,
            "display_height_cm": display_h,
            "scale_factor": round(display_w / natural_w, 3)
            if natural_w else None,
            "capped_by": capped,
            "upscaled": upscaled,
            "status": "warning" if warnings else "ok",
            "warnings": warnings,
        })
        rows.append(record)
        asset["width_px"] = width_px
        asset["height_px"] = height_px
        asset["display_width_cm"] = display_w
        asset["display_height_cm"] = display_h
        save_json(store.asset_path(aid), asset)
    summary = {
        "subject": SUBJECT,
        "content_width_cm": CONTENT_WIDTH_CM,
        "content_height_cm": CONTENT_HEIGHT_CM,
        "max_asset_height_cm": MAX_ASSET_HEIGHT_CM,
        "assets": len(rows),
        "ok": sum(1 for row in rows if row["status"] == "ok"),
        "warnings": sum(1 for row in rows if row["status"] == "warning"),
        "native_tables": sum(1 for row in rows
                             if row["mode"] == "native_table"),
        "images": sum(1 for row in rows if row["mode"] == "image"),
        "rows": rows,
    }
    save_json(FORMAT, format_profile())
    save_json(SCALING_JSON, summary)
    return summary


def build_html(summary: dict) -> Path:
    blocks = []
    for row in summary["rows"]:
        label = html.escape(str(row.get("label") or row["id"]))
        if row["mode"] == "native_table":
            asset = json.loads((BANK / "assets" / f"{row['id']}.json")
                               .read_text(encoding="utf-8"))
            body = (f'<div class="rec-html">'
                    f'{asset.get("mineru_table_html") or ""}</div>')
            dims = f"native table · {row.get('columns', 0)} columns"
        elif row["mode"] == "image":
            src = Path(row["source"]).resolve().as_uri()
            body = (f'<img src="{src}" style="width:{row["display_width_cm"]}cm;'
                    f'height:auto;">')
            dims = (f'{row["display_width_cm"]} × {row["display_height_cm"]} cm '
                    f'(natural {row["natural_cm"][0]} × '
                    f'{row["natural_cm"][1]} cm)')
        else:
            body = "<p class='warn'>No image source.</p>"
            dims = "missing"
        warn = ""
        if row.get("warnings"):
            warn = ("<p class='warn'>" + "; ".join(row["warnings"]) + "</p>")
        blocks.append(f"""
        <section class="asset">
          <h2>{row['id']} — {label}</h2>
          <p class="meta">{html.escape(str(row.get("kind")))} ·
            {html.escape(row["treatment"])} · {dims}</p>
          {warn}
          <div class="page-box">{body}</div>
        </section>
        """)
    page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>ICT450 — asset scaling check</title>
<style>
@page {{ size: A4 portrait; margin: 12mm; }}
body {{ font-family: Arial, sans-serif; font-size: 10pt; }}
h1 {{ font-size: 18pt; }}
h2 {{ font-size: 12pt; margin: 0 0 1mm; }}
.meta {{ color: #444; margin: 0 0 2mm; }}
.intro {{ page-break-after: always; }}
.asset {{ page-break-after: always; }}
.page-box {{ width: {CONTENT_WIDTH_CM}cm; height: {CONTENT_HEIGHT_CM}cm;
  border: 1px dashed #999; padding: 4mm; box-sizing: border-box;
  display: flex; align-items: flex-start; justify-content: center;
  overflow: hidden; }}
.rec-html table {{ border-collapse: collapse; width: 100%; font-size: 8pt; }}
.rec-html td, .rec-html th {{ border: 1px solid #000; padding: 1mm; }}
img {{ max-width: 100%; }}
.warn {{ color: #8a1f1f; }}
</style></head><body>
<section class="intro">
<h1>ICT450 — asset scaling check</h1>
<p>A4 content box: {CONTENT_WIDTH_CM} × {CONTENT_HEIGHT_CM} cm. Each asset is
shown at the size it will use in the paper. {summary['assets']} assets;
{summary['warnings']} warnings.</p>
</section>
{''.join(blocks)}
</body></html>"""
    SCALING_HTML.write_text(page, encoding="utf-8")
    return SCALING_HTML


def build_markdown(summary: dict) -> Path:
    lines = [
        "# ICT450 — asset scaling",
        "",
        f"Content box: **{CONTENT_WIDTH_CM} × {CONTENT_HEIGHT_CM} cm**.",
        f"Assets: {summary['assets']} · ok: {summary['ok']} · "
        f"warnings: {summary['warnings']} · native tables: "
        f"{summary['native_tables']} · images: {summary['images']}.",
        "",
        "| Asset | Kind | Treatment | Display | Status |",
        "|---|---|---|---|---|",
    ]
    for row in summary["rows"]:
        if row["mode"] == "native_table":
            display = f"{row['display_width_cm']} cm wide"
        elif row["mode"] == "image":
            display = (f"{row['display_width_cm']} × "
                       f"{row['display_height_cm']} cm")
        else:
            display = "missing"
        lines.append(
            f"| {row['id']} | {row.get('kind')} | {row['treatment']} | "
            f"{display} | {row['status']} |")
    lines += ["", "## Warnings", ""]
    warnings = [row for row in summary["rows"] if row.get("warnings")]
    if not warnings:
        lines.append("None.")
    for row in warnings:
        lines.append(f"- `{row['id']}`: " + "; ".join(row["warnings"]))
    SCALING_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return SCALING_MD


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-pdf", action="store_true")
    args = parser.parse_args()
    summary = compute()
    build_html(summary)
    build_markdown(summary)
    print(json.dumps({key: summary[key] for key in
                      ("assets", "ok", "warnings", "native_tables", "images")},
                     indent=2))
    print(SCALING_HTML)
    print(SCALING_MD)
    if not args.no_pdf:
        print(print_pdf(SCALING_HTML, SCALING_PDF))


if __name__ == "__main__":
    main()
