"""Build the mock paper .docx from the real FEB 2026 docx as template.

Working copy only - the original is never modified. Edits:
1. tokens: CS/FEB 2026/CSC662 -> CS/MOCK OCT 2026/CSC662 (cover + headers);
   conversion-artifact fixes (Tthe, CONFI DENTIAL, Teknologl, PART S, ...).
2. course text boxes: clean 4 rows (COURSE/COURSE CODE/EXAMINATION/TIME and
   COMPUTER SECURITY/CSC662/OCTOBER 2026 (MOCK)/3 HOURS).
3. body: all real exam content removed; generated blocks inserted by cloning
   the template's own question-block XML (headings, scenario, a)/b) numbered
   items, right-aligned "(N marks)" lines). numIds are reused from the
   original blocks so a)/b) numbering restarts per question.
4. "consists of N printed pages": N from the exported PDF page count.
5. PDF export via Microsoft Word (COM). Page-1 pixel comparison (MAD/SSIM)
   against the raw template rendered the same way.

Run:  uv run python -m src.assemble.build_docx_paper
"""
from __future__ import annotations

import copy
import json
import re
import subprocess
import tempfile
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

from src.config import OUTPUTS_DIR, subject_reference_dir

SRC = (subject_reference_dir("CSC662") /
       "CSC662 FEBRUARY 2026-raw docx.docx")
OUT_DOCX = OUTPUTS_DIR / "mock_paper_01.docx"
OUT_PDF = OUTPUTS_DIR / "mock_paper_01.pdf"
DOT_BIN = r"C:\Program Files\Graphviz\bin\dot.exe"

REF_CODE_OLD = "CS/FEB   2026/CSC662"
REF_CODE_NEW = "CS/MOCK OCT 2026/CSC662"
PART_A_HEADING = "PART A (80 MARKS)"
PART_B_HEADING = "PART B (20 MARKS)"

PLACEHOLDER = "[THEORY SLOT - {topic}, {marks} marks, {task}]"

# numIds used by the original Part A / Part B blocks (letters restart per block)
A_NUMIDS = ["11", "10", "8", "8", "7", "6", "5", "4", "3", "3"]
B_NUMIDS = ["2", "1"]


def set_para_text(p, text: str, keep_first_run: bool = True) -> None:
    """Write text into a paragraph element, preserving the first run's rPr.
    Newlines become <w:br/> inside that run."""
    runs = p.findall(qn("w:r"))
    if not runs:
        r = OxmlElement("w:r")
        p.append(r)
        runs = [r]
    for r in runs[1:]:
        p.remove(r)
    r0 = runs[0]
    for t in list(r0.findall(qn("w:t")))[1:]:
        r0.remove(t)
    t_el = r0.find(qn("w:t"))
    if t_el is None:
        t_el = OxmlElement("w:t")
        r0.append(t_el)
    parts = str(text).split("\n")
    t_el.text = parts[0]
    t_el.set(qn("xml:space"), "preserve")
    for extra in parts[1:]:
        r0.append(OxmlElement("w:br"))
        t2 = OxmlElement("w:t")
        t2.text = extra
        t2.set(qn("xml:space"), "preserve")
        r0.append(t2)


def para_text(p) -> str:
    return "".join(t.text or "" for t in p.findall(".//" + qn("w:t")))


def _has_graphics(p) -> bool:
    """True when the paragraph carries something set_para_text would destroy."""
    for tag in ("w:drawing", "w:pict", "w:object", "w:instrText", "w:fldSimple"):
        if p.find(".//" + qn(tag)) is not None:
            return True
    return False


def para_replace(p, old: str, new: str) -> bool:
    """Replace a token inside the runs that carry it - never removes runs
    (paragraphs can hold drawings/fields that must survive)."""
    joined = para_text(p)
    if old not in joined:
        return False
    done = False
    for t in p.findall(".//" + qn("w:t")):
        if old in (t.text or ""):
            t.text = t.text.replace(old, new)
            done = True
    if not done:
        if _has_graphics(p):
            # split token in a paragraph with a drawing/field: leave it to the
            # explicit per-run replacements instead of flattening the paragraph
            return False
        set_para_text(p, joined.replace(old, new))
    return True


def patch_runs(xml: str, fixes: list[tuple[str, str]]) -> str:
    """Apply exact whole-<w:t> text replacements in an XML part."""
    def repl(m: re.Match) -> str:
        text = m.group(2)
        for old, new in fixes:
            if text == old:
                text = new
                break
        return m.group(1) + text + m.group(3)
    return re.sub(r"(<w:t\b[^>]*>)([^<]*)(</w:t>)", repl, xml)


