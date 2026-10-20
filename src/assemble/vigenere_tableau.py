"""Render the 26 x 26 Vigenere tableau printed with computed questions."""
from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    names = ["arialbd.ttf", "arial.ttf", "calibrib.ttf", "calibri.ttf"]
    if bold:
        names = ["arialbd.ttf", "calibrib.ttf", "arial.ttf", "calibri.ttf"]
    for name in names:
        try:
            return ImageFont.truetype(f"C:/Windows/Fonts/{name}", size)
        except Exception:
            continue
    return ImageFont.load_default()


def build_tableau_png(out_path: Path, cell_w: int = 56,
                      cell_h: int = 42) -> Path:
    n = 27  # header row + header column + 26 values
    margin = 6
    title_h = 46
    width = margin * 2 + n * cell_w
    height = margin * 2 + title_h + n * cell_h
    img = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(img)
    font = _font(21)
    header_font = _font(21, bold=True)
    title = "Vigenere tableau (A = 0)"
    tfont = _font(24, bold=True)
    tb = draw.textbbox((0, 0), title, font=tfont)
    draw.text(((width - (tb[2] - tb[0])) / 2, margin + 2), title,
              fill=(20, 25, 30), font=tfont)
    for r in range(n):
        for c in range(n):
            x0 = margin + c * cell_w
            y0 = margin + title_h + r * cell_h
            x1 = x0 + cell_w
            y1 = y0 + cell_h
            is_header = r == 0 or c == 0
            fill = (225, 232, 240) if is_header else "white"
            draw.rectangle([x0, y0, x1, y1], fill=fill,
                           outline=(90, 100, 110), width=1)
            if r == 0 and c == 0:
                label = ""
            elif r == 0:
                label = ALPHABET[c - 1]
            elif c == 0:
                label = ALPHABET[r - 1]
            else:
                label = ALPHABET[(r - 1 + c - 1) % 26]
            if label:
                f = header_font if is_header else font
                bbox = draw.textbbox((0, 0), label, font=f)
                tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
                draw.text((x0 + (cell_w - tw) / 2,
                           y0 + (cell_h - th) / 2 - 1),
                          label, fill=(20, 25, 30), font=f)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path, dpi=(300, 300))
    return out_path


if __name__ == "__main__":
    from src.config import OUTPUTS_DIR
    p = build_tableau_png(OUTPUTS_DIR / "vigenere_tableau.png")
    print(p, Image.open(p).size)
