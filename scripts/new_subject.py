"""Scaffold a new subject without onboarding it.

The command creates registry metadata, a lifecycle state, the input/output
folders and a subject plugin package.  It never promotes the subject to
``available``, downloads papers, calls an LLM, uploads to R2 or deploys the
Worker.  Human checkpoints in ``docs/SUBJECT_PLAYBOOK.md`` still apply.

Examples:

    uv run python -m scripts.new_subject TEST000 --type C --dry-run
    uv run python -m scripts.new_subject CSC402 --type C --title "Programming I"
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from src import config
from src.subjects.lifecycle import new_state, save_state
from src.subjects.registry import load_subjects

VALID_TYPES = {"A", "B", "C"}
CODE_RE = re.compile(r"^[A-Z][A-Z0-9]{2,9}$")
TYPE_DESCRIPTION = {
    "A": "lecture slides + LLM theory",
    "B": "deterministic computed papers (no LLM)",
    "C": "hybrid: deterministic generators + LLM theory",
}


def _permissions() -> dict:
    blank = {
        "allowed": False,
        "basis": "unsure",
        "confirmed_by": "",
        "confirmed_on": "",
        "notes": "Record before stage 9. Do not publish until allowed is true.",
    }
    return {
        "papers": dict(blank),
        "scheme": dict(blank),
        "slides": dict(blank),
        "publication": dict(blank),
    }


def _capabilities(subject_type: str) -> dict:
    deterministic = subject_type == "B"
    return {
        "subject_type": subject_type,
        "generation": ("deterministic" if deterministic else
                       "llm_theory" if subject_type == "A" else "hybrid"),
        "prebuild": ("plugin" if deterministic else
                     "llm_seed_set" if subject_type == "A" else "plugin"),
        "public_documents": ("copy_cached" if deterministic else
                             "rebuild_scheme"),
        "needs_llm": not deterministic,
        "uses_slides": subject_type in {"A", "C"},
        "uses_past_papers": True,
        "deterministic": deterministic,
        "practice_mode": not deterministic,
        "placeholders": not deterministic,
        "public_scheme_requires_quote_marker": not deterministic,
        "planner_style": "modern",
    }


def _plugin_module(code: str) -> str:
    return f"src.subjects.{code.lower()}.plugin"


def _plugins(code: str, subject_type: str) -> dict:
    base = _plugin_module(code)
    plugins = {
        "generator_labels": f"{base}:generator_labels",
        "topic_labels": f"{base}:topic_labels",
    }
    if subject_type in {"A", "C"}:
        plugins.update({
            "plan": f"{base}:plan",
            "plan_markdown": f"{base}:plan_markdown",
            "plan_inputs": f"{base}:plan_inputs",
            "library_seeds": f"{base}:library_seeds",
            "library_metadata": f"{base}:library_metadata",
        })
    if subject_type in {"B", "C"}:
        plugins["prebuild"] = f"{base}:build_seed"
    return plugins


def _subject_json(code: str, title: str, subject_type: str,
                  order: int) -> dict:
    deterministic = subject_type == "B"
    return {
        "code": code,
        "title": title,
        "status": "coming_soon",
        "type": subject_type,
        "order": order,
        "has_practice_mode": not deterministic,
        "has_placeholders": not deterministic,
        "header_text": f"{code} {title.upper()}",
        "template_path": "",
        "fingerprint": {},
        "deck_map": {},
        "topic_deck_allowlist": {},
        "enabled_computed_generators": [],
        "capabilities": _capabilities(subject_type),
        "permissions": _permissions(),
        "plugins": _plugins(code, subject_type),
    }


def _plugin_source(code: str, subject_type: str) -> str:
    header = (
        f'"""Subject plugin scaffold for {code} ({TYPE_DESCRIPTION[subject_type]}).\n\n'
        "This file is the only place subject-specific pipeline code belongs.\n"
        "Replace the stubs after the stage-0 intake checkpoint.  The shared app\n"
        "loads this module through subjects/%s/subject.json.\n"
        '"""\n'
        "from __future__ import annotations\n\n"
    ) % code
    if subject_type == "A":
        body = '''

def plan(mode: str, style: str, computed_marks: int | None, seed: int):
    """Return ``(plan_object, summary_dict)`` for the LLM theory pipeline."""
    raise NotImplementedError(
        f"{subject_code} planner is not implemented; complete stages 4-5 first")


def plan_markdown(summary: dict) -> str:
    """Render the planner summary used by the local UI."""
    return "".join(f"- {key}: {value}\\n" for key, value in summary.items())


def plan_inputs(seed: int) -> dict:
    """Return paths to {plan, theory} for prebuild/bundle rebuilds."""
    raise NotImplementedError(
        f"{subject_code} plan inputs are not implemented")


def library_seeds() -> list[int]:
    """Return the accepted Library seed list (empty until stage 8)."""
    return []


def library_metadata(seed: int) -> dict:
    """Return planner metadata for one Library seed."""
    return {}


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}
'''.replace("{subject_code}", code)
    else:
        body = '''

def build_seed(seed: int, **kwargs) -> dict:
    """Build one deterministic paper and write meta.json in ``out_dir``."""
    raise NotImplementedError(
        f"{subject_code} deterministic builder is not implemented; complete "
        "stages 5-7 first")


def generator_labels() -> dict:
    return {}


def topic_labels() -> dict:
    return {}
'''.replace("{subject_code}", code)
    return header + body


