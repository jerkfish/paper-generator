"""V1/V2 ICT450 pilot helpers: paper register, exact text and DB asset rules."""
from __future__ import annotations

import json
from pathlib import Path

import pymupdf

from src.subjects.ict450 import bank_build, papers


def _pdf(path: Path, text: str, pages: int = 1) -> None:
    document = pymupdf.open()
    for _ in range(pages):
        page = document.new_page()
        page.insert_text((72, 72), text)
    document.save(str(path))
    document.close()


def test_cover_month_handles_ict450_cover_variants():
    assert papers.cover_month(
        "CONFIDENTIAL CD/FEB 2023/ICT450/ITS432") == "2023-FEB"
    assert papers.cover_month(
        "EXAMINATION : DECEMBER 2019") == "2019-DEC"
    assert papers.cover_month(
        "COURSE CODE ICT450 EXAMINATION JULY 2024") == "2024-JUL"
    assert papers.cover_month("no date here") == ""


def test_register_reconciles_duplicates_and_flags_provisional_months(tmp_path):
    papers_dir = tmp_path / "papers"
    papers_dir.mkdir()
    _pdf(papers_dir / "ICT450 (1).pdf", "CD/FEB 2023/ICT450/ITS432")
    (papers_dir / "copy.PDF").write_bytes(
        (papers_dir / "ICT450 (1).pdf").read_bytes())
    _pdf(papers_dir / "scanned.PDF", "")
    tracking = tmp_path / "tracking"
    summary = papers.register(papers_dir, tracking)
    assert summary["total"] == 3
    assert summary["unique"] == 2
    assert summary["duplicates"] == 1
    assert "scanned.PDF" in summary["month_provisional"]
    register = json.loads(
        (tracking / "papers_register.json").read_text(encoding="utf-8"))
    ids = {row["paper_id"] for row in register["unique_papers"]}
    assert "ICT450-2023-FEB" in ids
    assert any(row["paper_id"].startswith("ICT450-UNKNOWN-")
               for row in register["unique_papers"])


def test_marks_layout_flags_missing_nested_label_and_sums_visible_marks():
    text = (
        "QUESTION 1\n"
        "a) First part.\n(4 marks)\n"
        "b) Second part.\n(4 marks)\n"
        "c) Third part.\n"
        "ii) Nested part.\n(6 marks)\n")
    layout = bank_build._marks_layout(text)
    assert layout["marks"] == 14
    assert layout["subpart_gap"] is True
    assert [part["label"] for part in layout["subparts"]] == ["a", "b", "c"]

    clean = (
        "QUESTION 2\n"
        "a) First.\n(10 marks)\n"
        "b) Second.\n(10 marks)\n")
    layout = bank_build._marks_layout(clean)
    assert layout["marks"] == 20
    assert layout["subpart_gap"] is False


def test_question_text_preserves_sql_indentation_and_drops_only_marks():
    blocks = [
        {"type": "text", "text": "QUESTION 3", "page_idx": 0},
        {"type": "text",
         "text": "Write SQL:\nSELECT *\n  FROM DELIVERY\n WHERE status = 'delivered';",
         "page_idx": 0},
        {"type": "text", "text": "DELIVERY\\_ID and 10\\% tax", "page_idx": 0},
        {"type": "text", "text": "(10 marks)", "page_idx": 0},
    ]
    question = {"blocks": ["B0001", "B0002", "B0003", "B0004"]}
    exact, clean = bank_build._question_text(question, blocks)
    assert "  FROM DELIVERY" in clean
    assert "\n WHERE" in clean
    assert "(10 marks)" not in clean
    assert "(10 marks)" in exact
    assert "DELIVERY_ID and 10% tax" in clean
    assert bank_build.CODE_RE.search(clean)


def test_html_rows_and_native_check_reject_empty_or_mismatched_tables(tmp_path):
    rows = bank_build.html_rows(
        "<table><tr><td>A</td><td>B</td></tr>"
        "<tr><td>1</td><td>2</td></tr></table>")
    assert rows == [["A", "B"], ["1", "2"]]
    blank = tmp_path / "blank.pdf"
    _pdf(blank, "")
    check = bank_build.native_table_check(
        "<table><tr><td>A</td><td>B</td></tr></table>", blank, 0,
        [0, 0, 1000, 1000])
    assert check["accepted"] is False
    assert "text layer" in check["reason"]


