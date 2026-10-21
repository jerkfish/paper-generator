"""Plan or perform an R2 sync while staying inside the free tier.

The free tier is 10 GB-month storage, 1M Class A operations/month and 10M
Class B operations/month.  This tool budgets only a small fraction of that:

    storage      <= 1 GiB   (10% of the free storage)
    Class A      <= 10,000  (1% of the free Class A allowance)
    Class B      <= 100,000 (1% of the free Class B allowance)
    objects      <= 5,000

Dry-run is the default and needs no credentials.  ``--upload`` requires
``R2_ACCESS_KEY_ID`` and ``R2_SECRET_ACCESS_KEY`` in the environment and the
optional ``boto3`` package:

    uv run --with boto3 python -m scripts.r2_sync --bundle outputs/public_bundle --upload

Only one ListObjectsV2 call (Class A) is made per sync.  Files are uploaded
only when their SHA-256 differs from the local sync state, so re-running an
unchanged bundle costs one Class A operation and no Class B operations.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:  # local .env is gitignored; deployment uses real environment secrets
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

MAX_STORAGE_BYTES = 1 * 1024 ** 3        # 1 GiB
MAX_OBJECTS = 5_000
MAX_CLASS_A = 10_000
MAX_CLASS_B = 100_000
STATE_PATH = ROOT / "outputs" / "r2_sync_state.json"
LEDGER_PATH = ROOT / "outputs" / "r2_quota_ledger.json"
BACKUP_ROOT = ROOT / "outputs" / "public_bundle_backups"


def _month() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m")


def _load_json(path: Path, default: dict) -> dict:
    if not path.exists():
        return dict(default)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return dict(default)
    return data if isinstance(data, dict) else dict(default)


def _save_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n",
                    encoding="utf-8")


def _fresh_ledger() -> dict:
    return {"month": _month(), "class_a": 0, "class_b": 0,
            "objects": 0, "bytes": 0}


def load_ledger(path: Path = LEDGER_PATH) -> dict:
    data = _load_json(path, _fresh_ledger())
    if data.get("month") != _month():
        data = _fresh_ledger()
    return data


def bundle_files(bundle: Path) -> list[dict]:
    if not bundle.exists():
        raise FileNotFoundError(f"public bundle not found: {bundle}")
    files = []
    for path in sorted(bundle.rglob("*")):
        if not path.is_file():
            continue
        data = path.read_bytes()
        files.append({
            "path": path,
            "key": path.relative_to(bundle).as_posix(),
            "size": len(data),
            "sha256": hashlib.sha256(data).hexdigest(),
        })
    return files


def estimate(files: list[dict]) -> dict:
    return {"objects": len(files),
            "bytes": sum(f["size"] for f in files)}


def quota_errors(est: dict, ledger: dict) -> list[str]:
    errors = []
    if est["objects"] > MAX_OBJECTS:
        errors.append(f"{est['objects']} objects exceeds budget {MAX_OBJECTS}")
    if est["bytes"] > MAX_STORAGE_BYTES:
        errors.append(f"{est['bytes']} bytes exceeds budget {MAX_STORAGE_BYTES}")
    if ledger["class_a"] > MAX_CLASS_A:
        errors.append(f"Class A ledger {ledger['class_a']} exceeds {MAX_CLASS_A}")
    if ledger["class_b"] > MAX_CLASS_B:
        errors.append(f"Class B ledger {ledger['class_b']} exceeds {MAX_CLASS_B}")
    return errors


def _state() -> dict:
    data = _load_json(STATE_PATH, {"objects": {}, "class_a": 0,
                                   "class_b": 0, "month": _month()})
    if data.get("month") != _month():
        data["month"] = _month()
        data["class_a"] = 0
        data["class_b"] = 0
    data.setdefault("objects", {})
    return data


def plan(files: list[dict], state: dict, upload: bool) -> dict:
    known = state.get("objects", {})
    changed = [f for f in files
               if known.get(f["key"], {}).get("sha256") != f["sha256"]]
    # One LIST on upload.  Dry-run also reports the same worst case.
    class_a = 1 + len(changed) if upload else len(changed)
    return {"changed": changed, "class_a": class_a,
            "unchanged": len(files) - len(changed)}


def backup(bundle: Path) -> Path:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    target = BACKUP_ROOT / stamp
    target.mkdir(parents=True, exist_ok=False)
    shutil.copytree(bundle, target / "bundle")
    return target


def _client():
    try:
        import boto3
    except ImportError:
        raise SystemExit(
            "boto3 is not installed. Run with: "
            "uv run --with boto3 python -m scripts.r2_sync --upload")
    account = os.environ.get("R2_ACCOUNT_ID", "").strip()
    endpoint = os.environ.get("R2_ENDPOINT", "").strip()
    if not endpoint:
        if not account:
            raise SystemExit("set R2_ACCOUNT_ID or R2_ENDPOINT")
        endpoint = f"https://{account}.r2.cloudflarestorage.com"
    access = os.environ.get("R2_ACCESS_KEY_ID", "")
    secret = os.environ.get("R2_SECRET_ACCESS_KEY", "")
    if not access or not secret:
        raise SystemExit("set R2_ACCESS_KEY_ID and R2_SECRET_ACCESS_KEY")
    from botocore.config import Config
    return boto3.client(
        "s3", endpoint_url=endpoint, region_name="auto",
        aws_access_key_id=access, aws_secret_access_key=secret,
        config=Config(retries={"max_attempts": 1}))


def _changed_after_listing(files: list[dict], state: dict,
                           remote: dict[str, dict]) -> list[dict]:
    known = state.get("objects", {})
    changed = []
    for f in files:
        row = remote.get(f["key"])
        old = known.get(f["key"], {})
        if row is None:
            changed.append(f)
        elif int(row.get("size", -1)) != int(f["size"]):
            changed.append(f)
        elif old.get("sha256") != f["sha256"]:
            changed.append(f)
        elif old.get("etag") and row.get("etag") and old["etag"] != row["etag"]:
            changed.append(f)
    return changed


def upload(bundle: Path, files: list[dict], state: dict,
           bucket: str, dry_run: bool) -> dict:
    # Estimate before any network call from the local state.  This is a
    # best-effort plan; the real changed set is resolved from one LIST.
    local_row = plan(files, state, upload=True)
    ledger = load_ledger()
    projected = dict(ledger)
    projected["class_a"] = ledger["class_a"] + local_row["class_a"]
    errs = quota_errors(estimate(files), projected)
    if errs:
        raise SystemExit("quota guard stopped the sync: " + "; ".join(errs))

    print(f"bucket: {bucket}")
    print(f"objects: {len(files)}; bytes: {sum(f['size'] for f in files)}")
    print(f"upload: {len(local_row['changed'])} changed locally; "
          f"{local_row['unchanged']} unchanged")

    if dry_run:
        return {"uploaded": 0, "dry_run": True,
                "plan": {"changed": len(local_row["changed"]),
                         "unchanged": local_row["unchanged"],
                         "class_a": local_row["class_a"]}}

    backup_path = backup(bundle)
    print(f"local backup: {backup_path}")

    client = _client()
    ledger = load_ledger()
    # Reserve the LIST operation before making it.  If the process dies, the
    # ledger over-counts rather than under-counts, which keeps us compliant.
    ledger["class_a"] += 1
    _save_json(LEDGER_PATH, ledger)
    remote: dict[str, dict] = {}
    paginator = client.get_paginator("list_objects_v2")
    pages = 0
    for page in paginator.paginate(Bucket=bucket):
        pages += 1
        if pages > 1:  # every extra listing page is another Class A op
            ledger = load_ledger()
            ledger["class_a"] += 1
            _save_json(LEDGER_PATH, ledger)
        for obj in page.get("Contents", []):
            remote[obj["Key"]] = {"size": obj.get("Size", 0),
                                  "etag": str(obj.get("ETag", "")).strip('"')}

    changed = _changed_after_listing(files, state, remote)
    ledger = load_ledger()
    if ledger["class_a"] + len(changed) > MAX_CLASS_A:
        raise SystemExit(
            "quota guard stopped after the LIST: "
            f"{len(changed)} uploads would exceed Class A cap")
    print(f"upload: {len(changed)} changed; {len(files) - len(changed)} "
          f"unchanged; Class A this run: {pages + len(changed)}")

    uploaded = 0
    for f in changed:
        ledger = load_ledger()
        ledger["class_a"] += 1
        _save_json(LEDGER_PATH, ledger)
        response = client.put_object(Bucket=bucket, Key=f["key"],
                                     Body=f["path"].read_bytes(),
                                     ContentType=_content_type(f["key"]))
        uploaded += 1
        state.setdefault("objects", {})[f["key"]] = {
            "size": f["size"], "sha256": f["sha256"],
            "etag": str(response.get("ETag", "")).strip('"'),
        }
        print(f"PUT {f['key']}")

    state["month"] = _month()
    state["class_a"] = state.get("class_a", 0) + 1 + uploaded
    _save_json(STATE_PATH, state)

    ledger = load_ledger()
    ledger["objects"] = len(files)
    ledger["bytes"] = sum(f["size"] for f in files)
    _save_json(LEDGER_PATH, ledger)
    return {"uploaded": uploaded, "dry_run": False,
            "plan": {"changed": len(changed),
                     "unchanged": len(files) - len(changed),
                     "class_a": pages + uploaded}}

def _content_type(key: str) -> str:
    suffix = Path(key).suffix.lower()
    return {
        ".html": "text/html; charset=utf-8",
        ".css": "text/css; charset=utf-8",
        ".js": "application/javascript; charset=utf-8",
        ".json": "application/json",
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument."
                 "wordprocessingml.document",
    }.get(suffix, "application/octet-stream")


def check_bucket(bucket: str) -> dict:
    """Verify credentials with one LIST and report the bucket contents."""
    client = _client()
    ledger = load_ledger()
    ledger["class_a"] += 1
    _save_json(LEDGER_PATH, ledger)
    remote: dict[str, int] = {}
    pages = 0
    for page in client.get_paginator("list_objects_v2").paginate(Bucket=bucket):
        pages += 1
        if pages > 1:
            ledger = load_ledger()
            ledger["class_a"] += 1
            _save_json(LEDGER_PATH, ledger)
        for obj in page.get("Contents", []):
            remote[obj["Key"]] = int(obj.get("Size", 0))
    ledger = load_ledger()
    ledger["objects"] = len(remote)
    ledger["bytes"] = sum(remote.values())
    _save_json(LEDGER_PATH, ledger)
    return {"bucket": bucket, "objects": len(remote),
            "bytes": sum(remote.values()), "list_pages": pages,
            "class_a": pages}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bundle", default=str(ROOT / "outputs" / "public_bundle"))
    ap.add_argument("--bucket", default=os.environ.get("R2_BUCKET", "exampapers"))
    ap.add_argument("--upload", action="store_true",
                    help="perform the sync (default is a dry run)")
    ap.add_argument("--check", action="store_true",
                    help="verify R2 credentials with one bucket listing")
    args = ap.parse_args()
    if args.check:
        print(json.dumps(check_bucket(args.bucket), indent=2))
        return
    bundle = Path(args.bundle).resolve()
    files = bundle_files(bundle)
    est = estimate(files)
    ledger = load_ledger()
    errs = quota_errors(est, ledger)
    print(f"bundle: {bundle}")
    print(f"storage: {est['bytes']} bytes "
          f"({est['bytes'] / 1024 / 1024:.2f} MiB) of "
          f"{MAX_STORAGE_BYTES / 1024 / 1024:.0f} MiB budget")
    print(f"objects: {est['objects']} of {MAX_OBJECTS} budget")
    print(f"month: {ledger['month']} Class A {ledger['class_a']}/{MAX_CLASS_A}; "
          f"Class B {ledger['class_b']}/{MAX_CLASS_B}")
    if errs:
        for err in errs:
            print("QUOTA:", err, file=sys.stderr)
        raise SystemExit(2)
    result = upload(bundle, files, _state(), args.bucket,
                    dry_run=not args.upload)
    print(json.dumps(result, indent=2))
    if not args.upload:
        print("dry run: no network calls and no ledger changes")


if __name__ == "__main__":
    main()
