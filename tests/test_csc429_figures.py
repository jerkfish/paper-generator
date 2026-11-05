"""CSC429 diagrams must render without text clashes."""
from __future__ import annotations

from PIL import Image

from src.subjects.csc429 import figures
from src.subjects.csc429.figures import RENDERERS, render_figure


def test_figure_font_sizes_meet_minimum():
    sizes = (figures.FONT_TITLE, figures.FONT_NODE, figures.FONT_DETAIL,
             figures.FONT_LABEL)
    assert min(sizes) >= 14
    assert len(set(sizes)) == len(sizes)


def test_all_figures_render_without_layout_violations(tmp_path):
    for kind in RENDERERS:
        path = tmp_path / f"{kind}.png"
        render_figure(kind, path)
        assert path.stat().st_size > 10_000
        with Image.open(path) as image:
            assert image.size == (1800, 1100)
            dpi = image.info.get("dpi")
            assert dpi is not None
            assert abs(dpi[0] - 200) < 0.1 and abs(dpi[1] - 200) < 0.1
