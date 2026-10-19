"""Pixel-faithful cover page for the mock paper.

Geometry was measured from data/reference/cover_feb2026.jpg via WinRT OCR
word bounding boxes (see src/assemble/ocr_boxes.ps1). The cover is rendered
in a 1654x2340 viewport (the reference scan size) with absolute positioning;
comparison anchors are re-measured on the rendered PNG and reported.

The real crest is cropped from the reference scan (local personal use);
USE_REAL_CREST=False renders a generic placeholder instead.
"""
from __future__ import annotations

import html
import subprocess
import tempfile

from PIL import Image

from src.config import CREST_PATH, USE_REAL_CREST

REF_SIZE = (1654, 2340)

# measured anchors on the reference cover (x, y, [right edge])
ANCHORS = {
    "confidential": (199, 204),
    "refcode_right": (1440, 204),
    "crest_box": (490, 233, 1160, 340),
    "title": (574, 390),
    "final_exam": (654, 434),
    "course_label_x": 233,
    "course_value_x": 597,
    "course_rows_y": (594, 654, 715, 776),
    "course_box": (205, 570, 990, 815),
    "instructions": (198, 936),
    "item_num_x": 196,
    "item_text_x": 277,
    "item_y": (1000, 1096, 1192, 1288, 1448),
    "subitem_x": (312, 402),
    "dont_turn_y": 2021,
    "pages_y": 2069,
    "copyright_y": 2121,
}


def _crest_html() -> str:
    if USE_REAL_CREST and CREST_PATH.exists():
        return (f'<img src="file:///{str(CREST_PATH).replace(chr(92), "/")}" '
                f'style="position:absolute; left:{ANCHORS["crest_box"][0]}px; '
                f'top:{ANCHORS["crest_box"][1]}px; '
                f'width:{ANCHORS["crest_box"][2] - ANCHORS["crest_box"][0]}px;">')
    return ('<div style="position:absolute; left:490px; top:233px; width:670px; '
            'height:107px; border:1px dashed #999; text-align:center; '
            'line-height:100px; color:#999; font-size:12px;">'
            '[university crest placeholder]</div>')


