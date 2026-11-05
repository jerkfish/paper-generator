"""CSC429 three-seed pilot selection rules."""
from __future__ import annotations

from src.subjects.csc429 import seed_pilot


def _question(index: int, part: str, marks: int, diagram: bool) -> dict:
    return {
        "question_id": f"CSC429-2024-01-{part}{index}",
        "paper_id": f"CSC429-2024-{index:02d}",
        "part": part,
        "marks": marks,
        "asset_ids": ["asset"] if diagram else [],
        "figure_refs": ["Figure 1"] if diagram else [],
        "asset_status": "linked" if diagram else "missing",
        "review_flags": [],
        "source_spans": [{
            "page": 1, "bbox": [70, 200, 500, 212],
            "text": f"Question {index} text.",
        }],
        "text": f"Question {index} text.",
    }


def test_plan_seed_is_real_bank_and_unique_papers():
    questions = []
    index = 1
    for marks, count, diagram_count in ((5, 4, 2), (10, 8, 3), (20, 2, 1)):
        for offset in range(count):
            questions.append(_question(
                index, "B" if marks == 20 else "A", marks,
                offset < diagram_count))
            index += 1
    assets = {
        f"asset-{index}": {
            "asset_id": f"asset-{index}", "kind": "figure",
            "label": "Figure 1",
            "page": 1, "content_bbox": [70, 100, 500, 190],
            "path": "missing.png", "width_px": 100, "height_px": 80,
        }
        for index in range(1, 21)
    }
    questions = [
        {**question,
         "asset_ids": ([f"asset-{index}"] if question["asset_ids"] else [])}
        for index, question in enumerate(questions, start=1)
    ]
    bank = {"questions": questions}
    plan = seed_pilot.plan_seed(
        1, bank, assets, set(), {}, require_table=False)
    assert len(plan["slots"]) == 11
    assert sum(slot["marks"] for slot in plan["slots"]) == 100
    assert [slot["slot"] for slot in plan["slots"]] == [
        "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "B1"]
    assert len({slot["paper_id"] for slot in plan["slots"]}) == 11
    assert sum(1 for slot in plan["slots"] if slot["diagram"]) == 5
    assert all(
        any(block["type"] == "text" for block in slot["content"])
        for slot in plan["slots"])


def test_numbering_definitions_match_the_updated_list_format():
    import docx
    from docx.oxml.ns import qn

    document = docx.Document(str(seed_pilot.TEMPLATE))
    numbering = seed_pilot._QuestionNumbering(document)
    letter_id = numbering.letter("a")
    numbering.letter("b")
    roman_id = numbering.roman("i")
    root = document.part.numbering_part.element
    formats = {}
    for num in root.findall(qn("w:num")):
        if int(num.get(qn("w:numId"))) not in {letter_id, roman_id}:
            continue
        abstract_id = num.find(qn("w:abstractNumId")).get(qn("w:val"))
        abstract = next(
            item for item in root.findall(qn("w:abstractNum"))
            if item.get(qn("w:abstractNumId")) == abstract_id)
        level = abstract.find(qn("w:lvl"))
        formats[int(num.get(qn("w:numId")))] = (
            level.find(qn("w:numFmt")).get(qn("w:val")),
            level.find(qn("w:lvlText")).get(qn("w:val")),
        )
    assert formats[letter_id] == ("lowerLetter", "%1)")
    assert formats[roman_id] == ("lowerRoman", "%1.")
