"""HTML/SVG diagrams for ICT450 answer sheets.

The ERD renderer draws entity boxes and Crow's Foot relationships from a
compact spec.  Answers stay as data; this module only handles layout and
rendering, using the same Edge/Playwright path as the review sheets.
"""
from __future__ import annotations

import html
from pathlib import Path

HEADER_H = 34
ROW_H = 26
DEFAULT_W = 205
PAD = 10


def _entity_box(entity: dict) -> dict:
    attrs = entity.get("attrs") or []
    width = int(entity.get("width") or DEFAULT_W)
    height = HEADER_H + max(1, len(attrs)) * ROW_H
    return {
        "id": entity["id"],
        "name": entity.get("name") or entity["id"],
        "x": int(entity.get("x") or 0),
        "y": int(entity.get("y") or 0),
        "width": width,
        "height": height,
        "attrs": attrs,
    }


def _anchor(box: dict, side: str) -> tuple[float, float]:
    gap = 7
    if side == "top":
        return (box["x"] + box["width"] / 2, box["y"] - gap)
    if side == "bottom":
        return (box["x"] + box["width"] / 2,
                box["y"] + box["height"] + gap)
    if side == "left":
        return (box["x"] - gap, box["y"] + box["height"] / 2)
    return (box["x"] + box["width"] + gap, box["y"] + box["height"] / 2)


def _nearest_side(box: dict, point: tuple[float, float]) -> str:
    px, py = point
    distances = {
        "top": abs(py - box["y"]),
        "bottom": abs(py - (box["y"] + box["height"])),
        "left": abs(px - box["x"]),
        "right": abs(px - (box["x"] + box["width"])),
    }
    return min(distances, key=distances.get)


def _crow(path: list[tuple[float, float]], many: bool) -> str:
    (x1, y1), (x2, y2) = path[-2], path[-1]
    dx, dy = x2 - x1, y2 - y1
    length = max((dx * dx + dy * dy) ** 0.5, 1)
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    if many:
        size = 15
        spread = 8
        back = (x2 - ux * size, y2 - uy * size)
        lines = [
            (x2, y2, back[0] + px * spread, back[1] + py * spread),
            (x2, y2, back[0] - px * spread, back[1] - py * spread),
            (x2, y2, back[0], back[1]),
        ]
        return "".join(
            f'<line x1="{a:.1f}" y1="{b:.1f}" x2="{c:.1f}" y2="{d:.1f}" '
            'stroke="#334155" stroke-width="1.5"/>'
            for a, b, c, d in lines)
    tick = 6
    cx, cy = x2 - ux * tick, y2 - uy * tick
    return (
        f'<line x1="{cx + px * tick:.1f}" y1="{cy + py * tick:.1f}" '
        f'x2="{cx - px * tick:.1f}" y2="{cy - py * tick:.1f}" '
        'stroke="#334155" stroke-width="1.8"/>')


def _route(start: tuple[float, float], end: tuple[float, float],
           waypoints: list[list[float]] | None) -> list[tuple[float, float]]:
    points = [start]
    for point in waypoints or []:
        points.append((float(point[0]), float(point[1])))
    points.append(end)
    return points


def _card_label(point: tuple[float, float], side: str, text: str) -> str:
    offsets = {
        "top": (10, -6),
        "bottom": (10, 16),
        "left": (-14, -4),
        "right": (14, -4),
    }
    dx, dy = offsets.get(side, (12, 0))
    x, y = point[0] + dx, point[1] + dy
    return (f'<text x="{x:.1f}" y="{y:.1f}" text-anchor="middle" '
            f'font-size="12" font-weight="700" fill="#475569">{text}</text>')

def _label_point(path: list[tuple[float, float]]) -> tuple[float, float]:
    best = max(
        zip(path, path[1:]),
        key=lambda pair: (pair[1][0] - pair[0][0]) ** 2
        + (pair[1][1] - pair[0][1]) ** 2,
    )
    (x1, y1), (x2, y2) = best
    return ((x1 + x2) / 2, (y1 + y2) / 2)


