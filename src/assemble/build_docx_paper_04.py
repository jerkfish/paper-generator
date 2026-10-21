"""Build mock_paper_04 from the revised realistic plan + theory drafts.

The cover/header/footer pipeline is the same FEB 2026 template pipeline used
for paper 01.  Body content comes from:
  - outputs/eval_final_deepseek/seed_12_planner.json (slot table),
  - outputs/eval_final_deepseek/seed_12_theory.json (accepted sourced questions and
    explicit placeholders),
  - a code-built Vigenere 6-mark computed question with the 26 x 26 tableau
    printed in the question (2006-10 Q2d / 2017-07 Q10 style).
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import tempfile
import zipfile
from pathlib import Path

import docx
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm

from src.assemble.build_docx_paper import (
    A_NUMIDS,
    B_NUMIDS,
    PART_A_HEADING,
    PART_B_HEADING,
    SRC,
    _num_id_counter,
    _strip_char_scale,
    clone_block,
    clone_numbering,
    export_pdf,
    fix_cover_refcode,
    para_replace,
    para_text,
    patch_refcode_box,
    patch_runs,
    set_para_text,
)
from src.assemble.vigenere_tableau import build_tableau_png
from src.config import OUTPUTS_DIR, PUBLIC_BUILD, PUBLIC_STRIP_BRANDING
from src.generators import ciphers as C

OUT_DOCX = OUTPUTS_DIR / "mock_paper_04.docx"
OUT_PDF = OUTPUTS_DIR / "mock_paper_04.pdf"
PLAN_JSON = OUTPUTS_DIR / "eval_final_deepseek/seed_12_planner.json"
THEORY_JSON = OUTPUTS_DIR / "eval_final_deepseek/seed_12_theory.json"
PLACEHOLDER = ("[THEORY PLACEHOLDER - {topic}, {marks} marks, {task}. "
               "No sourced question passed verification.]")


def _plan() -> tuple[dict, dict]:
    plan = json.loads(PLAN_JSON.read_text(encoding="utf-8"))
    return plan, {s["slot"]: s for s in plan["slots"]}


def _theory() -> tuple[dict, dict]:
    if not THEORY_JSON.exists():
        return {}, {}
    payload = json.loads(THEORY_JSON.read_text(encoding="utf-8"))
    accepted = {q["slot"]: q for q in payload.get("accepted", [])}
    placeholders = {p["slot"]: p for p in payload.get("placeholders", [])}
    return accepted, placeholders


def _vigenere_question() -> dict:
    plaintext = "SECURE LOGIN NOW"
    key = "CIPHER"
    ct = C.vigenere_encrypt(plaintext, key)
    answer = C.vigenere_decrypt(ct, key)
    return {
        "cipher": "vigenere", "plaintext": plaintext, "key": key,
        "ciphertext": ct, "task": "decrypt", "marks": 6, "answer": answer,
        "working": "",
    }


def _computed_question(slot: dict) -> dict | None:
    kind = slot.get("computed_type")
    if kind == "vigenere":
        q = _vigenere_question()
        q["marks"] = slot["marks"]
        return q
    # Paper 02's realistic plan has only one computed Vigenere slot.  The
    # fallback keeps the builder usable if a practice plan is supplied.
    path = OUTPUTS_DIR / "computed_questions.json"
    if path.exists():
        questions = json.loads(path.read_text(encoding="utf-8"))
        for q in questions:
            if q.get("marks") == slot["marks"] and str(
                    q.get("cipher", "")).startswith(str(kind).split("_")[0]):
                return q
    return None


def _slot_text(slot: dict, accepted: dict, placeholders: dict,
               qmap: dict[str, dict]) -> str:
    if slot["kind"] == "theory":
        if slot["slot"] in accepted:
            return accepted[slot["slot"]]["question"]
        return PLACEHOLDER.format(topic=slot["topic"], marks=slot["marks"],
                                  task=slot["task"])
    q = qmap.get(slot["slot"])
    if q is None:
        return (f"[COMPUTED PLACEHOLDER - {slot['computed_type']}, "
                f"{slot['marks']} marks]")
    from src.assemble.build_docx_paper import paper_question
    return paper_question(q, include_marks=False).strip()


def _cover_and_template(doc) -> None:
    # Same paper-01 cover fixes: ref code, crest-safe token replacement, clean
    # course text boxes.
    for p in doc.paragraphs:
        para_replace(p._p, "CS/FEB   2026/CSC662", "CS/MOCK OCT 2026/CSC662")
        para_replace(p._p, "CS/FEB 2026/CSC662", "CS/MOCK OCT 2026/CSC662")
        para_replace(p._p, "CS/FEB", "CS/MOCK OCT")
        fix_cover_refcode(p._p)
        para_replace(p._p, "Tthe", "The")
        para_replace(p._p, "PART S", "PART B")

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


def _attach_body_header_footer(doc) -> None:
    rel_ids = {}
    for rid, rel in doc.part.rels.items():
        rel_ids.setdefault(rel.target_ref, rid)
    body_sect = doc.element.body.find(qn("w:sectPr"))
    if body_sect is None:
        return
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


def build(public: bool | None = None) -> bool:
    """Build the paper. Returns True when public branding was applied."""
    is_public = PUBLIC_BUILD if public is None else bool(public)
    plan, slots = _plan()
    accepted, placeholders = _theory()
    qmap: dict[str, dict] = {}
    for sid, s in slots.items():
        if s["kind"] == "computed":
            q = _computed_question(s)
            if q is not None:
                qmap[sid] = q

    tableau = build_tableau_png(OUTPUTS_DIR / "vigenere_tableau.png")
    tmp = Path(tempfile.mkdtemp())

    doc = docx.Document(str(SRC))
    paras = doc.paragraphs

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
                      if para_text(p._p).strip().startswith("PART")
                      and i > part_a_idx)
    end_idx = next(i for i, p in enumerate(paras)
                   if "END OF QUESTION PAPER" in para_text(p._p))
    q1_idx = next(i for i, p in enumerate(paras)
                  if para_text(p._p).strip() == "QUESTION 1"
                  and i > part_a_idx)
    q2_idx = next(i for i, p in enumerate(paras)
                  if para_text(p._p).strip() == "QUESTION 2"
                  and i > q1_idx)
    bq1_idx = next(i for i, p in enumerate(paras)
                   if para_text(p._p).strip() == "QUESTION 1"
                   and i > part_b_idx)
    bq2_idx = next(i for i, p in enumerate(paras)
                   if para_text(p._p).strip() == "QUESTION 2"
                   and i > bq1_idx)

    pattern_a = [paras[i]._p for i in range(q1_idx, q2_idx)]
    pattern_b = [paras[i]._p for i in range(bq1_idx, bq2_idx)]
    set_para_text(paras[part_a_idx]._p, PART_A_HEADING)
    part_b_heading = copy.deepcopy(paras[part_b_idx]._p)
    set_para_text(part_b_heading, PART_B_HEADING)

    body = doc.element.body
    for i in range(part_a_idx + 1, end_idx):
        body.remove(paras[i]._p)

    images: list[Path] = []
    new_a = []
    for i in range(1, 11):
        a_id, b_id = f"A{i}a", f"A{i}b"
        a_slot, b_slot = slots[a_id], slots[b_id]
        a_text = _slot_text(a_slot, accepted, placeholders, qmap)
        b_text = _slot_text(b_slot, accepted, placeholders, qmap)
        img = None
        if ((a_slot["kind"] == "computed"
             and a_slot.get("computed_type") == "vigenere")
                or (b_slot["kind"] == "computed"
                    and b_slot.get("computed_type") == "vigenere")):
            img = str(tableau)
            images.append(tableau)
        new_a += clone_block(
            pattern_a, f"QUESTION {i}", "", a_text,
            f"({a_slot['marks']} marks)", b_text,
            f"({b_slot['marks']} marks)", a_numids[i - 1], img)

    new_b = []
    for i, (a_id, b_id) in enumerate([("B1a", "B1b"), ("B2a", "B2b")],
                                    start=1):
        a_slot, b_slot = slots[a_id], slots[b_id]
        scenario = (accepted.get(a_id, {}).get("scenario")
                    or accepted.get(b_id, {}).get("scenario") or "")
        new_b += clone_block(
            pattern_b, f"QUESTION {i}", scenario,
            _slot_text(a_slot, accepted, placeholders, qmap),
            f"({a_slot['marks']} marks)",
            _slot_text(b_slot, accepted, placeholders, qmap),
            f"({b_slot['marks']} marks)", b_numids[i - 1])

    end_el = paras[end_idx]._p
    for p in new_a + [part_b_heading] + new_b:
        end_el.addprevious(p)

    # Tighten the cloned blocks: the template carries several empty spacer
    # paragraphs.  Remove them from the generated body (never remove a
    # paragraph carrying a drawing or a section break).
    body_start = next(i for i, p in enumerate(doc.paragraphs)
                      if para_text(p._p).strip() == PART_A_HEADING)
    for p in list(doc.paragraphs[body_start:]):
        if (not para_text(p._p).strip()
                and p._p.find(".//" + qn("w:drawing")) is None
                and p._p.find(".//" + qn("w:pict")) is None
                and p._p.find(".//" + qn("w:br")) is None
                and p._p.find(".//" + qn("w:sectPr")) is None):
            body.remove(p._p)

    # Keep each a)/b) stem with its (N marks) line.
    for p in doc.paragraphs:
        if p._p.find(".//" + qn("w:numPr")) is not None:
            pPr = p._p.find(qn("w:pPr"))
            if pPr is None:
                pPr = OxmlElement("w:pPr")
                p._p.insert(0, pPr)
            if pPr.find(qn("w:keepNext")) is None:
                pPr.append(OxmlElement("w:keepNext"))
            if pPr.find(qn("w:keepLines")) is None:
                pPr.append(OxmlElement("w:keepLines"))

    # Images (Vigenere tableau) are inserted after the blocks have parents.
    image_idx = 0
    for p in doc.paragraphs:
        if para_text(p._p).strip() == "IMAGE_PLACEHOLDER":
            set_para_text(p._p, "")
            if image_idx < len(images):
                p.add_run().add_picture(str(images[image_idx]), width=Cm(15.2))
                image_idx += 1
                # The manual revision leaves one blank line between the
                # tableau and the next question.
                p._p.addnext(OxmlElement("w:p"))

    # Formatting pass matched to the manually revised mock: bold section and
    # question headings, 1.5 line spacing in the body, bold running header.
    if doc.paragraphs:
        for r in doc.paragraphs[0].runs:
            r.bold = True
    body_start = next(i for i, p in enumerate(doc.paragraphs)
                      if para_text(p._p).strip().startswith("PART A"))
    for p in doc.paragraphs[body_start:]:
        p.paragraph_format.line_spacing = 1.5
        text = para_text(p._p).strip()
        if (text.startswith("PART A") or text.startswith("PART B")
                or text.startswith("QUESTION ")
                or text == "END OF QUESTION PAPER"):
            for r in p.runs:
                r.bold = True
    # One blank line under each PART heading, as in the manual revision.
    for p in list(doc.paragraphs):
        if para_text(p._p).strip() in (PART_A_HEADING, PART_B_HEADING):
            p._p.addnext(OxmlElement("w:p"))

    # Drop trailing empty paragraphs after END, preserving sections.
    end_pos = next(i for i, p in enumerate(doc.paragraphs)
                   if "END OF QUESTION PAPER" in para_text(p._p))
    for p in list(doc.paragraphs[end_pos + 1:]):
        if (not para_text(p._p).strip()
                and p._p.find(".//" + qn("w:drawing")) is None
                and p._p.find(".//" + qn("w:sectPr")) is None):
            body.remove(p._p)

    _cover_and_template(doc)
    _attach_body_header_footer(doc)
    doc.save(str(OUT_DOCX))

    # Header/footer token fixes (same raw-zip patch as paper 01).
    fixes = {"word/header1.xml": [("CONFI", "CONFIDENTIAL"), ("DENTIAL", ""),
                                  ("CS/FEB", "CS/MOCK OCT")],
             "word/header2.xml": [("CONFI", "CONFIDENTIAL"), ("DENTIAL", ""),
                                  ("CS/FEB", "CS/MOCK OCT")],
             "word/footer1.xml": [],
             "word/footer2.xml": [("Teknologl", "Teknologi")],
             "word/footer3.xml": [("Tekno", "Teknologi"), ("l", ""),
                                  ("ogi", "")]}
    tmp_docx = tmp / "patched.docx"
    with zipfile.ZipFile(str(OUT_DOCX)) as zread, \
            zipfile.ZipFile(str(tmp_docx), "w",
                            zipfile.ZIP_DEFLATED) as zwrite:
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

    pages = export_pdf(OUT_DOCX, OUT_PDF)
    d2 = docx.Document(str(OUT_DOCX))
    for p in d2.paragraphs:
        if "This examination paper consists of" in para_text(p._p):
            set_para_text(p._p, f"This examination paper consists of {pages} "
                               "printed pages")
    d2.save(str(OUT_DOCX))
    pages2 = export_pdf(OUT_DOCX, OUT_PDF)
    if is_public and PUBLIC_STRIP_BRANDING:
        from src.assemble.generic_build import publicise
        publicise(OUT_DOCX)
        # Never leave a private-branded PDF beside a public DOCX.
        if OUT_PDF.exists():
            OUT_PDF.unlink()
        pages2 = export_pdf(OUT_DOCX, OUT_PDF)
    print(f"paper 04: pages={pages2} "
          f"(first export {pages}, match={pages == pages2})")
    print(f"wrote {OUT_DOCX} and {OUT_PDF}")
    return is_public


if __name__ == "__main__":
    build()