def test_native_check_accepts_an_exact_typed_table(tmp_path):
    pdf = tmp_path / "typed.pdf"
    document = pymupdf.open()
    page = document.new_page()
    page.insert_text((72, 72), "A")
    page.insert_text((150, 72), "B")
    page.insert_text((72, 100), "1")
    page.insert_text((150, 100), "2")
    document.save(str(pdf))
    document.close()
    html = ("<table><tr><td>A</td><td>B</td></tr>"
            "<tr><td>1</td><td>2</td></tr></table>")
    check = bank_build.native_table_check(html, pdf, 0, [0, 0, 1000, 1000])
    assert check["accepted"] is True
    assert check["rows"] == 2
    assert check["columns"] == 2


def test_review_decisions_update_statuses_and_keep_recreations_pending(
        tmp_path, monkeypatch):
    from src.bank.store import BankStore
    from src.subjects.ict450 import review

    bank = BankStore(tmp_path / "bank").ensure()
    question = {
        "id": "ICT450-2023-FEB-Q1", "source_paper": "ICT450-2023-FEB",
        "marks": 20, "status": "extracted", "review_flags": [],
        "native_text_blocks": [{"text": "Question text"}],
    }
    asset = {
        "id": "ICT450-2023-FEB-A01", "source_paper": "ICT450-2023-FEB",
        "kind": "table", "label": "Table 1", "verdict": "pending",
        "mineru_table_html": "<table><tr><td>A</td></tr></table>",
    }
    bank.save_question(question)
    bank.save_asset(asset)
    decisions = tmp_path / "decisions.json"
    decisions.write_text(json.dumps({"questions": {
        "ICT450-2023-FEB-Q1": {
            "verdict": "approved",
            "assets": {"ICT450-2023-FEB-A01": "use_recreation"},
        }}}), encoding="utf-8")
    monkeypatch.setattr(review, "BANK", tmp_path / "bank")
    result = review.apply_decisions(decisions)
    assert result["counts"]["approved"] == 1
    assert result["counts"]["use_recreation"] == 1
    saved_question = bank.load_question("ICT450-2023-FEB-Q1")
    saved_asset = bank.load_asset("ICT450-2023-FEB-A01")
    assert saved_question["status"] == "approved"
    assert saved_asset["review_choice"] == "use_recreation"
    assert saved_asset["verdict"] == "pending"
    assert saved_asset["recreation_status"] == "pending_review"
    assert (tmp_path / "bank" / "approvals.json").is_file()

    fix = tmp_path / "fix_decisions.json"
    fix.write_text(json.dumps({
        "round": "fix_review",
        "questions": {"ICT450-2023-FEB-Q1": {
            "verdict": "approved",
            "assets": {"ICT450-2023-FEB-A01": {
                "choice": "use_recreation", "notes": "looks correct"}},
        }}}), encoding="utf-8")
    review.apply_decisions(fix)
    saved_asset = bank.load_asset("ICT450-2023-FEB-A01")
    assert saved_asset["verdict"] == "approved"
    assert saved_asset["recreation_status"] == "approved"
    assert saved_asset["review_notes"] == "looks correct"

    more = tmp_path / "more_work.json"
    more.write_text(json.dumps({
        "round": "fix_review",
        "questions": {"ICT450-2023-FEB-Q1": {
            "verdict": "approved",
            "assets": {"ICT450-2023-FEB-A01": {
                "choice": "needs_more_work", "notes": "column width"}},
        }}}), encoding="utf-8")
    review.apply_decisions(more)
    assert bank.load_question("ICT450-2023-FEB-Q1")["status"] == "needs_fix"
    saved_asset = bank.load_asset("ICT450-2023-FEB-A01")
    assert saved_asset["verdict"] == "pending"
    assert saved_asset["recreation_status"] == "needs_more_work"


def test_manual_recreations_cover_the_assets_without_mineru_html():
    from src.subjects.ict450 import review

    expected = {
        "ICT450-2019-JUN-A42",
        "ICT450-2024-JAN-A11",
        "ICT450-2024-JUL-A16",
        "ICT450-2025-JUL-F21",
        "ICT450-2025-JUL-F22",
    }
    assert expected <= set(review.MANUAL_RECREATIONS)
    for fragment in review.MANUAL_RECREATIONS.values():
        assert "<" in fragment and len(fragment) > 100


