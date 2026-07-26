#!/usr/bin/env python3
"""Measure aggregate FindMate growth and enforce the active-promotion stop rule."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

DEFAULT_REPOSITORY = "merc1305/findMate"
DEFAULT_CONFIG = Path(__file__).with_name("strategies.json")
DEFAULT_BASELINE = Path(__file__).with_name("baseline.json")
API_ROOT = "https://api.github.com"
PROFILE_REPLY_MARKER = "FINDMATE_OWNER_PROFILE_V1"
VALIDATION_RECEIPT_MARKER = "<!-- findmate-validation:"
RECEIPT_EXPIRY_PATTERN = re.compile(r"^- Expires: `(\d{4}-\d{2}-\d{2})`$", re.M)
SKILLS_SH_BADGE_URL = "https://www.skills.sh/b/merc1305/findMate"
FINDMATE_SITE_URL = "https://findmate-owner-network.xvwbgtt855.chatgpt.site"
WEB_DISCOVERY_URLS = {
    "landing": FINDMATE_SITE_URL,
    "robots": f"{FINDMATE_SITE_URL}/robots.txt",
    "sitemap": f"{FINDMATE_SITE_URL}/sitemap.xml",
    "llms": f"{FINDMATE_SITE_URL}/llms.txt",
}
MAX_EXTERNAL_STATUS_BYTES = 128 * 1024
MAX_CLAUDE_CATALOG_BYTES = 4 * 1024 * 1024
SEMVER_TAG_RULESET_NAME = "Protect semver release tags"
PORTABLE_SKILL_ASSET_NAME = "find-complementary-founders.skill.zip"
PORTABLE_SKILL_CHECKSUM_NAME = (
    "find-complementary-founders.skill.zip.sha256"
)
CLAUDE_COMMUNITY_CATALOG_URL = (
    "https://raw.githubusercontent.com/anthropics/"
    "claude-plugins-community/main/.claude-plugin/marketplace.json"
)
CLAUDE_COMMUNITY_EXPECTED_SOURCE = "https://github.com/merc1305/findMate"
SKILL_SEARCH_INDEX_QUERY = (
    'repo:merc1305/findMate '
    'path:skills/find-complementary-founders/SKILL.md '
    '"find a cofounder"'
)
GITHUB_ACTION_REFERENCE_QUERY = (
    '"uses: merc1305/findMate@" '
    "path:.github/workflows "
    "-repo:merc1305/findMate"
)
DISTRIBUTION_PULL_REQUESTS = (
    {
        "channel": "awesome_copilot",
        "repository": "github/awesome-copilot",
        "number": 2438,
    },
    {
        "channel": "openhands_extensions",
        "repository": "OpenHands/extensions",
        "number": 419,
    },
    {
        "channel": "aas_core",
        "repository": "sickn33/agentic-awesome-skills",
        "number": 992,
    },
)


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
    return github_url_json(f"{API_ROOT}/repos/{repository}{endpoint}", token)


def github_url_json(url: str, token: str | None) -> object:
    request = Request(
        url,
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
        raise GrowthError(f"GitHub request failed for {url}: {exc}") from exc


def optional_github_json(
    repository: str, endpoint: str, token: str | None
) -> tuple[object | None, str | None]:
    try:
        return github_json(repository, endpoint, token), None
    except GrowthError as exc:
        return None, str(exc)


def code_search_total_count(value: object) -> int:
    if not isinstance(value, dict):
        raise GrowthError("GitHub code-search response must be an object")
    total_count = value.get("total_count")
    if not isinstance(total_count, int) or total_count < 0:
        raise GrowthError("GitHub code-search response lacks total_count")
    return total_count


def code_search_indicates_index(value: object) -> bool:
    return code_search_total_count(value) > 0


def optional_skill_search_index(
    token: str | None,
) -> tuple[bool | None, str | None]:
    query = urlencode({"q": SKILL_SEARCH_INDEX_QUERY, "per_page": 1})
    try:
        value = github_url_json(f"{API_ROOT}/search/code?{query}", token)
        return code_search_indicates_index(value), None
    except GrowthError as exc:
        return None, str(exc)


def optional_github_action_references(
    token: str | None,
) -> tuple[int | None, str | None]:
    query = urlencode({"q": GITHUB_ACTION_REFERENCE_QUERY, "per_page": 1})
    try:
        value = github_url_json(f"{API_ROOT}/search/code?{query}", token)
        return code_search_total_count(value), None
    except GrowthError as exc:
        return None, str(exc)


def external_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "Accept": (
                "text/plain,application/xml,text/markdown,text/html,"
                "image/svg+xml;q=0.8"
            ),
            "User-Agent": "findmate-distribution-monitor/1.0",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(MAX_EXTERNAL_STATUS_BYTES + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise GrowthError(f"External status request failed: {exc}") from exc
    if len(body) > MAX_EXTERNAL_STATUS_BYTES:
        raise GrowthError("External status response exceeded 128 KiB")
    return body.decode("utf-8", errors="replace")


def external_json(url: str, max_bytes: int) -> object:
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "findmate-distribution-monitor/1.0",
        },
    )
    try:
        with urlopen(request, timeout=20) as response:
            body = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise GrowthError(f"External JSON request failed: {exc}") from exc
    if len(body) > max_bytes:
        raise GrowthError(
            f"External JSON response exceeded {max_bytes} bytes"
        )
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise GrowthError(f"External JSON response was invalid: {exc}") from exc


def badge_indicates_skills_sh_listing(svg: str) -> bool:
    normalized = svg.casefold()
    return "<svg" in normalized and "resource not found" not in normalized


def optional_skills_sh_listing() -> tuple[bool | None, str | None]:
    try:
        return badge_indicates_skills_sh_listing(
            external_text(SKILLS_SH_BADGE_URL)
        ), None
    except GrowthError as exc:
        return None, str(exc)


def summarize_web_discovery(
    documents: dict[str, str],
    errors: dict[str, str],
) -> dict:
    landing = documents.get("landing", "")
    robots = documents.get("robots", "")
    sitemap = documents.get("sitemap", "")
    llms = documents.get("llms", "")
    checks = {
        "canonical_landing": (
            f'rel="canonical" href="{FINDMATE_SITE_URL}"' in landing
            or f'rel="canonical" href="{FINDMATE_SITE_URL}/"' in landing
        ),
        "robots_links_sitemap": (
            f"Sitemap: {FINDMATE_SITE_URL}/sitemap.xml" in robots
        ),
        "sitemap_lists_landing": (
            f"<loc>{FINDMATE_SITE_URL}</loc>" in sitemap
            or f"<loc>{FINDMATE_SITE_URL}/</loc>" in sitemap
        ),
        "llms_routes_to_canonical_skill": (
            llms.startswith("# FindMate\n")
            and "assess only its own owner" in llms
            and (
                "github.com/merc1305/findMate/blob/main/skills/"
                "find-complementary-founders/SKILL.md"
            )
            in llms
        ),
    }
    return {
        "site_url": FINDMATE_SITE_URL,
        "endpoint_urls": WEB_DISCOVERY_URLS,
        "live": all(checks.values()) if not errors else None,
        "checks": checks,
        "errors": errors,
        "note": (
            "Live means only that four bounded public documents expose the "
            "expected canonical and own-owner discovery contract. It does "
            "not prove indexing, a visit, an agent read, an install, a "
            "profile submission, or a star."
        ),
    }


def optional_web_discovery() -> dict:
    documents: dict[str, str] = {}
    errors: dict[str, str] = {}
    for name, url in WEB_DISCOVERY_URLS.items():
        try:
            documents[name] = external_text(url)
        except GrowthError as exc:
            errors[name] = str(exc)
    return summarize_web_discovery(documents, errors)


def summarize_distribution_pull_request(
    channel: str,
    repository: str,
    number: int,
    value: object | None,
    error: str | None,
) -> dict:
    summary = {
        "channel": channel,
        "repository": repository,
        "number": number,
        "url": f"https://github.com/{repository}/pull/{number}",
        "state": "unavailable",
        "merged_at": None,
        "updated_at": None,
        "error": error,
    }
    if not isinstance(value, dict):
        return summary
    merged_at = value.get("merged_at")
    state = value.get("state")
    if isinstance(merged_at, str) and merged_at:
        summary["state"] = "merged"
        summary["merged_at"] = merged_at
    elif state in {"open", "closed"}:
        summary["state"] = state
    updated_at = value.get("updated_at")
    if isinstance(updated_at, str):
        summary["updated_at"] = updated_at
    summary["error"] = None
    return summary


def summarize_release_supply_chain(
    release: object | None,
    release_error: str | None,
    rulesets: object | None,
    rulesets_error: str | None,
) -> dict:
    summary = {
        "latest_tag": None,
        "latest_url": None,
        "latest_immutable": None,
        "semver_tag_ruleset_active": None,
        "portable_skill_archive": {
            "present": None,
            "download_count": None,
            "size": None,
            "digest": None,
        },
        "portable_skill_checksum_present": None,
        "errors": [
            error
            for error in (release_error, rulesets_error)
            if isinstance(error, str)
        ],
        "note": (
            "Release immutability applies only to releases published after "
            "the repository setting was enabled. The active v* tag ruleset "
            "still prevents update or deletion of matching tags. Asset "
            "download_count is aggregate, is not unique-user telemetry, and "
            "can include maintainer verification."
        ),
    }
    if isinstance(release, dict):
        tag = release.get("tag_name")
        url = release.get("html_url")
        immutable = release.get("immutable")
        if isinstance(tag, str):
            summary["latest_tag"] = tag
        if isinstance(url, str):
            summary["latest_url"] = url
        if isinstance(immutable, bool):
            summary["latest_immutable"] = immutable
        assets = release.get("assets")
        if isinstance(assets, list):
            archive = next(
                (
                    item
                    for item in assets
                    if isinstance(item, dict)
                    and item.get("name") == PORTABLE_SKILL_ASSET_NAME
                ),
                None,
            )
            checksum = next(
                (
                    item
                    for item in assets
                    if isinstance(item, dict)
                    and item.get("name") == PORTABLE_SKILL_CHECKSUM_NAME
                ),
                None,
            )
            summary["portable_skill_archive"]["present"] = archive is not None
            summary["portable_skill_checksum_present"] = checksum is not None
            if archive is not None:
                download_count = archive.get("download_count")
                size = archive.get("size")
                digest = archive.get("digest")
                if isinstance(download_count, int):
                    summary["portable_skill_archive"][
                        "download_count"
                    ] = download_count
                if isinstance(size, int):
                    summary["portable_skill_archive"]["size"] = size
                if isinstance(digest, str):
                    summary["portable_skill_archive"]["digest"] = digest
    if isinstance(rulesets, list):
        summary["semver_tag_ruleset_active"] = any(
            isinstance(item, dict)
            and item.get("name") == SEMVER_TAG_RULESET_NAME
            and item.get("target") == "tag"
            and item.get("enforcement") == "active"
            for item in rulesets
        )
    return summary


def summarize_claude_community_catalog(
    catalog: object | None,
    error: str | None,
) -> dict:
    summary = {
        "catalog_url": CLAUDE_COMMUNITY_CATALOG_URL,
        "catalog_plugin_count": None,
        "listed": None,
        "state": "unavailable",
        "source_url": None,
        "source_sha": None,
        "error": error,
        "note": (
            "Only an exact findmate entry sourced from merc1305/findMate and "
            "pinned to a 40-character commit SHA counts as a listing. A name "
            "collision or unpinned entry is reported separately."
        ),
    }
    if not isinstance(catalog, dict):
        return summary
    plugins = catalog.get("plugins")
    if not isinstance(plugins, list):
        summary["error"] = "Claude community catalog lacks a plugins array"
        return summary
    summary["catalog_plugin_count"] = len(plugins)
    entry = next(
        (
            item
            for item in plugins
            if isinstance(item, dict) and item.get("name") == "findmate"
        ),
        None,
    )
    if entry is None:
        summary["listed"] = False
        summary["state"] = "not_listed"
        summary["error"] = None
        return summary
    source = entry.get("source")
    source_url = source.get("url") if isinstance(source, dict) else None
    source_sha = source.get("sha") if isinstance(source, dict) else None
    if isinstance(source_url, str):
        summary["source_url"] = source_url
    if isinstance(source_sha, str):
        summary["source_sha"] = source_sha
    normalized_source = (
        source_url.rstrip("/").removesuffix(".git").casefold()
        if isinstance(source_url, str)
        else None
    )
    normalized_expected = (
        CLAUDE_COMMUNITY_EXPECTED_SOURCE.rstrip("/").casefold()
    )
    valid_source_sha = (
        isinstance(source_sha, str)
        and re.fullmatch(r"[0-9a-fA-F]{40}", source_sha) is not None
    )
    if normalized_source == normalized_expected and valid_source_sha:
        summary["listed"] = True
        summary["state"] = "listed_expected_source"
    elif normalized_source == normalized_expected:
        summary["listed"] = False
        summary["state"] = "canonical_source_unpinned"
    else:
        summary["listed"] = False
        summary["state"] = "name_conflict"
    summary["error"] = None
    return summary


def optional_claude_community_catalog() -> dict:
    try:
        catalog = external_json(
            CLAUDE_COMMUNITY_CATALOG_URL,
            MAX_CLAUDE_CATALOG_BYTES,
        )
        return summarize_claude_community_catalog(catalog, None)
    except GrowthError as exc:
        return summarize_claude_community_catalog(None, str(exc))


def summarize_github_owner_pool(comments: object) -> dict:
    summary = {
        "marked_own_owner_submissions": 0,
        "inline_sources": 0,
        "linked_sources": 0,
        "machine_validated_current_receipts": 0,
    }
    if not isinstance(comments, list):
        return summary
    today = datetime.now(timezone.utc).date()
    for comment in comments:
        if not isinstance(comment, dict):
            continue
        body = comment.get("body")
        linked_source = (
            isinstance(body, str)
            and "Owner-approved profile: https://" in body
        )
        inline_source = (
            isinstance(body, str)
            and "Owner-approved profile: inline" in body
            and "FINDMATE_PROFILE_JSON_BEGIN\n" in body
            and "\nFINDMATE_PROFILE_JSON_END" in body
        )
        if (
            isinstance(body, str)
            and body.startswith(f"{PROFILE_REPLY_MARKER}\n")
            and "I represent my own owner." in body
            and linked_source != inline_source
            and "Canonical profile SHA-256: " in body
            and "Expires: " in body
        ):
            summary["marked_own_owner_submissions"] += 1
            key = "inline_sources" if inline_source else "linked_sources"
            summary[key] += 1

        user = comment.get("user")
        login = user.get("login") if isinstance(user, dict) else None
        if (
            isinstance(body, str)
            and login == "github-actions[bot]"
            and VALIDATION_RECEIPT_MARKER in body
            and "✅ **FindMate profile admitted" in body
        ):
            expiry_match = RECEIPT_EXPIRY_PATTERN.search(body)
            if expiry_match:
                try:
                    expires_on = datetime.strptime(
                        expiry_match.group(1),
                        "%Y-%m-%d",
                    ).date()
                except ValueError:
                    continue
                if expires_on >= today:
                    summary["machine_validated_current_receipts"] += 1
    return summary


def count_github_owner_submissions(comments: object) -> int:
    return summarize_github_owner_pool(comments)[
        "marked_own_owner_submissions"
    ]


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
    distribution_surfaces: dict | None = None,
) -> dict:
    stars = repo_data.get("stargazers_count")
    if not isinstance(stars, int):
        raise GrowthError("GitHub response lacks an integer stargazers_count")
    baseline_stars = baseline.get("stars")
    if not isinstance(baseline_stars, int):
        raise GrowthError("Baseline lacks an integer stars value")
    stop_above = config["stop_active_promotion_above_stars"]
    state = promotion_state(stars, stop_above)
    github_pool = (
        summarize_github_owner_pool(github_thread_comments)
        if github_thread_comments is not None
        else None
    )

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
                github_pool["marked_own_owner_submissions"]
                if github_pool is not None
                else None
            ),
            "github_inline_sources": (
                github_pool["inline_sources"]
                if github_pool is not None
                else None
            ),
            "github_linked_sources": (
                github_pool["linked_sources"]
                if github_pool is not None
                else None
            ),
            "github_machine_validated_current_receipts": (
                github_pool["machine_validated_current_receipts"]
                if github_pool is not None
                else None
            ),
            "github_error": github_thread_error,
            "note": (
                "Syntactic source counts only; every inline or linked profile "
                "still requires local schema, hash, consent, and expiry "
                "validation."
            ),
        },
        "distribution_surfaces": distribution_surfaces or {},
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
        skills_sh_listed, skills_sh_error = optional_skills_sh_listing()
        skill_search_indexed, skill_search_error = optional_skill_search_index(
            token
        )
        action_references, action_references_error = (
            optional_github_action_references(token)
        )
        latest_release, latest_release_error = optional_github_json(
            args.repository,
            "/releases/latest",
            token,
        )
        repository_rulesets, repository_rulesets_error = optional_github_json(
            args.repository,
            "/rulesets",
            token,
        )
        claude_community = optional_claude_community_catalog()
        web_discovery = optional_web_discovery()
        catalog_pull_requests = []
        for item in DISTRIBUTION_PULL_REQUESTS:
            value, error = optional_github_json(
                item["repository"],
                f"/pulls/{item['number']}",
                token,
            )
            catalog_pull_requests.append(
                summarize_distribution_pull_request(
                    item["channel"],
                    item["repository"],
                    item["number"],
                    value,
                    error,
                )
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
            distribution_surfaces={
                "skills_sh": {
                    "listed": skills_sh_listed,
                    "badge_url": SKILLS_SH_BADGE_URL,
                    "error": skills_sh_error,
                    "note": (
                        "A listing appears only after a genuine telemetry-enabled "
                        "skills CLI install; maintainer tests are not counted."
                    ),
                },
                "github_skill_search": {
                    "indexed": skill_search_indexed,
                    "query": SKILL_SEARCH_INDEX_QUERY,
                    "error": skill_search_error,
                    "note": (
                        "True only when public GitHub Code Search returns the "
                        "new exact owner-intent phrase from the canonical skill."
                    ),
                },
                "github_action_references": {
                    "count": action_references,
                    "query": GITHUB_ACTION_REFERENCE_QUERY,
                    "error": action_references_error,
                    "note": (
                        "Aggregate public workflow references only; no repository "
                        "names, owner identities, workflow runs, or profile data "
                        "are collected."
                    ),
                },
                "release_supply_chain": summarize_release_supply_chain(
                    latest_release,
                    latest_release_error,
                    repository_rulesets,
                    repository_rulesets_error,
                ),
                "claude_community": claude_community,
                "web_discovery": web_discovery,
                "catalog_pull_requests": catalog_pull_requests,
            },
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