def patch_refcode_box(xml: str, width_pt: float = 145.0) -> str:
    """Widen the header's ref-code VML text box in place. The template box is
    ~103pt wide, sized for 'CS/FEB 2026/CSC662'; the longer mock code wraps and
    the second line is clipped outside the 12pt-high box."""
    def repl(m: re.Match) -> str:
        block = m.group(0)
        if "CS/MOCK OCT" not in block:
            return block
        ml = re.search(r"margin-left:([\d.]+)pt", block)
        wd = re.search(r"width:([\d.]+)pt", block)
        if not (ml and wd):
            return block
        right = float(ml.group(1)) + float(wd.group(1))
        left = right - width_pt
        block = re.sub(r"margin-left:[\d.]+pt", f"margin-left:{left:.2f}pt",
                       block, count=1)
        block = re.sub(r"width:[\d.]+pt", f"width:{width_pt:.2f}pt",
                       block, count=1)
        return block
    return re.sub(r"<v:shape\b.*?</v:shape>", repl, xml, flags=re.S)


def _num_id_counter(doc) -> int:
    numbering = doc.part.numbering_part.element
    ids = [int(n.get(qn("w:numId"))) for n in numbering.findall(qn("w:num"))]
    return max(ids, default=0) + 1


def clone_numbering(doc, old_numid: str, new_numid: int) -> str:
    """Create a fresh w:num that reuses an existing abstractNum but restarts
    at 1. Reusing the template numId across questions continues the lettering
    (Q4 showed c)/d) because it shared Q3's numId)."""
    numbering = doc.part.numbering_part.element
    abstract = None
    for num in numbering.findall(qn("w:num")):
        if num.get(qn("w:numId")) == str(old_numid):
            abstract = num.find(qn("w:abstractNumId")).get(qn("w:val"))
            break
    if abstract is None:
        raise KeyError(f"numId {old_numid} not found")
    num = OxmlElement("w:num")
    num.set(qn("w:numId"), str(new_numid))
    abs_el = OxmlElement("w:abstractNumId")
    abs_el.set(qn("w:val"), abstract)
    num.append(abs_el)
    override = OxmlElement("w:lvlOverride")
    override.set(qn("w:ilvl"), "0")
    start = OxmlElement("w:startOverride")
    start.set(qn("w:val"), "1")
    override.append(start)
    num.append(override)
    numbering.append(num)
    return str(new_numid)


def fix_cover_refcode(p) -> None:
    """Keep the longer mock ref code on one line: trim the padding spaces and
    make the code's spaces non-breaking (the cover token is split across runs)."""
    ts = p.findall(".//" + qn("w:t"))
    code_t = next((t for t in ts if "CS/MOCK OCT" in (t.text or "")), None)
    if code_t is None:
        return
    code_t.text = code_t.text.replace("CS/MOCK OCT", "CS/MOCK OCT")
    after = False
    for t in ts:
        if t is code_t:
            after = True
            continue
        if after and (t.text or "") == " ":
            t.text = " "
            break
    for t in ts:
        txt = t.text or ""
        if len(txt) >= 20 and not txt.strip():
            t.text = " " * 27
            t.set(qn("xml:space"), "preserve")
            break


def _strip_char_scale(p) -> None:
    """Remove w:w (character scaling); cloned 'COURSE' paragraphs carry 105%,
    which makes 'COURSE CODE' wrap inside the course text box."""
    for el in p.findall(".//" + qn("w:w")):
        el.getparent().remove(el)


def _role(blocks: list, text: str) -> int:
    for i, p in enumerate(blocks):
        if para_text(p).strip() == text:
            return i
    raise ValueError(f"pattern paragraph not found: {text!r}")


