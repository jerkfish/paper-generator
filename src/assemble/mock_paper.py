"""Step 7 - assemble the mock paper and marking scheme PDFs.

Layout mirrors the modern two-part papers (JUN/DEC 2019, FEB 2022):
cover -> instructions -> PART A (10 x [2m + 6m]) -> PART B (2 x [5m + 5m]),
total 100 marks, 3 hours. Computed questions (classical ciphers, ACM/ACL)
fill the slots where modern papers actually place computation; theory slots
are clearly-visible placeholders.

HTML -> PDF via headless Edge (Playwright); ACM diagrams rendered with
Graphviz (dot -> svg).

Run:  uv run python -m src.assemble.mock_paper
"""
from __future__ import annotations

import html
import json
import subprocess

from pypdf import PdfReader

from src.config import OUTPUTS_DIR

DOT_BIN = r"C:\Program Files\Graphviz\bin\dot.exe"

PLACEHOLDER = ("[THEORY SLOT - {topic}, {marks} marks, {task}]<br/>"
               "<i>(placeholder until the sourced-theory module is built)</i>")


def _load_computed() -> list[dict]:
    return json.loads((OUTPUTS_DIR / "computed_questions.json")
                      .read_text(encoding="utf-8"))


def _load_acm() -> list[dict]:
    return json.loads((OUTPUTS_DIR / "acm_questions.json").read_text(encoding="utf-8"))


def dot_to_svg(dot_source: str) -> str:
    try:
        proc = subprocess.run([DOT_BIN, "-Tsvg"], input=dot_source, text=True,
                              capture_output=True, timeout=60)
        if proc.returncode == 0:
            svg = proc.stdout
            if svg.startswith("<?xml"):
                svg = svg[svg.index(">") + 1:]
            return svg
    except (OSError, subprocess.SubprocessError):
        pass
    return ""


def _pick(questions: list[dict], cipher: str, task: str, marks: int,
          n: int = 1) -> list[dict]:
    return [q for q in questions
            if q["cipher"] == cipher and q["task"] == task and q["marks"] == marks][:n]


def build_slots(computed: list[dict], acm: list[dict]) -> dict[str, dict | None]:
    caesar2 = _pick(computed, "caesar", "decrypt", 2, 2)
    cipher6 = [q for q in computed if q["marks"] == 6 and q["task"] == "encrypt"]
    slots = {
        "Q2a": caesar2[0] if caesar2 else None,
        "Q4a": caesar2[1] if len(caesar2) >= 2 else None,
        "Q2b": cipher6[0] if len(cipher6) >= 1 else None,
        "Q4b": cipher6[1] if len(cipher6) >= 2 else None,
        "Q5b": cipher6[2] if len(cipher6) >= 3 else None,
        "Q3b": acm[0] if acm else None,
    }
    return slots


def _question_text(q: dict) -> str:
    marks = q.get("marks") or (q.get("scenario") or {}).get("marks") or 0
    return q["question"].replace(f"({marks} marks)", "").strip()


def _qblock(num: int, a: str, b: str, am: int, bm: int) -> str:
    return (f'<div class="q"><div class="qno">QUESTION {num}</div>'
            f'<p class="sub">a) {a} <span class="marks">({am} marks)</span></p>'
            f'<p class="sub">b) {b} <span class="marks">({bm} marks)</span></p>'
            f"</div>")


