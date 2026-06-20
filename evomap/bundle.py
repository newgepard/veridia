"""CLI for building a local EvoMap GEP bundle from a Veridia trace."""

from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from evomap.assets import DEFAULT_VALIDATION_COMMANDS, build_bundle, load_trace


def read_git_diff() -> str | None:
    """Return the current backend-oriented diff, if git is available."""
    paths = ["evomap", "tests", "tools", "pyproject.toml"]
    result = subprocess.run(
        ["git", "diff", "--", *paths],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    diff = result.stdout.strip()
    return diff or None


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a local EvoMap GEP bundle from a Veridia trace.")
    parser.add_argument("--trace", required=True, help="Input Veridia trace JSON.")
    parser.add_argument("--out", default="artifacts/evomap-bundle.json", help="Output bundle JSON.")
    parser.add_argument(
        "--validation-command",
        action="append",
        dest="validation_commands",
        help="Validation command to place in the Gene. Repeat to include multiple commands.",
    )
    parser.add_argument(
        "--no-git-diff",
        action="store_true",
        help="Do not include the current backend git diff in the Capsule.",
    )
    args = parser.parse_args()

    trace_path = Path(args.trace)
    trace = load_trace(trace_path)
    validation_commands = tuple(args.validation_commands or DEFAULT_VALIDATION_COMMANDS)
    diff_text = None if args.no_git_diff else read_git_diff()

    bundle = build_bundle(
        trace,
        source_trace=str(trace_path),
        validation_commands=validation_commands,
        diff_text=diff_text,
    )
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)
        f.write("\n")

    assets = bundle["assets"]
    print(f"wrote {out}")
    print(f"  assets={', '.join(asset['type'] for asset in assets)}")
    print(f"  frames={bundle['summary']['frames']} microscope={bundle['summary']['microscope_records']}")
    print(f"  confidence={assets[1]['confidence']:.2f}")


if __name__ == "__main__":
    main()
