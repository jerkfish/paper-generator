"""P3: build local HTML review sheets for the asset-first bank.

Each paper gets one sheet.  The sheet shows the source crop, the extracted
native content, the recreation preview (tables only) and verdict controls.
Decisions export as JSON; they are not written into approvals.json until the
owner has reviewed them.
"""
from __future__ import annotations

import html
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from src import config

TRACKING = config.TRACKING_DIR / "csc429"
BANK = TRACKING / "bank"
QUESTIONS = BANK / "questions"
ASSETS = BANK / "assets"
REVIEW = BANK / "review"


def _load(path: Path, default):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def _esc(value) -> str:
    return html.escape(str(value or ""))


def _native_table(table: dict) -> str:
    if not table:
        return "<p class='muted'>No native table.</p>"
    parts = ["<table class='native'>"]
    for row in table.get("rows") or []:
        parts.append("<tr>")
        for cell in row.get("cells") or []:
            colspan = int(cell.get("colspan") or 1)
            attr = f" colspan='{colspan}'" if colspan > 1 else ""
            parts.append(
                f"<td{attr}>{_esc(cell.get('text', ''))}</td>")
        parts.append("</tr>")
    parts.append("</table>")
    return "".join(parts)


def _asset_block(asset: dict) -> str:
    aid = asset["id"]
    crop = f"../assets/{aid}.png"
    compare = (asset.get("compare") or {})
    side = compare.get("side_by_side") or ""
    side_rel = ""
    if side:
        side_rel = "../../" + side.replace("\\", "/")
        # side is relative to PROJECT_ROOT; review/ lives under bank/review.
        side_rel = f"../../{side.replace('data/tracking/csc429/', '')}"
    verdict_options = [
        ("use_original", "Use original crop",
         asset.get("treatment") == "crop" or asset.get("kind") != "table"),
        ("use_recreation", "Use native table",
         bool(asset.get("native_table"))),
    ]
    select = "".join(
        f"<option value='{value}'{' selected' if selected else ''}"
        f"{'' if enabled else ' disabled'}>{_esc(label)}</option>"
        for value, label, selected in verdict_options
        for enabled in ([True] if value == "use_original"
                        else [bool(asset.get("native_table"))]))
    return f"""
    <div class="asset" data-aid="{_esc(aid)}">
      <div class="asset-head">
        <b>{_esc(asset.get('label') or aid)}</b>
        <span class="badge">{_esc(asset.get('kind'))}</span>
        <span class="badge">p{_esc(asset.get('page'))}</span>
        <span class="badge">{_esc(asset.get('treatment'))}</span>
        <span class="badge">{_esc(compare.get('status', 'pending'))}</span>
        <span class="badge">score {_esc(compare.get('score', ''))}</span>
      </div>
      <div class="asset-grid">
        <div><div class="label">Original crop</div>
          <a href="{crop}" target="_blank"><img src="{crop}" alt="{_esc(aid)}"></a>
        </div>
        <div><div class="label">Extracted native</div>
          {_native_table(asset.get('native_table'))}
        </div>
        <div><div class="label">Recreation / compare</div>
          {"<a href='" + side_rel + "' target='_blank'><img src='" + side_rel + "'></a>" if side_rel else "<p class='muted'>Not recreated; original crop enforced.</p>"}
        </div>
      </div>
      <label>Asset verdict
        <select class="asset-choice">{select}</select>
      </label>
      <p class="muted">{_esc(compare.get('reason', ''))}</p>
    </div>
    """


