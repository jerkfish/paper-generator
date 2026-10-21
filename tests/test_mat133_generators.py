from __future__ import annotations

import random
import re

import docx
from pathlib import Path

import pytest

from src.mat133.build_docx import build_paper_docx, build_scheme_docx, validate_docx
from src.mat133.generators.registry import REGISTRY, generate_topic
from src.mat133.models import Mat133Paper, Mat133Question
from src.render.mathfig import formula_png
from src.mat133.taxonomy import SUBTOPIC_IDS, TOPIC_IDS


def test_registry_covers_every_taxonomy_subtopic() -> None:
    expected = {
        f"{topic}.{sub}"
        for topic in TOPIC_IDS if topic != "other"
        for sub in SUBTOPIC_IDS[topic]
    }
    assert set(REGISTRY) == expected
    assert len(REGISTRY) == 57


@pytest.mark.parametrize("generator_id", sorted(REGISTRY))
def test_generator_outputs_question_and_exact_key(generator_id, tmp_path):
    generator = REGISTRY[generator_id]
    part = generator.generate(random.Random(1234), out_dir=tmp_path)
    assert part.text.strip()
    assert part.answer.strip()
    assert part.solution_steps
    assert part.answer_latex.strip()
    assert part.solution_latex
    for index, latex in enumerate([part.answer_latex, *part.solution_latex]):
        assert formula_png(latex, tmp_path / f"{generator_id}-{index}.png").exists()
    assert part.marks > 0
    assert part.topic == generator.topic
    assert part.subtopic == generator.subtopic
    for field in (part.text, part.answer, *part.solution_steps):
        assert "nan" not in field.lower()
        assert "zoo" not in field.lower()


def test_all_topics_generate_a_paper(tmp_path) -> None:
    questions = []
    for number, topic in enumerate((t for t in TOPIC_IDS if t != "other"), 1):
        parts = generate_topic(topic, seed=21, out_dir=tmp_path / "figures")
        for index, part in enumerate(parts):
            part.label = chr(97 + index)
        questions.append(Mat133Question(number=number, parts=parts))
    paper = Mat133Paper(month="NOVEMBER", year=2026, questions=questions)
    paper_docx = build_paper_docx(paper, tmp_path / "paper.docx")
    scheme_docx = build_scheme_docx(paper, tmp_path / "scheme.docx")
    for path, is_scheme in ((paper_docx, False), (scheme_docx, True)):
        check = validate_docx(path, paper, scheme=is_scheme)
        assert check["xml_valid"]
        assert check["forbidden_tokens"] == []
        if is_scheme:
            assert check["part_labels_found"] == check["expected_parts"]
            body_xml = docx.Document(str(path)).element.body.xml
            table_xml = "".join(re.findall(r"<w:tbl>.*?</w:tbl>",
                                           body_xml, re.S))
            table_text = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>",
                                             table_xml))
            for phrase in ("Working:", "Question:", "Answer:", "Marking notes:",
                           "The denominator cannot be zero", "Now solve",
                           "Subtract", "Use the "):
                assert phrase not in table_text
            assert not re.search(r"(?m)^\s*\d+\.\s", table_text)
            assert "M1" in table_text or "A1" in table_text
            scheme_doc = docx.Document(str(path))
            images = [rel for rel in scheme_doc.part.rels.values()
                      if "image" in rel.target_ref]
            assert len(images) >= len(
                [p for q in paper.questions for p in q.parts]) + 1
        else:
            assert check["question_headings"] == len(paper.questions)
        assert check["has_crest"]
