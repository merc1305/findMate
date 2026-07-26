#!/usr/bin/env python3
"""Run a zero-data, zero-network demonstration of the FindMate matcher."""

from __future__ import annotations

import importlib.util
import json
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "find-complementary-founders" / "scripts"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


assess = load_module("demo_assess_profile", SCRIPTS / "assess_profile.py")
matcher = load_module("demo_match_profiles", SCRIPTS / "match_profiles.py")


def consent() -> dict:
    today = datetime.now(timezone.utc).date()
    return {
        "public_profile": True,
        "approved_at": today.isoformat(),
        "expires_on": (today + timedelta(days=30)).isoformat(),
        "scope": "Synthetic local demo only; never publish",
    }


def evidence_item(
    identifier: str,
    kind: str,
    stage: str,
    functions: list[str],
    note: str,
) -> dict:
    return {
        "id": identifier,
        "kind": kind,
        "stages": [stage],
        "functions": functions,
        "private_note": note,
        "share": False,
    }


def synthetic_input(role: str) -> dict:
    common = {
        "preferences": {"stages": [], "functions": []},
        "public_contact": {
            "type": "github_issues",
            "url": "https://github.com/merc1305/findMate/issues",
        },
        "consent": consent(),
    }
    if role == "builder":
        return {
            **common,
            "alias": "synthetic-builder",
            "summary": (
                "Synthetic product engineer seeking an early go-to-market "
                "and operations partner."
            ),
            "evidence": [
                evidence_item(
                    "synthetic-prototype",
                    "shipped_artifact",
                    "zero_to_one",
                    ["product", "engineering"],
                    "Synthetic demo: produced a first working prototype.",
                ),
                evidence_item(
                    "synthetic-discovery",
                    "shipped_artifact",
                    "zero_to_one",
                    ["problem_discovery", "product", "engineering"],
                    "Synthetic demo: turned a problem hypothesis into a tool.",
                ),
            ],
            "seeking": {
                "stages": ["one_to_ten"],
                "functions": ["go_to_market", "operations"],
                "project_themes": ["agent tools"],
                "collaboration_modes": ["project-partner"],
                "shared_principles": ["evidence over hype"],
            },
        }
    if role == "operator":
        return {
            **common,
            "alias": "synthetic-operator",
            "summary": (
                "Synthetic early-market operator seeking a product and "
                "engineering partner."
            ),
            "evidence": [
                evidence_item(
                    "synthetic-customers",
                    "customer_outcome",
                    "one_to_ten",
                    ["go_to_market", "operations"],
                    "Synthetic demo: created a repeatable customer loop.",
                ),
                evidence_item(
                    "synthetic-delivery",
                    "operational_outcome",
                    "one_to_ten",
                    ["go_to_market", "operations"],
                    "Synthetic demo: documented repeatable delivery.",
                ),
            ],
            "seeking": {
                "stages": ["zero_to_one"],
                "functions": ["product", "engineering"],
                "project_themes": ["agent tools"],
                "collaboration_modes": ["project-partner"],
                "shared_principles": ["evidence over hype"],
            },
        }
    raise ValueError(f"Unsupported synthetic role: {role}")


def run_demo() -> dict:
    builder_public, _ = assess.build_profiles(synthetic_input("builder"))
    operator_public, _ = assess.build_profiles(synthetic_input("operator"))

    with tempfile.TemporaryDirectory(prefix="findmate-demo-") as directory:
        temporary = Path(directory)
        builder_path = temporary / "synthetic-builder.public.json"
        operator_path = temporary / "synthetic-operator.public.json"
        assess.write_json(builder_path, builder_public, private=False)
        assess.write_json(operator_path, operator_public, private=False)
        builder = matcher.load_profile(builder_path)
        operator = matcher.load_profile(operator_path)
        result = matcher.score_match(builder, operator)

    result["profile_source"] = "synthetic-operator.public.json"
    return {
        "demo": "synthetic; no owner data, network, credentials, or public writes",
        "owner_alias": builder["alias"],
        "temporary_public_profiles": [
            "synthetic-builder.public.json",
            "synthetic-operator.public.json",
        ],
        "method": "heuristic shortlist; not a compatibility verdict",
        "match": result,
    }


def main() -> int:
    print(json.dumps(run_demo(), indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