def _question_block(question: dict, assets: dict[str, dict],
                    unsure_by_qid: dict[str, list[dict]]) -> str:
    qid = question["id"]
    assets_html = "".join(
        _asset_block(assets[aid]) for aid in question.get("assets") or []
        if aid in assets)
    unsure = unsure_by_qid.get(qid, [])
    unsure_html = ""
    if unsure:
        unsure_html = "<div class='unsure'><b>Unsure / needs fix</b><ul>" + "".join(
            f"<li>{_esc(item.get('code'))}: {_esc(item.get('detail'))} "
            f"({_esc(item.get('path'))})</li>" for item in unsure) + "</ul></div>"
    text = question.get("native_text_blocks", [{}])[0].get("text", "")
    refs = ", ".join(question.get("refs") or []) or "—"
    return f"""
    <section class="question" data-qid="{_esc(qid)}"
             data-hash="{_esc(question.get('content_hash'))}">
      <h2>QUESTION {_esc(question.get('slot'))} <span class="marks">({_esc(question.get('marks'))} marks)</span></h2>
      <div class="meta">
        {_esc(question.get('source_paper'))} · page {_esc(question.get('pages'))}
        · {_esc(question.get('topic_primary'))}
        · status <b>{_esc(question.get('status'))}</b>
        · refs: {_esc(refs)}
      </div>
      {unsure_html}
      <pre class="native-text">{_esc(text)}</pre>
      {assets_html}
      <div class="verdict">
        <label>Question verdict
          <select class="question-choice">
            <option value="">— choose —</option>
            <option value="approved">Approve</option>
            <option value="rejected">Reject</option>
            <option value="needs_fix">Needs fix</option>
          </select>
        </label>
        <label>Notes <textarea class="notes" rows="2"></textarea></label>
      </div>
    </section>
    """


CSS = """
body{font-family:Arial,Helvetica,sans-serif;margin:24px;background:#f4f5f7;color:#111}
h1{margin:0 0 4px} .sub{color:#555;margin-bottom:18px}
.question{background:#fff;border:1px solid #d8dbe0;border-radius:8px;padding:16px;margin:20px 0}
.question h2{font-size:18px;margin:0 0 4px} .marks{font-weight:400;color:#555}
.meta{font-size:12px;color:#555;margin-bottom:10px}
.native-text{white-space:pre-wrap;font:13px/1.45 Consolas,monospace;background:#fafafa;border:1px solid #eee;padding:10px}
.unsure{background:#fff1f0;border:1px solid #ffb3ad;padding:8px;margin:8px 0;font-size:13px}
.asset{border-top:1px solid #eee;padding:12px 0}
.asset-head{display:flex;gap:8px;align-items:center;flex-wrap:wrap;margin-bottom:8px}
.badge{background:#eef1f5;border-radius:10px;padding:2px 8px;font-size:11px;color:#333}
.asset-grid{display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;align-items:start}
.label{font-size:11px;text-transform:uppercase;color:#666;margin-bottom:4px}
.asset img{max-width:100%;max-height:360px;border:1px solid #ccc;background:#fff}
table.native{border-collapse:collapse;width:100%;font-size:12px}
table.native td{border:1px solid #333;padding:3px 5px;vertical-align:top}
.verdict{display:flex;gap:16px;align-items:flex-start;margin-top:12px;flex-wrap:wrap}
.verdict label{font-size:12px;display:flex;flex-direction:column;gap:4px}
select,textarea{font:13px Arial;padding:5px}
textarea{width:360px}
.muted{color:#777;font-size:12px}
.sticky{position:sticky;top:0;background:#f4f5f7;padding:12px 0;z-index:5}
button{font:13px Arial;padding:8px 12px;margin-right:8px;cursor:pointer}
"""

JS = """
const paper = document.body.dataset.paper;
function collect(){
  const out={subject:"CSC429",paper_id:paper,exported_at:new Date().toISOString(),questions:{}};
  document.querySelectorAll('.question').forEach(q=>{
    const qid=q.dataset.qid;
    const verdict=q.querySelector('.question-choice').value;
    const notes=q.querySelector('.notes').value;
    const assets={};
    q.querySelectorAll('.asset').forEach(a=>{
      const choice=a.querySelector('.asset-choice');
      if(choice && choice.value) assets[a.dataset.aid]=choice.value;
    });
    if(verdict || notes || Object.keys(assets).length){
      out.questions[qid]={verdict,notes,assets,content_hash:q.dataset.hash};
    }
  });
  return out;
}
function download(){
  const data=collect();
  const blob=new Blob([JSON.stringify(data,null,2)],{type:'application/json'});
  const a=document.createElement('a');
  a.href=URL.createObjectURL(blob);
  a.download=`CSC429-${paper}-decisions.json`;
  a.click();
  URL.revokeObjectURL(a.href);
}
function stash(){
  localStorage.setItem('csc429-review-'+paper,JSON.stringify(collect()));
}
document.addEventListener('change',stash);
document.addEventListener('input',stash);
const saved=localStorage.getItem('csc429-review-'+paper);
if(saved){
  try{
    const data=JSON.parse(saved);
    Object.entries(data.questions||{}).forEach(([qid,row])=>{
      const q=document.querySelector(`.question[data-qid="${qid}"]`);
      if(!q) return;
      q.querySelector('.question-choice').value=row.verdict||'';
      q.querySelector('.notes').value=row.notes||'';
      Object.entries(row.assets||{}).forEach(([aid,choice])=>{
        const a=q.querySelector(`.asset[data-aid="${aid}"] .asset-choice`);
        if(a) a.value=choice;
      });
    });
  }catch(e){}
}
"""


