"""Show or set the R2 lifecycle rule through the Cloudflare API.

The bucket-scoped R2 S3 token cannot edit lifecycle configuration, so this
script uses CLOUDFLARE_API_TOKEN instead. The token needs
`Account -> Workers R2 Storage Write` to apply a rule and
`Account -> Workers R2 Storage Read` to show the current rules.

    uv run python -m scripts.r2_lifecycle --show
    uv run python -m scripts.r2_lifecycle --apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass


def _account_id() -> str:
    value = (os.environ.get("CLOUDFLARE_ACCOUNT_ID") or
             os.environ.get("R2_ACCOUNT_ID") or "").strip()
    if not value:
        raise SystemExit("set CLOUDFLARE_ACCOUNT_ID or R2_ACCOUNT_ID")
    return value


def _api(method: str, path: str, body: dict | None = None) -> dict:
    token = os.environ.get("CLOUDFLARE_API_TOKEN", "").strip()
    if not token:
        raise SystemExit("set CLOUDFLARE_API_TOKEN")
    url = f"https://api.cloudflare.com/client/v4{path}"
    response = httpx.request(
        method, url, json=body, timeout=30,
        headers={"Authorization": f"Bearer {token}"})
    try:
        data = response.json()
    except Exception:
        data = {"success": False, "errors": [{"message": response.text[:200]}]}
    if response.status_code >= 400 or not data.get("success"):
        errors = data.get("errors") or [{"message": response.text[:200]}]
        message = "; ".join(str(e.get("message", e)) for e in errors)
        if response.status_code in (401, 403) or "Authentication" in message:
            raise SystemExit(
                "Cloudflare API permission denied: add "
                "'Account -> Workers R2 Storage Write' to the token "
                f"({message})")
        raise SystemExit(f"Cloudflare API error: {message}")
    return data


def show(account: str, bucket: str) -> None:
    data = _api("GET", f"/accounts/{account}/r2/buckets/{bucket}/lifecycle")
    print(json.dumps(data.get("result", {}), indent=2))


def apply(account: str, bucket: str, prefix: str, days: int) -> None:
    body = {
        "rules": [{
            "id": "expire-shared-7d",
            "conditions": {"prefix": prefix},
            "enabled": True,
            "deleteObjectsTransition": {
                "condition": {"type": "Age", "maxAge": days * 86400},
            },
        }],
    }
    print(json.dumps(body, indent=2))
    _api("PUT", f"/accounts/{account}/r2/buckets/{bucket}/lifecycle", body)
    print("lifecycle rule applied")
    show(account, bucket)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=os.environ.get("R2_BUCKET", "exampapers"))
    ap.add_argument("--prefix", default="shared/")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--apply", action="store_true")
    ap.add_argument("--show", action="store_true",
                    help="show the current rules (the default)")
    args = ap.parse_args()
    if args.days < 1:
        raise SystemExit("days must be at least 1")
    account = _account_id()
    if args.apply:
        apply(account, args.bucket, args.prefix, args.days)
    else:
        show(account, args.bucket)


if __name__ == "__main__":
    main()