def _paper_html(slots: dict, cover_png: str = "") -> str:
    topics = {1: "attacks/malware", 2: "classical ciphers",
              3: "access control models", 4: "classical ciphers",
              5: "authentication/biometrics", 6: "software/OS security",
              7: "network security", 8: "trusted computing",
              9: "authentication/biometrics", 10: "attacks/malware"}

    a_parts = []
    for i in range(1, 11):
        key = f"Q{i}"
        a, b = None, None
        if i == 2:
            a = _question_text(slots["Q2a"]) if slots["Q2a"] else None
            b = _question_text(slots["Q2b"]) if slots["Q2b"] else None
        elif i == 3:
            a = PLACEHOLDER.format(topic="access control models", marks=2,
                                   task="short objective")
            b = _question_text(slots["Q3b"]) if slots["Q3b"] else None
        elif i == 4:
            a = _question_text(slots["Q4a"]) if slots["Q4a"] else None
            b = _question_text(slots["Q4b"]) if slots["Q4b"] else None
        elif i == 5:
            a = PLACEHOLDER.format(topic="authentication/biometrics", marks=2,
                                   task="short objective")
            b = _question_text(slots["Q5b"]) if slots["Q5b"] else None
        if a is None:
            a = PLACEHOLDER.format(topic=topics[i], marks=2, task="short objective")
        if b is None:
            b = PLACEHOLDER.format(topic=topics[i], marks=6, task="define/explain")
        a_parts.append(_qblock(i, a, b, 2, 6))

    b_parts = []
    for i, (topic, task) in enumerate([
            ("attacks/malware", "scenario/justify"),
            ("authentication/biometrics", "scenario/justify")], start=1):
        a = PLACEHOLDER.format(topic=topic, marks=5, task=task)
        b = PLACEHOLDER.format(topic=topic, marks=5, task=task)
        b_parts.append(_qblock(i, a, b, 5, 5))

    cover = (f'<img src="file:///{cover_png.replace(chr(92), "/")}" '
             f'style="width:100%; display:block;">'
             '<div style="page-break-before: always;"></div>') if cover_png else ""
    return f"""<!doctype html><html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 2.2cm 2cm; }}
body {{ font-family: 'Times New Roman', serif; font-size: 11pt; }}
h2.part {{ text-align: center; font-size: 13pt; page-break-before: always; }}
h2.part.first {{ page-break-before: auto; }}
.q {{ margin-bottom: 1.6em; }}
.qno {{ font-weight: bold; }}
.sub {{ margin: 3px 0 3px 1em; line-height: 1.35; }}
.marks {{ float: right; }}
.footer {{ text-align: center; margin-top: 2em; }}
</style></head><body>
{cover}
<h2 class="part first">PART A (10 Questions)</h2>
{''.join(a_parts)}
<h2 class="part">PART B (2 Questions)</h2>
{''.join(b_parts)}
<div class="footer">END OF QUESTION PAPER</div>
</body></html>"""


_SCHEME_SLOTS = [
    ("Q2a", "PART A Q2a (2 marks)", "computed (solver validated on real papers)"),
    ("Q2b", "PART A Q2b (6 marks)", "computed - convention unverified (encrypt-only)"),
    ("Q3b", "PART A Q3b (6 marks)", "computed (consistency machine-verified)"),
    ("Q4a", "PART A Q4a (2 marks)", "computed (solver validated on real papers)"),
    ("Q4b", "PART A Q4b (6 marks)", "computed - convention unverified (encrypt-only)"),
    ("Q5b", "PART A Q5b (6 marks)",
     "computed - convention unverified (Playfair I/J + X padding pending slide check)"),
]


