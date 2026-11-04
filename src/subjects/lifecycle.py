"""Subject lifecycle state: stages 0-10, evidence and human gates.

The playbook is the authority for what each stage means.  This module is the
machine-readable companion used by ``scripts/new_subject.py`` and
``scripts/lifecycle_status.py``.  A stage is only "done" when its evidence
exists and its human checkpoint (where required) was recorded.
"""
from __future__ import annotations

import json
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA_VERSION = 1
DONE_STATUSES = {"done", "skipped", "not_applicable"}
VALID_STATUSES = {"pending", "in_progress", "blocked", *DONE_STATUSES}

STAGES: tuple[dict[str, Any], ...] = (
    {
        "key": "0_intake",
        "title": "Intake and permissions",
        "human": True,
        "purpose": "Confirm subject identity, type, inputs and permission basis.",
    },
    {
        "key": "1_preprocess",
        "title": "Paper preprocessing",
        "human": True,
        "purpose": "Rename by cover, deduplicate, OCR and register papers.",
    },
    {
        "key": "2_scheme_slides",
        "title": "Scheme and slides",
        "human": True,
        "purpose": "Inventory the official scheme and lecture slides.",
    },
    {
        "key": "3_template",
        "title": "Template and cover",
        "human": True,
        "purpose": "Approve the paper/scheme template and cover layout.",
    },
    {
        "key": "4_taxonomy_question_log",
        "title": "Taxonomy and question log",
        "human": True,
        "purpose": "Derive topics, marks and question metadata from papers.",
    },
    {
        "key": "5_fingerprint_planner",
        "title": "Fingerprint and planner",
        "human": True,
        "purpose": "Approve the paper fingerprint and the slot planner.",
    },
    {
        "key": "6_generators",
        "title": "Generators",
        "human": True,
        "purpose": "Implement and validate computed/theory generators.",
    },
    {
        "key": "7_builders_qa",
        "title": "Builders and QA",
        "human": True,
        "purpose": "Build paper/scheme DOCX/PDF and pass structural QA.",
    },
    {
        "key": "8_library_prebuild",
        "title": "Library prebuild",
        "human": True,
        "purpose": "Build the accepted 20-seed Library without live LLM calls.",
    },
    {
        "key": "9_publish",
        "title": "Publish",
        "human": True,
        "purpose": "Build the public bundle, upload and deploy the Worker.",
    },
    {
        "key": "10_close_out",
        "title": "Close-out",
        "human": True,
        "purpose": "Record evidence, costs, unsure items and sign-off.",
    },
)

STAGE_KEYS = tuple(stage["key"] for stage in STAGES)
STAGE_BY_KEY = {stage["key"]: stage for stage in STAGES}


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _today() -> str:
    return date.today().isoformat()


def blank_stage(spec: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "pending",
        "evidence": [],
        "llm_cost_usd": 0.0,
        "blockers": [],
        "human_approval": {
            "required": bool(spec.get("human")),
            "approved": False,
            "by": "",
            "on": "",
            "note": "",
        },
        "notes": "",
    }


def new_state(code: str, subject_type: str,
              template_path: str = "") -> dict[str, Any]:
    code = code.upper()
    stages = {key: blank_stage(STAGE_BY_KEY[key]) for key in STAGE_KEYS}
    # A new scaffold has not started stage 0; make the pending human decisions
    # explicit instead of pretending intake was completed.
    unsure = [
        {
            "stage": "0_intake",
            "item": f"Confirm {code} title, subject type ({subject_type}) and "
                    "curriculum order with the subject owner.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record papers permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record scheme permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "0_intake",
            "item": f"Record lecture-slides permission for {code}.",
            "blocking": True,
            "opened": _today(),
        },
        {
            "stage": "9_publish",
            "item": f"Record publication permission for {code} before any "
                    "upload or deploy.",
            "blocking": True,
            "opened": _today(),
        },
    ]
    return {
        "schema_version": SCHEMA_VERSION,
        "subject": code,
        "type": subject_type,
        "template_path": template_path,
        "created": _now(),
        "updated": _now(),
        "stages": stages,
        "unsure": unsure,
        "llm_cost": {
            "currency": "USD",
            "total_usd": 0.0,
            "by_stage": {key: 0.0 for key in STAGE_KEYS},
        },
    }


