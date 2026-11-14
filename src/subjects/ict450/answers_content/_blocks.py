"""Small block builders for ICT450 answer content."""
from __future__ import annotations


def p(text: str) -> dict:
    return {"type": "p", "text": text.strip()}


def h(text: str) -> dict:
    return {"type": "h", "text": text.strip()}


def bullets(*items: str) -> dict:
    return {"type": "bullets", "items": [item.strip() for item in items]}


def sub(label: str, marks: int, text: str = "",
        items: list[str] | None = None,
        blocks: list[dict] | None = None) -> dict:
    return {
        "type": "sub",
        "label": label,
        "marks": marks,
        "text": text.strip(),
        "items": [item.strip() for item in (items or [])],
        "blocks": blocks or [],
    }


def sql(code: str, caption: str = "") -> dict:
    return {"type": "sql", "code": code.strip("\n"), "caption": caption}


def schema(lines: list[str], caption: str = "") -> dict:
    return {"type": "schema", "lines": [line.strip() for line in lines],
            "caption": caption}


def table(caption: str, columns: list[str], rows: list[list[str]],
          widths: list[int] | None = None) -> dict:
    return {"type": "table", "caption": caption, "columns": columns,
            "rows": rows, "widths": widths or []}


def erd(caption: str, spec: dict) -> dict:
    return {"type": "erd", "caption": caption, "spec": spec}


def callout(text: str) -> dict:
    return {"type": "callout", "text": text.strip()}


def flatten(blocks: list[dict]) -> str:
    lines: list[str] = []
    for block in blocks:
        kind = block.get("type")
        if kind in {"p", "h", "callout"}:
            lines.append(str(block.get("text") or ""))
        elif kind == "bullets":
            lines.extend(f"- {item}" for item in block.get("items") or [])
        elif kind == "sub":
            head = f"{block.get('label')})"
            if block.get("text"):
                head += " " + str(block["text"])
            lines.append(head)
            lines.extend(f"- {item}" for item in block.get("items") or [])
            lines.append(flatten(block.get("blocks") or []))
        elif kind == "sql":
            if block.get("caption"):
                lines.append(str(block["caption"]))
            lines.append(str(block.get("code") or ""))
        elif kind == "schema":
            if block.get("caption"):
                lines.append(str(block["caption"]))
            lines.extend(str(line) for line in block.get("lines") or [])
        elif kind == "table":
            if block.get("caption"):
                lines.append(str(block["caption"]))
            lines.append(" | ".join(str(col) for col in block["columns"]))
            for row in block.get("rows") or []:
                lines.append(" | ".join(str(cell) for cell in row))
        elif kind == "erd":
            lines.append(str(block.get("caption") or "ERD diagram"))
    return "\n".join(line for line in lines if line.strip()).strip()
