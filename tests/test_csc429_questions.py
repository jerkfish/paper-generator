"""Tests for the CSC429 verbatim question-bank builder.

The tests use small synthetic layouts so they never depend on the real
dataset.  They cover furniture removal, page continuation, OCR heading
variants, heading recovery, subparts, marks, references and unsure entries.
"""
from __future__ import annotations

import json
from pathlib import Path

from src.subjects.csc429.questions import build_question_bank


def _line(text: str, x: float, y: float, w: float = 400, h: float = 12) -> dict:
    return {"text": text, "bbox": [x, y, x + w, y + h]}


def _page(number: int, lines: list[dict]) -> dict:
    return {
        "page": number,
        "width": 600,
        "height": 800,
        "lines": lines,
        "captions": [],
    }


def _write_layout(root: Path, paper_id: str, pages: list[dict]) -> Path:
    layout_dir = root / "layout"
    layout_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "paper": f"{paper_id}.pdf",
        "paper_id": paper_id,
        "source_kind": "text",
        "pages": pages,
        "caption_lines": 0,
    }
    path = layout_dir / f"{paper_id}.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _base_pages() -> list[dict]:
    """Three content pages plus a PART B page.

    Part A has question 1, 2 and 4; question 3 is intentionally absent so
    the builder must recover it.  Question 4 has no mark block.
    """
    return [
        _page(
            1,
            [
                _line("CONFIDENTIAL", 80, 20, 90),
                _line("CS/JAN 2099/CSC429", 400, 20, 140),
                _line("PART A (50 MARKS)", 70, 90, 200),
                _line("QUESTION 1", 70, 110, 120),
                _line(
                    "Question 1 is based on Figure 2(a) and Table 1.",
                    70,
                    130,
                    380,
                ),
                _line("a) Explain the diagram in Figure 2(a).", 70, 160, 380),
                _line("(2 marks)", 500, 175, 70),
                _line("b) Name Table 1 columns.", 70, 200, 300),
                _line("and continue the answer here.", 70, 220, 300),
                _line("(3 marks)", 500, 235, 70),
                _line("© Hak Cipta Universiti Teknologi MARA", 70, 780, 300),
            ],
        ),
        _page(
            2,
            [
                _line("CONFIDENTIAL", 80, 20, 90),
                _line("2", 300, 20, 10),
                _line("This is a continuation of part b.", 70, 100, 320),
                _line("OUESTION 2", 70, 200, 120),
                _line("Sketch Figure 2.", 70, 225, 200),
                _line("(1 mark)", 500, 240, 70),
            ],
        ),
        _page(
            3,
            [
                _line("QUESTION 4", 70, 100, 120),
                _line("Discuss Table 1.", 70, 125, 200),
                _line("PART B (10 MARKS)", 70, 300, 200),
                _line("QUESTION 1", 70, 330, 120),
                _line("Write an essay.", 70, 355, 200),
                _line("(10 marks)", 500, 370, 70),
            ],
        ),
    ]


def _questions(bank: dict, paper_id: str) -> list[dict]:
    return [q for q in bank["questions"] if q["paper_id"] == paper_id]


