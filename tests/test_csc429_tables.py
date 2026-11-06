"""Native table reconstruction for the CSC429 pilot."""
from __future__ import annotations

from src.subjects.csc429 import seed_pilot, tables


def _line(text, x, y, w, h=12):
    return {"text": text, "bbox": [x, y, x + w, y + h]}


def test_table_is_recreated_without_its_caption():
    asset = {
        "asset_id": "CSC429-2099-01-T1",
        "kind": "table",
        "label": "Table 1",
        "content_bbox": [50, 120, 550, 250],
    }
    page = {
        "width": 600,
        "height": 800,
        "lines": [
            _line("Table 1: Machine Instruction", 200, 100, 220),
            _line("Zero-address", 100, 130, 100),
            _line("One-address", 250, 130, 100),
            _line("Three-address", 400, 130, 120),
            _line("PUSH m", 100, 150, 70),
            _line("LOAD m", 250, 150, 70),
            _line("ADD (x,y,z)", 400, 150, 100),
            _line("POP m", 100, 170, 70),
            _line("STOR m", 250, 170, 70),
            _line("SUB (x,y,z)", 400, 170, 100),
        ],
    }
    table = tables.extract_table(asset, page)
    assert table is not None
    assert table["columns"] == 3
    assert [row["cells"][0]["text"] for row in table["rows"]] == [
        "Zero-address", "PUSH m", "POP m"
    ]
    assert table["rows"][2]["cells"][2]["text"] == "SUB (x,y,z)"
    assert all("Table 1:" not in cell["text"]
               for row in table["rows"] for cell in row["cells"])


def test_mixed_figure_is_recreated_as_text_not_prompt_text():
    question = {
        "source_spans": [
            {"page": 1, "bbox": [70, 300, 520, 315],
             "text": "a) Read the excerpt in Figure 1."},
            {"page": 1, "bbox": [80, 400, 500, 415],
             "text": "The excerpt is a long paragraph about a loom and punched cards."},
            {"page": 1, "bbox": [80, 415, 480, 430],
             "text": "The next line continues the same excerpt for the figure."},
        ],
        "figure_refs": ["Figure 1"],
    }
    asset = {
        "asset_id": "CSC429-2099-01-F1",
        "kind": "figure",
        "label": "Figure 1",
        "confidence": "medium",
        "review_flags": ["prose_column"],
        "content_bbox": [300, 250, 560, 460],
    }
    page = {
        "width": 600,
        "height": 800,
        "lines": [
            _line("a) Read the excerpt in Figure 1.", 70, 300, 450, 15),
            _line("The excerpt is a long paragraph about a loom and punched cards.",
                  80, 400, 420, 15),
            _line("The next line continues the same excerpt for the figure.",
                  80, 415, 400, 15),
        ],
    }
    assert seed_pilot._is_mixed_asset(asset, page, question)
    lines = seed_pilot._mixed_lines(asset, page)
    texts = [line["text"] for line in lines]
    assert any("loom" in text for text in texts)
    assert not any(text.startswith("a)") for text in texts)


def test_label_only_subpart_is_joined_to_its_text():
    spans = [
        {"page": 1, "bbox": [70, 100, 90, 112], "text": "a)"},
        {"page": 1, "bbox": [100, 100, 300, 112], "text": "Define interrupt."},
        {"page": 1, "bbox": [70, 130, 90, 142], "text": "b)"},
        {"page": 1, "bbox": [100, 130, 350, 142], "text": "Give an example."},
    ]
    paragraphs = seed_pilot._group_paragraphs(spans)
    assert [paragraph["text"] for paragraph in paragraphs] == [
        "a) Define interrupt.", "b) Give an example."
    ]