def _scheme_html(slots: dict) -> str:
    items = []
    for key, label, _confidence in _SCHEME_SLOTS:
        q = slots[key]
        if q is None:
            items.append(f'<div class="q"><b>{label} - {key}</b> '
                         '<span class="lab placeholder">no computed question '
                         'available in this slot</span></div>')
            continue
        if q.get("dot"):
            confidence, kind = "computed (consistency machine-verified)", "computed"
        elif q.get("cipher") == "playfair":
            confidence, kind = ("computed - convention unverified (Playfair I/J "
                                "+ X padding pending slide check)"), "unverified"
        elif q.get("task") == "decrypt":
            confidence, kind = ("computed (solver validated on real papers)"), "computed"
        else:
            confidence, kind = ("computed - convention unverified (encrypt-only)"), \
                "unverified"
        body = f"<pre>{html.escape(q['question'])}</pre>"
        if q.get("answer"):
            body += (f'<div class="answer">{q["answer"]}</div>'
                     if "matrix" not in str(q.get("answer")) else
                     f'<div class="answer">{q["answer"]}</div>')
        if q.get("dot"):
            body += f'<div class="dot">{dot_to_svg(q["dot"])}</div>'
        items.append(f'<div class="q"><b>{label}</b> '
                     f'<span class="lab {kind}">{confidence}</span>{body}</div>')

    items.append(
        '<div class="q"><b>All remaining slots (theory placeholders, 72 marks)</b> '
        '<span class="lab placeholder">placeholder - sourced-theory module not '
        'built yet</span></div>')
    return """<!doctype html><html><head><meta charset="utf-8">
<style>
@page {{ size: A4; margin: 2cm; }}
body {{ font-family: 'Times New Roman', serif; font-size: 11pt; }}
h1 {{ text-align: center; }}
.q {{ margin-bottom: 1.2em; }}
pre {{ font-family: 'Courier New', monospace; font-size: 9.5pt; white-space: pre-wrap;
      background: #f6f6f6; padding: 6px; }}
.answer {{ border-left: 3px solid #666; padding-left: 8px; margin: 6px 0; }}
.lab {{ font-style: italic; font-size: 9pt; }}
.computed {{ color: #1a6b1a; }}
.unverified {{ color: #a06a00; }}
.placeholder {{ color: #888; }}
.dot svg {{ max-width: 100%; }}
</style></head><body>
<h1>CSC662 - MARKING SCHEME (mock paper, October 2026)</h1>
<p>Confidence labels: <span class="computed">computed</span> /
<span class="unverified">computed - convention unverified</span> /
<span class="placeholder">placeholder</span>.</p>
""" + "".join(items) + "</body></html>"


def html_to_pdf(page_html: str, out_path) -> int:
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="msedge", headless=True)
        page = browser.new_page()
        page.set_content(page_html, wait_until="load")
        page.pdf(path=str(out_path), format="A4", print_background=True)
        browser.close()
    return len(PdfReader(str(out_path)).pages)


def main() -> None:
    computed = _load_computed()
    acm = _load_acm()
    slots = build_slots(computed, acm)
    used = [k for k, v in slots.items() if v]
    computed_marks = sum(8 if k in ("Q2a", "Q2b", "Q4a", "Q4b", "Q5b") else 6
                         for k in used)
    print(f"computed slots filled: {used} -> {computed_marks} marks "
          f"(placeholders carry the rest to 100)")

    # pixel-faithful cover page (see src/assemble/cover.py)
    from src.assemble import cover as cover_mod

    cover_png = OUTPUTS_DIR / "cover_page.png"
    n_pages = 6  # measured from the reference cover; updated below
    cover_mod.render_cover_png(cover_mod.build_cover_html(n_pages), cover_png)
    paper_html = _paper_html(slots, cover_png=str(cover_png))
    probe = OUTPUTS_DIR / "mock_paper_probe.pdf"
    paper_pages = html_to_pdf(paper_html, probe)
    cover_mod.render_cover_png(cover_mod.build_cover_html(paper_pages), cover_png)
    paper_html = _paper_html(slots, cover_png=str(cover_png))
    paper_pages = html_to_pdf(paper_html, OUTPUTS_DIR / "mock_paper_01.pdf")
    probe.unlink(missing_ok=True)

    scheme_pages = html_to_pdf(_scheme_html(slots), OUTPUTS_DIR / "mock_scheme_01.pdf")
    print(f"mock_paper_01.pdf: {paper_pages} pages")
    print(f"mock_scheme_01.pdf: {scheme_pages} pages")

    print("\n=== layout comparison (vs real modern papers) ===")
    real_pages = {"CSC662 JUNE 2019": 7, "CSC662 DECEMBER 2019": 6,
                  "CSC662 FEBRUARY 2022": 14}
    for name, pages in real_pages.items():
        print(f"  real {name}: {pages} pages | mock: {paper_pages} pages "
              f"(diff {'+' if paper_pages - pages >= 0 else ''}{paper_pages - pages})")
    print("  structure: real = Part A 10x(2+6) + Part B 2x(5+5) = 100 marks")
    print(f"  mock     = same slotting; {computed_marks} computed + "
          f"{100 - computed_marks} placeholder marks = 100")
    print("  differences: placeholders instead of real theory text; 'MOCK' header; "
          "no real Answer Booklet; fonts/spacing approximated; FEB 2022 includes "
          "a name/marks-grid cover (14 pages) - ours does not.")


if __name__ == "__main__":
    main()
