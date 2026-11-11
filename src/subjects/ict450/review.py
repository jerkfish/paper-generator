"""Import the owner's review decisions and build a needs-fix print sheet.

The owner reviews the bank in the CSC429-style HTML sheet and exports
``review_decisions.json``.  This module applies those decisions to the bank,
then renders only the questions/assets that still need a recreation, so the
owner can review the HTML recreations on paper.

Run:
    uv run python -m src.subjects.ict450.review apply
    uv run python -m src.subjects.ict450.review sheet
    uv run python -m src.subjects.ict450.review all
"""
from __future__ import annotations

import argparse
import html
import json
import subprocess
from collections import Counter
from pathlib import Path

from PIL import Image

from src import config
from src.bank.store import BankStore, load_json, save_json
from src.subjects.ict450.papers import SUBJECT

TRACKING = config.TRACKING_DIR / "ict450" / "v2"
BANK = TRACKING / "bank"
REVIEW = BANK / "review"
DECISIONS = REVIEW / "review_decisions.json"
SHEET_HTML = REVIEW / "needs_fix.html"
SHEET_PDF = REVIEW / "needs_fix.pdf"
REVIEWED_ON = "2026-11-11"

EDGE_CANDIDATES = (
    Path(r"C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe"),
    Path(r"C:/Program Files/Microsoft/Edge/Application/msedge.exe"),
)


def _store() -> BankStore:
    return BankStore(BANK)


def apply_decisions(path: Path = DECISIONS) -> dict:
    """Apply question/asset verdicts; recreations stay pending until reviewed."""
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    decisions = payload.get("questions") or {}
    store = _store()
    approvals = load_json(store.approvals_path, {"schema_version": 1,
                                                 "by_qid": {}})
    approvals.setdefault("by_qid", {})
    counts = {"approved": 0, "needs_fix": 0, "rejected": 0,
              "use_original": 0, "use_recreation": 0}
    updated_questions = []
    for qid, decision in decisions.items():
        question = store.load_question(qid)
        if not question:
            raise SystemExit(f"decision references a missing question: {qid}")
        verdict = str(decision.get("verdict") or "").strip()
        if verdict not in {"approved", "needs_fix", "rejected"}:
            raise SystemExit(f"{qid}: invalid verdict {verdict!r}")
        question["status"] = verdict
        question["review_verdict"] = verdict
        question["reviewed_on"] = REVIEWED_ON
        question["review_warnings"] = list(question.get("review_flags") or [])
        asset_decisions = dict(decision.get("assets") or {})
        for aid, choice in asset_decisions.items():
            asset = store.load_asset(aid)
            if not asset:
                raise SystemExit(f"{qid}: missing asset {aid}")
            if choice not in {"use_original", "use_recreation"}:
                raise SystemExit(f"{aid}: invalid choice {choice!r}")
            asset["review_choice"] = choice
            asset["reviewed_on"] = REVIEWED_ON
            counts[choice] += 1
            if choice == "use_original":
                asset["verdict"] = "approved"
                asset["selected_treatment"] = "crop"
                asset["recreation_status"] = "not_needed"
            else:
                asset["verdict"] = "pending"
                asset["selected_treatment"] = (
                    "native_table" if asset.get("kind") == "table"
                    else "html_recreation")
                asset["recreation_status"] = "pending_review"
            save_json(store.asset_path(aid), asset)
        save_json(store.question_path(qid), question)
        approvals["by_qid"][qid] = {
            "verdict": verdict,
            "assets": asset_decisions,
            "reviewed_on": REVIEWED_ON,
            "source": str(Path(path)),
        }
        counts[verdict] += 1
        updated_questions.append(qid)
    save_json(store.approvals_path, approvals)
    summary = refresh_report()
    return {
        "subject": SUBJECT,
        "questions": len(updated_questions),
        "counts": counts,
        "approvals": str(store.approvals_path),
        "summary": summary,
    }