def erd_svg(spec: dict) -> tuple[str, int, int]:
    boxes = {box["id"]: box for box in
             (_entity_box(entity) for entity in spec.get("entities") or [])}
    width = int(spec.get("width") or 0)
    height = int(spec.get("height") or 0)
    if not width:
        width = max((box["x"] + box["width"] for box in boxes.values()),
                    default=800) + 40
    height = max([height] + [box["y"] + box["height"] + 40
                           for box in boxes.values()])
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{width}" height="{height}" viewBox="0 0 {width} {height}" '
        'font-family="Arial, Helvetica, sans-serif">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    for relationship in spec.get("relationships") or []:
        source = boxes[relationship["from"]]
        target = boxes[relationship["to"]]
        from_side = relationship.get("from_side") or "right"
        to_side = relationship.get("to_side") or "left"
        start = _anchor(source, from_side)
        end = _anchor(target, to_side)
        path = _route(start, end, relationship.get("waypoints"))
        point_text = " ".join(f"{x:.1f},{y:.1f}" for x, y in path)
        parts.append(
            f'<polyline points="{point_text}" fill="none" '
            'stroke="#334155" stroke-width="1.5" '
            'stroke-linejoin="round" stroke-linecap="round"/>')
        parts.append(_crow(path, relationship.get("to_card") == "many"))
        if relationship.get("from_card") == "many":
            parts.append(_crow(list(reversed(path)), True))
        parts.append(_card_label(
            start, from_side,
            "1" if relationship.get("from_card") != "many" else "M"))
        parts.append(_card_label(
            end, to_side,
            "1" if relationship.get("to_card") != "many" else "M"))
        lx, ly = _label_point(path)
        label = html.escape(str(relationship.get("label") or ""))
        if label:
            parts.append(
                f'<rect x="{lx - 4 - len(label) * 3.1:.1f}" '
                f'y="{ly - 9:.1f}" width="{8 + len(label) * 6.2:.1f}" '
                'height="16" rx="3" fill="#ffffff" fill-opacity="0.92"/>')
            parts.append(
                f'<text x="{lx:.1f}" y="{ly + 4:.1f}" text-anchor="middle" '
                'font-size="10" fill="#1f3864" font-weight="600">'
                f'{label}</text>')
    for box in boxes.values():
        parts.append(
            f'<rect x="{box["x"]}" y="{box["y"]}" width="{box["width"]}" '
            f'height="{box["height"]}" rx="4" fill="#ffffff" '
            'stroke="#1f3864" stroke-width="1.5"/>')
        parts.append(
            f'<rect x="{box["x"]}" y="{box["y"]}" width="{box["width"]}" '
            f'height="{HEADER_H}" rx="4" fill="#1f3864"/>')
        parts.append(
            f'<rect x="{box["x"]}" y="{box["y"] + HEADER_H - 4}" '
            f'width="{box["width"]}" height="4" fill="#1f3864"/>')
        parts.append(
            f'<text x="{box["x"] + box["width"] / 2}" '
            f'y="{box["y"] + 22}" text-anchor="middle" font-size="17" '
            'font-weight="700" fill="#ffffff" letter-spacing="0.4">'
            f'{html.escape(box["name"])}</text>')
        for index, attr in enumerate(box["attrs"]):
            if isinstance(attr, str):
                attr = {"name": attr}
            name = html.escape(str(attr.get("name") or ""))
            key = str(attr.get("key") or "").upper()
            y = box["y"] + HEADER_H + index * ROW_H + 15
            x = box["x"] + 10
            if key:
                width = {"PK": 34, "FK": 32}.get(key, 52)
                parts.append(
                    f'<text x="{x}" y="{y}" font-size="12" '
                    'font-weight="700" fill="#b45309">'
                    f'{key}</text>')
                x += width + 4
            decoration = ("text-decoration=\"underline\"" if key == "PK"
                          else "")
            style = ("font-weight=\"700\"" if key == "PK"
                     else "font-style=\"italic\"" if key == "FK" else "")
            parts.append(
                f'<text x="{x}" y="{y}" font-size="16" fill="#0f172a" '
                f'{decoration} {style}>{name}</text>')
            if index < len(box["attrs"]) - 1:
                parts.append(
                    f'<line x1="{box["x"] + 8}" '
                    f'y1="{box["y"] + HEADER_H + (index + 1) * ROW_H}" '
                    f'x2="{box["x"] + box["width"] - 8}" '
                    f'y2="{box["y"] + HEADER_H + (index + 1) * ROW_H}" '
                    'stroke="#e2e8f0" stroke-width="0.7"/>')
    parts.append("</svg>")
    return "\n".join(parts), width, height


def render_erd(spec: dict, target: Path) -> Path:
    """Render an ERD spec to a high-resolution PNG."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    svg, width, height = erd_svg(spec)
    page = (
        "<html><head><meta charset='utf-8'><style>"
        "body{margin:0;background:#fff}#diagram{display:inline-block}"
        "</style></head><body>"
        f"<div id='diagram'>{svg}</div></body></html>")
    html_path = target.with_suffix(".html")
    html_path.write_text(page, encoding="utf-8")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="msedge", headless=True)
        view = browser.new_page(
            viewport={"width": width + 20, "height": height + 20},
            device_scale_factor=2,
        )
        view.goto(html_path.resolve().as_uri())
        view.locator("#diagram").screenshot(path=str(target))
        browser.close()
    return target