def test_question_bank_verbatim_parts_subparts_marks_and_refs(tmp_path: Path):
    paper_id = "CSC429-2099-01"
    _write_layout(tmp_path, paper_id, _base_pages())

    bank = build_question_bank(tmp_path)
    assert bank["llm_used"] is False
    assert bank["cost_usd"] == 0
    assert bank["subject"] == "CSC429"
    assert bank["summary"]["papers"] == 1

    questions = _questions(bank, paper_id)
    assert [q["question_id"] for q in questions] == [
        f"{paper_id}-A1",
        f"{paper_id}-A2",
        f"{paper_id}-A3",  # recovered placeholder
        f"{paper_id}-A4",
        f"{paper_id}-B1",
    ]

    q1 = questions[0]
    expected_q1 = "\n".join(
        [
            "Question 1 is based on Figure 2(a) and Table 1.",
            "a) Explain the diagram in Figure 2(a).",
            "b) Name Table 1 columns.",
            "and continue the answer here.",
            "This is a continuation of part b.",
        ]
    )
    assert q1["text"] == expected_q1
    assert q1["part"] == "A"
    assert q1["question_no"] == 1
    assert q1["slot"] == "A1"
    assert q1["pages"] == [1, 2]
    assert q1["marks"] == 5
    assert q1["marks_source"] == "explicit"
    assert q1["figure_refs"] == ["Figure 2", "Table 1"]
    # Right-margin mark blocks and page furniture are not part of the body.
    assert "(2 marks)" not in q1["text"]
    assert "(3 marks)" not in q1["text"]
    assert "CONFIDENTIAL" not in q1["text"]
    assert "Hak Cipta" not in q1["text"]
    # Verbatim source spans reconstruct the text.
    assert "\n".join(span["text"] for span in q1["source_spans"]) == q1["text"]
    assert {span["page"] for span in q1["source_spans"]} == {1, 2}

    assert [sub["label"] for sub in q1["subparts"]] == ["a", "b"]
    assert q1["subparts"][0]["marks"] == 2
    assert q1["subparts"][0]["marks_source"] == "explicit"
    assert q1["subparts"][1]["marks"] == 3
    assert q1["subparts"][1]["marks_source"] == "explicit"
    assert "This is a continuation of part b." in q1["subparts"][1]["text"]
    assert q1["subparts"][0]["figure_refs"] == ["Figure 2"]

    # The title-case reference must not become a second heading.
    assert "Question 1 is based on Figure 2(a) and Table 1." in q1["text"]

    # OCR heading variant is detected and flagged, not dropped.
    q2 = questions[1]
    assert q2["question_no"] == 2
    assert q2["text"] == "Sketch Figure 2."
    assert q2["marks"] == 1
    assert q2["marks_source"] == "explicit"
    assert [sub["label"] for sub in q2["subparts"]] == ["main"]
    assert "ocr_heading_variant" in q2["review_flags"]

    # One missing number -> recovered heading, no invented body text.
    q3 = questions[2]
    assert q3["heading_recovered"] is True
    assert q3["text"] == ""
    assert q3["source_spans"] == []
    assert q3["marks"] is None
    assert q3["confidence"] < 0.5
    assert any(
        entry["code"] == "heading_recovered"
        and entry.get("question_id") is None
        for entry in bank["unsure"]
    )

    # Missing marks are recorded as null/unsure, never inferred.
    q4 = questions[3]
    assert q4["text"] == "Discuss Table 1."
    assert q4["marks"] is None
    assert q4["marks_source"] == "missing"
    assert "missing_marks" in q4["review_flags"]
    assert any(
        entry["code"] == "missing_marks"
        and entry.get("question_id") == q4["question_id"]
        for entry in bank["unsure"]
    )

    # PART B restarts numbering; ids are part-scoped.
    b1 = questions[4]
    assert b1["part"] == "B"
    assert b1["question_no"] == 1
    assert b1["question_id"] == f"{paper_id}-B1"
    assert b1["marks"] == 10

    assert bank["summary"]["questions"] == 5
    assert bank["summary"]["by_part"] == {"A": 4, "B": 1}
    assert bank["summary"]["with_marks"] == 3
    assert bank["summary"]["missing_marks"] == 2
    assert bank["summary"]["heading_recovered"] == 1


