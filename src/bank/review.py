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


def _review_image(store: BankStore, rel: str, alt: str) -> str:
    path = (store.review_dir.parent / rel.replace("../", "", 1)
            if rel.startswith("../") else store.review_dir / rel)
    if not path.is_file():
        return "<p class='muted'>No image.</p>"
    return (f"<a href='{rel}' target='_blank'>"
            f"<img src='{rel}' alt='{_esc(alt)}'></a>")


def _asset_block(store: BankStore, asset: dict) -> str:
    aid = str(asset.get("id") or "")
    original_rel = (asset.get("review_original_path")
                    or asset.get("review_path")
                    or f"../assets/{aid}.png")
    owner_file = str(asset.get("owner_recreation_file") or "")
    recreation_rel = f"owner_recreations/{owner_file}" if owner_file else ""
    image = _review_image(store, original_rel, aid)
    recreation = (_review_image(store, recreation_rel, f"{aid} recreation")
                  if recreation_rel else "<p class='muted'>No recreation.</p>")
    native = _native_table_preview(asset.get("native_table"))
    choice = str(asset.get("review_choice") or "")
    note = str(asset.get("review_note_text")
               or asset.get("review_notes") or "")
    return f"""
    <div class="asset" data-aid="{_esc(aid)}">
      <div class="asset-head">
        <b>{_esc(asset.get('label') or aid)}</b>
        <span class="badge">{_esc(asset.get('kind'))}</span>
        <span class="badge">page {_esc(asset.get('page') or asset.get('source_page') or '?')}</span>
        <span class="badge">{_esc(asset.get('treatment'))}</span>
      </div>
      <div class="asset-grid">
        <div><div class="label">Original</div>{image}</div>
        <div><div class="label">Extracted</div>{native}</div>
        <div><div class="label">Recreation</div>{recreation}</div>
      </div>
      <label>Verdict
        <select class="asset-choice">
          <option value="use_original" {'selected' if choice == 'use_original' else ''}>Use original</option>
          <option value="use_recreation" {'selected' if choice == 'use_recreation' else ''}>Use recreation</option>
        </select>
      </label>
      <label>Comment
        <textarea class="asset-comment" rows="3"
          placeholder="Comment for this figure / table / crop">{_esc(note)}</textarea>
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
    verdict = str(question.get("status")
                  or question.get("review_verdict") or "")
    note = str(question.get("review_note_text")
               or question.get("review_notes") or "")
    return f"""
    <section class="question" id="{_esc(qid)}" data-qid="{_esc(qid)}"
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
          <option value="approved" {'selected' if verdict == 'approved' else ''}>Approve</option>
          <option value="needs_fix" {'selected' if verdict == 'needs_fix' else ''}>Needs fix</option>
          <option value="rejected" {'selected' if verdict == 'rejected' else ''}>Reject</option>
        </select>
      </label>
      <label>Comment
        <textarea class="question-comment" rows="3"
          placeholder="Comment for this question">{_esc(note)}</textarea>
      </label>
    </section>
    """


def build_review_sheet(store: BankStore, out_dir: Path,
                       *, subject: str, title: str = "",
                       extra_assets: list[dict] | None = None,
                       only_status: set[str] | None = None,
                       filename: str = "index.html",
                       export_name: str = "review_decisions.json") -> Path:
    """Write a review sheet and return its path.

    ``extra_assets`` renders assets that are not linked to a question (for
    example an unassigned MinerU crop) with their own comment boxes.
    ``only_status`` limits the sheet to questions in those statuses.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    questions = [question for question in store.questions()
                 if only_status is None
                 or question.get("status") in only_status]
    assets = {str(asset.get("id")): asset for asset in store.assets()}
    sections = "".join(
        _question_block(store, question, assets) for question in questions)
    if not sections:
        sections = "<p class='muted'>No questions match this review sheet.</p>"
    unassigned = ""
    if extra_assets:
        unassigned = (
            "<section class='unassigned'><h2>Unassigned assets</h2>"
            "<p>These MinerU crops are not linked to a question yet. "
            "Comment on any that belong to a question or should be "
            "discarded.</p>"
            + "".join(_asset_block(store, asset) for asset in extra_assets)
            + "</section>")
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
textarea {{ width: 100%; font-family: Arial, sans-serif; font-size: 10pt;
  margin-top: .25rem; }}
</style></head><body>
<h1>{_esc(title or subject)} — question bank review</h1>
<p>Review each question and asset. Export the decisions as JSON before
updating approvals.</p>
<button onclick="exportDecisions()">Export decisions JSON</button>
{sections}
{unassigned}
<script>
function exportDecisions() {{
  const questions = {{}};
  document.querySelectorAll('.question').forEach((node) => {{
    const qid = node.dataset.qid;
    const comment = node.querySelector('.question-comment')?.value || '';
    questions[qid] = {{
      verdict: node.querySelector('.question-choice').value,
      comment: comment,
      notes: comment,
      assets: {{}}
    }};
    node.querySelectorAll('.asset').forEach((asset) => {{
      const assetComment =
        asset.querySelector('.asset-comment')?.value || '';
      questions[qid].assets[asset.dataset.aid] = {{
        choice: asset.querySelector('.asset-choice').value,
        comment: assetComment,
        notes: assetComment
      }};
    }});
  }});
  const unassignedAssets = {{}};
  document.querySelectorAll('.unassigned .asset').forEach((asset) => {{
    const assetComment =
      asset.querySelector('.asset-comment')?.value || '';
    unassignedAssets[asset.dataset.aid] = {{
      choice: asset.querySelector('.asset-choice').value,
      comment: assetComment,
      notes: assetComment
    }};
  }});
  const payload = {{
    schema: 'bank.review-decisions.v1',
    subject: {json.dumps(subject)},
    exported_on: new Date().toISOString().slice(0, 10),
    questions: questions,
    unassigned_assets: unassignedAssets
  }};
  const blob = new Blob([JSON.stringify(payload, null, 2)],
    {{type: 'application/json'}});
  const link = document.createElement('a');
  link.href = URL.createObjectURL(blob);
  link.download = {json.dumps(export_name)};
  link.click();
}}
</script>
</body></html>
"""
    index = out_dir / filename
    index.write_text(page, encoding="utf-8")
    return index