def clone_block(pattern: list, heading: str, scenario: str, a_text: str,
                a_marks: str, b_text: str, b_marks: str, numid: str,
                image: str | None = None) -> list:
    blocks = [copy.deepcopy(p) for p in pattern]
    idx_head = _role(blocks, "QUESTION 1")
    num_idx = [i for i, p in enumerate(blocks)
               if p.find(".//" + qn("w:numPr")) is not None]
    idx_a, idx_b = num_idx[0], num_idx[1]
    idx_scen = next(i for i, p in enumerate(blocks)
                    if i < idx_a and len(para_text(p).split()) > 8)
    idx_am = next(i for i in range(idx_a + 1, idx_b)
                  if re.match(r"^\(\d+ marks\)$", para_text(blocks[i]).strip()))
    idx_bm = next(i for i in range(idx_b + 1, len(blocks))
                  if re.match(r"^\(\d+ marks\)$", para_text(blocks[i]).strip()))

    set_para_text(blocks[idx_head], heading)
    set_para_text(blocks[idx_scen], scenario)
    set_para_text(blocks[idx_a], a_text)
    set_para_text(blocks[idx_am], a_marks)
    set_para_text(blocks[idx_b], b_text)
    set_para_text(blocks[idx_bm], b_marks)
    for idx in (idx_a, idx_b):
        for numid_el in blocks[idx].findall(".//" + qn("w:numId")):
            numid_el.set(qn("w:val"), numid)
    out = blocks
    if image:
        img_p = copy.deepcopy(blocks[idx_bm])
        set_para_text(img_p, "IMAGE_PLACEHOLDER")
        for r in img_p.findall(qn("w:r"))[1:]:
            img_p.remove(r)
        # center the picture paragraph
        pPr = img_p.find(qn("w:pPr"))
        if pPr is not None:
            for jc in pPr.findall(qn("w:jc")):
                pPr.remove(jc)
            jc = OxmlElement("w:jc")
            jc.set(qn("w:val"), "center")
            pPr.append(jc)
        out.append(img_p)
    return out


def _pick(questions: list[dict], cipher: str, task: str, marks: int,
          n: int = 1) -> list[dict]:
    return [q for q in questions
            if q["cipher"] == cipher and q["task"] == task and q["marks"] == marks][:n]


def _columnar_3x4_question() -> dict:
    """Q5b: a 3 x 4 columnar decrypt with the course's grid check in mind.
    Code-only (no LLM): 10-letter plaintext pads to 12 cells with X, so the
    scheme also demonstrates the padding convention. Marked computed in the
    scheme; the 3 x 4 convention itself still needs lecturer confirmation."""
    from src.generators import ciphers as C

    plaintext = "LOGIN AUDIT"
    rows, columns = 3, 4
    ct = C.columnar_encrypt(plaintext, columns, rows=rows)
    answer = C.columnar_decrypt(ct, columns, rows=rows)
    return {
        "cipher": "columnar",
        "plaintext": plaintext,
        "key": str(columns),
        "rows": rows,
        "task": "decrypt",
        "marks": 6,
        "question": ("Decrypt the following ciphertext using columnar "
                     "transposition with a 3 x 4 grid (3 rows, 4 columns).\n"
                     f"{ct}\n(6 marks)"),
        "answer": answer,
        "ciphertext": ct,
        "working": "",
    }


def build_slots() -> dict:
    computed = json.loads((OUTPUTS_DIR / "computed_questions.json").read_text())
    acm = json.loads((OUTPUTS_DIR / "acm_questions.json").read_text())
    caesar2 = _pick(computed, "caesar", "decrypt", 2, 2)
    cipher6 = [q for q in computed if q["marks"] == 6 and q["task"] == "encrypt"]
    return {
        "Q2a": caesar2[0] if caesar2 else None,
        "Q4a": caesar2[1] if len(caesar2) >= 2 else None,
        "Q2b": cipher6[0] if len(cipher6) >= 1 else None,
        "Q4b": cipher6[1] if len(cipher6) >= 2 else None,
        "Q5b": _columnar_3x4_question(),
        "Q3b": acm[0] if acm else None,
    }