def refresh_report() -> dict:
    """Recompute bank counts after a review import, without rebuilding."""
    store = _store()
    questions = list(store.questions())
    assets = [row for row in store.assets() if not row.get("superseded_by")]
    statuses = Counter(str(row.get("status")) for row in questions)
    choices = Counter(str(row.get("review_choice") or "unreviewed")
                      for row in assets)
    pending = [row["id"] for row in assets
               if row.get("review_choice") == "use_recreation"
               and row.get("recreation_status") == "pending_review"]
    index = load_json(BANK / "index.json", {})
    index.update({
        "status": dict(sorted(statuses.items())),
        "approved": statuses.get("approved", 0),
        "needs_fix": statuses.get("needs_fix", 0),
        "rejected": statuses.get("rejected", 0),
        "review_use_original": choices.get("use_original", 0),
        "review_use_recreation": choices.get("use_recreation", 0),
        "review_pending_assets": len(pending),
    })
    save_json(BANK / "index.json", index)
    gate = load_json(BANK / "gate1_report.json", {})
    gate["review"] = {
        "imported_on": REVIEWED_ON,
        "questions": len(questions),
        "status": dict(sorted(statuses.items())),
        "asset_choices": dict(sorted(choices.items())),
        "pending_recreations": len(pending),
        "gate_status": "awaiting_owner_review",
    }
    save_json(BANK / "gate1_report.json", gate)
    summary = {
        "subject": SUBJECT,
        "questions": len(questions),
        "status": dict(sorted(statuses.items())),
        "asset_choices": dict(sorted(choices.items())),
        "pending_recreations": len(pending),
        "pending_ids": pending,
    }
    save_json(BANK / "review_import_report.json", summary)
    lines = [
        "# ICT450 — owner review import",
        "",
        f"Imported on **{REVIEWED_ON}** from `review_decisions.json`.",
        "",
        "## Questions",
        "",
    ]
    for key, value in sorted(statuses.items()):
        lines.append(f"- {key}: {value}")
    lines += ["", "## Assets", ""]
    for key, value in sorted(choices.items()):
        lines.append(f"- {key}: {value}")
    lines += [
        "",
        f"**{len(pending)} recreations are pending review.**",
        "",
        "The fix sheet is `review/needs_fix.html` and `review/needs_fix.pdf`.",
        "Gate A remains pending until the recreations are reviewed.",
        "",
    ]
    (BANK / "review_import_report.md").write_text(
        "\n".join(lines), encoding="utf-8")
    return summary