def state_path(root: Path, code: str) -> Path:
    return Path(root) / "subjects" / code.upper() / "lifecycle_state.json"


def load_state(root: Path, code: str) -> dict[str, Any] | None:
    path = state_path(root, code)
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None
    return data if isinstance(data, dict) else None


def save_state(root: Path, code: str, state: dict[str, Any]) -> Path:
    path = state_path(root, code)
    path.parent.mkdir(parents=True, exist_ok=True)
    state["updated"] = _now()
    path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
    return path


def next_stage(state: dict[str, Any]) -> str | None:
    stages = state.get("stages") or {}
    for key in STAGE_KEYS:
        status = (stages.get(key) or {}).get("status", "pending")
        if status not in DONE_STATUSES:
            return key
    return None


def _evidence_missing(evidence: list[str]) -> list[str]:
    missing = []
    for value in evidence or []:
        text = str(value)
        if not text or text.startswith(("http://", "https://")):
            continue
        if not Path(text).exists():
            missing.append(text)
    return missing


def stage_blockers(state: dict[str, Any], stage: str,
                   root: Path | None = None) -> list[str]:
    spec = STAGE_BY_KEY.get(stage)
    if spec is None:
        return [f"unknown stage {stage}"]
    entry = (state.get("stages") or {}).get(stage) or {}
    status = str(entry.get("status", "pending"))
    blockers = [f"stage is {status}"] if status == "blocked" else []
    blockers.extend(str(item) for item in entry.get("blockers") or []
                    if item)
    for item in state.get("unsure") or []:
        if item.get("stage") == stage and item.get("blocking"):
            blockers.append(f"unsure: {item.get('item')}")
    if status in DONE_STATUSES:
        missing = _evidence_missing(entry.get("evidence") or [])
        if missing:
            blockers.append("missing evidence: " + ", ".join(missing))
        approval = entry.get("human_approval") or {}
        if spec.get("human") and not approval.get("approved"):
            blockers.append(
                f"[HUMAN] approval not recorded for {spec['title']}")
    if stage == "9_publish":
        # Permissions are recorded in subject.json, not in lifecycle_state.
        # The status command adds a registry-aware check on top of this.
        pass
    return blockers


def status_report(root: Path, code: str) -> dict[str, Any]:
    code = code.upper()
    state = load_state(root, code)
    if state is None:
        return {
            "subject": code,
            "initialized": False,
            "next_stage": STAGE_KEYS[0],
            "stage_title": STAGE_BY_KEY[STAGE_KEYS[0]]["title"],
            "status": "missing",
            "blockers": [
                "lifecycle_state.json is missing; run the stage-0 intake "
                "scaffold or create it from the playbook template",
            ],
            "human_checkpoint": True,
        }
    stage = next_stage(state)
    if stage is None:
        return {
            "subject": code,
            "initialized": True,
            "next_stage": None,
            "stage_title": "Complete",
            "status": "done",
            "blockers": [],
            "human_checkpoint": False,
            "updated": state.get("updated", ""),
        }
    entry = (state.get("stages") or {}).get(stage) or {}
    blockers = stage_blockers(state, stage, root)
    # Previous incomplete stages are always the first blocker.
    for key in STAGE_KEYS:
        if key == stage:
            break
        prior = (state.get("stages") or {}).get(key) or {}
        if prior.get("status") not in DONE_STATUSES:
            blockers.insert(0, f"previous stage incomplete: {key}")
            break
    return {
        "subject": code,
        "initialized": True,
        "next_stage": stage,
        "stage_title": STAGE_BY_KEY[stage]["title"],
        "status": entry.get("status", "pending"),
        "blockers": blockers,
        "human_checkpoint": bool(STAGE_BY_KEY[stage].get("human")),
        "updated": state.get("updated", ""),
        "unsure_count": sum(1 for item in state.get("unsure") or []
                            if item.get("blocking")),
        "llm_cost_usd": float((state.get("llm_cost") or {})
                              .get("total_usd", 0.0)),
    }
