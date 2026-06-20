"""CLI for explicit EvoMap /a2a/validate dry-runs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from evomap.client import EvoMapError, NodeCredentials, validate_bundle


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Dry-run an EvoMap bundle with /a2a/validate. Requires explicit node env vars."
    )
    parser.add_argument("--bundle", required=True, help="Bundle JSON produced by python -m evomap.bundle.")
    parser.add_argument("--node-id-env", default="EVOMAP_NODE_ID", help="Env var containing node_id.")
    parser.add_argument("--node-secret-env", default="EVOMAP_NODE_SECRET", help="Env var containing node_secret.")
    parser.add_argument("--base-url", default="https://evomap.ai", help="EvoMap base URL.")
    parser.add_argument("--timeout", type=float, default=30.0)
    args = parser.parse_args()

    with Path(args.bundle).open("r", encoding="utf-8") as f:
        bundle = json.load(f)
    try:
        credentials = NodeCredentials.from_env(args.node_id_env, args.node_secret_env)
    except EvoMapError as exc:
        parser.exit(2, f"evomap validate: {exc}\n")
    try:
        response = validate_bundle(
            bundle["assets"],
            credentials,
            base_url=args.base_url,
            timeout=args.timeout,
        )
    except EvoMapError as exc:
        parser.exit(1, f"evomap validate: {exc}\n")
    print(json.dumps(response, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
