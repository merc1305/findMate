#!/usr/bin/env python3
"""Run the canonical validator and expose bounded GitHub Action outputs."""

from __future__ import annotations

import argparse
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VALIDATOR_PATH = (
    ROOT
    / "skills"
    / "find-complementary-founders"
    / "scripts"
    / "validate_profile.py"
)
SHA256_PATTERN = re.compile(r"^[0-9a-f]{64}$")
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ActionOutputError(ValueError):
    """Raised when the bounded Action-output contract cannot be written."""


def load_validator():
    spec = importlib.util.spec_from_file_location(
        "findmate_action_profile_validator",
        VALIDATOR_PATH,
    )
    if spec is None or spec.loader is None:
        raise ActionOutputError("cannot load the canonical profile validator")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def append_github_outputs(path: Path, result: dict) -> None:
    """Append only the fixed, non-identifying validation outputs."""

    canonical_sha256 = result.get("canonical_sha256")
    expires_on = result.get("expires_on")
    if (
        not isinstance(canonical_sha256, str)
        or SHA256_PATTERN.fullmatch(canonical_sha256) is None
    ):
        raise ActionOutputError("validator returned an invalid canonical SHA-256")
    if (
        not isinstance(expires_on, str)
        or DATE_PATTERN.fullmatch(expires_on) is None
    ):
        raise ActionOutputError("validator returned an invalid expiry date")
    if path.is_symlink():
        raise ActionOutputError("refusing to write GitHub outputs through a symlink")

    try:
        with path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(f"canonical_sha256={canonical_sha256}\n")
            handle.write(f"expires_on={expires_on}\n")
    except OSError as exc:
        raise ActionOutputError(f"cannot write GitHub outputs: {exc}") from exc


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--github-output",
        type=Path,
        help=(
            "GitHub's per-step output file. Only canonical_sha256 and "
            "expires_on are appended after successful validation."
        ),
    )
    parser.add_argument("profile", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        validator = load_validator()
        result = validator.validate_profile(validator.load_json(args.profile))
        if args.github_output is not None:
            append_github_outputs(args.github_output, result)
    except (ActionOutputError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    json.dump(result, sys.stdout, indent=2, ensure_ascii=False, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