def test_bank_build_links_assets_and_reports_unresolved_reference(
        tmp_path, monkeypatch):
    tracking = tmp_path / "tracking"
    bank = tracking / "bank"
    cache = tracking / "mineru" / "ICT450-2023-FEB" / "vlm_x"
    review = cache / "review"
    pages = review / "pages"
    pages.mkdir(parents=True)
    papers_dir = tmp_path / "ICT450"
    papers_dir.mkdir()
    pdf = papers_dir / "paper.pdf"
    _pdf(pdf, "QUESTION 1\nSee Figure 1 and Figure 2.")
    from PIL import Image
    Image.new("RGB", (200, 200), "white").save(pages / "page_001.png")
    content = [
        {"type": "text", "text": "QUESTION 1", "page_idx": 0},
        {"type": "text", "text": "Explain Figure 1 and Figure 2.",
         "page_idx": 0},
        {"type": "text", "text": "(20 marks)", "page_idx": 0},
        {"type": "image", "img_path": "images/fig1.jpg",
         "image_caption": ["Figure 1: Example"], "page_idx": 0,
         "bbox": [100, 100, 300, 300]},
    ]
    content_path = cache / "content_list.json"
    content_path.write_text(json.dumps(content), encoding="utf-8")
    normalized = {
        "paper_id": "ICT450-2023-FEB",
        "model": "vlm",
        "content_list": str(content_path),
        "questions": [{
            "question_id": "ICT450-2023-FEB-Q1",
            "number": 1,
            "page_idx": 0,
            "y": 0,
            "bbox": [0, 0, 100, 20],
            "blocks": ["B0001", "B0002", "B0003"],
            "text": "Explain Figure 1 and Figure 2.",
            "subparts": [],
            "refs": ["Figure 1", "Figure 2"],
            "marks": 20,
            "assets": ["MU-B0004"],
        }],
        "assets": [{
            "asset_id": "MU-B0004",
            "question_index": 0,
            "page_idx": 0,
            "bbox": [100, 100, 300, 300],
            "kind": "image",
            "label": "Figure 1",
            "caption": "Figure 1: Example",
            "img_path": "",
            "table_html": "",
            "provenance": {"parser": "mineru", "model": "vlm"},
        }],
        "fallback": [{
            "asset_id": "FB-Q1-Figure2",
            "question_id": "ICT450-2023-FEB-Q1",
            "label": "Figure 2",
            "page_idx": 0,
            "path": str(pages / "page_001.png"),
            "treatment": "page_crop_fallback",
            "reason": "missing",
        }],
    }
    (review / "normalized.json").write_text(json.dumps(normalized),
                                            encoding="utf-8")
    (tracking / "papers_register.json").write_text(json.dumps({
        "unique_papers": [{
            "paper_id": "ICT450-2023-FEB",
            "file": pdf.name,
            "sha256": "x",
            "pages": 1,
            "month_year": "2023-FEB",
            "month_source": "pdf_text",
        }]}), encoding="utf-8")
    (tracking / "extraction_status.json").write_text(json.dumps({
        "model": "vlm",
        "papers": {"ICT450-2023-FEB": {
            "status": "done", "cache_dir": str(cache)}},
        "summary": {"documents_uploaded": 1},
    }), encoding="utf-8")
    monkeypatch.setattr(bank_build, "TRACKING", tracking)
    monkeypatch.setattr(bank_build, "BANK", bank)
    monkeypatch.setattr(bank_build, "REGISTER",
                        tracking / "papers_register.json")
    monkeypatch.setattr(bank_build, "STATUS",
                        tracking / "extraction_status.json")
    monkeypatch.setattr(bank_build, "REPORT_JSON", bank / "gate1_report.json")
    monkeypatch.setattr(bank_build, "REPORT_MD", bank / "gate1_report.md")
    from src import config
    monkeypatch.setattr(config, "PAPERS_ROOT", tmp_path)

    report = bank_build.build()
    question = json.loads((bank / "questions"
                           / "ICT450-2023-FEB-Q1.json").read_text())
    assert question["assets"]
    assert question["fallback_assets"]
    assert question["refs_unresolved"] == ["Figure 2"]
    assert any(item["code"] == "UNRESOLVED_REFERENCE"
               for item in report["unsure"])
    assert report["index"]["questions"] == 1
    assert (bank / "review" / "index.html").is_file()