def build_cover_html(paper_pages: int = 6) -> str:
    ref = f"CS/MOCK OCT 2026/CSC662"
    crest = _crest_html()
    box = ANCHORS["course_box"]
    labels = ["COURSE", "COURSE CODE", "EXAMINATION", "TIME"]
    values = ["COMPUTER SECURITY", "CSC662", "OCTOBER 2026 (MOCK)", "3 HOURS"]
    rows = ""
    for (label, value), y in zip(zip(labels, values), ANCHORS["course_rows_y"]):
        # coordinates relative to the box (its origin is ANCHORS course_box[0:2])
        rows += (f'<div style="position:absolute; '
                 f'left:{ANCHORS["course_label_x"] - box[0]}px; '
                 f'top:{y - 3 - box[1]}px; font-weight:bold; font-size:16px; '
                 f'font-family:Arial;">{label}</div>'
                 f'<div style="position:absolute; '
                 f'left:{ANCHORS["course_value_x"] - box[0]}px; '
                 f'top:{y - 3 - box[1]}px; font-weight:bold; font-size:16px; '
                 f'font-family:Arial;">{value}</div>')

    items_html = ""
    item1 = ("This question paper consists of two (2) parts: PART A (10 Questions)"
             '<br/><span style="padding-left:582px;">PART B (2 Questions)</span>')
    items = [
        ("1.", item1),
        ("2.", "Answer ALL questions in the Answer Booklet. Start each answer on a "
         "new page."),
        ("3.", "Do not bring any material into the examination room unless "
         "permission is given by the invigilator."),
        ("4.", 'Please check to make sure that this examination pack consists of:'
               '<br/><span style="padding-left:35px;">i) the Question Paper</span>'
               '<br/><span style="padding-left:35px;">ii) an Answer Booklet - '
               'provided by the Faculty</span>'),
        ("5.", "Answer ALL questions in English."),
    ]
    item_ys = ANCHORS["item_y"]
    for (num, text), y in zip(items, item_ys):
        items_html += (f'<div style="position:absolute; left:{ANCHORS["item_num_x"]}px; '
                       f'top:{y - 3}px; font-size:14px; font-family:Arial;">{num}</div>'
                       f'<div style="position:absolute; left:{ANCHORS["item_text_x"]}px; '
                       f'top:{y - 3}px; font-size:14px; line-height:1.35; '
                       f'font-family:Arial;">{text}</div>')

    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>body {{ margin:0; background:#fff; }} p {{ margin:0; }}</style></head>
<body style="width:1654px; height:2340px;">
<div style="position:absolute; left:{ANCHORS['confidential'][0]}px;
 top:{ANCHORS['confidential'][1] - 3}px; font-weight:bold; font-size:15px;
 font-family:Arial; letter-spacing:1px;">CONFIDENTIAL</div>
<div style="position:absolute; left:1157px; top:{ANCHORS['confidential'][1] - 3}px;
 width:{ANCHORS['refcode_right'][0] - 1157}px; text-align:right; font-weight:bold;
 font-size:15px; font-family:Arial;">{ref}</div>
{crest}
<div style="position:absolute; left:200px; top:346px; width:1254px;
 border-top:1px solid #000;"></div>
<div style="position:absolute; left:550px; top:{ANCHORS['title'][1] - 3}px; width:499px;
 text-align:center; font-weight:bold; font-size:19px;
 font-family:Arial;">UNIVERSITI TEKNOLOGI MARA</div>
<div style="position:absolute; left:626px; top:{ANCHORS['final_exam'][1] - 3}px;
 width:338px; text-align:center; font-weight:bold; font-size:19px;
 font-family:Arial;">FINAL EXAMINATION</div>
<div style="position:absolute; left:200px; top:465px; width:1254px;
 border-top:1px solid #000;"></div>
<div style="position:absolute; left:{box[0]}px; top:{box[1]}px;
 width:{box[2] - box[0]}px; height:{box[3] - box[1]}px; border:3px solid #000;
 font-family:Arial;">
  <div style="position:absolute; left:5px; top:5px; right:5px; bottom:5px;
   border:1px solid #000;"></div>
  {rows}
</div>
<div style="position:absolute; left:{ANCHORS['instructions'][0]}px;
 top:{ANCHORS['instructions'][1] - 3}px; font-weight:bold; font-size:15px;
 text-decoration:underline; font-family:Arial;">INSTRUCTIONS TO CANDIDATES</div>
{items_html}
<div style="position:absolute; left:200px; top:1960px; width:1254px;
 border-top:1px solid #000;"></div>
<div style="position:absolute; left:422px; top:{ANCHORS['dont_turn_y'] - 3}px;
 width:794px; text-align:left; font-weight:bold; font-size:15px;
 font-family:Arial;">DO NOT TURN THIS PAGE UNTIL YOU ARE TOLD TO DO SO</div>
<div style="position:absolute; left:200px; top:2050px; width:1254px;
 border-top:1px solid #000;"></div>
<div style="position:absolute; left:510px; top:{ANCHORS['pages_y'] - 3}px;
 width:634px; text-align:center; font-style:italic; font-size:13px;
 font-family:Arial;">This examination paper consists of {paper_pages} printed
 pages</div>
<div style="position:absolute; left:200px; top:{ANCHORS['copyright_y'] - 3}px;
 font-size:12px; font-family:Arial;">(c) Hak Cipta Universiti Teknologi MARA</div>
<div style="position:absolute; left:1230px; top:{ANCHORS['copyright_y'] - 3}px;
 width:208px; text-align:right; font-weight:bold; font-size:13px;
 font-family:Arial;">CONFIDENTIAL</div>
</body></html>"""


def render_cover_png(page_html: str, out_path) -> None:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page(viewport={"width": 1654, "height": 2340},
                                device_scale_factor=1)
        page.set_content(page_html, wait_until="load")
        page.screenshot(path=str(out_path), full_page=True)
        browser.close()


def ocr_boxes(image_path: str) -> list[tuple[str, int, int, int, int]]:
    from pathlib import Path

    ps1 = Path(__file__).with_name("ocr_boxes.ps1")
    abs_path = str(Path(image_path).resolve())  # WinRT needs an absolute path
    proc = subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(ps1), abs_path],
        capture_output=True, timeout=180)
    out = []
    for line in proc.stdout.decode("utf-8", errors="replace").splitlines():
        parts = line.split("|")
        if len(parts) == 5:
            out.append((parts[0], int(parts[1]), int(parts[2]),
                        int(parts[3]), int(parts[4])))
    return out


def compare_anchors(mine_path, reference_path) -> str:
    """OCR both covers and report anchor deltas for the iteration loop."""
    ref = ocr_boxes(reference_path)
    mine = ocr_boxes(mine_path)

    def find(words, target, mode="first"):
        hits = [(x, y, w) for (t, x, y, w, h) in words
                if target.lower() in t.lower()]
        if not hits:
            return None
        if mode == "footer":
            return next((h for h in hits if h[1] > 1900), None)
        if mode == "in_title_band":
            return next((h for h in hits if 370 <= h[1] <= 500), None)
        if mode == "in_box_band":
            return next((h for h in hits if 550 <= h[1] <= 850), None)
        if mode == "topband_last":
            return max((h for h in hits if h[1] < 300), key=lambda h: h[0] + h[2],
                       default=None)
        return hits[0]

    def right_edge(hit):
        return (hit[0] + hit[2], hit[1])

    rows = []
    for label, ref_word, my_word, mode in [
        ("CONFIDENTIAL (top-left)", "CONFIDENTIAL", "CONFIDENTIAL", "first"),
        ("ref code (right edge)", "CSC662", "CSC662", "topband_last"),
        ("title", "TEKNOLOGI", "TEKNOLOGI", "in_title_band"),
        ("FINAL EXAMINATION", "EXAMINATION", "EXAMINATION", "in_title_band"),
        ("course label", "COURSE", "COURSE", "in_box_band"),
        ("instructions", "INSTRUCTIONS", "INSTRUCTIONS", "first"),
        ("DO NOT TURN (footer)", "DO", "DO", "footer"),
        ("copyright", "Hak", "Hak", "first"),
    ]:
        r = find(ref, ref_word, mode)
        m = find(mine, my_word, mode)
        if label.startswith("ref code"):
            rr, mm = right_edge(r) if r else None, right_edge(m) if m else None
            if rr and mm:
                rows.append(f"  {label:24} ref_right=({rr[0]},{rr[1]}) "
                            f"mine_right=({mm[0]},{mm[1]}) "
                            f"dx={mm[0]-rr[0]:+d} dy={mm[1]-rr[1]:+d}")
                continue
        if r and m:
            rows.append(f"  {label:24} ref=({r[0]},{r[1]}) mine=({m[0]},{m[1]}) "
                        f"dx={m[0]-r[0]:+d} dy={m[1]-r[1]:+d}")
        else:
            rows.append(f"  {label:24} ref={'ok' if r else 'MISSING'} "
                        f"mine={'ok' if m else 'MISSING'}")
    return "\n".join(rows)


def side_by_side(mine_path, reference_path, out_path, overlay_path) -> None:
    ref = Image.open(reference_path).convert("RGB")
    mine = Image.open(mine_path).convert("RGB").resize(ref.size)
    gap = 20
    canvas = Image.new("RGB", (ref.width * 2 + gap, ref.height), "white")
    canvas.paste(ref, (0, 0))
    canvas.paste(mine, (ref.width + gap, 0))
    canvas.save(out_path)
    blend = Image.blend(ref, mine, alpha=0.45)
    blend.save(overlay_path)
