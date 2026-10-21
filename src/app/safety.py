"""Phase 0 safety: secret leak scan and public-file path guards."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

from src import config

SECRET_ENV_NAMES = (
    "DEEPSEEK_API_KEY",
    "QWEN_API_KEY",
    "MOCKGEN_API_KEY",
    "CF_API_TOKEN",
    "CLOUDFLARE_API_TOKEN",
    "R2_ACCESS_KEY_ID",
    "R2_SECRET_ACCESS_KEY",
    "TURNSTILE_SECRET_KEY",
)

TEXT_SUFFIXES = {
    ".py", ".html", ".htm", ".css", ".js", ".mjs", ".json", ".md",
    ".toml", ".txt", ".yml", ".yaml", ".ps1", ".sh", ".sql", ".ini",
    ".cfg", ".conf", ".example", ".lock",
}
ROOT_FILES = (
    "README.md", "pyproject.toml", "uv.lock", ".gitignore",
    "wrangler.toml", "wrangler.jsonc", "Dockerfile", "docker-compose.yml",
)
SCAN_DIRS = ("src", "tests", "scripts", "cloudflare", "design", "subjects")


class SecretLeakError(RuntimeError):
    pass


class ForbiddenPathError(PermissionError):
    pass


def _secret_values() -> dict[str, str]:
    out = {}
    for name in SECRET_ENV_NAMES:
        value = os.environ.get(name, "")
        if len(value) >= 8:
            out[name] = value
    return out


def tracked_text_files(root: Path | None = None) -> list[Path]:
    """Conservative stand-in for tracked files without invoking git.

    Scans source, tests, docs, design and deploy config. Excludes .env,
    .git, .venv, outputs and data (runtime/generated material).
    """
    root = Path(root or config.PROJECT_ROOT)
    files: list[Path] = []
    for name in ROOT_FILES:
        p = root / name
        if p.exists() and p.is_file():
            files.append(p)
    for dirname in SCAN_DIRS:
        base = root / dirname
        if not base.exists():
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if any(part in {".git", ".venv", "__pycache__", ".pytest_cache"}
                   for part in p.parts):
                continue
            if p.name == ".env" or p.name.startswith(".env."):
                continue
            if p.suffix.lower() in TEXT_SUFFIXES or p.name == "Dockerfile":
                files.append(p)
    return sorted(set(files))


def find_secret_leaks(paths: list[Path],
                      secrets: dict[str, str] | None = None
                      ) -> list[tuple[str, str]]:
    """Return (env name, file path) without exposing the secret value."""
    secrets = _secret_values() if secrets is None else secrets
    leaks: list[tuple[str, str]] = []
    for p in paths:
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        for name, value in secrets.items():
            if value and value in text:
                leaks.append((name, str(p)))
    return leaks


def assert_no_secret_leaks(root: Path | None = None) -> None:
    secrets = _secret_values()
    if not secrets:
        return
    leaks = find_secret_leaks(tracked_text_files(root), secrets)
    if leaks:
        rendered = ", ".join(f"{name} in {path}" for name, path in leaks)
        raise SecretLeakError(
            "secret value found in a tracked text file: " + rendered)


def forbidden_roots() -> list[Path]:
    return [
        Path(config.DATA_DIR) / "reference",
        Path(config.ORIGINAL_PAPERS_DIR),
        Path(config.PAPERS_DIR),
        Path(config.LECTURE_DECKS_DIR),
    ]


def is_forbidden_path(path: Path) -> bool:
    p = Path(path).resolve()
    if p.name == ".env" or p.name.startswith(".env."):
        return True
    for root in forbidden_roots():
        try:
            root = root.resolve()
        except Exception:
            continue
        if p == root or root in p.parents:
            return True
    return False


def is_servable_path(path: Path,
                     allowed_roots: list[Path] | None = None) -> bool:
    p = Path(path).resolve()
    if is_forbidden_path(p):
        return False
    allowed = allowed_roots or [config.WEB_RUNS_DIR, config.WEB_CACHE_DIR]
    for root in allowed:
        try:
            root = Path(root).resolve()
        except Exception:
            continue
        if p == root or root in p.parents:
            return True
    return False


def ensure_servable(path: Path,
                    allowed_roots: list[Path] | None = None) -> Path:
    p = Path(path).resolve()
    if not is_servable_path(p, allowed_roots):
        raise ForbiddenPathError(
            f"refusing to serve a file outside the public/private output roots: {p}")
    return p


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true",
                    help="scan tracked text files for secret values")
    args = ap.parse_args()
    if args.check:
        assert_no_secret_leaks()
        print(f"secret scan ok: {len(tracked_text_files())} text files")
    else:
        print("nothing to do; pass --check")


if __name__ == "__main__":
    main()
