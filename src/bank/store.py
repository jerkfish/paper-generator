"""File-backed question-bank store shared by recycle subjects."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterator


def load_json(path: Path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def save_json(path: Path, payload) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")
    return path


class BankStore:
    """A bank rooted at ``data/tracking/<code>/bank``."""

    def __init__(self, root: Path):
        self.root = Path(root)

    @property
    def questions_dir(self) -> Path:
        return self.root / "questions"

    @property
    def assets_dir(self) -> Path:
        return self.root / "assets"

    @property
    def plans_dir(self) -> Path:
        return self.root / "plans"

    @property
    def review_dir(self) -> Path:
        return self.root / "review"

    @property
    def answers_path(self) -> Path:
        return self.root / "answers.json"

    @property
    def approvals_path(self) -> Path:
        return self.root / "approvals.json"

    @property
    def corrections_path(self) -> Path:
        return self.root / "corrections.json"

    @property
    def unsure_path(self) -> Path:
        return self.root / "unsure.json"

    def ensure(self) -> "BankStore":
        for path in (self.questions_dir, self.assets_dir, self.plans_dir,
                     self.review_dir):
            path.mkdir(parents=True, exist_ok=True)
        return self

    def question_path(self, question_id: str) -> Path:
        return self.questions_dir / f"{question_id}.json"

    def asset_path(self, asset_id: str) -> Path:
        return self.assets_dir / f"{asset_id}.json"

    def load_question(self, question_id: str) -> dict:
        return load_json(self.question_path(question_id), {})

    def save_question(self, question: dict) -> Path:
        return save_json(self.question_path(question["id"]), question)

    def load_asset(self, asset_id: str) -> dict:
        return load_json(self.asset_path(asset_id), {})

    def save_asset(self, asset: dict) -> Path:
        return save_json(self.asset_path(asset["id"]), asset)

    def questions(self) -> Iterator[dict]:
        for path in sorted(self.questions_dir.glob("*.json")):
            payload = load_json(path, {})
            if isinstance(payload, dict) and payload:
                yield payload

    def assets(self) -> Iterator[dict]:
        for path in sorted(self.assets_dir.glob("*.json")):
            payload = load_json(path, {})
            if isinstance(payload, dict) and payload:
                yield payload

    def approved_questions(self) -> list[dict]:
        return [row for row in self.questions()
                if row.get("status") == "approved"]

    def answers(self) -> dict:
        return load_json(self.answers_path, {})

    def answers_by_question(self) -> dict[str, dict]:
        return dict((self.answers().get("by_qid") or {}))

    def save_answers(self, payload: dict) -> Path:
        return save_json(self.answers_path, payload)

    def approvals(self) -> dict:
        return load_json(self.approvals_path, {})

    def corrections(self) -> dict:
        return load_json(self.corrections_path, {})

    def unsure(self) -> dict:
        return load_json(self.unsure_path, {})

    def index(self) -> dict:
        return load_json(self.root / "index.json", {})

    def gate_report(self) -> dict:
        return load_json(self.root / "gate1_report.json", {})

    def rejected_hashes(self, registry_path: Path | None = None) -> set[str]:
        payload = load_json(registry_path or self.root / "rejected_registry.json",
                            {})
        hashes: set[str] = set()
        for key in ("assets", "files"):
            value = payload.get(key)
            if isinstance(value, dict):
                hashes.update(str(item) for item in value)
        if isinstance(payload.get("hashes"), list):
            hashes.update(str(item) for item in payload["hashes"])
        return hashes
