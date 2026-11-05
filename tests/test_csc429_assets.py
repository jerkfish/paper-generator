"""CSC429 asset crop tests on a synthetic scanned page."""
from __future__ import annotations

import json

from PIL import Image, ImageDraw

from src.subjects.csc429 import assets


def _write(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_caption_is_metadata_not_captured_in_the_crop(tmp_path, monkeypatch):
    tracking = tmp_path / "csc429"
    pages_dir = tracking / "pages"
    layout_dir = tracking / "layout"
    asset_dir = tracking / "assets"
    paper_id = "CSC429-2024-01"
    page_image = pages_dir / paper_id / "page_001.jpg"
    page_image.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("RGB", (600, 800), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((100, 200, 500, 300), fill="black")
    draw.text((200, 318), "Figure 1: Test diagram", fill="black")
    image.save(page_image, "JPEG", quality=90, dpi=(200, 200))
    _write(pages_dir / paper_id / "manifest.json", {
        "paper": "paper.pdf", "paper_id": paper_id, "page_count": 1,
        "pages": [{
            "page": 1, "image": str(page_image.relative_to(tmp_path)),
            "width": 600, "height": 800, "page_points": [600, 800],
            "embedded_images": [], "drawings": 0,
        }],
    })
    _write(layout_dir / f"{paper_id}.json", {
        "paper": "paper.pdf", "paper_id": paper_id,
        "source_kind": "ocr", "pages": [{
            "page": 1, "width": 600, "height": 800,
            "lines": [
                {"text": "QUESTION 1", "bbox": [50, 100, 150, 120]},
                {"text": "Figure 1: Test diagram",
                 "bbox": [200, 318, 400, 330]},
            ],
            "captions": [{"text": "Figure 1: Test diagram",
                          "bbox": [200, 318, 400, 330]}],
        }],
    })
    monkeypatch.setattr(assets, "TRACKING", tracking)
    monkeypatch.setattr(assets, "PAGES", pages_dir)
    monkeypatch.setattr(assets, "LAYOUT", layout_dir)
    monkeypatch.setattr(assets, "ASSETS", asset_dir)
    monkeypatch.setattr(assets.config, "PROJECT_ROOT", tmp_path)
    manifest = assets.build_assets(force=True)
    assert manifest["counts"]["assets"] == 1
    record = manifest["assets"][0]
    assert record["label"] == "Figure 1"
    assert record["kind"] == "figure"
    assert record["confidence"] == "high"
    assert (tmp_path / record["path"]).is_file()
    assert record["bbox_pdf"][1] < 210
    # The caption is metadata only; the delivered crop ends above it.
    assert record["bbox_pdf"][3] <= 318
    assert record["caption"].startswith("Figure 1")
    assert (asset_dir / paper_id / "contact_sheet.png").is_file()


def test_reference_without_caption_is_unresolved(tmp_path, monkeypatch):
    tracking = tmp_path / "csc429"
    pages_dir = tracking / "pages"
    layout_dir = tracking / "layout"
    asset_dir = tracking / "assets"
    paper_id = "CSC429-2024-01"
    page_image = pages_dir / paper_id / "page_001.jpg"
    page_image.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (600, 800), "white").save(page_image, "JPEG")
    _write(pages_dir / paper_id / "manifest.json", {
        "paper": "paper.pdf", "paper_id": paper_id, "page_count": 1,
        "pages": [{
            "page": 1, "image": str(page_image.relative_to(tmp_path)),
            "width": 600, "height": 800, "page_points": [600, 800],
            "embedded_images": [], "drawings": 0,
        }],
    })
    _write(layout_dir / f"{paper_id}.json", {
        "paper": "paper.pdf", "paper_id": paper_id,
        "source_kind": "ocr", "pages": [{
            "page": 1, "width": 600, "height": 800,
            "lines": [{"text": "See Figure 2 for details.",
                       "bbox": [50, 100, 300, 120]}],
            "captions": [],
        }],
    })
    monkeypatch.setattr(assets, "TRACKING", tracking)
    monkeypatch.setattr(assets, "PAGES", pages_dir)
    monkeypatch.setattr(assets, "LAYOUT", layout_dir)
    monkeypatch.setattr(assets, "ASSETS", asset_dir)
    monkeypatch.setattr(assets.config, "PROJECT_ROOT", tmp_path)
    manifest = assets.build_assets(force=True)
    assert manifest["counts"]["assets"] == 0
    assert manifest["counts"]["unresolved"] == 1
    unresolved = manifest["unresolved"][0]
    assert unresolved["label"] == "Figure 2"
    assert unresolved["page_image"]
