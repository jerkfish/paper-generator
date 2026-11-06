"""Deterministic diagrams for CSC429 diagram questions.

The diagrams use the detailed box-and-arrow style.  Text is measured and
boxes are sized around it; the renderer fails if a label touches a line or a
box, if boxes are cramped, or if content leaves the canvas.
"""
from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 1600
HEIGHT = 1000
MARGIN = 40
PAD = 28
GAP = 44
INK = "#14213D"
FILL = "#E8F0FE"
TEXT = "#111111"
OUTLINE = "#8FA9C9"
FONT_REGULAR = "C:/Windows/Fonts/arial.ttf"
FONT_BOLD = "C:/Windows/Fonts/arialbd.ttf"

FONT_TITLE = 52
FONT_NODE = 44
FONT_DETAIL = 36
FONT_LABEL = 34
LINE_GAP = 8


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    path = FONT_BOLD if bold else FONT_REGULAR
    try:
        return ImageFont.truetype(path, size)
    except OSError:
        return ImageFont.load_default()


def _text_metrics(draw: ImageDraw.ImageDraw, text: str,
                  font: ImageFont.FreeTypeFont) -> tuple[int, int]:
    widths = []
    heights = []
    for line in str(text).split("\n"):
        bbox = draw.textbbox((0, 0), line, font=font)
        widths.append(bbox[2] - bbox[0])
        heights.append(bbox[3] - bbox[1])
    width = max(widths) if widths else 0
    height = sum(heights) + LINE_GAP * max(0, len(heights) - 1)
    return width, height


def _draw_text_center(draw: ImageDraw.ImageDraw,
                      box: tuple[int, int, int, int], text: str,
                      font: ImageFont.FreeTypeFont) -> None:
    left, top, right, bottom = box
    lines = str(text).split("\n")
    sizes = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        sizes.append((bbox[2] - bbox[0], bbox[3] - bbox[1], bbox[1]))
    total = sum(height for _, height, _ in sizes) + LINE_GAP * (
        len(sizes) - 1)
    y = top + (bottom - top - total) / 2
    for line, (width, height, offset) in zip(lines, sizes):
        x = left + (right - left - width) / 2
        draw.text((x, y - offset), line, font=font, fill=TEXT)
        y += height + LINE_GAP


def _rects_overlap(a: tuple[int, int, int, int],
                   b: tuple[int, int, int, int]) -> bool:
    return not (a[2] <= b[0] or b[2] <= a[0]
                or a[3] <= b[1] or b[3] <= a[1])


def _orientation(a: tuple[int, int], b: tuple[int, int],
                 c: tuple[int, int]) -> int:
    value = ((b[0] - a[0]) * (c[1] - a[1])
             - (b[1] - a[1]) * (c[0] - a[0]))
    return (value > 0) - (value < 0)


def _on_segment(a: tuple[int, int], b: tuple[int, int],
                c: tuple[int, int]) -> bool:
    return (min(a[0], b[0]) <= c[0] <= max(a[0], b[0])
            and min(a[1], b[1]) <= c[1] <= max(a[1], b[1]))


def _segments_intersect(a: tuple[int, int], b: tuple[int, int],
                        c: tuple[int, int], d: tuple[int, int]) -> bool:
    o1 = _orientation(a, b, c)
    o2 = _orientation(a, b, d)
    o3 = _orientation(c, d, a)
    o4 = _orientation(c, d, b)
    if o1 != o2 and o3 != o4:
        return True
    return ((o1 == 0 and _on_segment(a, b, c))
            or (o2 == 0 and _on_segment(a, b, d))
            or (o3 == 0 and _on_segment(c, d, a))
            or (o4 == 0 and _on_segment(c, d, b)))


