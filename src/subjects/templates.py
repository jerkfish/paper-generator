"""Shared stage-3 template/cover inventory and installation.

The module never edits a source template.  ``--install`` copies a source DOCX
into ``data/reference/<CODE>/<CODE> TEMPLATE.docx`` after the human checkpoint,
and ``--check`` writes a structural report to the tracking folder.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import shutil
import zipfile
from pathlib import Path

import docx

from src import config
from src.subjects.registry import SubjectNotFound, get_subject


def template_candidates(root: Path, code: str) -> list[Path]:
    reference = Path(root) / "data" / "reference" / code.upper()
    if not reference.is_dir():
        return []
    return sorted(path for path in reference.glob("*.docx")
                  if path.is_file() and not path.name.startswith("~$"))


def resolve_template(root: Path, code: str) -> Path | None:
    try:
        subject = get_subject(code, root)
    except SubjectNotFound:
        subject = None
    if subject is not None and subject.template_path:
        candidate = Path(root) / subject.template_path
        if candidate.is_file():
            return candidate
    candidates = template_candidates(root, code)
    return candidates[0] if candidates else None


def check_template(path: Path) -> dict:
    path = Path(path)
    result = {
        "path": str(path),
        "exists": path.is_file(),
        "xml_valid": False,
        "paragraphs": 0,
        "sections": 0,
        "headers": 0,
        "footers": 0,
        "images": 0,
        "cover_text": "",
        "problems": [],
    }
    if not path.is_file():
        result["problems"].append("template file is missing")
        return result
    try:
        document = docx.Document(str(path))
    except Exception as error:
        result["problems"].append(f"cannot open DOCX: {error}")
        return result
    result["paragraphs"] = len(document.paragraphs)
    result["sections"] = len(document.sections)
    for section in document.sections:
        for header in (section.header, section.first_page_header):
            if any(p.text.strip() for p in header.paragraphs):
                result["headers"] += 1
        for footer in (section.footer, section.first_page_footer):
            if any(p.text.strip() for p in footer.paragraphs):
                result["footers"] += 1
    try:
        with zipfile.ZipFile(str(path)) as archive:
            result["images"] = len([
                name for name in archive.namelist()
                if name.startswith("word/media/")])
            if result["headers"] == 0 and result["footers"] == 0:
                # Some Word templates keep header/footer text in VML/drawing
                # parts that python-docx does not expose as paragraphs.
                for name in archive.namelist():
                    if not (name.startswith("word/header")
                            or name.startswith("word/footer")):
                        continue
                    xml = archive.read(name).decode("utf-8", errors="replace")
                    texts = re.findall(r"<w:t[^>]*>(.*?)</w:t>", xml)
                    if any(html.unescape(text).strip() for text in texts):
                        if name.startswith("word/header"):
                            result["headers"] += 1
                        else:
                            result["footers"] += 1
        result["xml_valid"] = True
    except Exception as error:
        result["problems"].append(f"invalid DOCX archive: {error}")
    cover = "\n".join(p.text for p in document.paragraphs[:25])
    result["cover_text"] = " ".join(cover.split())[:500]
    if result["sections"] < 1:
        result["problems"].append("no document section")
    if not result["cover_text"]:
        result["problems"].append("cover text is empty")
    if result["headers"] == 0 and result["footers"] == 0:
        result["problems"].append("no header/footer text found")
    return result


def install_template(root: Path, code: str, source: Path,
                     apply: bool = False) -> dict:
    code = code.upper()
    source = Path(source).resolve()
    if not source.is_file():
        raise SystemExit(f"template source not found: {source}")
    if source.suffix.lower() != ".docx":
        raise SystemExit("template source must be a .docx file")
    target = (Path(root) / "data" / "reference" / code /
              f"{code} TEMPLATE.docx")
    result = {
        "source": str(source),
        "target": str(target),
        "would_write": not target.exists()
        or source.read_bytes() != target.read_bytes(),
        "written": False,
    }
    if apply and result["would_write"]:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        result["written"] = True
        subject_path = Path(root) / "subjects" / code / "subject.json"
        if subject_path.exists():
            data = json.loads(subject_path.read_text(encoding="utf-8"))
            data["template_path"] = target.relative_to(root).as_posix()
            subject_path.write_text(json.dumps(data, indent=2) + "\n",
                                    encoding="utf-8")
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--install", default="")
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--root", default=str(config.PROJECT_ROOT),
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    root = Path(args.root).resolve()
    code = args.subject.upper()
    if args.install:
        result = install_template(root, code, Path(args.install),
                                  apply=args.apply)
        print(json.dumps(result, indent=2))
        if not args.apply:
            print("dry run only; pass --apply to copy the template")
        return
    path = resolve_template(root, code)
    if path is None:
        raise SystemExit(f"no template found for {code} under "
                         f"data/reference/{code}")
    result = check_template(path)
    tracking = Path(root) / "data" / "tracking" / code.lower()
    tracking.mkdir(parents=True, exist_ok=True)
    (tracking / "template_check.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if not args.check:
        print("inventory only; pass --check for the stage-3 report")
    if result["problems"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