# Manual HTML recreations for assets where MinerU emitted no table HTML.  Each
# is transcribed from the source crop; the text is not invented.
MANUAL_RECREATIONS: dict[str, str] = {
    "ICT450-2019-JUN-A42": """
<div class="receipt">
  <div class="center"><b>AB BISTRO RESTAURANT</b><br>(001812777-AB)<br>
  Lot No.18, Jalan LKP 7,<br>77000 Jasin<br>Melaka<br>
  Tel : 017-2345678</div>
  <p><b>TABLE 30</b><br>
  No&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;: 101<br>
  Date&nbsp;&nbsp;&nbsp;: 17/01/2019&nbsp;&nbsp;11:23:24<br>
  Server : Nurul Najwa</p>
  <hr class="dashed">
  <table class="rec-table">
    <tr><th>Menu<br>ID</th><th>Menu<br>Description</th><th>Quantity</th>
        <th>Price (RM)</th><th>Amount</th></tr>
    <tr><td>M10</td><td>Tomyam Thai</td><td>1</td>
        <td>RM 10.00</td><td>RM 10.00</td></tr>
    <tr><td>M12</td><td>Daging Masak Pedas</td><td>1</td>
        <td>RM 7.00</td><td>RM 7.00</td></tr>
    <tr><td>M13</td><td>Kangkung Goreng</td><td>1</td>
        <td>RM 3.00</td><td>RM 3.00</td></tr>
    <tr><td>M15</td><td>Telur Bistik</td><td>1</td>
        <td>RM 4.00</td><td>RM 4.00</td></tr>
    <tr><td>D4</td><td>Teh Ais</td><td>2</td>
        <td>RM 2.50</td><td>RM 5.00</td></tr>
    <tr><td>D16</td><td>Milo Tabur</td><td>2</td>
        <td>RM 2.50</td><td>RM 5.00</td></tr>
  </table>
  <div class="right">
    <b>TOTAL : RM 34.00</b><br>
    Payment : RM 50.00<br>
    Balance : RM 16.00
  </div>
  <div class="center"><b>THANK YOU AND COME AGAIN!</b></div>
</div>
""",
    "ICT450-2024-JAN-A11": """
<div class="flow">
  <div class="flow-head"><div>STAGE</div>
    <div>HARDWARE / SOFTWARE<br>DEPENDENT</div></div>
  <div class="flow-row"><div class="box blank">i)</div>
    <div class="arrow">&rarr;</div><div class="box round">v)</div></div>
  <div class="flow-down">&#8595;</div>
  <div class="flow-row"><div class="box blank">ii)</div></div>
  <div class="flow-down">&#8595;</div>
  <div class="flow-row"><div class="box blank">iii)</div>
    <div class="arrow">&rarr;</div>
    <div class="box round">DBMS - Dependent</div></div>
  <div class="flow-down">&#8595;</div>
  <div class="flow-row"><div class="box blank">iv)</div>
    <div class="arrow">&rarr;</div><div class="box round">vi)</div></div>
</div>
""",
    "ICT450-2024-JUL-A16": """
<div class="receipt">
  <div class="right"><b class="logo">Sasa eStore</b><br>
  Lot 10, Jalan Parameswara<br>06-2226666 | hq@sasa.com</div>
  <p><b>BILL TO</b><br>
  Adilla Yusof (Member ID : SS11)<br>
  No. 12, Jalan Seringin 8,<br>
  Desa Seringin, 71800 Nilai, Negeri Sembilan.</p>
  <div class="right"><b>INVOICE # 100</b><br>Date: 26/02/2024</div>
  <table class="rec-table">
    <thead><tr><th>Item Name</th><th>Quantity</th>
      <th>Unit Price</th><th>Amount</th></tr></thead>
    <tr><td>Green Deep Lip &amp; Eye Remover</td><td>1</td>
        <td>65</td><td>$65.00</td></tr>
    <tr><td>Argan Oil Cleansing Foam</td><td>1</td>
        <td>49</td><td>$49.00</td></tr>
    <tr><td>10% Niacinamide Serum</td><td>1</td>
        <td>56</td><td>$56.00</td></tr>
    <tr><td>Alaska Volcano Clay Mask Stick</td><td>2</td>
        <td>44</td><td>$88.00</td></tr>
    <tr><td>Argan Oil Cleansing Foam</td><td>1</td>
        <td>49</td><td>$49.00</td></tr>
    <tr class="total"><td colspan="3">TOTAL</td><td>$307.00</td></tr>
  </table>
  <div class="right">Paid Amount&nbsp;&nbsp;$310.00<br>
  Balance Due&nbsp;&nbsp;$3.00</div>
  <p>Make all checks payable to Sasa eStore</p>
  <p>If you have any questions concerning this invoice, use the following
  contact information:<br>Azlina, 012-1234567, azlina@sasa.com</p>
  <p><b>THANK YOU FOR YOUR BUSINESS!</b></p>
</div>
""",
    "ICT450-2025-JUL-F21": """
<div>
  <div class="center"><b>Table 3 : Employee Skills Records of IT Creative
  Solution in 2025</b></div>
  <table class="rec-table small">
    <tr><th>Item</th><th>Staff<br>ID</th><th>Staff<br>Name</th>
        <th>Position</th><th>Department ID<br>&amp; Name</th>
        <th>Skill ID &amp;<br>Skill Name</th><th>Completion<br>Date</th></tr>
    <tr><td>1.</td><td>304</td><td>Intan Syafinaz</td><td>Analyst</td>
        <td>D1 - Data Analytic</td><td>AD - Advanced Database</td>
        <td>1/1/2025</td></tr>
    <tr><td>2.</td><td>304</td><td>Intan Syafinaz</td><td>Analyst</td>
        <td>D1 - Data Analytic</td><td>BM - Basic DB Manipulation</td>
        <td>3/1/2025</td></tr>
    <tr><td>3.</td><td>301</td><td>Robert James</td><td>UI/UX Designer</td>
        <td>D2 - Software development</td><td>AD - Advanced Database</td>
        <td>1/1/2025</td></tr>
    <tr><td>4.</td><td>302</td><td>Mohd Fikri Mohd Ali</td><td>Developer</td>
        <td>D2 - Software development</td><td>-</td><td>-</td></tr>
    <tr><td>5.</td><td>307</td><td>Zinnirah</td><td>Developer</td>
        <td>D2 - Software development</td><td>AD - Advanced Database</td>
        <td>1/1/2025</td></tr>
    <tr><td>6.</td><td>307</td><td>Zinnirah</td><td>Developer</td>
        <td>D2 - Software development</td><td>FF - Frontend Frameworks</td>
        <td>Not complete yet</td></tr>
    <tr><td>7.</td><td>305</td><td>Linda Clark</td><td>System Admin</td>
        <td>D3 - Network and Systems Administration</td>
        <td>BM - Basic DB Manipulation</td><td>3/1/2025</td></tr>
  </table>
</div>
""",
    "ICT450-2025-JUL-F22": """
<div>
  <div class="center"><b>Table 4 : Relational Schema for XY Company</b></div>
  <div class="schema">
    EMPLOYEE (EmpID, EmpFirstName, EmpLastName, EmpHireDate, JobCode)<br><br>
    JOB (JobCode, JobName, JobChargeHour)<br><br>
    PROJECT (ProjCode, ProjName)<br><br>
    ASSIGN (AssignID, AssignDate, AssignHours, ProjCode, EmpID)
  </div>
</div>
""",
}


