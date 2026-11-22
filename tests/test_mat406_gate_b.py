"""MAT406 Gate B proofing and standard-cover guards."""
from __future__ import annotations

import json
import re
from pathlib import Path

import pymupdf
import pytest

ROOT = Path(__file__).resolve().parents[1]
TRACKING = ROOT / "data" / "tracking" / "mat406" / "v2"
SEEDS = ROOT / "outputs" / "review" / "mat406_v2" / "seeds"


def _load(path: Path, default=None):
    if not path.is_file():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def test_paper_template_uses_standard_cover_with_visible_time():
    template = ROOT / "data" / "reference" / "MAT406" / "MAT406 TEMPLATE.docx"
    if not template.is_file():
        pytest.skip("MAT406 paper template is not built")
    import zipfile
    with zipfile.ZipFile(template) as source:
        xml = source.read("word/document.xml").decode("utf-8")
    assert "width:3400" in xml
    assert "FOUNDATION" in xml and "MATHEMATICS" in xml
    assert "HOURS" in xml
    assert "CSC662" not in xml
    assert "COMPUTER SECURITY" not in xml


def test_scheme_template_is_the_owner_fixed_file():
    from src.subjects.mat406.format_v3 import SCHEME_TEMPLATE
    assert SCHEME_TEMPLATE.name == "scheme-template-fix.docx"
    assert SCHEME_TEMPLATE.is_file()


def test_v5_printed_text_restorations_are_complete():
    report = _load(TRACKING / "text_corrections_v5.json")
    if not report:
        pytest.skip("MAT406 V5 corrections are not built")
    assert not report.get("missing")
    assert len(report.get("applied") or []) >= 25
    assert len(report.get("questions") or []) >= 19
    bank = TRACKING / "bank" / "questions"
    for row in report["applied"]:
        question = _load(bank / f"{row['question_id']}.json")
        assert question is not None
        part = next((part for part in question.get("parts") or []
                     if str(part.get("label")) == row["part"]), None)
        assert part is not None
        assert str(part.get("text") or "").strip() == str(
            row.get("new") or "").strip()


def test_seed_covers_show_crest_title_and_duration():
    for seed in (1, 2, 3):
        for kind in ("paper", "scheme"):
            path = SEEDS / f"seed_{seed:02d}" / f"{kind}.pdf"
            if not path.is_file():
                pytest.skip("MAT406 Gate B seeds are not built")
            with pymupdf.open(str(path)) as document:
                text = re.sub(r"\s+", " ", document[0].get_text())
                assert "FOUNDATION MATHEMATICS" in text
                assert "MAT406" in text
                assert "CSC662" not in text
                assert "COMPUTER SECURITY" not in text
                assert document[0].get_images()


def test_scheme_question_numbers_match_the_paper():
    for seed in (1, 2, 3):
        scheme = SEEDS / f"seed_{seed:02d}" / "scheme.pdf"
        if not scheme.is_file():
            pytest.skip("MAT406 Gate B seeds are not built")
        with pymupdf.open(str(scheme)) as document:
            text = "\n".join(page.get_text() for page in document)
        headings = [row.strip() for row in
                    re.findall(r"PART [AB].*|QUESTION \d+", text)]
        expected = ["PART A — MARKING SCHEME"] + [
            f"QUESTION {n}" for n in range(1, 5)] + [
            "PART B — MARKING SCHEME"] + [
            f"QUESTION {n}" for n in range(1, 5)]
        assert headings[:len(expected)] == expected


def test_gate_b_page_counts_match_printed_footers():
    summary = _load(SEEDS / "build_summary.json")
    if not summary:
        pytest.skip("MAT406 Gate B package is not built")
    for row in summary["seeds"]:
        seed = row["seed"]
        for kind, key in (("paper", "paper_pages"),
                          ("scheme", "scheme_pages")):
            path = SEEDS / f"seed_{seed:02d}" / f"{kind}.pdf"
            with pymupdf.open(str(path)) as document:
                assert len(document) == row[key]
                cover = document[0].get_text()
                match = re.search(r"consists of (\d+) printed pages", cover)
                assert match and int(match.group(1)) == row[key]



def test_equation_blocks_get_vertical_spacing():
    import docx
    from docx.shared import Pt
    from src.subjects.mat406.assemble_v5 import _add_part_text

    document = docx.Document()
    part = {
        "text": "\n".join([
            "Consider the following system of linear equations:",
            "$x + y = 2$",
            "$x - y = 0$",
            "Find the values of x and y.",
        ]),
        "marks": 5,
    }
    _add_part_text(document, part, Path("."), "spacing-test", "b", False)
    paragraphs = document.paragraphs
    assert "Consider the following" in paragraphs[0].text
    assert paragraphs[1].paragraph_format.space_before == Pt(10)
    assert paragraphs[2].paragraph_format.space_after == Pt(10)


def test_figure_and_caption_have_vertical_spacing():
    import docx
    from docx.shared import Pt
    from src.subjects.mat406.assemble_v5 import _add_picture

    asset = (ROOT / "data" / "tracking" / "mat406" / "v2" / "bank" /
             "assets" / "A-MAT406-2021-JUL-Q1-F1.png")
    if not asset.is_file():
        pytest.skip("MAT406 figure asset is not built")
    document = docx.Document()
    _add_picture(document, {"path": str(asset), "label": "Figure 1"}, 1)
    picture, caption = document.paragraphs[-2:]
    assert picture.paragraph_format.space_before == Pt(12)
    assert picture.paragraph_format.space_after == Pt(6)
    assert caption.paragraph_format.space_before == Pt(6)
    assert caption.paragraph_format.space_after == Pt(12)