def test_assets_are_linked_by_label_and_source_page(tmp_path: Path):
    paper_id = "CSC429-2099-02"
    _write_layout(tmp_path, paper_id, _base_pages())
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "manifest.json").write_text(
        json.dumps(
            {
                "assets": [
                    {
                        "asset_id": "fig-2-p1",
                        "label": "Figure 2",
                        "page": 1,
                        "paper_id": paper_id,
                    },
                    {
                        "asset_id": "fig-2-p2",
                        "label": "Figure 2",
                        "page": 2,
                        "paper_id": paper_id,
                    },
                    {
                        "asset_id": "tab-1-p1",
                        "label": "Table 1",
                        "page": 1,
                        "paper_id": paper_id,
                    },
                    {
                        "asset_id": "tab-1-p3",
                        "label": "Table 1",
                        "page": 3,
                        "paper_id": paper_id,
                    },
                ]
            }
        ),
        encoding="utf-8",
    )

    bank = build_question_bank(tmp_path)
    q1, q2 = _questions(bank, paper_id)[:2]
    assert q1["asset_ids"] == ["fig-2-p1", "tab-1-p1"]
    assert q1["asset_status"] == "linked"
    assert q2["asset_ids"] == ["fig-2-p2"]
    assert q2["asset_status"] == "linked"
    assert bank["summary"]["with_assets"] == 3
    assert bank["summary"]["unresolved_refs"] == 0


def test_multiple_heading_gaps_and_long_question_are_unsure(tmp_path: Path):
    paper_id = "CSC429-2099-03"
    pages = [
        _page(1, [_line("PART A", 70, 90), _line("QUESTION 1", 70, 110),
                  _line("Body on page one.", 70, 130)]),
        _page(2, [_line("Body on page two.", 70, 100)]),
        _page(3, [_line("Body on page three.", 70, 100)]),
        _page(4, [_line("QUESTION 5", 70, 100), _line("Last question.", 70, 125)]),
    ]
    _write_layout(tmp_path, paper_id, pages)

    bank = build_question_bank(tmp_path)
    q1 = _questions(bank, paper_id)[0]
    assert q1["pages"] == [1, 2, 3]
    assert "question_spans_many_pages" in q1["review_flags"]
    codes = {entry["code"] for entry in bank["unsure"]}
    assert "long_question" in codes
    assert "multiple_heading_gaps" in codes
    # Four gap numbers (2, 3, 4) are recovered and reported individually.
    recovered = [
        q for q in _questions(bank, paper_id) if q["heading_recovered"]
    ]
    assert len(recovered) == 3


def test_missing_bboxes_are_reported_without_failing(tmp_path: Path):
    paper_id = "CSC429-2099-04"
    layout_dir = tmp_path / "layout"
    layout_dir.mkdir(parents=True)
    (layout_dir / f"{paper_id}.json").write_text(
        json.dumps(
            {
                "paper": "broken.pdf",
                "paper_id": paper_id,
                "source_kind": "ocr",
                "pages": [
                    {
                        "page": 1,
                        "width": 600,
                        "height": 800,
                        "lines": [
                            {"text": "QUESTION 1"},  # no bbox at all
                            {"text": "PART A", "bbox": [70, 90, 200, 102]},
                        ],
                        "captions": [],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    bank = build_question_bank(tmp_path)
    codes = {entry["code"] for entry in bank["unsure"]}
    assert "missing_bbox" in codes
    assert "no_questions_found" in codes
    assert bank["summary"]["questions"] == 0
    assert bank["papers"][0]["status"] == "no_questions"


def test_registered_paper_without_layout_is_reported(tmp_path: Path):
    (tmp_path / "papers_register.json").write_text(
        json.dumps(
            [
                {
                    "source": "missing.pdf",
                    "month": "MARCH",
                    "year": 2098,
                    "duplicate_of": "",
                }
            ]
        ),
        encoding="utf-8",
    )

    bank = build_question_bank(tmp_path)
    assert bank["summary"]["papers"] == 1
    assert bank["papers"][0]["paper_id"] == "CSC429-2098-03"
    assert bank["papers"][0]["status"] == "no_layout"
    assert any(
        entry["code"] == "no_layout_coordinates" for entry in bank["unsure"]
    )


def test_deterministic_rebuild(tmp_path: Path):
    paper_id = "CSC429-2099-05"
    _write_layout(tmp_path, paper_id, _base_pages())

    first = build_question_bank(tmp_path)
    second = build_question_bank(tmp_path)
    assert first == second
    on_disk = json.loads(
        (tmp_path / "question_bank_draft.json").read_text(encoding="utf-8")
    )
    assert on_disk["summary"] == first["summary"]
