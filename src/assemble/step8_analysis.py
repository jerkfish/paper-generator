"""Step 8 layout measurements: mock vs the three clean modern papers.

Renders pages 2..N at 200 DPI, measures header/footer ink, question-heading
style, a)/b) numbering, mark-label alignment and spacing, and writes
outputs/step8_layout_metrics.json plus side-by-side question pages.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf
from PIL import Image, ImageDraw, ImageFont

from src.config import OUTPUTS_DIR

PAPERS = {
    "mock": ("outputs/mock_paper_01.pdf", None),
    "JUN2019": ("data/papers/CSC662 JUNE 2019.PDF",
                "data/tracking/ocr_cache/CSC662-2019-06.txt"),
    "DEC2019": ("data/papers/CSC662 DECEMBER 2019.PDF", None),
    "FEB2022": ("data/papers/CSC662 FEBRUARY 2022.pdf", None),
}
PAGE_DIR = OUTPUTS_DIR / "step8_pages"
PAGE_DIR.mkdir(exist_ok=True)
DPI = 200
ZOOM = DPI / 72.0


def render_pages(path: str, name: str) -> list[Path]:
    d = pymupdf.open(path)
    out = []
    for i, page in enumerate(d):
        pix = page.get_pixmap(matrix=pymupdf.Matrix(ZOOM, ZOOM))
        p = PAGE_DIR / f"{name}_p{i + 1}.png"
        pix.save(str(p))
        out.append(p)
    return out


def ink_fraction(png: Path, y0f: float, y1f: float) -> float:
    im = Image.open(png).convert("L")
    w, h = im.size
    import numpy as np
    a = np.asarray(im, dtype=float)
    band = a[int(h * y0f):int(h * y1f), :]
    return float((band < 160).mean())


def text_in_band(page, y0f: float, y1f: float) -> str:
    h = page.rect.height
    clip = pymupdf.Rect(0, h * y0f, page.rect.width, h * y1f)
    return page.get_text("text", clip=clip)


def question_spans(page) -> list[dict]:
    out = []
    d = page.get_text("dict")
    for block in d.get("blocks", []):
        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            text = "".join(s.get("text", "") for s in spans).strip()
            if re.match(r"^QUESTION\s+\d+", text):
                first = spans[0]
                out.append({
                    "text": text,
                    "x0": first["bbox"][0], "y0": first["bbox"][1],
                    "size": max(float(s["size"]) for s in spans),
                    "flags": first["flags"],
                })
    return out


def words_matching(page, pattern: str) -> list[dict]:
    out = []
    for w in page.get_text("words"):
        if re.match(pattern, w[4]):
            out.append({"text": w[4], "x0": w[0], "y0": w[1], "x1": w[2]})
    return out


def ocr_cache_pages(path: str) -> list[str]:
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    parts = re.split(r"===== PAGE \d+ =====", text)
    return [p.strip() for p in parts if p.strip()]


def measure() -> dict:
    result = {}
    for name, (path, ocr_path) in PAPERS.items():
        d = pymupdf.open(path)
        pages = render_pages(path, name)
        n = len(d)
        body_idx = range(1, n)  # pages 2..N
        header_hits = footer_hits = 0
        header_ink, footer_ink, body_ink = [], [], []
        q_sizes, q_bold, q_x = [], [], []
        ab_count = mark_count = 0
        mark_right = []
        question_gap = []
        for i in body_idx:
            page = d[i]
            top = text_in_band(page, 0.0, 0.12)
            bottom = text_in_band(page, 0.88, 1.0)
            if "CONFIDENTIAL" in top and ("CS/" in top or "CS /" in top):
                header_hits += 1
            if "Hak Cipta" in bottom or "CONFIDENTIAL" in bottom:
                footer_hits += 1
            header_ink.append(ink_fraction(pages[i], 0.0, 0.12))
            footer_ink.append(ink_fraction(pages[i], 0.88, 1.0))
            body_ink.append(ink_fraction(pages[i], 0.12, 0.88))
            spans = question_spans(page)
            for s in spans:
                q_sizes.append(round(float(s["size"]), 1))
                q_bold.append(bool(int(s["flags"]) & 16))
                q_x.append(round(float(s["x0"]) / page.rect.width, 4))
            ys = [float(s["y0"]) for s in spans]
            question_gap += [round(ys[j + 1] - ys[j], 1)
                             for j in range(len(ys) - 1)]
            ab_count += len(words_matching(page, r"^[ab]\)$"))
            marks = words_matching(page, r".*marks?\)$")
            mark_count += len(marks)
            mark_right += [round(float(m["x1"]) / page.rect.width, 4)
                           for m in marks]

        ocr = ocr_cache_pages(ocr_path) if ocr_path else []
        ocr_q = sum(len(re.findall(r"\bQUESTION\s+\d+", t)) for t in ocr[1:])
        ocr_ab = sum(len(re.findall(r"(?:^|\s)[ab]\)", t)) for t in ocr[1:])
        ocr_marks = sum(len(re.findall(r"\(\d+\s*marks?\)", t)) for t in ocr[1:])
        if ocr:
            header_hits = sum(1 for t in ocr[1:] if "CONFIDENTIAL" in t
                              and re.search(r"CS[IJ]?/?JUN", t))
            footer_hits = sum(1 for t in ocr[1:] if "CONFIDENTIAL" in t
                              and "Hak Cipta" in t)
        result[name] = {
            "pages": n,
            "page_size_pt": [round(d[0].rect.width, 1), round(d[0].rect.height, 1)],
            "header_pages": f"{header_hits}/{n - 1}" if n > 1 else "0/0",
            "footer_pages": f"{footer_hits}/{n - 1}" if n > 1 else "0/0",
            "header_ink_median": round(float(__import__("numpy").median(header_ink)), 5) if header_ink else None,
            "footer_ink_median": round(float(__import__("numpy").median(footer_ink)), 5) if footer_ink else None,
            "body_ink_median": round(float(__import__("numpy").median(body_ink)), 5) if body_ink else None,
            "question_sizes": sorted(set(q_sizes)),
            "question_bold": f"{sum(q_bold)}/{len(q_bold)}" if q_bold else "n/a",
            "question_x_frac": round(float(__import__("numpy").median(q_x)), 4) if q_x else None,
            "question_gap_median_pt": round(float(__import__("numpy").median(question_gap)), 1) if question_gap else None,
            "ab_count": ab_count,
            "mark_count": mark_count,
            "mark_right_frac_median": round(float(__import__("numpy").median(mark_right)), 4) if mark_right else None,
            "ocr_question_headings": ocr_q if ocr else None,
            "ocr_ab_count": ocr_ab if ocr else None,
            "ocr_mark_count": ocr_marks if ocr else None,
        }
    return result


def side_by_side(left: Path, right: Path, out: Path, left_label: str,
                 right_label: str) -> None:
    a = Image.open(left).convert("RGB")
    b = Image.open(right).convert("RGB")
    # same width, preserve aspect; pad shorter to same height
    width = 1100
    a = a.resize((width, int(a.height * width / a.width)))
    b = b.resize((width, int(b.height * width / b.width)))
    h = max(a.height, b.height)
    gap, label_h = 18, 28
    canvas = Image.new("RGB", (width * 2 + gap, h + label_h), "white")
    canvas.paste(a, (0, label_h))
    canvas.paste(b, (width + gap, label_h))
    d = ImageDraw.Draw(canvas)
    try:
        font = ImageFont.truetype("arial.ttf", 16)
    except Exception:
        font = ImageFont.load_default()
    d.text((4, 4), left_label, fill="black", font=font)
    d.text((width + gap + 4, 4), right_label, fill="black", font=font)
    canvas.save(out)


def main() -> None:
    metrics = measure()
    (OUTPUTS_DIR / "step8_layout_metrics.json").write_text(
        json.dumps(metrics, indent=2), encoding="utf-8")
    for name, m in metrics.items():
        print(f"{name:8} pages={m['pages']} size={m['page_size_pt']} "
              f"hdr={m['header_pages']} ftr={m['footer_pages']} "
              f"ink(h/f/b)={m['header_ink_median']}/{m['footer_ink_median']}/"
              f"{m['body_ink_median']} qsize={m['question_sizes']} "
              f"bold={m['question_bold']} qx={m['question_x_frac']} "
              f"gap={m['question_gap_median_pt']} "
              f"a/b={m['ab_count']} marks={m['mark_count']} "
              f"mark_right={m['mark_right_frac_median']}")
        if m["ocr_question_headings"] is not None:
            print(f"         OCR: q={m['ocr_question_headings']} "
                  f"a/b={m['ocr_ab_count']} marks={m['ocr_mark_count']}")

    side_by_side(PAGE_DIR / "mock_p2.png", PAGE_DIR / "DEC2019_p2.png",
                 OUTPUTS_DIR / "step8_side_by_side.png",
                 "MOCK page 2", "DEC 2019 page 2")
    side_by_side(PAGE_DIR / "mock_p2.png", PAGE_DIR / "JUN2019_p2.png",
                 OUTPUTS_DIR / "step8_side_by_side_jun2019.png",
                 "MOCK page 2", "JUN 2019 page 2")
    side_by_side(PAGE_DIR / "mock_p2.png", PAGE_DIR / "FEB2022_p2.png",
                 OUTPUTS_DIR / "step8_side_by_side_feb2022.png",
                 "MOCK page 2", "FEB 2022 page 2")
    print("wrote step8_layout_metrics.json and side-by-side images")


if __name__ == "__main__":
    main()