# The two fallback assets are full-page crops; these fractions isolate the
# table region for the printed comparison.  The bank keeps the full page.
PREVIEW_CROPS = {
    "ICT450-2025-JUL-F21": (0.06, 0.17, 0.90, 0.36),
    "ICT450-2025-JUL-F22": (0.05, 0.10, 0.90, 0.23),
}


def _thumb(asset: dict) -> str:
    aid = str(asset.get("id"))
    source = Path(asset.get("crop_path") or "")
    target = REVIEW / "thumbs" / f"{aid}.jpg"
    if source.is_file():
        target.parent.mkdir(parents=True, exist_ok=True)
        with Image.open(source) as image:
            image = image.convert("RGB")
            box = PREVIEW_CROPS.get(aid)
            if box:
                width, height = image.size
                image = image.crop((int(box[0] * width), int(box[1] * height),
                                    int(box[2] * width),
                                    int(box[3] * height)))
            if image.width > 1400:
                height = int(image.height * 1400 / image.width)
                image = image.resize((1400, height))
            image.save(target, "JPEG", quality=82)
    return f"thumbs/{aid}.jpg"


def _recreation_html(asset: dict) -> str:
    aid = str(asset.get("id"))
    if aid in MANUAL_RECREATIONS:
        return MANUAL_RECREATIONS[aid]
    table_html = str(asset.get("mineru_table_html") or "").strip()
    if table_html:
        return f'<div class="rec-html">{table_html}</div>'
    return "<p class='missing'>No HTML recreation available.</p>"


def _question_section(question: dict, assets: list[dict]) -> str:
    qid = html.escape(str(question.get("id")))
    text = html.escape(
        (question.get("native_text_blocks") or [{}])[0].get("text", ""))
    pages = question.get("pages") or []
    warnings = question.get("review_warnings") or []
    blocks = []
    for asset in assets:
        aid = html.escape(str(asset.get("id")))
        label = html.escape(str(asset.get("label") or asset.get("id")))
        choice = html.escape(str(asset.get("review_choice") or ""))
        blocks.append(f"""
        <div class="asset">
          <div class="asset-title">{label}
            <span class="tag">{qid}</span>
            <span class="tag">{html.escape(str(asset.get('kind')))}</span>
            <span class="tag">{choice}</span>
            <span class="tag">page {asset.get('page')}</span>
          </div>
          <div class="compare">
            <div><div class="cap">Original crop</div>
              <img class="original" src="{_thumb(asset)}" alt="{aid}"></div>
            <div><div class="cap">HTML recreation</div>
              <div class="recreation">{_recreation_html(asset)}</div></div>
          </div>
          <div class="verdict-line">
            Recreation review:
            <span class="box"></span> use recreation
            <span class="box"></span> keep original
            <span class="box"></span> needs more work
            &nbsp;&nbsp; Notes: ______________________________________
          </div>
        </div>
        """)
    warning_line = (
        f"<p class='warn'>Bank warnings: {html.escape('; '.join(warnings))}</p>"
        if warnings else "")
    return f"""
    <section class="question">
      <h2>{qid} <span class="marks">({question.get('marks')} marks)</span></h2>
      <p class="meta">Source: {html.escape(str(question.get('source_paper')))}
        · page {', '.join(str(page) for page in pages)}
        · owner verdict: {html.escape(str(question.get('review_verdict')))}</p>
      {warning_line}
      <pre class="qtext">{text}</pre>
      {''.join(blocks) if blocks else "<p class='missing'>No recreation assets.</p>"}
    </section>
    """


def build_sheet(out: Path = SHEET_HTML) -> Path:
    store = _store()
    questions = list(store.questions())
    selected = []
    for question in questions:
        linked = [store.load_asset(aid)
                  for aid in question.get("assets") or []]
        linked = [asset for asset in linked if asset]
        recreation = [asset for asset in linked
                      if asset.get("review_choice") == "use_recreation"]
        if question.get("review_verdict") == "needs_fix" or recreation:
            selected.append((question, recreation))
    selected.sort(key=lambda item: str(item[0].get("id")))
    sections = "".join(_question_section(question, assets)
                       for question, assets in selected)
    page = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>ICT450 — needs-fix review</title>