def paper_question(q: dict, include_marks: bool = True) -> str:
    """Paper-facing stem: state the key/table/grid/filler and the method in
    the lecture's own wording. The raw LLM question is not used for the four
    classical-cipher types, because it omitted those conventions."""
    marks = q.get("marks") or (q.get("scenario") or {}).get("marks") or 0
    tail = f"\n({marks} marks)" if include_marks else ""
    cipher = q.get("cipher")
    if cipher == "caesar":
        shift = str(q.get("key", "")).split("=")[-1].strip()
        direction = "left" if q.get("task") == "decrypt" else "right"
        action = "decrypt the following ciphertext" if q.get("task") == "decrypt" \
            else "encrypt the following plaintext"
        return (f"Using Caesar Cipher technique, {action} with a shift of "
                f"{shift} (replace each letter with the one {shift} positions "
                f"to the {direction}).\n{q['ciphertext'] if q.get('task') == 'decrypt' else q['plaintext']}{tail}")
    if cipher == "playfair":
        action = ("Decrypt the ciphertext below" if q.get("task") == "decrypt"
                  else "Encrypt the message below")
        value = q.get("ciphertext") if q.get("task") == "decrypt" else q.get("plaintext")
        return (f"{action} using Playfair encryption with the key {q['key']}. "
                f"Use a 5 x 5 grid, merge I and J, and use X as the filler "
                f"between repeated letters and at the end if needed.\n"
                f"{value}{tail}")
    if cipher == "columnar":
        key = q.get("key")
        rows = q.get("rows")
        if isinstance(key, str) and key.strip().isdigit():
            cols = int(key.strip())
            key_text = f"the column size, {cols}"
        elif key:
            cols = len(re.sub(r"[^A-Za-z]", "", str(key)))
            key_text = f"the keyword {key}"
        else:
            cols = None
            key_text = "the stated grid"
        if rows is None and cols:
            letters = re.sub(r"[^A-Za-z]", "", q["ciphertext"])
            rows = (len(letters) + cols - 1) // cols
        grid = f"{rows} x {cols} matrix ({rows} rows, {cols} columns)"
        return (f"Decrypt the following ciphertext using columnar "
                f"transposition with a {grid}. Put the ciphertext into the "
                f"columns, read the plaintext out of the rows, and ignore the "
                f"filler X at the end. The key is {key_text}.\n"
                f"{q['ciphertext']}{tail}")
    if cipher == "vigenere":
        return (f"Decrypt the following ciphertext using the Vigenere cipher "
                f"with the key {q['key']}. Use the standard 26 x 26 Vigenere "
                f"tableau, writing the key over the message and repeating it "
                f"as necessary.\n{q['ciphertext']}{tail}")
    if cipher == "affine":
        return (f"Decrypt the following ciphertext using the affine cipher "
                f"with key {q['key']}. Use E(x) = (a x + b) mod 26 and decrypt "
                f"with the modular inverse of a.\n{q['ciphertext']}{tail}")
    if cipher == "vernam":
        merge = bool(q.get("ij_merge", False))
        alphabet = "I/J-merged (25 letters)" if merge else "26 letters"
        return (f"Decrypt the following ciphertext using a one-time pad with "
                f"the key numbers {q['key']}. Subtract the key numbers modulo "
                f"the {alphabet} alphabet, A=0.\n{q['ciphertext']}{tail}")
    return q.get("question", "")


def _qtext(q: dict) -> str:
    return paper_question(q, include_marks=False).strip()


def _ph(topic: str, marks: int, task: str) -> str:
    return PLACEHOLDER.format(topic=topic, marks=marks, task=task)


def _acm_scenario_text(q: dict) -> str:
    """Scenario/grants for the question paper. The matrix, ACLs, capability
    lists and diagram are the ANSWER; the grants are the given data."""
    s = q["scenario"]
    grants = []
    for g in s["grants"]:
        grants.append(f"{g['user']} can {', '.join(g['rights'])} {g['object']}")
    return (f"Assume a computer system with the accounts: "
            f"{', '.join(s['users'])}. " + "; ".join(grants) + ".")


def _acm_b_text(q: dict) -> str:
    return ("Based on the scenario above, write the access control matrix (ACM), "
            "the access control lists (ACL) and the capability lists (CL), and "
            "draw the diagram.")


def _acm_image(q: dict, out_dir: Path) -> str:
    png = out_dir / "acm_diagram.png"
    proc = subprocess.run([DOT_BIN, "-Tpng", "-o", str(png)], input=q["dot"],
                          text=True, capture_output=True, timeout=60)
    return str(png) if proc.returncode == 0 and png.exists() else ""