def _docs(code: str, title: str, subject_type: str,
          paths: list[str]) -> str:
    return f"""# {code} — {title}

Status: **coming_soon** (scaffolded, not onboarded).

Type **{subject_type}**: {TYPE_DESCRIPTION[subject_type]}.

## Lifecycle

Read `docs/SUBJECT_PLAYBOOK.md` before changing this subject, then
`subjects/{code}/lifecycle_state.json`. Run:

```bash
uv run python -m scripts.lifecycle_status {code}
```

The first work item is stage 0 intake. Do not set the registry status to
`available`, publish, upload or deploy until every [HUMAN] gate is recorded.

## Inputs

- Working papers: `data/papers/{code}/` (originals are read-only)
- Tracking artifacts: `data/tracking/{code.lower()}/`
- Reference template: `data/reference/{code}/` (not created yet)
- Lecture slides (type A/C): `data/lecturedecks/{code}/` (not created yet)

## Subject code

Subject-specific pipeline code belongs only in
`src/subjects/{code.lower()}/`. Shared preprocessing is in
`src/subjects/preprocess.py`, `src/subjects/templates.py` and
`src/subjects/forbidden.py`.

## Scaffold files

{chr(10).join(f"- `{path}`" for path in paths)}

## First commands after intake approval

```bash
# stage 1: register/dedupe/OCR working papers (no rename by default)
uv run python -m src.subjects.preprocess --subject {code} --register --corpus

# stage 3: inventory the template
uv run python -m src.subjects.templates --subject {code} --check

# every stage: gates
uv run python -m src.app.safety --check
uv run pytest -q
cd cloudflare/worker && bun test
```
"""


def _plan(root: Path, code: str, title: str, subject_type: str,
          order: int | None = None) -> dict:
    subjects = load_subjects(root)
    if code in subjects:
        raise SystemExit(f"subject {code} already exists in {root}/subjects")
    if order is None:
        order = max((s.order for s in subjects.values()), default=0) + 1
    subject = _subject_json(code, title, subject_type, order)
    state = new_state(code, subject_type)
    package = root / "src" / "subjects" / code.lower()
    files = {
        f"subjects/{code}/subject.json": json.dumps(subject, indent=2) + "\n",
        f"subjects/{code}/lifecycle_state.json": json.dumps(state, indent=2) + "\n",
        f"docs/{code}.md": _docs(
            code, title, subject_type, [
                f"subjects/{code}/subject.json",
                f"subjects/{code}/lifecycle_state.json",
                f"docs/{code}.md",
                f"src/subjects/{code.lower()}/__init__.py",
                f"src/subjects/{code.lower()}/plugin.py",
                f"data/papers/{code}/",
                f"data/tracking/{code.lower()}/",
            ]),
        f"src/subjects/{code.lower()}/__init__.py": "",
        f"src/subjects/{code.lower()}/plugin.py": _plugin_source(
            code, subject_type),
        f"data/tracking/{code.lower()}/README.md": (
            f"# {code} tracking\n\nGenerated by `scripts/new_subject.py`.\n"
            "Register, dedupe and OCR outputs belong here; never modify the "
            "source papers.\n"),
        f"data/papers/{code}/.gitkeep": "",
    }
    directories = [str(package), str(root / "data" / "papers" / code),
                   str(root / "data" / "tracking" / code.lower())]
    return {
        "root": str(root),
        "code": code,
        "title": title,
        "type": subject_type,
        "order": order,
        "directories": directories,
        "files": files,
        "subject": subject,
        "lifecycle_state": state,
    }


def scaffold(root: Path, code: str, title: str, subject_type: str,
             order: int | None = None, dry_run: bool = False,
             force: bool = False) -> dict:
    plan = _plan(root, code, title, subject_type, order)
    plan["dry_run"] = dry_run
    plan["written"] = []
    if dry_run:
        return plan
    for relative, content in plan["files"].items():
        path = root / relative
        if path.exists() and not force:
            raise SystemExit(
                f"refusing to overwrite {path}; pass --force to replace")
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        plan["written"].append(str(path))
    for directory in plan["directories"]:
        Path(directory).mkdir(parents=True, exist_ok=True)
    save_state(root, code, plan["lifecycle_state"])
    return plan


def _print_plan(plan: dict) -> None:
    print(f"DRY RUN: {plan['code']} ({plan['type']}) — no files written")
    print(f"root: {plan['root']}")
    print(f"title: {plan['title']}  order: {plan['order']}")
    print("would create:")
    for directory in plan["directories"]:
        print(f"  dir  {directory}")
    for relative in plan["files"]:
        print(f"  file {relative}")
    print("\nsubjects/%s/subject.json" % plan["code"])
    print(json.dumps(plan["subject"], indent=2))
    print("\nsubjects/%s/lifecycle_state.json" % plan["code"])
    print(json.dumps(plan["lifecycle_state"], indent=2))
    print("\nlifecycle: stage 0_intake is pending; all [HUMAN] gates unapproved")
    print("status remains coming_soon; no onboarding, LLM call, upload or deploy")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("--type", dest="subject_type", required=True,
                    choices=sorted(VALID_TYPES))
    ap.add_argument("--title", default="")
    ap.add_argument("--order", type=int, default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--root", default=str(config.PROJECT_ROOT),
                    help=argparse.SUPPRESS)
    args = ap.parse_args()
    code = args.code.strip().upper()
    if not CODE_RE.fullmatch(code):
        raise SystemExit(
            "code must be 3-10 uppercase letters/digits and start with a letter")
    title = args.title.strip() or f"New subject {code}"
    root = Path(args.root).resolve()
    if not (root / "subjects").is_dir():
        raise SystemExit(f"no subjects/ registry under {root}")
    plan = scaffold(root, code, title, args.subject_type, args.order,
                    dry_run=args.dry_run, force=args.force)
    if args.dry_run:
        _print_plan(plan)
    else:
        print(f"created {len(plan['written'])} files for {code} "
              f"({args.subject_type}); status=coming_soon")


if __name__ == "__main__":
    main()
