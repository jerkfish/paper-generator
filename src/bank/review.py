"""Generic HTML review sheet for a recycled question bank.

The sheet keeps the CSC429 review workflow: for every asset the reviewer sees
the original crop, the extracted native content and any recreation, then
chooses “use original” or “use recreation”.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

from src.bank.store import BankStore


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _native_table_preview(table: dict | None) -> str:
    if not table:
        return "<p class='muted'>No recreation.</p>"
    parts = ["<table class='native'>"]
    for row in table.get("rows") or []:
        parts.append("<tr>")
        for cell in row.get("cells") or []:
            colspan = int(cell.get("colspan") or 1)
            attr = f" colspan='{colspan}'" if colspan > 1 else ""
            parts.append(f"<td{attr}>{_esc(cell.get('text', ''))}</td>")
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def _asset_block(store: BankStore, asset: dict) -> str:
    aid = str(asset.get("id") or "")
    image_rel = f"../assets/{aid}.png"
    image_path = store.assets_dir / f"{aid}.png"
    image = (
        f"<a href='{image_rel}' target='_blank'>"
        f"<img src='{image_rel}' alt='{_esc(aid)}'></a>"
        if image_path.is_file() else "<p class='muted'>No crop.</p>"
    )
    native = _native_table_preview(asset.get("native_table"))
    return f"""
    <div class="asset" data-aid="{_esc(aid)}">
      <div class="asset-head">
        <b>{_esc(asset.get('label') or aid)}</b>
        <span class="badge">{_esc(asset.get('kind'))}</span>
        <span class="badge">page {_esc(asset.get('page'))}</span>
        <span class="badge">{_esc(asset.get('treatment'))}</span>
      </div>
      <div class="asset-grid">
        <div><div class="label">Original</div>{image}</div>
        <div><div class="label">Extracted</div>{native}</div>
        <div><div class="label">Recreation</div>{native}</div>
      </div>
      <label>Verdict
        <select class="asset-choice">
          <option value="use_original">Use original</option>
          <option value="use_recreation">Use recreation</option>
        </select>
      </label>
    </div>
    """


def _question_block(store: BankStore, question: dict,
                    assets: dict[str, dict]) -> str:
    qid = str(question.get("id") or "")
    text = (question.get("native_text_blocks") or [{}])[0].get("text", "")
    refs = ", ".join(str(ref) for ref in question.get("refs") or []) or "—"
    body = "".join(
        _asset_block(store, assets[aid])
        for aid in question.get("assets") or [] if aid in assets)
    return f"""
    <section class="question" data-qid="{_esc(qid)}"
             data-hash="{_esc(question.get('content_hash'))}">
      <h2>QUESTION {_esc(question.get('slot') or qid)}
        <span class="marks">({_esc(question.get('marks'))} marks)</span></h2>
      <p><b>Source:</b> {_esc(question.get('source_paper'))}
         · page {_esc(question.get('pages'))}
         · refs: {_esc(refs)}</p>
      <pre>{_esc(text)}</pre>
      {body or "<p class='muted'>No linked assets.</p>"}
      <label>Question verdict
        <select class="question-choice">
          <option value="approved">Approve</option>
          <option value="needs_fix">Needs fix</option>
          <option value="rejected">Reject</option>
        </select>
      </label>
    </section>
    """


def build_review_sheet(store: BankStore, out_dir: Path,
                       *, subject: str, title: str = "") -> Path:
    """Write ``index.html`` and return its path."""
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    questions = list(store.questions())
    assets = {str(asset.get("id")): asset for asset in store.assets()}
    sections = "".join(
        _question_block(store, question, assets) for question in questions)
    page = f"""<!doctype html>
<html><head><meta charset="utf-8">
<title>{_esc(title or subject)} — bank review</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 2rem; color: #222; }}
.question {{ border-top: 3px solid #333; margin-top: 2rem; padding-top: 1rem; }}
.asset {{ border: 1px solid #bbb; margin: 1rem 0; padding: .75rem; }}
.asset-head .badge {{ background: #eee; padding: .1rem .4rem; margin-left: .4rem; }}
.asset-grid {{ display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 1rem; }}
.asset-grid img {{ max-width: 100%; max-height: 320px; }}
.label {{ font-weight: bold; margin-bottom: .3rem; }}
pre {{ white-space: pre-wrap; background: #f7f7f7; padding: .75rem; }}
table.native {{ border-collapse: collapse; width: 100%; }}
table.native td {{ border: 1px solid #999; padding: .25rem; font-size: 12px; }}
.muted {{ color: #777; }}
.marks {{ font-weight: normal; }}
</style></head><body>
<h1>{_esc(title or subject)} — question bank review</h1>
<p>Review each question and asset. Export the decisions as JSON before
updating approvals.</p>
<button onclick="exportDecisions()">Export decisions JSON</button>
{sections}
<script>
function exportDecisions() {{
  const questions = {{}};
  document.querySelectorAll('.question').forEach((node) => {{
    const qid = node.dataset.qid;
    questions[qid] = {{
      verdict: node.querySelector('.question-choice').value,
      assets: {{}}
    }};
    node.querySelectorAll('.asset').forEach((asset) => {{
      questions[qid].assets[asset.dataset.aid] =
        asset.querySelector('.asset-choice').value;
    }});
  }});
  const blob = new Blob([JSON.stringify({{subject: {json.dumps(subject)},
    questions}}, null, 2)], {{type: 'application/json'}});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = 'review_decisions.json';
  link.click();
}}
</script>
</body></html>
"""
    index = out_dir / "index.html"
    index.write_text(page, encoding="utf-8")
    return index