def main() -> None:
    slots = build_slots()
    tmp = Path(tempfile.mkdtemp())

    doc = docx.Document(str(SRC))
    paras = doc.paragraphs

    # fresh numbering ids so a)/b) restart in every question (the template
    # reuses numIds 8 and 3, which made Q4 and Q10 continue at c)/d))
    next_num = _num_id_counter(doc)
    a_numids = []
    for old in A_NUMIDS:
        a_numids.append(clone_numbering(doc, old, next_num))
        next_num += 1
    b_numids = []
    for old in B_NUMIDS:
        b_numids.append(clone_numbering(doc, old, next_num))
        next_num += 1

    part_a_idx = next(i for i, p in enumerate(paras)
                      if para_text(p._p).strip() == "PART A")
    part_b_idx = next(i for i, p in enumerate(paras)
                      if para_text(p._p).strip().startswith("PART") and i > part_a_idx)
    end_idx = next(i for i, p in enumerate(paras)
                   if "END OF QUESTION PAPER" in para_text(p._p))
    q1_idx = next(i for i, p in enumerate(paras)
                  if para_text(p._p).strip() == "QUESTION 1" and i > part_a_idx)
    q2_idx = next(i for i, p in enumerate(paras)
                  if para_text(p._p).strip() == "QUESTION 2" and i > q1_idx)
    bq1_idx = next(i for i, p in enumerate(paras)
                   if para_text(p._p).strip() == "QUESTION 1" and i > part_b_idx)
    bq2_idx = next(i for i, p in enumerate(paras)
                   if para_text(p._p).strip() == "QUESTION 2" and i > bq1_idx)

    pattern_a = [paras[i]._p for i in range(q1_idx, q2_idx)]
    pattern_b = [paras[i]._p for i in range(bq1_idx, bq2_idx)]
    set_para_text(paras[part_a_idx]._p, PART_A_HEADING)
    part_b_heading = copy.deepcopy(paras[part_b_idx]._p)
    set_para_text(part_b_heading, PART_B_HEADING)

    # remove all real body content between the PART A heading and END
    body = doc.element.body
    for i in range(part_a_idx + 1, end_idx):
        body.remove(paras[i]._p)

    topics = {1: "attacks/malware", 2: "classical ciphers",
              3: "access control models", 4: "classical ciphers",
              5: "authentication/biometrics", 6: "software/OS security",
              7: "network security", 8: "trusted computing",
              9: "authentication/biometrics", 10: "attacks/malware"}
    new_a = []
    for i in range(1, 11):
        key = f"Q{i}"
        a, b, am, bm, img = None, None, "2", "6", ""
        scen = "Refer to the question items below."
        if i == 2:
            a = _qtext(slots["Q2a"]) if slots["Q2a"] else None
            b = _qtext(slots["Q2b"]) if slots["Q2b"] else None
        elif i == 3:
            a = _ph("access control models", 2, "short objective")
            if slots["Q3b"]:
                # scenario text only - the diagram is the ANSWER and belongs in
                # the marking scheme, not in the question paper
                scen = _acm_scenario_text(slots["Q3b"])
                b = _acm_b_text(slots["Q3b"])
        elif i == 4:
            a = _qtext(slots["Q4a"]) if slots["Q4a"] else None
            b = _qtext(slots["Q4b"]) if slots["Q4b"] else None
        elif i == 5:
            a = _ph("authentication/biometrics", 2, "short objective")
            b = _qtext(slots["Q5b"]) if slots["Q5b"] else None
        a = a or _ph(topics[i], 2, "short objective")
        b = b or _ph(topics[i], 6, "define/explain")
        new_a += clone_block(pattern_a, f"QUESTION {i}", scen, a,
                             f"({am} marks)", b, f"({bm} marks)",
                             a_numids[i - 1], img)

    new_b = []
    for i, (topic, task) in enumerate([
            ("attacks/malware", "scenario/justify"),
            ("authentication/biometrics", "scenario/justify")], start=1):
        new_b += clone_block(pattern_b, f"QUESTION {i}", "Refer to the scenario.",
                             _ph(topic, 5, task), "(5 marks)", _ph(topic, 5, task),
                             "(5 marks)", b_numids[i - 1])

    end_el = paras[end_idx]._p
    for p in new_a + [part_b_heading] + new_b:
        end_el.addprevious(p)

    # pictures must be added once the paragraphs have real document parents
    from docx.shared import Cm

    for p in doc.paragraphs:
        if para_text(p._p).strip() == "IMAGE_PLACEHOLDER":
            set_para_text(p._p, "")
            p.add_run().add_picture(acm_img, width=Cm(11))

    # the template leaves empty paragraphs after END; when the body fits on
    # four pages they spill a blank fifth page. Drop trailing empties (keep
    # any paragraph carrying a section break).
    end_pos = next(i for i, p in enumerate(doc.paragraphs)
                   if "END OF QUESTION PAPER" in para_text(p._p))
    for p in list(doc.paragraphs[end_pos + 1:]):
        if (not para_text(p._p).strip()
                and p._p.find(".//" + qn("w:drawing")) is None
                and p._p.find(".//" + qn("w:sectPr")) is None):
            body.remove(p._p)

    # cover: ref code, artifacts, printed-pages count
    for p in doc.paragraphs:
        para_replace(p._p, "CS/FEB   2026/CSC662", "CS/MOCK OCT 2026/CSC662")
        para_replace(p._p, "CS/FEB 2026/CSC662", "CS/MOCK OCT 2026/CSC662")
        # the cover token is split across runs ("CS/FEB" | " " | "2026/CSC662"),
        # so patch the run-level fragment too (keeps the floating crest drawing)
        para_replace(p._p, "CS/FEB", "CS/MOCK OCT")
        fix_cover_refcode(p._p)
        para_replace(p._p, "Tthe", "The")
        para_replace(p._p, "PART S", "PART B")

    # course text boxes -> clean rows
    txbx_iter = doc.element.body.iter(qn("w:txbxContent"))
    labels = ["COURSE", "COURSE CODE", "EXAMINATION", "TIME"]
    values = ["COMPUTER SECURITY", "CSC662", "OCTOBER 2026 (MOCK)", "3 HOURS"]
    for box_idx, txbx in enumerate(list(txbx_iter)):
        rows = labels if box_idx == 0 else values
        old_ps = list(txbx.findall(qn("w:p")))
        first = copy.deepcopy(old_ps[0]) if old_ps else None
        if first is None:
            continue
        for p in old_ps:
            txbx.remove(p)
        if box_idx == 0:
            # the DOCX conversion dropped the colon column (visible at
            # x≈533px in the reference); widen the label box and add a tab to
            # 2160 twips (= the reference colon column), then ":"
            shape = txbx.getparent()
            while shape is not None and not shape.tag.endswith("}shape"):
                shape = shape.getparent()
            if shape is not None:
                style = shape.get("style", "")
                style = re.sub(r"width:[\d.]+", "width:2560", style, count=1)
                shape.set("style", style)
        for j, row in enumerate(rows):
            p = copy.deepcopy(first)
            set_para_text(p, row)
            _strip_char_scale(p)
            if box_idx == 0:
                pPr = p.find(qn("w:pPr"))
                if pPr is not None:
                    tabs = OxmlElement("w:tabs")
                    tab = OxmlElement("w:tab")
                    tab.set(qn("w:val"), "left")
                    tab.set(qn("w:pos"), "2130")
                    tabs.append(tab)
                    pPr.insert(0, tabs)
                r0 = p.find(qn("w:r"))
                if r0 is not None:
                    r0.append(OxmlElement("w:tab"))
                    colon = OxmlElement("w:t")
                    colon.text = ":"
                    colon.set(qn("xml:space"), "preserve")
                    r0.append(colon)
            if j > 0:
                pPr = p.find(qn("w:pPr"))
                if pPr is not None:
                    for sp in pPr.findall(qn("w:spacing")):
                        pPr.remove(sp)
                    sp = OxmlElement("w:spacing")
                    sp.set(qn("w:before"), "174")
                    sp.set(qn("w:line"), "235")
                    sp.set(qn("w:lineRule"), "exact")
                    pPr.append(sp)
            txbx.append(p)

    # The real questions carried the body's section breaks, so removing them
    # also removed the header/footer references. Re-attach the template's body
    # header/footer to the final section (cover keeps its own footer, no header).
    rel_ids = {}
    for rid, rel in doc.part.rels.items():
        rel_ids.setdefault(rel.target_ref, rid)
    body_sect = doc.element.body.find(qn("w:sectPr"))
    if body_sect is not None:
        refs = []
        if "header1.xml" in rel_ids:
            refs.append(("w:headerReference", rel_ids["header1.xml"]))
        if "footer2.xml" in rel_ids:
            refs.append(("w:footerReference", rel_ids["footer2.xml"]))
        for i, (tag, rid) in enumerate(refs):
            el = OxmlElement(tag)
            el.set(qn("w:type"), "default")
            el.set(qn("r:id"), rid)
            body_sect.insert(i, el)

    doc.save(str(OUT_DOCX))

    # headers/footers: fix tokens + typos (raw zip part rewrite).
    # The conversion split words across runs ("CONFI"+"DENTIAL", "Tekno"+"l"+
    # "ogi", "CS/FEB"), so patch exact whole-run texts, not the joined string.
    import zipfile
    import shutil

    fixes = {"word/header1.xml": [("CONFI", "CONFIDENTIAL"), ("DENTIAL", ""),
                                  ("CS/FEB", "CS/MOCK OCT")],
             "word/header2.xml": [("CONFI", "CONFIDENTIAL"), ("DENTIAL", ""),
                                  ("CS/FEB", "CS/MOCK OCT")],
             "word/footer1.xml": [],
             "word/footer2.xml": [("Teknologl", "Teknologi")],
             "word/footer3.xml": [("Tekno", "Teknologi"), ("l", ""), ("ogi", "")]}
    # rewrite zip with patched parts
    tmp_docx = tmp / "patched.docx"
    with zipfile.ZipFile(str(OUT_DOCX)) as zread, \
            zipfile.ZipFile(str(tmp_docx), "w", zipfile.ZIP_DEFLATED) as zwrite:
        for item in zread.infolist():
            data = zread.read(item.filename)
            if item.filename in fixes:
                text = data.decode("utf-8")
                text = patch_runs(text, fixes[item.filename])
                if item.filename.startswith("word/header"):
                    text = patch_refcode_box(text)
                data = text.encode("utf-8")
            zwrite.writestr(item, data)
    shutil.move(str(tmp_docx), str(OUT_DOCX))

    # printed-pages count: export -> count -> update -> re-export
    pages = export_pdf(OUT_DOCX, OUT_PDF)
    doc = docx.Document(str(OUT_DOCX))
    for p in doc.paragraphs:
        if "This examination paper consists of" in para_text(p._p):
            set_para_text(p._p, f"This examination paper consists of {pages} "
                               "printed pages")
    doc.save(str(OUT_DOCX))
    pages2 = export_pdf(OUT_DOCX, OUT_PDF)
    print(f"printed-pages field: first export {pages}, final {pages2} "
          f"(match: {pages == pages2})")
    print(f"wrote {OUT_DOCX} and {OUT_PDF}")

    # structural verification: the crest drawing survived, headers/footers fixed
    with zipfile.ZipFile(str(OUT_DOCX)) as z:
        media = [n for n in z.namelist() if n.startswith("word/media/")]
        hdr = "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>",
                                 z.read("word/header1.xml").decode("utf-8")))
        ftr2 = "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>",
                                  z.read("word/footer2.xml").decode("utf-8")))
        ftr3 = "".join(re.findall(r"<w:t\b[^>]*>([^<]*)</w:t>",
                                  z.read("word/footer3.xml").decode("utf-8")))
    doc = docx.Document(str(OUT_DOCX))
    p0 = doc.paragraphs[0]._p
    embeds = [el.get(qn("r:embed")) for el in p0.findall(".//" + qn("a:blip"))]
    targets = []
    for rid in embeds:
        try:
            targets.append(doc.part.rels[rid].target_ref)
        except KeyError:
            targets.append("MISSING")
    print(f"crest check: cover drawings={len(p0.findall('.//' + qn('w:drawing')))} "
          f"embeds={embeds} targets={targets} media={media}")
    print(f"header check: {hdr} | footers: {ftr2} / {ftr3}")

    # leakage check: no 8+ word sequence from the original QUESTION BODY
    # (cover, instructions, PART headings and END line are kept by design)
    orig = docx.Document(str(SRC))
    orig_body = [p.text for p in orig.paragraphs[part_a_idx + 1: part_b_idx]] + \
        [p.text for p in orig.paragraphs[part_b_idx + 1: end_idx]]
    orig_words = " ".join(orig_body).split()
    new_words = " ".join(p.text for p in doc.paragraphs).split()
    new_set = set()
    for i in range(len(new_words) - 7):
        new_set.add(" ".join(new_words[i:i + 8]).lower())
    leaked = []
    for i in range(len(orig_words) - 7):
        seq = " ".join(orig_words[i:i + 8]).lower()
        if seq in new_set:
            leaked.append(seq)
    print(f"leakage check: {len(leaked)} 8-word sequences from the original question "
          f"body found in the mock {'(FAIL)' if leaked else '(PASS)'}")
    for seq in leaked[:5]:
        print("   leaked:", seq[:90])

    # page-1 pixel comparison vs the raw template, exported the same way.
    # The template is never modified, so a cached render newer than the file is
    # just as valid and avoids depending on a free Word instance.
    import pymupdf as fitz
    import numpy as np
    from PIL import Image

    def page1_png(pdf_path: Path, out_path: Path, width: int = 1654):
        d = fitz.open(str(pdf_path))
        page = d[0]
        zoom = width / page.rect.width
        pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom))
        pix.save(str(out_path))
        return out_path

    mine_p1 = page1_png(OUT_PDF, OUTPUTS_DIR / "mock_p1.png")
    ref_p1 = OUTPUTS_DIR / "template_p1.png"
    if not (ref_p1.exists() and ref_p1.stat().st_mtime >= SRC.stat().st_mtime):
        template_pdf = tmp / "template_raw.pdf"
        export_pdf(SRC, template_pdf)
        page1_png(template_pdf, ref_p1)
    else:
        print(f"page-1 reference: cached {ref_p1.name} (template unchanged)")
    a = np.asarray(Image.open(mine_p1).convert("L"), dtype=np.float64)
    b = np.asarray(Image.open(ref_p1).convert("L"), dtype=np.float64)
    h = min(a.shape[0], b.shape[0])
    w = min(a.shape[1], b.shape[1])
    a, b = a[:h, :w], b[:h, :w]

    mad = float(np.mean(np.abs(a - b)))

    def box_filter(im: np.ndarray, win: int = 7) -> np.ndarray:
        s = np.cumsum(np.cumsum(im, axis=0), axis=1)
        m = np.zeros_like(im)
        m[win:, win:] = s[:-win, :-win]
        m[win:, 0] = s[:-win, -1]
        m[0, win:] = s[-1, :-win]
        m[0, 0] = s[-1, -1]
        return m / (win * win)

    def windowed_ssim(a: np.ndarray, b: np.ndarray, win: int = 7) -> float:
        c1, c2 = 6.5025, 58.5225
        ma, mb = box_filter(a, win), box_filter(b, win)
        va = box_filter(a * a, win) - ma * ma
        vb = box_filter(b * b, win) - mb * mb
        cov = box_filter(a * b, win) - ma * mb
        s = ((2 * ma * mb + c1) * (2 * cov + c2)) / \
            ((ma * ma + mb * mb + c1) * (va + vb + c2))
        return float(s.mean())

    diff_frac = float(np.mean(np.abs(a - b) > 30))
    ssim = windowed_ssim(a, b)
    print(f"page-1 comparison: MAD={mad:.1f}/255, diff>30 fraction={diff_frac:.3f}, "
          f"windowed SSIM={ssim:.6f} (resolution {w}x{h})")

    side = Image.new("L", (w * 2 + 10, h), 255)
    side.paste(Image.fromarray(b.astype("uint8")), (0, 0))
    side.paste(Image.fromarray(a.astype("uint8")), (w + 10, 0))
    side.save(OUTPUTS_DIR / "cover_side_by_side.png")
    diff = np.abs(a - b) > 30
    Image.fromarray((diff * 255).astype("uint8")).save(
        OUTPUTS_DIR / "cover_diff_mask.png")
    print("wrote mock_p1.png, template_p1.png, cover_side_by_side.png, "
          "cover_diff_mask.png")