<style>
@page {{ size: A4 portrait; margin: 12mm; }}
body {{ font-family: Arial, sans-serif; color: #111; font-size: 10pt; }}
h1 {{ font-size: 18pt; margin: 0 0 4mm; }}
h2 {{ font-size: 13pt; margin: 0 0 2mm; }}
.meta, .warn {{ color: #444; margin: 1mm 0; }}
.warn {{ color: #8a1f1f; }}
.question {{ page-break-after: always; }}
.qtext {{ white-space: pre-wrap; background: #f4f4f4; padding: 3mm;
          font-family: "Courier New", monospace; font-size: 8.5pt; }}
.asset {{ border: 1px solid #999; padding: 3mm; margin: 3mm 0;
          page-break-inside: avoid; }}
.asset-title {{ font-weight: bold; margin-bottom: 2mm; }}
.tag {{ background: #e8e8e8; font-weight: normal; padding: 0 2mm;
        margin-left: 2mm; font-size: 8pt; }}
.compare {{ display: grid; grid-template-columns: 1fr 1fr; gap: 4mm; }}
.cap {{ font-weight: bold; margin-bottom: 1mm; }}
img.original {{ max-width: 100%; max-height: 95mm; border: 1px solid #ccc; }}
.recreation {{ border: 1px solid #ccc; padding: 3mm; min-height: 40mm; }}
.rec-html table, table.rec-table {{ border-collapse: collapse;
  width: 100%; font-size: 8pt; }}
.rec-html td, .rec-html th, table.rec-table td, table.rec-table th {{
  border: 1px solid #000; padding: 1mm; vertical-align: top; }}
table.rec-table.small {{ font-size: 7.5pt; }}
.center {{ text-align: center; }}
.right {{ text-align: right; }}
.receipt {{ font-family: "Courier New", monospace; font-size: 8.5pt; }}
.logo {{ font-size: 16pt; }}
hr.dashed {{ border: 0; border-top: 1px dashed #000; }}
tr.total td {{ font-weight: bold; border-top: 2px solid #000; }}
.schema {{ border: 1px solid #000; padding: 4mm; font-family: "Courier New",
           monospace; font-size: 9pt; }}
.flow {{ width: 100%; }}
.flow-head {{ display: grid; grid-template-columns: 1fr 1fr;
              font-weight: bold; text-align: center; margin-bottom: 3mm; }}
.flow-row {{ display: grid; grid-template-columns: 55% 6% 39%;
             align-items: center; margin: 2mm 0; }}
.flow-row .box {{ border: 2px solid #000; min-height: 14mm;
                  padding: 2mm; box-sizing: border-box; width: 100%; }}
.flow-row .box.round {{ border-radius: 3mm; font-size: 8.5pt; }}
.arrow {{ font-size: 18pt; text-align: center; }}
.flow-down {{ text-align: center; font-size: 18pt; }}
.verdict-line {{ margin-top: 2mm; font-size: 9pt; }}
.box {{ display: inline-block; width: 3.5mm; height: 3.5mm;
        border: 1px solid #000; vertical-align: -0.5mm; margin-left: 3mm; }}
.missing {{ color: #8a1f1f; }}
@media print {{ .question {{ page-break-after: always; }} }}
</style></head><body>
<h1>ICT450 — needs-fix review</h1>
<p>Only questions with a needs-fix verdict or a “use recreation” asset.
Review the HTML recreation against the original crop, mark the printed sheet,
and return the decisions. {len(selected)} questions.</p>
{sections}
</body></html>
"""
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def print_pdf(html_path: Path = SHEET_HTML, pdf_path: Path = SHEET_PDF) -> Path:
    edge = next((path for path in EDGE_CANDIDATES if path.is_file()), None)
    if edge is None:
        raise SystemExit("Microsoft Edge was not found for HTML-to-PDF print")
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    command = [
        str(edge), "--headless", "--disable-gpu", "--no-pdf-header-footer",
        f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri(),
    ]
    result = subprocess.run(command, capture_output=True, text=True,
                            timeout=180)
    if result.returncode != 0 or not pdf_path.is_file():
        raise SystemExit(
            f"Edge print failed ({result.returncode}): "
            f"{result.stderr[-500:]}")
    return pdf_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["apply", "sheet", "all"])
    parser.add_argument("--decisions", type=Path, default=DECISIONS)
    args = parser.parse_args()
    if args.command in {"apply", "all"}:
        print(json.dumps(apply_decisions(args.decisions),
                         indent=2, ensure_ascii=False))
    if args.command in {"sheet", "all"}:
        path = build_sheet()
        print(path)
        print(print_pdf())


if __name__ == "__main__":
    main()
