#!/usr/bin/env python3
"""Render a private, human-readable Founder Complement Canvas offline."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

MAX_INPUT_BYTES = 256 * 1024
STAGES = (
    "zero_to_one",
    "one_to_ten",
    "ten_to_hundred",
)
FUNCTIONS = (
    "problem_discovery",
    "product",
    "engineering",
    "design",
    "go_to_market",
    "operations",
    "people_leadership",
    "capital_partnerships",
)
LEVELS = {"unknown", "observed", "practiced", "strong", "standout"}
CONFIDENCE = {"none", "low", "medium", "high"}
STAGE_LABELS = {
    "zero_to_one": "0→1",
    "one_to_ten": "1→10",
    "ten_to_hundred": "10→100",
}
FUNCTION_LABELS = {
    name: name.replace("_", " ") for name in FUNCTIONS
}
MARKDOWN_SPECIAL = re.compile(r"([\\`*_{}\[\]<>()#+.!|~-])")


class ReportError(ValueError):
    """Raised when a private assessment cannot be rendered safely."""


def safe_string(value: object, field: str, maximum: int) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ReportError(f"{field} must be a non-empty string")
    clean = value.strip()
    if len(clean) > maximum:
        raise ReportError(f"{field} exceeds {maximum} characters")
    return clean


def score_label(score: int) -> str:
    if score == 0:
        return "unknown"
    if score < 25:
        return "observed"
    if score < 50:
        return "practiced"
    if score < 75:
        return "strong"
    return "standout"


def markdown_text(value: object, field: str, maximum: int = 280) -> str:
    clean = safe_string(value, field, maximum)
    return MARKDOWN_SPECIAL.sub(r"\\\1", clean)


def load_assessment(path: Path) -> dict:
    if path.is_symlink():
        raise ReportError(f"Refusing to read through symlink: {path}")
    try:
        size = path.stat().st_size
    except OSError as exc:
        raise ReportError(f"Cannot inspect {path}: {exc}") from exc
    if size > MAX_INPUT_BYTES:
        raise ReportError(
            f"Private assessment exceeds {MAX_INPUT_BYTES} bytes"
        )
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ReportError(f"Cannot load private assessment: {exc}") from exc
    if not isinstance(value, dict):
        raise ReportError("Private assessment must be a JSON object")
    return value


def validated_vectors(
    value: object,
    dimensions: tuple[str, ...],
    field: str,
) -> list[dict]:
    if not isinstance(value, dict) or set(value) != set(dimensions):
        raise ReportError(
            f"{field} must contain exactly: {', '.join(dimensions)}"
        )
    result: list[dict] = []
    for name in dimensions:
        entry = value.get(name)
        if not isinstance(entry, dict):
            raise ReportError(f"{field}.{name} must be an object")
        score = entry.get("score")
        level = entry.get("level")
        confidence = entry.get("confidence")
        evidence_count = entry.get("evidence_count")
        if (
            isinstance(score, bool)
            or not isinstance(score, int)
            or not 0 <= score <= 100
        ):
            raise ReportError(f"{field}.{name}.score must be 0-100")
        if level not in LEVELS:
            raise ReportError(f"{field}.{name}.level is invalid")
        if confidence not in CONFIDENCE:
            raise ReportError(f"{field}.{name}.confidence is invalid")
        if (
            isinstance(evidence_count, bool)
            or not isinstance(evidence_count, int)
            or not 0 <= evidence_count <= 50
        ):
            raise ReportError(
                f"{field}.{name}.evidence_count must be 0-50"
            )
        if level != score_label(score):
            raise ReportError(
                f"{field}.{name} has inconsistent score and level"
            )
        result.append(
            {
                "name": name,
                "score": score,
                "level": level,
                "confidence": confidence,
                "evidence_count": evidence_count,
            }
        )
    return result


def string_list(
    value: object,
    field: str,
    *,
    maximum_items: int = 10,
) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum_items:
        raise ReportError(
            f"{field} must be a list with at most {maximum_items} items"
        )
    return [
        markdown_text(item, f"{field}[{index}]", 80)
        for index, item in enumerate(value)
    ]


def dimension_list(
    value: object,
    field: str,
    allowed: tuple[str, ...],
) -> list[str]:
    if not isinstance(value, list):
        raise ReportError(f"{field} must be a list")
    result: list[str] = []
    for item in value:
        if item not in allowed:
            raise ReportError(f"{field} contains unsupported dimension")
        if item not in result:
            result.append(item)
    return result


def labeled_items(
    values: list[str],
    labels: dict[str, str],
) -> str:
    if not values:
        return "- not specified"
    return "\n".join(f"- {labels[value]}" for value in values)


def vector_lines(values: list[dict], labels: dict[str, str]) -> str:
    demonstrated = [item for item in values if item["level"] != "unknown"]
    demonstrated.sort(
        key=lambda item: (
            item["score"],
            item["evidence_count"],
            item["name"],
        ),
        reverse=True,
    )
    if not demonstrated:
        return "- no demonstrated vector yet; more evidence is needed"
    return "\n".join(
        (
            f"- **{labels[item['name']]}** — {item['level']} "
            f"({item['confidence']} confidence; "
            f"{item['evidence_count']} evidence item(s))"
        )
        for item in demonstrated
    )


def render_report(assessment: dict) -> str:
    if assessment.get("schema_version") != "1.0":
        raise ReportError("Unsupported private assessment schema")
    publication_state = assessment.get("publication_state")
    if publication_state not in {
        "private_draft_only",
        "public_profile_approved",
    }:
        raise ReportError("Assessment has an invalid publication_state")

    alias = markdown_text(assessment.get("alias"), "alias", 50)
    summary = markdown_text(assessment.get("summary"), "summary", 280)
    generated_at = markdown_text(
        assessment.get("generated_at"),
        "generated_at",
        40,
    )
    stage_vectors = validated_vectors(
        assessment.get("stage_contributions"),
        STAGES,
        "stage_contributions",
    )
    function_vectors = validated_vectors(
        assessment.get("functional_contributions"),
        FUNCTIONS,
        "functional_contributions",
    )

    preferences = assessment.get("preferences")
    seeking = assessment.get("seeking")
    evidence = assessment.get("evidence")
    if not isinstance(preferences, dict):
        raise ReportError("preferences must be an object")
    if not isinstance(seeking, dict):
        raise ReportError("seeking must be an object")
    if not isinstance(evidence, list) or not 1 <= len(evidence) <= 50:
        raise ReportError("evidence must contain 1-50 items")

    preferred_stages = dimension_list(
        preferences.get("stages"),
        "preferences.stages",
        STAGES,
    )
    preferred_functions = dimension_list(
        preferences.get("functions"),
        "preferences.functions",
        FUNCTIONS,
    )
    sought_stages = dimension_list(
        seeking.get("stages"),
        "seeking.stages",
        STAGES,
    )
    sought_functions = dimension_list(
        seeking.get("functions"),
        "seeking.functions",
        FUNCTIONS,
    )
    themes = string_list(
        seeking.get("project_themes"),
        "seeking.project_themes",
    )
    modes = string_list(
        seeking.get("collaboration_modes"),
        "seeking.collaboration_modes",
        maximum_items=5,
    )
    principles = string_list(
        seeking.get("shared_principles"),
        "seeking.shared_principles",
    )

    unknown_stages = [
        STAGE_LABELS[item["name"]]
        for item in stage_vectors
        if item["level"] == "unknown"
    ]
    unknown_functions = [
        FUNCTION_LABELS[item["name"]]
        for item in function_vectors
        if item["level"] == "unknown"
    ]
    share_selected = sum(
        1
        for item in evidence
        if isinstance(item, dict) and item.get("share") is True
    )

    return "\n".join(
        [
            "FINDMATE_PRIVATE_COMPLEMENT_CANVAS_V1",
            "",
            f"# Founder Complement Canvas — {alias}",
            "",
            (
                "> Private draft. Do not publish or forward without the "
                "owner's separate approval."
            ),
            "",
            f"Generated: {generated_at}",
            f"Assessment state: `{publication_state}`",
            "",
            "## Working hypothesis",
            "",
            summary,
            "",
            "## Demonstrated stage contribution",
            "",
            vector_lines(stage_vectors, STAGE_LABELS),
            "",
            "## Demonstrated functional contribution",
            "",
            vector_lines(function_vectors, FUNCTION_LABELS),
            "",
            "## Work the owner says they prefer",
            "",
            "Stages:",
            labeled_items(preferred_stages, STAGE_LABELS),
            "",
            "Functions:",
            labeled_items(preferred_functions, FUNCTION_LABELS),
            "",
            "## Complement sought",
            "",
            "Stages:",
            labeled_items(sought_stages, STAGE_LABELS),
            "",
            "Functions:",
            labeled_items(sought_functions, FUNCTION_LABELS),
            "",
            "Project themes:",
            "\n".join(f"- {item}" for item in themes)
            if themes
            else "- not specified",
            "",
            "Collaboration modes:",
            "\n".join(f"- {item}" for item in modes)
            if modes
            else "- not specified",
            "",
            "Shared operating principles:",
            "\n".join(f"- {item}" for item in principles)
            if principles
            else "- not specified",
            "",
            "## Unknowns are not weaknesses",
            "",
            (
                "- Stages with insufficient evidence: "
                + (", ".join(unknown_stages) if unknown_stages else "none")
            ),
            (
                "- Functions with insufficient evidence: "
                + (
                    ", ".join(unknown_functions)
                    if unknown_functions
                    else "none"
                )
            ),
            "",
            "## Evidence boundary",
            "",
            f"- Evidence items evaluated: {len(evidence)}",
            f"- Items tentatively selected for public proof: {share_selected}",
            (
                "- Raw private notes, proof URLs, contact routes, and consent "
                "data are intentionally omitted from this canvas."
            ),
            (
                "- Scores order an evidence review; they are not personality "
                "types, compatibility diagnoses, or identity verification."
            ),
            "",
            "## Owner review",
            "",
            "1. Correct any outcome, stage, function, or confidence that the evidence does not support.",
            "2. Add missing evidence instead of treating an unknown as an inability.",
            "3. Decide whether the complement sought matches the actual project and commitment.",
            "4. Stop here unless a later, exact public profile and destination are separately approved.",
            "",
            (
                "This file performs no network request and authorizes no "
                "installation, publication, repository star, contact, identity "
                "exchange, or introduction."
            ),
            "",
        ]
    )


def write_private_report(path: Path, content: str) -> None:
    if not path.name.endswith(".private.md"):
        raise ReportError("private report filename must end in .private.md")
    if path.is_symlink():
        raise ReportError(f"Refusing to write through symlink: {path}")
    path.parent.mkdir(parents=True, exist_ok=True)
    flags = os.O_WRONLY | os.O_CREAT | os.O_TRUNC | getattr(os, "O_NOFOLLOW", 0)
    fd = os.open(path, flags, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        os.fchmod(handle.fileno(), 0o600)
        handle.write(content)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("assessment", type=Path)
    parser.add_argument("--output", required=True, type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        assessment = load_assessment(args.assessment)
        write_private_report(args.output, render_report(assessment))
    except ReportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(
        json.dumps(
            {
                "ok": True,
                "artifact": "private_founder_complement_canvas",
                "public_write": False,
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