def _segment_intersects_rect(start: tuple[int, int],
                             end: tuple[int, int],
                             rect: tuple[int, int, int, int]) -> bool:
    left, top, right, bottom = rect
    for point in (start, end):
        if left <= point[0] <= right and top <= point[1] <= bottom:
            return True
    edges = (
        ((left, top), (right, top)),
        ((right, top), (right, bottom)),
        ((right, bottom), (left, bottom)),
        ((left, bottom), (left, top)),
    )
    return any(_segments_intersect(start, end, a, b) for a, b in edges)


def _check_inside(box: tuple[int, int, int, int],
                  margin: int = MARGIN) -> None:
    if (box[0] < margin or box[1] < margin
            or box[2] > WIDTH - margin or box[3] > HEIGHT - margin):
        raise ValueError(f"box outside canvas margin: {box}")


def _box_center(draw: ImageDraw.ImageDraw, cx: int, cy: int, text: str,
                font: ImageFont.FreeTypeFont,
                boxes: list[tuple[int, int, int, int]],
                fill: str = FILL) -> tuple[int, int, int, int]:
    width, height = _text_metrics(draw, text, font)
    box = (int(cx - width / 2 - PAD), int(cy - height / 2 - PAD),
           int(cx + width / 2 + PAD), int(cy + height / 2 + PAD))
    _check_inside(box)
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=INK, width=4)
    _draw_text_center(draw, box, text, font)
    boxes.append(box)
    return box


def _box_at(draw: ImageDraw.ImageDraw, x: int, y: int, text: str,
            font: ImageFont.FreeTypeFont,
            boxes: list[tuple[int, int, int, int]],
            fill: str = FILL) -> tuple[int, int, int, int]:
    width, height = _text_metrics(draw, text, font)
    box = (x, y, x + width + 2 * PAD, y + height + 2 * PAD)
    _check_inside(box)
    draw.rounded_rectangle(box, radius=16, fill=fill, outline=INK, width=4)
    _draw_text_center(draw, box, text, font)
    boxes.append(box)
    return box


def _arrowhead(draw: ImageDraw.ImageDraw, point: tuple[int, int],
               other: tuple[int, int]) -> None:
    angle = math.atan2(point[1] - other[1], point[0] - other[0])
    size = 22
    left = (point[0] - size * math.cos(angle - 0.45),
            point[1] - size * math.sin(angle - 0.45))
    right = (point[0] - size * math.cos(angle + 0.45),
             point[1] - size * math.sin(angle + 0.45))
    draw.polygon([point, left, right], fill=INK)


def _arrow(draw: ImageDraw.ImageDraw, start: tuple[int, int],
           end: tuple[int, int], *, double: bool = False,
           width: int = 5) -> None:
    draw.line([start, end], fill=INK, width=width)
    _arrowhead(draw, end, start)
    if double:
        _arrowhead(draw, start, end)


def _polyline_arrow(draw: ImageDraw.ImageDraw,
                    points: list[tuple[int, int]], *,
                    double: bool = False, width: int = 5) -> None:
    for start, end in zip(points, points[1:]):
        draw.line([start, end], fill=INK, width=width)
    _arrowhead(draw, points[-1], points[-2])
    if double:
        _arrowhead(draw, points[0], points[1])


def _label_beside(draw: ImageDraw.ImageDraw, text: str,
                  start: tuple[int, int], end: tuple[int, int],
                  boxes: list[tuple[int, int, int, int]],
                  labels: list[tuple[int, int, int, int]],
                  *, side: int = 1, along: float = 0.5) -> None:
    font = _font(FONT_LABEL)
    width, height = _text_metrics(draw, text, font)
    mid_x = start[0] + (end[0] - start[0]) * along
    mid_y = start[1] + (end[1] - start[1]) * along
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    length = math.hypot(dx, dy) or 1.0
    nx, ny = -dy / length, dx / length
    offset = 100 * side
    cx = mid_x + nx * offset
    cy = mid_y + ny * offset
    box = (int(cx - width / 2 - 12), int(cy - height / 2 - 8),
           int(cx + width / 2 + 12), int(cy + height / 2 + 8))
    _check_inside(box, margin=20)
    for other in boxes:
        if _rects_overlap(box, other):
            raise ValueError(
                f"arrow label overlaps a box: {text} {box} vs {other}")
    for other in labels:
        if _rects_overlap(box, other):
            raise ValueError(f"arrow labels overlap: {text}")
    if _segment_intersects_rect(start, end, box):
        raise ValueError(f"arrow label touches its line: {text}")
    labels.append(box)
    draw.rounded_rectangle(box, radius=8, fill="white", outline=OUTLINE,
                           width=2)
    _draw_text_center(draw, box, text, font)


