"""MAT133 math rendering framework smoke tests."""
from __future__ import annotations

from pathlib import Path

from src.render.mathfig import (formula_png, function_plot, normalize_latex,
                                number_line, pie_chart)


def test_formula_renders_symbols_and_fraction(tmp_path):
    out = formula_png(
        r"\frac{4x}{x-4} \leq 3 \rightarrow (-\infty,-3)\cup(2,\infty)",
        tmp_path / "formula.png")
    assert out.exists() and out.stat().st_size > 1000
    assert normalize_latex(r"a \le b \ge c") == r"a \leq b \geq c"


def test_graph_pie_and_number_line(tmp_path):
    graph = function_plot("(x-1)**2/-8 - 3", -3, 6, tmp_path / "graph.png")
    pie = pie_chart(["A", "B"], [3, 7], tmp_path / "pie.png")
    line = number_line([(-10, -3, False, False), (2, 10, False, False)],
                       points=[-3, 2], out_path=tmp_path / "line.png")
    for path in (graph, pie, line):
        assert path.exists() and path.stat().st_size > 1000
