"""Print the next lifecycle stage and what blocks it.

Reads ``subjects/<CODE>/lifecycle_state.json`` (the playbook's machine-readable
state) and the subject registry.  It is read-only: it never advances a stage.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from src import config
from src.subjects.lifecycle import (
    STAGE_BY_KEY,
    STAGE_KEYS,
    load_state,
    stage_blockers,
    status_report,
)
from src.subjects.registry import SubjectNotFound, get_subject


def _permission_blockers(subject) -> list[str]:
    blockers = []
    for name in ("papers", "scheme", "slides", "publication"):
        permission = (subject.permissions or {}).get(name) or {}
        if not permission.get("allowed"):
            basis = permission.get("basis") or "unsure"
            blockers.append(
                f"permission {name}: not allowed (basis={basis})")
    return blockers


def report(root: Path, code: str) -> dict:
    code = code.upper()
    data = status_report(root, code)
    try:
        subject = get_subject(code, root)
    except SubjectNotFound:
        data["blockers"].append("subject is not in the registry")
        return data
    data["type"] = subject.subject_type
    data["registry_status"] = subject.status
    state = load_state(root, code)
    if state is not None:
        data["lifecycle_status"] = state.get("lifecycle_status")
        data["stop_reason"] = state.get("stop_reason", "")
        if str(state.get("type", "")).upper() != subject.subject_type:
            data["blockers"].append(
                "lifecycle type does not match subject.json type")
        # Completed stages still need evidence and human signatures.
        for key in STAGE_KEYS:
            if key == data.get("next_stage"):
                break
            problems = stage_blockers(state, key, root)
            data["blockers"].extend(f"{key}: {problem}"
                                    for problem in problems)
        next_key = data.get("next_stage")
        if next_key in STAGE_KEYS:
            index = STAGE_KEYS.index(next_key)
            if index >= STAGE_KEYS.index("9_publish"):
                data["blockers"].extend(_permission_blockers(subject))
        data["unsure"] = [
            item for item in state.get("unsure") or []
            if item.get("blocking")
        ]
        data["llm_cost_usd"] = float(
            (state.get("llm_cost") or {}).get("total_usd", 0.0))
        data["stage_statuses"] = {
            key: (state.get("stages") or {}).get(key, {}).get(
                "status", "pending")
            for key in STAGE_KEYS
        }
    return data


def _print(data: dict) -> None:
    print(f"{data['subject']} type {data.get('type', '?')} "
          f"registry={data.get('registry_status', '?')}")
    if not data.get("initialized"):
        print("lifecycle_state.json: MISSING")
    if data.get("lifecycle_status") == "stopped":
        print("Lifecycle: STOPPED")
        if data.get("stop_reason"):
            print(f"Stop reason: {data['stop_reason']}")
        print("Next stage: none (lifecycle stopped)")
    elif data.get("next_stage") is None:
        print("Next stage: none — lifecycle complete")
    else:
        title = STAGE_BY_KEY[data["next_stage"]]["title"]
        human = " [HUMAN]" if data.get("human_checkpoint") else ""
        print(f"Next stage: {data['next_stage']} — {title}{human} "
              f"({data.get('status')})")
    blockers = data.get("blockers") or []
    print("Blockers:" if blockers else "Blockers: none")
    for blocker in blockers:
        print(f"  - {blocker}")
    if data.get("stage_statuses"):
        print("Stages:")
        for key in STAGE_KEYS:
            print(f"  {key:24} {data['stage_statuses'].get(key, 'pending')}")
    unsure = data.get("unsure") or []
    if unsure:
        print(f"Open unsure items: {len(unsure)}")
        for item in unsure:
            print(f"  - [{item.get('stage')}] {item.get('item')}")
    print(f"LLM cost recorded: ${data.get('llm_cost_usd', 0.0):.4f}")
    print(f"updated: {data.get('updated', '')}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("code")
    ap.add_argument("--root", default=str(config.PROJECT_ROOT),
                    help=argparse.SUPPRESS)
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--strict", action="store_true",
                    help="exit 1 when the next stage has blockers")
    args = ap.parse_args()
    data = report(Path(args.root).resolve(), args.code)
    if args.json:
        print(json.dumps(data, indent=2))
    else:
        _print(data)
    if args.strict and data.get("blockers"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