def build() -> dict:
    REVIEW.mkdir(parents=True, exist_ok=True)
    questions = [_load(path, {}) for path in QUESTIONS.glob("*.json")]
    assets = {row["id"]: row for row in
              (_load(path, {}) for path in ASSETS.glob("*.json")) if row.get("id")}
    unsure = _load(BANK / "unsure.json", {}).get("items", [])
    unsure_by_qid = defaultdict(list)
    for item in unsure:
        if item.get("question_id"):
            unsure_by_qid[item["question_id"]].append(item)
    by_paper = defaultdict(list)
    for question in questions:
        by_paper[question["source_paper"]].append(question)
    links = []
    for paper_id, rows in sorted(by_paper.items()):
        rows.sort(key=lambda row: (
            0 if row.get("status") == "needs_fix" else 1,
            -int(row.get("marks") or 0),
            min(row.get("pages") or [0]),
            str(row.get("slot", "")),
        ))
        blocks = "".join(
            _question_block(row, assets, unsure_by_qid) for row in rows)
        page = f"""<!doctype html><html><head><meta charset="utf-8">
<title>CSC429 review — {_esc(paper_id)}</title><style>{CSS}</style></head>
<body data-paper="{_esc(paper_id)}">
<div class="sticky">
<h1>CSC429 review — {_esc(paper_id)}</h1>
<div class="sub">{len(rows)} questions · sorted by unsure first, then marks, then page.
Review each asset and question, then export the decisions JSON.</div>
<button onclick="download()">Export decisions JSON</button>
<button onclick="localStorage.removeItem('csc429-review-'+document.body.dataset.paper);location.reload()">Clear saved decisions</button>
</div>
{blocks}
<script>{JS}</script>
</body></html>"""
        target = REVIEW / f"{paper_id}.html"
        target.write_text(page, encoding="utf-8")
        links.append((paper_id, target.name, len(rows)))
    index_rows = "".join(
        f"<tr><td><a href='{_esc(name)}'>{_esc(paper)}</a></td>"
        f"<td>{count}</td></tr>" for paper, name, count in links)
    index = f"""<!doctype html><html><head><meta charset="utf-8">
<title>CSC429 review sheets</title><style>{CSS}</style></head><body>
<h1>CSC429 P3 review sheets</h1>
<p class="sub">Gate 1 is human review. Each paper has one sheet. Export the
decisions JSON for each paper, then place it in the bank inbox for import.</p>
<table class="native"><tr><th>Paper</th><th>Questions</th></tr>
{index_rows}</table></body></html>"""
    (REVIEW / "index.html").write_text(index, encoding="utf-8")
    (REVIEW / "README.md").write_text(
        "# CSC429 review sheets\n\n"
        "Open `index.html` or a paper sheet. Review every asset and question, "
        "then click **Export decisions JSON**. Put the exported files in "
        "`data/tracking/csc429/bank/inbox/`.\n\n"
        "HTML sheets are local only; no server or publication is involved.\n",
        encoding="utf-8")
    summary = {
        "schema_version": 1,
        "subject": "CSC429",
        "stage": "P3",
        "papers": len(links),
        "questions": len(questions),
        "assets": len(assets),
        "unsure": len(unsure),
        "index": "data/tracking/csc429/bank/review/index.html",
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
    (BANK / "review_index.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    return summary


def main() -> None:
    print(json.dumps(build(), indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