def export_pdf(docx_path: Path, pdf_path: Path) -> int:
    """Word COM export to PDF; returns the PDF page count."""
    from pypdf import PdfReader

    docx_path = Path(docx_path).resolve()
    pdf_path = Path(pdf_path).resolve()
    ps1 = tmp_ps(docx_path, pdf_path)
    try:
        subprocess.run(["powershell.exe", "-NoProfile", "-ExecutionPolicy",
                        "Bypass", "-File", str(ps1)], capture_output=True,
                       timeout=300)
    finally:
        ps1.unlink(missing_ok=True)
    if not pdf_path.exists():
        raise RuntimeError("Word PDF export failed")
    return len(PdfReader(str(pdf_path)).pages)


def tmp_ps(docx_path: Path, pdf_path: Path) -> Path:
    """Generate the export script in the system temp dir (never next to the
    documents). Opens read-only and suppresses dialogs so a file that another
    Word instance holds cannot block the export."""
    with tempfile.NamedTemporaryFile("w", suffix=".ps1", delete=False,
                                     encoding="utf-8") as fh:
        fh.write(f"""
$word = New-Object -ComObject Word.Application
$word.Visible = $false
$word.DisplayAlerts = 0
$doc = $word.Documents.Open("{docx_path}", $false, $true)
$doc.SaveAs([ref]"{pdf_path}", [ref]17)
$doc.Close([ref]$false)
$word.Quit([ref]$false)
""")
    return Path(fh.name)


if __name__ == "__main__":
    main()
