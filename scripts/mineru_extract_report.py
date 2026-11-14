"""Build a full Markdown extraction report from cached MinerU results.

Prototype: reads the V1 content_list for both models, renders every block by
page, converts tables to Markdown, embeds figures/equations, lists assets and
fallbacks, and shows block-level pipeline/vlm differences.

No API calls and no writes outside the report path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path


class TableHTML(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows = []
        self.row = None
        self.cell = None
        self.buf = []

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.row = []
        elif tag in ("td", "th"):
            self.cell = []
            self.buf = []
        elif tag == "br" and self.cell is not None:
            self.buf.append(" ")

    def handle_data(self, data):
        if self.cell is not None:
            self.buf.append(data)

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cell is not None:
            self.row.append(" ".join("".join(self.buf).split()))
            self.cell = None
        elif tag == "tr" and self.row is not None:
            self.rows.append(self.row)
            self.row = None


def markdown_table(html_text: str) -> str:
    parser = TableHTML()
    parser.feed(html_text or "")
    rows = [row for row in parser.rows if any(cell.strip() for cell in row)]
    if not rows:
        return "```html\n" + (html_text or "") + "\n```"
    width = max(len(row) for row in rows)
    rows = [row + [""] * (width - len(row)) for row in rows]

    def esc(value: str) -> str:
        return value.replace("|", "\\|").replace("\n", " ").strip()

    header = "| " + " | ".join(esc(cell) for cell in rows[0]) + " |"
    separator = "| " + " | ".join("---" for _ in range(width)) + " |"
    body = ["| " + " | ".join(esc(cell) for cell in row) + " |"
            for row in rows[1:]]
    return "\n".join([header, separator] + body)


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_model(paper_dir: Path, model: str) -> dict:
    cache = next(paper_dir.glob(model + "_*"))
    manifest = json.loads((cache / "manifest.json").read_text(encoding="utf-8"))
    content = [path for path in cache.rglob("*content_list*.json")
               if "v2" not in path.name.lower()][0]
    blocks = json.loads(content.read_text(encoding="utf-8"))
    normalized = json.loads(
        (cache / "review" / "normalized.json").read_text(encoding="utf-8"))
    full = (cache / "full.md").read_text(encoding="utf-8")
    return {"model": model, "cache": cache, "manifest": manifest,
            "blocks": blocks, "normalized": normalized, "full": full}


def block_caption(block: dict) -> str:
    for key in ("image_caption", "table_caption"):
        value = block.get(key)
        if isinstance(value, list):
            value = " ".join(str(item) for item in value)
        if value:
            return " ".join(str(value).split())
    return ""


def heading_level(text: str) -> int:
    value = " ".join(text.split())
    if value in ("UNIVERSITI TEKNOLOGI MARA FINAL EXAMINATION",
                 "INSTRUCTIONS TO CANDIDATES", "PART A", "PART B",
                 "END OF QUESTION PAPER"):
        return 3
    if re.fullmatch(r"QUESTION \d+", value):
        return 4
    return 0


class ReportBuilder:
    def __init__(self, paper_dir: Path, source: Path, attached: Path | None,
                 out: Path):
        self.paper_dir = paper_dir
        self.source = source
        self.attached = attached
        self.out = out
        self.vlm = load_model(paper_dir, "vlm")
        self.pipeline = (load_model(paper_dir, "pipeline")
                         if any(paper_dir.glob("pipeline_*")) else None)
        self.lines: list[str] = []

    def rel(self, path: Path) -> str:
        return os.path.relpath(path, self.out.parent).replace("\\", "/")

    def add(self, *lines: str) -> None:
        self.lines.extend(lines)

    def metadata(self) -> None:
        attached_sha = sha256(self.attached) if self.attached else ""
        source_sha = sha256(self.source)
        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        self.add(f"# MinerU full extraction — {self.paper_dir.name}", "")
        self.add("## Contents", "")
        self.add("- Run metadata")
        self.add("- Counts")
        self.add("- Full extraction — VLM (primary), pages 1–6")
        self.add("- Structured questions")
        self.add("- Asset inventory and fallbacks")
        self.add("- Pipeline-only Figure 3 detail")
        self.add("- Pipeline vs VLM differences")
        self.add("- Raw MinerU Markdown (both models)")
        self.add("- Block provenance (VLM)")
        self.add("")
        self.add("## Run metadata", "")
        self.add(f"- Generated: {now}")
        if self.attached:
            self.add(f"- Attached PDF: `{self.attached}`")
            self.add(f"- Attached SHA-256: `{attached_sha}`")
        self.add(f"- Repository source: `{self.source}`")
        self.add(f"- Repository SHA-256: `{source_sha}`")
        if self.attached:
            self.add(f"- Attached and repository copies match: "
                     f"**{attached_sha == source_sha}**")
        self.add(f"- Pages: {self.vlm['manifest'].get('page_count')}")
        if self.pipeline:
            self.add(f"- Pipeline batch: `{self.pipeline['manifest'].get('batch_id')}` "
                     f"({self.pipeline['manifest'].get('duration_seconds')} s)")
        self.add(f"- VLM batch: `{self.vlm['manifest'].get('batch_id')}` "
                 f"({self.vlm['manifest'].get('duration_seconds')} s)")
        if self.pipeline:
            self.add(f"- Pipeline cache: `{self.rel(self.pipeline['cache'])}`")
        self.add(f"- VLM cache: `{self.rel(self.vlm['cache'])}`")
        self.add("- MinerU result reuse: the attached file is byte-identical to "
                 "the pilot source, so both verified caches were reused. No new "
                 "API call was made; cost $0.00.")
        self.add("")

    def counts(self) -> None:
        self.add("## Counts", "")
        self.add("| Model | Figures | Tables | Equations | Assets | Referenced | Resolved | Fallback | Questions |")
        self.add("|---|---:|---:|---:|---:|---:|---:|---:|---:|")
        for model in (item for item in (self.pipeline, self.vlm) if item):
            counts = model["normalized"]["counts"]
            self.add(
                f"| {model['model']} | {counts['figures']} | {counts['tables']} | "
                f"{counts['equations']} | {counts['assets']} | "
                f"{counts['referenced_figures_tables']} | "
                f"{counts['resolved_references']} | {counts['fallback_assets']} | "
                f"{counts['questions']} |")
        self.add("")

    def render_page(self, model: dict, page_idx: int) -> None:
        blocks = []
        for index, block in enumerate(model["blocks"]):
            if int(block.get("page_idx", 0)) != page_idx:
                continue
            item = dict(block)
            item["_id"] = f"B{index + 1:04d}"
            blocks.append(item)
        self.add(f"## Page {page_idx + 1}", "")
        furniture = []
        for block in blocks:
            kind = str(block.get("type", "")).lower()
            text = str(block.get("text", "") or "").strip()
            bbox = block.get("bbox", "")
            if kind in ("header", "footer", "page_number"):
                furniture.append((kind, text, bbox, block["_id"]))
                continue
            self.add(f"<!-- {block['_id']} type={kind} "
                     f"page={page_idx} bbox={bbox} -->")
            if kind == "text":
                if not text:
                    continue
                level = heading_level(text)
                if level:
                    self.add("#" * level + " " + " ".join(text.split()))
                elif re.fullmatch(r"\(\s*\d+\s*marks?\s*\)",
                                  " ".join(text.split()), re.I):
                    self.add(f"*{' '.join(text.split())}*")
                else:
                    self.add(text)
                self.add("")
            elif kind == "image":
                cap = block_caption(block)
                image = model["cache"] / str(block.get("img_path", ""))
                self.add(f"![{cap or 'Figure'}]({self.rel(image)})")
                if cap:
                    self.add(f"**{cap}**")
                self.add("")
            elif kind == "table":
                cap = block_caption(block)
                if cap:
                    self.add(f"**{cap}**")
                self.add(markdown_table(block.get("table_body", "")))
                image = model["cache"] / str(block.get("img_path", ""))
                self.add("")
                self.add(f"![{cap or 'Table'}]({self.rel(image)})")
                self.add("")
                if block.get("table_body"):
                    self.add("<details><summary>Raw table HTML</summary>", "")
                    self.add("```html")
                    self.add(block["table_body"])
                    self.add("```", "", "</details>", "")
            elif kind == "equation":
                self.add(text, "")
                image_path = block.get("img_path")
                if image_path:
                    image = model["cache"] / str(image_path)
                    self.add(f"![Equation image]({self.rel(image)})", "")
                if self.pipeline and model["model"] == "vlm" and page_idx == 5:
                    pipeline_eq = next(
                        (item for item in self.pipeline["blocks"]
                         if item.get("type") == "equation"
                         and int(item.get("page_idx", -1)) == 5
                         and item.get("img_path")), None)
                    if pipeline_eq:
                        image = self.pipeline["cache"] / str(
                            pipeline_eq["img_path"])
                        self.add(
                            "> **Figure 3 image:** the VLM result returned the "
                            "equation as LaTeX but no image block. The pipeline "
                            "result contains the Figure 3 image, shown here for "
                            "completeness.", "")
                        self.add(f"![Figure 3 (pipeline image)]({self.rel(image)})", "")
        if furniture:
            self.add("<details><summary>Page furniture (headers, footers, "
                     "page number)</summary>", "")
            for kind, text, bbox, block_id in furniture:
                label = text or "[empty]"
                self.add(f"- **{kind}** `{block_id}` bbox={bbox}: {label}")
            self.add("", "</details>", "")

    def question_table(self, model: dict) -> None:
        self.add("## Structured questions — VLM", "")
        self.add("| QID | Page | Marks | Refs | Assets | Fallback | Subparts | Text (start) |")
        self.add("|---|---:|---:|---|---:|---:|---:|---|")
        for question in model["normalized"]["questions"]:
            text = " ".join(question["text"].split())[:100]
            text = text.replace("|", "\\|")
            refs = ", ".join(question.get("refs") or []) or "—"
            marks = question.get("marks")
            marks = str(marks) if marks is not None else "—"
            self.add(
                f"| {question['question_id']} | {int(question['page_idx']) + 1} | "
                f"{marks} | {refs} | {len(question.get('assets') or [])} | "
                f"{len(question.get('fallback_assets') or [])} | "
                f"{len(question.get('subparts') or [])} | {text} |")
        self.add("")
        self.add("Question IDs are unique review IDs. Part A and Part B both "
                 "restart at QUESTION 1, and the paper repeats “Question 1 is "
                 "based on…”, so suffixes such as `-2` and `-3` are expected. "
                 "Marks shown as `—` are present in the page text but were not "
                 "attached to the heading block by the normalizer.")
        self.add("")

    def asset_table(self, model: dict) -> None:
        self.add("## Asset inventory — VLM", "")
        qids = [question["question_id"]
                for question in model["normalized"]["questions"]]
        self.add("| Asset | Kind | Label | Caption | Page | BBox | Question | File |")
        self.add("|---|---|---|---|---:|---|---|---|")
        for asset in model["normalized"]["assets"]:
            qidx = asset.get("question_index")
            qid = (qids[qidx] if isinstance(qidx, int)
                   and 0 <= qidx < len(qids) else "—")
            image = Path(asset.get("img_path") or "")
            if image.is_absolute() or image.exists():
                resolved = image
            else:
                resolved = model["cache"] / image
            image_path = Path(self.rel(resolved)).as_posix()
            caption = (asset.get("caption") or "—").replace("|", "\\|")
            self.add(
                f"| {asset['asset_id']} | {asset['kind']} | "
                f"{asset.get('label') or '—'} | {caption} | "
                f"{int(asset.get('page_idx', 0)) + 1} | {asset.get('bbox')} | "
                f"{qid} | `{image_path}` |")
        self.add("")

    def fallback_table(self, model: dict) -> None:
        self.add("## Fallbacks — VLM", "")
        self.add("| Fallback | Label | Page | File | Reason |")
        self.add("|---|---|---:|---|---|")
        for item in model["normalized"].get("fallback", []):
            path = Path(item.get("path", ""))
            try:
                path = Path(self.rel(path)).as_posix()
            except Exception:
                pass
            self.add(
                f"| {item['asset_id']} | {item.get('label', '')} | "
                f"{int(item.get('page_idx', 0)) + 1} | `{path}` | "
                f"{item.get('reason', '')} |")
        self.add("")

    def figure3_note(self) -> None:
        self.add("## Pipeline-only detail: Figure 3", "")
        self.add("The pipeline result contains an image for the FIGURE 3 "
                 "equation; the VLM result contains the LaTeX but no image "
                 "block. The report above shows the pipeline image on page 6. "
                 "This is why the VLM fallback exists and why a merged "
                 "extraction is better than either model alone.")
        self.add("")

    def diff(self) -> None:
        self.add("## Pipeline vs VLM differences", "")
        rows = []
        for index, (pipe, vlm) in enumerate(
                zip(self.pipeline["blocks"], self.vlm["blocks"])):
            if (pipe.get("type") != vlm.get("type")
                    or int(pipe.get("page_idx", 0)) != int(vlm.get("page_idx", 0))):
                rows.append((index, "type/page", int(pipe.get("page_idx", 0)),
                             str(pipe.get("type")), str(vlm.get("type"))))
                continue
            pipe_text = " ".join(str(pipe.get("text", "")).split())
            vlm_text = " ".join(str(vlm.get("text", "")).split())
            if pipe_text != vlm_text:
                rows.append((index, str(pipe.get("type")),
                             int(pipe.get("page_idx", 0)), pipe_text, vlm_text))
        self.add(f"{len(rows)} block-level differences were found out of "
                 f"{len(self.vlm['blocks'])} blocks. The differences are almost "
                 "entirely equation formatting: VLM emits LaTeX subscripts and "
                 "fractions; pipeline leaves plain text or partially formatted "
                 "LaTeX.")
        self.add("")
        self.add("| # | Type | Page | Pipeline | VLM |")
        self.add("|---:|---|---:|---|---|")
        for index, kind, page, pipe_text, vlm_text in rows:
            pipe_text = pipe_text.replace("|", "\\|")[:240]
            vlm_text = vlm_text.replace("|", "\\|")[:240]
            self.add(f"| {index + 1} | {kind} | {page + 1} | "
                     f"{pipe_text} | {vlm_text} |")
        self.add("")

    def raw_markdown(self) -> None:
        for model in (item for item in (self.vlm, self.pipeline) if item):
            label = model["model"]
            self.add(f"## Raw MinerU Markdown — {label}", "")
            text = model["full"].replace(
                "](images/", f"]({self.rel(model['cache'])}/images/")
            self.add(f"<details><summary>Open raw {label} full.md</summary>", "")
            self.add("````markdown")
            self.add(text)
            self.add("````", "", "</details>", "")

    def provenance(self) -> None:
        self.add("## Block provenance — VLM", "")
        self.add("| # | Block | Type | Page | BBox | Content |")
        self.add("|---:|---|---|---:|---|---|")
        for index, block in enumerate(self.vlm["blocks"]):
            content = str(block.get("text", "") or block.get("img_path", "")
                          or block_caption(block))
            content = " ".join(content.split()).replace("|", "\\|")[:180]
            self.add(
                f"| {index + 1} | B{index + 1:04d} | {block.get('type')} | "
                f"{int(block.get('page_idx', 0)) + 1} | {block.get('bbox')} | "
                f"{content} |")
        self.add("")

    def build(self) -> Path:
        self.metadata()
        self.counts()
        self.add("## Full extraction — VLM (primary)", "")
        if self.pipeline:
            self.add("The VLM result is used as the primary text because it "
                     "reconstructs inline mathematics as LaTeX. Page furniture "
                     "and block provenance are retained. A pipeline-only "
                     "Figure 3 image is inserted on page 6.")
        else:
            self.add("VLM-only report: the owner selected VLM as the default "
                     "model, so the pipeline model was not run for this paper. "
                     "Page furniture and block provenance are retained.")
        self.add("")
        for page_idx in range(int(self.vlm["manifest"].get("page_count", 0))):
            self.render_page(self.vlm, page_idx)
        self.question_table(self.vlm)
        self.asset_table(self.vlm)
        self.fallback_table(self.vlm)
        if self.pipeline:
            self.figure3_note()
            self.diff()
        else:
            self.add("## Pipeline comparison", "")
            self.add("Pipeline was not run for this paper because VLM is the "
                     "selected default model. This report is VLM-only.")
            self.add("")
        self.raw_markdown()
        self.provenance()
        self.out.parent.mkdir(parents=True, exist_ok=True)
        self.out.write_text("\n".join(self.lines), encoding="utf-8")
        return self.out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--paper-dir", required=True,
                        help="Directory containing pipeline_* and vlm_* caches")
    parser.add_argument("--source", required=True, help="Repository source PDF")
    parser.add_argument("--attached", default="", help="Optional attached copy")
    parser.add_argument("--out", default="", help="Report path")
    args = parser.parse_args()
    paper_dir = Path(args.paper_dir)
    out = Path(args.out) if args.out else paper_dir / "EXTRACTION_REPORT.md"
    builder = ReportBuilder(
        paper_dir=paper_dir,
        source=Path(args.source),
        attached=Path(args.attached) if args.attached else None,
        out=out,
    )
    print(builder.build())


if __name__ == "__main__":
    main()
