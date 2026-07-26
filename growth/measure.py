#!/usr/bin/env python3
"""Measure aggregate FindMate growth and enforce the active-promotion stop rule."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

DEFAULT_REPOSITORY = "merc1305/findMate"
DEFAULT_CONFIG = Path(__file__).with_name("strategies.json")
DEFAULT_BASELINE = Path(__file__).with_name("baseline.json")
API_ROOT = "https://api.github.com"
PROFILE_REPLY_MARKER = "FINDMATE_OWNER_PROFILE_V1"


class GrowthError(ValueError):
    """Raised when growth configuration or GitHub data is invalid."""


def read_object(path: Path) -> dict:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GrowthError(f"Cannot load {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise GrowthError(f"{path} must contain a JSON object")
    return value


def promotion_state(stars: int, stop_above: int) -> dict:
    if stars < 0 or stop_above < 0:
        raise GrowthError("Star counts and thresholds must be non-negative")
    stopped = stars > stop_above
    return {
        "active_promotion": not stopped,
        "stopped": stopped,
        "stop_above_stars": stop_above,
        "next_stop_count": stop_above + 1,
        "stars_until_stop": max(0, stop_above + 1 - stars),
    }


def validate_strategy_config(config: dict) -> None:
    if config.get("schema_version") != "1.0":
        raise GrowthError("Unsupported growth strategy schema")
    threshold = config.get("stop_active_promotion_above_stars")
    if not isinstance(threshold, int) or threshold < 0:
        raise GrowthError("Invalid active-promotion threshold")
    guardrails = config.get("guardrails")
    if not isinstance(guardrails, list) or not guardrails:
        raise GrowthError("Growth strategy guardrails are required")
    experiments = config.get("experiments")
    if not isinstance(experiments, list) or len(experiments) < 10:
        raise GrowthError("At least ten growth experiments are required")
    identifiers: set[str] = set()
    for experiment in experiments:
        if not isinstance(experiment, dict):
            raise GrowthError("Each experiment must be an object")
        identifier = experiment.get("id")
        if not isinstance(identifier, str) or not identifier:
            raise GrowthError("Every experiment needs an id")
        if identifier in identifiers:
            raise GrowthError(f"Duplicate experiment id: {identifier}")
        identifiers.add(identifier)
        if experiment.get("status") not in {"active", "planned", "retired"}:
            raise GrowthError(f"{identifier} has an invalid status")
        if not isinstance(experiment.get("active_promotion"), bool):
            raise GrowthError(f"{identifier} must declare active_promotion")


def github_json(repository: str, endpoint: str, token: str | None) -> object:
    request = Request(
        f"{API_ROOT}/repos/{repository}{endpoint}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "findmate-ethical-growth-loop/1.0",
            **({"Authorization": f"Bearer {token}"} if token else {}),
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            return json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise GrowthError(f"GitHub request failed for {endpoint or '/'}: {exc}") from exc


def optional_github_json(
    repository: str, endpoint: str, token: str | None
) -> tuple[object | None, str | None]:
    try:
        return github_json(repository, endpoint, token), None
    except GrowthError as exc:
        return None, str(exc)


def count_github_owner_submissions(comments: object) -> int:
    if not isinstance(comments, list):
        return 0
    total = 0
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        body = comment.get("body")
        if (
            isinstance(body, str)
            and body.startswith(f"{PROFILE_REPLY_MARKER}\n")
            and "I represent my own owner." in body
            and "Owner-approved profile: https://" in body
            and "Canonical profile SHA-256: " in body
            and "Expires: " in body
        ):
            total += 1
    return total


def build_status(
    repository: str,
    repo_data: dict,
    baseline: dict,
    config: dict,
    *,
    views: dict | None = None,
    clones: dict | None = None,
    referrers: list | None = None,
    traffic_errors: list[str] | None = None,
    github_thread_comments: list | None = None,
    github_thread_error: str | None = None,
) -> dict:
    stars = repo_data.get("stargazers_count")
    if not isinstance(stars, int):
        raise GrowthError("GitHub response lacks an integer stargazers_count")
    baseline_stars = baseline.get("stars")
    if not isinstance(baseline_stars, int):
        raise GrowthError("Baseline lacks an integer stars value")
    stop_above = config["stop_active_promotion_above_stars"]
    state = promotion_state(stars, stop_above)

    experiments = []
    for experiment in config["experiments"]:
        effective_status = experiment["status"]
        if state["stopped"] and experiment["active_promotion"]:
            effective_status = "stopped_at_threshold"
        experiments.append(
            {
                "id": experiment["id"],
                "name": experiment["name"],
                "configured_status": experiment["status"],
                "effective_status": effective_status,
                "active_promotion": experiment["active_promotion"],
                "primary_metric": experiment["primary_metric"],
            }
        )

    return {
        "schema_version": "1.0",
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "repository": repository,
        "stars": stars,
        "star_delta_from_baseline": stars - baseline_stars,
        "promotion": state,
        "traffic_14d": {
            "views": views,
            "clones": clones,
            "referrers": referrers,
            "errors": traffic_errors or [],
        },
        "owner_profile_pool": {
            "github_issue_number": 2,
            "github_marked_own_owner_submissions": (
                count_github_owner_submissions(github_thread_comments)
                if github_thread_comments is not None
                else None
            ),
            "github_error": github_thread_error,
            "note": (
                "Syntactic count only; linked profiles still require local "
                "schema, hash, consent, and expiry validation."
            ),
        },
        "experiments": experiments,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repository", default=DEFAULT_REPOSITORY)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--baseline", type=Path, default=DEFAULT_BASELINE)
    parser.add_argument("--output", type=Path)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        config = read_object(args.config)
        validate_strategy_config(config)
        baseline = read_object(args.baseline)
        token = os.environ.get("GITHUB_TOKEN")
        repo_data = github_json(args.repository, "", token)
        if not isinstance(repo_data, dict):
            raise GrowthError("GitHub repository response must be an object")

        traffic: dict[str, object | None] = {}
        errors: list[str] = []
        for name, endpoint in (
            ("views", "/traffic/views"),
            ("clones", "/traffic/clones"),
            ("referrers", "/traffic/popular/referrers"),
        ):
            value, error = optional_github_json(args.repository, endpoint, token)
            traffic[name] = value
            if error:
                errors.append(error)
        github_comments, github_thread_error = optional_github_json(
            args.repository,
            "/issues/2/comments?per_page=100",
            token,
        )
        status = build_status(
            args.repository,
            repo_data,
            baseline,
            config,
            views=traffic["views"] if isinstance(traffic["views"], dict) else None,
            clones=traffic["clones"] if isinstance(traffic["clones"], dict) else None,
            referrers=(
                traffic["referrers"]
                if isinstance(traffic["referrers"], list)
                else None
            ),
            traffic_errors=errors,
            github_thread_comments=(
                github_comments if isinstance(github_comments, list) else None
            ),
            github_thread_error=github_thread_error,
        )
    except GrowthError as exc:
        print(f"growth error: {exc}", file=sys.stderr)
        return 1

    serialized = json.dumps(status, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized, encoding="utf-8")
    else:
        sys.stdout.write(serialized)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