def _check_gaps(boxes: list[tuple[int, int, int, int]]) -> None:
    for index, first in enumerate(boxes):
        for second in boxes[index + 1:]:
            if _rects_overlap(first, second):
                raise ValueError("diagram boxes overlap")
            dx = max(second[0] - first[2], first[0] - second[2])
            dy = max(second[1] - first[3], first[1] - second[3])
            if max(dx, dy) < GAP:
                raise ValueError("diagram boxes are too close")


def _canvas() -> tuple[Image.Image, ImageDraw.ImageDraw]:
    image = Image.new("RGB", (WIDTH, HEIGHT), "white")
    return image, ImageDraw.Draw(image)


def _render_von_neumann(path: Path) -> None:
    image, draw = _canvas()
    boxes: list[tuple[int, int, int, int]] = []
    labels: list[tuple[int, int, int, int]] = []
    draw.rounded_rectangle((480, 160, 1200, 940), radius=24, outline=OUTLINE,
                           width=3)
    draw.text((500, 175), "CPU", font=_font(FONT_TITLE), fill=INK)
    source = _box_center(draw, 200, 380, "Input",
                         _font(FONT_NODE, bold=True), boxes)
    sink = _box_center(draw, 200, 760, "Output",
                       _font(FONT_NODE, bold=True), boxes)
    memory = _box_center(draw, 1440, 560, "Memory",
                         _font(FONT_NODE, bold=True), boxes)
    cu = _box_center(draw, 760, 330, "Control Unit",
                     _font(FONT_NODE, bold=True), boxes)
    alu = _box_center(draw, 720, 700, "ALU",
                      _font(FONT_NODE, bold=True), boxes)
    registers = _box_center(draw, 1040, 700, "Registers",
                            _font(FONT_NODE, bold=True), boxes)
    _check_gaps(boxes)
    _arrow(draw, (source[2], (source[1] + source[3]) // 2), (480, 380))
    _label_beside(draw, "data", (source[2], (source[1] + source[3]) // 2),
                  (480, 380), boxes, labels, side=-1)
    _arrow(draw, (480, 760), (sink[2], (sink[1] + sink[3]) // 2))
    _label_beside(draw, "results", (480, 760),
                  (sink[2], (sink[1] + sink[3]) // 2), boxes, labels,
                  side=1)
    _arrow(draw, (1200, 560), (memory[0], (memory[1] + memory[3]) // 2),
           double=True)
    _label_beside(draw, "data", (1200, 560),
                  (memory[0], (memory[1] + memory[3]) // 2), boxes, labels,
                  side=-1)
    _arrow(draw, ((cu[0] + cu[2]) // 2, cu[3]),
           ((alu[0] + alu[2]) // 2, alu[1]))
    _label_beside(draw, "control", ((cu[0] + cu[2]) // 2, cu[3]),
                  ((alu[0] + alu[2]) // 2, alu[1]), boxes, labels, side=1)
    _arrow(draw, (cu[2], cu[1] + 50), (registers[0], registers[1] + 50))
    _label_beside(draw, "control", (cu[2], cu[1] + 50),
                  (registers[0], registers[1] + 50), boxes, labels,
                  side=-1)
    _arrow(draw, (alu[2], (alu[1] + alu[3]) // 2),
           (registers[0], (registers[1] + registers[3]) // 2))
    _label_beside(draw, "result", (alu[2], (alu[1] + alu[3]) // 2),
                  (registers[0], (registers[1] + registers[3]) // 2),
                  boxes, labels, side=1)
    image.save(path, dpi=(200, 200))


def _render_cpu_datapath(path: Path) -> None:
    image, draw = _canvas()
    boxes: list[tuple[int, int, int, int]] = []
    labels: list[tuple[int, int, int, int]] = []
    draw.rounded_rectangle((60, 140, 1250, 960), radius=24, outline=OUTLINE,
                           width=3)
    draw.text((80, 150), "CPU", font=_font(FONT_TITLE), fill=INK)
    cu = _box_center(draw, 240, 330, "Control Unit",
                     _font(FONT_NODE, bold=True), boxes)
    alu = _box_center(draw, 240, 800, "ALU",
                      _font(FONT_NODE, bold=True), boxes)
    pc = _box_center(draw, 680, 250, "PC", _font(FONT_NODE, bold=True),
                     boxes)
    ir = _box_center(draw, 680, 400, "IR", _font(FONT_NODE, bold=True),
                     boxes)
    mar = _box_center(draw, 680, 550, "MAR", _font(FONT_NODE, bold=True),
                      boxes)
    mbr = _box_center(draw, 680, 700, "MBR", _font(FONT_NODE, bold=True),
                      boxes)
    ac = _box_center(draw, 680, 850, "AC", _font(FONT_NODE, bold=True),
                     boxes)
    memory = _box_center(draw, 1440, 560, "Memory",
                         _font(FONT_NODE, bold=True), boxes)
    _check_gaps(boxes)
    _arrow(draw, ((cu[0] + cu[2]) // 2, cu[3]),
           ((alu[0] + alu[2]) // 2, alu[1]))
    _label_beside(draw, "control", ((cu[0] + cu[2]) // 2, cu[3]),
                  ((alu[0] + alu[2]) // 2, alu[1]), boxes, labels, side=1)
    top_y = 165
    _polyline_arrow(draw, [
        ((cu[0] + cu[2]) // 2, cu[1]),
        ((cu[0] + cu[2]) // 2, top_y),
        (pc[0] + (pc[2] - pc[0]) // 2, top_y),
        (pc[0] + (pc[2] - pc[0]) // 2, pc[1]),
    ])
    _label_beside(draw, "control", ((cu[0] + cu[2]) // 2, top_y),
                  (pc[0] + (pc[2] - pc[0]) // 2, top_y), boxes, labels,
                  side=1, along=0.55)
    lane_left = pc[0] - 55
    _polyline_arrow(draw, [
        (pc[0], (pc[1] + pc[3]) // 2),
        (lane_left, (pc[1] + pc[3]) // 2),
        (lane_left, (mar[1] + mar[3]) // 2),
        (mar[0], (mar[1] + mar[3]) // 2),
    ])
    _label_beside(draw, "address", (lane_left, (pc[1] + pc[3]) // 2),
                  (lane_left, (mar[1] + mar[3]) // 2), boxes, labels,
                  side=1)
    lane_right = mbr[2] + 55
    _polyline_arrow(draw, [
        (mbr[2], (mbr[1] + mbr[3]) // 2),
        (lane_right, (mbr[1] + mbr[3]) // 2),
        (lane_right, (ir[1] + ir[3]) // 2),
        (ir[2], (ir[1] + ir[3]) // 2),
    ])
    _label_beside(draw, "instruction", (lane_right, (mbr[1] + mbr[3]) // 2),
                  (lane_right, (ir[1] + ir[3]) // 2), boxes, labels,
                  side=1)
    _arrow(draw, (mar[2], (mar[1] + mar[3]) // 2),
           (memory[0], (memory[1] + memory[3]) // 2), double=True)
    _label_beside(draw, "address", (mar[2], (mar[1] + mar[3]) // 2),
                  (memory[0], (memory[1] + memory[3]) // 2), boxes, labels,
                  side=-1)
    _arrow(draw, (mbr[2], (mbr[1] + mbr[3]) // 2),
           (memory[0], (memory[1] + memory[3]) // 2), double=True)
    _label_beside(draw, "data", (mbr[2], (mbr[1] + mbr[3]) // 2),
                  (memory[0], (memory[1] + memory[3]) // 2), boxes, labels,
                  side=1)
    _arrow(draw, (alu[2], (alu[1] + alu[3]) // 2),
           (ac[0], (ac[1] + ac[3]) // 2), double=True)
    _label_beside(draw, "operands / result",
                  (alu[2], (alu[1] + alu[3]) // 2),
                  (ac[0], (ac[1] + ac[3]) // 2), boxes, labels, side=1)
    image.save(path, dpi=(200, 200))


def _render_cache_mapping(path: Path) -> None:
    image, draw = _canvas()
    segments = ["Tag (4 bits)", "Line (3 bits)", "Offset (9 bits)"]
    font = _font(FONT_DETAIL, bold=True)
    widths = []
    for segment in segments:
        width, _ = _text_metrics(draw, segment, font)
        widths.append(width + 2 * PAD)
    total = sum(widths)
    bar = (MARGIN, 80, MARGIN + total, 200)
    _check_inside(bar)
    draw.rounded_rectangle(bar, radius=14, fill=FILL, outline=INK, width=4)
    x = bar[0]
    for index, (segment, width) in enumerate(zip(segments, widths)):
        if index:
            draw.line([(x, bar[1]), (x, bar[3])], fill=INK, width=3)
        _draw_text_center(draw, (x, bar[1], x + width, bar[3]), segment,
                          font)
        x += width
    draw.text((MARGIN, 230), "Cache state", font=_font(FONT_NODE, bold=True),
              fill=INK)
    headers = ["Line", "Valid", "Tag", "Data"]
    rows = []
    for line in range(8):
        if line == 3:
            rows.append(("3", "1", "0010", "0xA5"))
        elif line == 5:
            rows.append(("5", "1", "0001", "0x3C"))
        else:
            rows.append((str(line), "0", "----", "----"))
    cell_font = _font(34)
    header_font = _font(36, bold=True)
    column_widths = [180, 180, 180, 520]
    row_height = 70
    table_left = MARGIN
    table_top = 285
    table_right = table_left + sum(column_widths)
    table_bottom = table_top + row_height * 9
    _check_inside((table_left, table_top, table_right, table_bottom))
    x = table_left
    for width, header in zip(column_widths, headers):
        cell = (x, table_top, x + width, table_top + row_height)
        draw.rectangle(cell, fill=FILL, outline=INK, width=3)
        _draw_text_center(draw, cell, header, header_font)
        x += width
    for row_index, row in enumerate(rows):
        y = table_top + row_height * (row_index + 1)
        x = table_left
        for width, value in zip(column_widths, row):
            cell = (x, y, x + width, y + row_height)
            draw.rectangle(cell, outline=INK, width=2)
            _draw_text_center(draw, cell, value, cell_font)
            x += width
    box = _box_at(draw, 1180, 320, "Addresses\n0x1A2B\n0x2A2B",
                  _font(FONT_DETAIL, bold=True), [])
    if _rects_overlap(box, (table_left, table_top, table_right,
                           table_bottom)):
        raise ValueError("cache address box overlaps the table")
    image.save(path, dpi=(200, 200))


RENDERERS = {
    "von_neumann": _render_von_neumann,
    "cpu_datapath": _render_cpu_datapath,
    "cache_mapping": _render_cache_mapping,
}


def render_figure(kind: str, path: Path) -> None:
    renderer = RENDERERS.get(kind)
    if renderer is None:
        raise ValueError(f"unknown CSC429 figure kind: {kind}")
    path.parent.mkdir(parents=True, exist_ok=True)
    renderer(path)
