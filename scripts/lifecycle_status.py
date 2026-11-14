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
    GATE_KEYS,
    GATE_TITLES,
    STAGE_BY_KEY,
    STAGE_BY_KEY_V2,
    STAGE_KEYS,
    STAGE_KEYS_V2,
    gate_approved,
    gate_status,
    is_v2,
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
        v2 = is_v2(state)
        keys = STAGE_KEYS_V2 if v2 else STAGE_KEYS
        data["lifecycle_status"] = state.get("lifecycle_status")
        data["stop_reason"] = state.get("stop_reason", "")
        if str(state.get("type", "")).upper() != subject.subject_type:
            data["blockers"].append(
                "lifecycle type does not match subject.json type")
        # Completed stages still need evidence and, for v1, signatures.
        for key in keys:
            if key == data.get("next_stage"):
                break
            problems = stage_blockers(state, key, root)
            data["blockers"].extend(f"{key}: {problem}"
                                    for problem in problems)
        next_key = data.get("next_stage")
        publish_key = "V7_publish" if v2 else "9_publish"
        if next_key in keys and keys.index(next_key) >= keys.index(
                publish_key):
            data["blockers"].extend(_permission_blockers(subject))
        data["unsure"] = [
            item for item in state.get("unsure") or []
            if item.get("blocking")
        ]
        data["parser_provenance"] = list(
            state.get("parser_provenance") or [])
        data["llm_cost_usd"] = float(
            (state.get("llm_cost") or {}).get("total_usd", 0.0))
        data["stage_statuses"] = {
            key: (state.get("stages") or {}).get(key, {}).get(
                "status", "pending")
            for key in keys
        }
        if v2:
            data["lifecycle_schema"] = 2
            data["strategy"] = state.get("strategy")
            data["gates"] = {key: gate_status(state, key)
                             for key in GATE_KEYS}
            data["gates_open"] = [key for key in GATE_KEYS
                                  if not gate_approved(state, key)]
            data["bank"] = dict(state.get("bank") or {})
            data["answers"] = dict(state.get("answers") or {})
    return data


def _print(data: dict) -> None:
    v2 = data.get("lifecycle_schema") == 2
    by_key = STAGE_BY_KEY_V2 if v2 else STAGE_BY_KEY
    keys = STAGE_KEYS_V2 if v2 else STAGE_KEYS
    print(f"{data['subject']} type {data.get('type', '?')} "
          f"registry={data.get('registry_status', '?')}"
          + (f" — schema v2 / {data.get('strategy') or 'recycle'}"
             if v2 else ""))
    if not data.get("initialized"):
        print("lifecycle_state.json: MISSING")
    if data.get("lifecycle_status") == "stopped":
        print("Lifecycle: STOPPED")
        if data.get("stop_reason"):
            print(f"Stop reason: {data['stop_reason']}")
        print("Next stage: none (lifecycle stopped)")
    elif data.get("next_stage") is None and data.get("unsure"):
        print("Next stage: none — lifecycle has open blocking unsure items")
    elif data.get("next_stage") is None:
        print("Next stage: none — lifecycle complete")
    else:
        title = by_key[data["next_stage"]]["title"]
        human = " [HUMAN]" if data.get("human_checkpoint") else ""
        print(f"Next stage: {data['next_stage']} — {title}{human} "
              f"({data.get('status')})")
        if data.get("next_gate"):
            print(f"Stage gate: {data['next_gate']} "
                  f"({GATE_TITLES[data['next_gate']]})")
    if v2:
        print("Gates:")
        for key in GATE_KEYS:
            gate = (data.get("gates") or {}).get(key) or {}
            print(f"  Gate {key}: {gate.get('status', 'pending')} "
                  f"({GATE_TITLES[key]})")
    blockers = data.get("blockers") or []
    print("Blockers:" if blockers else "Blockers: none")
    for blocker in blockers:
        print(f"  - {blocker}")
    if data.get("stage_statuses"):
        print("Stages:")
        for key in keys:
            print(f"  {key:24} {data['stage_statuses'].get(key, 'pending')}")
    if v2 and data.get("bank"):
        bank = data["bank"]
        print("Bank: " + ", ".join(f"{k}={v}" for k, v in bank.items()))
    unsure = data.get("unsure") or []
    if unsure:
        print(f"Open unsure items: {len(unsure)}")
        for item in unsure:
            print(f"  - [{item.get('stage')}] {item.get('item')}")
    provenance = data.get("parser_provenance") or []
    if provenance:
        print("Parser provenance:")
        for row in provenance:
            line = (
                f"  - {row.get('paper_id','?')}: "
                f"{row.get('parser','?')}/{row.get('model','?')} "
                f"pages={row.get('pages','?')} "
                f"task={row.get('task_id','')} "
                f"cache={row.get('cache_path','')}")
            if row.get("report"):
                line += f" report={row['report']}"
            print(line)
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
