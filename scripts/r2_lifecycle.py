"""Set the R2 lifecycle rule for shared gallery files via the S3 API.

The free-tier R2 credentials already configured in .env can manage the bucket
lifecycle; no separate Cloudflare API token is needed.

    uv run --with boto3 python -m scripts.r2_lifecycle          # show
    uv run --with boto3 python -m scripts.r2_lifecycle --apply  # apply
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except Exception:
    pass

from scripts.r2_sync import LEDGER_PATH, _client, _save_json, load_ledger


def rule(prefix: str, days: int) -> dict:
    return {
        "ID": "expire-shared-7d" if prefix == "shared/" else f"expire-{days}d",
        "Status": "Enabled",
        "Filter": {"Prefix": prefix},
        "Expiration": {"Days": days},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bucket", default=os.environ.get("R2_BUCKET", "exampapers"))
    ap.add_argument("--prefix", default="shared/")
    ap.add_argument("--days", type=int, default=7)
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if args.days < 1:
        raise SystemExit("days must be at least 1")
    config = {"Rules": [rule(args.prefix, args.days)]}
    print(json.dumps({"bucket": args.bucket, **config}, indent=2))
    if not args.apply:
        print("dry run: pass --apply to set the lifecycle rule")
        return
    client = _client()
    try:
        client.put_bucket_lifecycle_configuration(
            Bucket=args.bucket,
            LifecycleConfiguration=config,
        )
    except Exception as error:
        if "AccessDenied" in str(error):
            raise SystemExit(
                "AccessDenied: the bucket-scoped Object Read & Write token "
                "cannot edit lifecycle rules. Add the rule in the R2 dashboard "
                "or use a temporary Admin Read & Write token.") from None
        raise
    ledger = load_ledger()
    ledger["class_a"] += 1
    _save_json(LEDGER_PATH, ledger)
    current = client.get_bucket_lifecycle_configuration(Bucket=args.bucket)
    print(json.dumps(current.get("Rules", []), indent=2))
    print("lifecycle rule applied")


if __name__ == "__main__":
    main()
