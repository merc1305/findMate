#!/usr/bin/env python3
"""Measure aggregate FindMate growth and enforce the active-promotion stop rule."""

from __future__ import annotations

import argparse
import base64
import binascii
import json
import os
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
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
    "agent_skills": (
        "https://merc1305.github.io/findMate/"
        ".well-known/agent-skills/index.json"
    ),
}
MAX_EXTERNAL_STATUS_BYTES = 128 * 1024
MAX_CLAUDE_CATALOG_BYTES = 4 * 1024 * 1024
MAX_AGENT_PLUGINS_CATALOG_BYTES = 4 * 1024 * 1024
MAX_AGENT_SKILL_INDEX_BYTES = 2 * 1024 * 1024
MAX_AAS_SKILL_BYTES = 512 * 1024
MAX_MOLTBOOK_THREAD_BYTES = 1_000_000
MAX_MOLTBOOK_COMMENT_NODES = 1_000
SEMVER_TAG_RULESET_NAME = "Protect semver release tags"
PORTABLE_SKILL_ASSET_NAME = "find-complementary-founders.skill.zip"
PORTABLE_SKILL_CHECKSUM_NAME = (
    "find-complementary-founders.skill.zip.sha256"
)
MOLTBOOK_THREAD_ID = "25f3a177-acb6-4a88-8375-6dade2059042"
MOLTBOOK_THREAD_URL = (
    f"https://www.moltbook.com/post/{MOLTBOOK_THREAD_ID}"
)
MOLTBOOK_THREAD_API_URL = (
    "https://www.moltbook.com/api/v1/posts/"
    f"{MOLTBOOK_THREAD_ID}/comments?sort=old"
)
MOLTBOOK_HOST_AGENT_ID = "f919976d-85d4-4421-b72b-0736ae994fbf"
MOLTBOOK_PROFILE_HASH_PATTERN = re.compile(
    r"^Canonical profile SHA-256: ([0-9a-f]{64})$",
    re.M,
)
MOLTBOOK_PROFILE_EXPIRY_PATTERN = re.compile(
    r"^Expires: (\d{4}-\d{2}-\d{2})$",
    re.M,
)
MOLTBOOK_PROFILE_URL_PATTERN = re.compile(
    r"^Owner-approved profile: https://\S+$",
    re.M,
)
CLAUDE_COMMUNITY_CATALOG_URL = (
    "https://raw.githubusercontent.com/anthropics/"
    "claude-plugins-community/main/.claude-plugin/marketplace.json"
)
CLAUDE_COMMUNITY_EXPECTED_SOURCE = "https://github.com/merc1305/findMate"
AAS_CORE_REPOSITORY = "sickn33/agentic-awesome-skills"
AAS_CORE_SKILL_PATH = "skills/find-complementary-founders/SKILL.md"
AAS_CORE_EXPECTED_SOURCE = "source_repo: merc1305/findMate"
AGENT_PLUGINS_REPOSITORY = "dmgrok/agent-plugins"
AGENT_PLUGINS_SUBMISSION_ISSUE = 100
AGENT_PLUGINS_PULL_REQUEST = 101
AGENT_PLUGINS_CATALOG_URL = (
    "https://raw.githubusercontent.com/dmgrok/"
    "agent-plugins/main/catalog.json"
)
AGENT_PLUGINS_EXPECTED_SOURCE = "https://github.com/merc1305/findMate"
AGENT_PLUGINS_EXPECTED_PATH = "skills/find-complementary-founders"
AGENT_SKILL_INDEX_README_URL = (
    "https://raw.githubusercontent.com/heilcheng/"
    "awesome-agent-skills/main/README.md"
)
AGENT_SKILL_INDEX_EXPECTED_LINK = (
    "[merc1305/findMate]"
    "(https://github.com/merc1305/findMate/tree/main/"
    "skills/find-complementary-founders)"
)
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
PROFILE_CARD_REFERENCE_QUERY = (
    '"FINDMATE_OWNER_PROFILE_CARD_V1" '
    "extension:md "
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
    {
        "channel": "aas_proactive_update",
        "repository": "sickn33/agentic-awesome-skills",
        "number": 1011,
    },
    {
        "channel": "agent_skill_index",
        "repository": "heilcheng/awesome-agent-skills",
        "number": 377,
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


def summarize_traffic_provenance(
    clones: dict | None,
    repository_actions: object | None,
    repository_actions_error: str | None,
) -> dict:
    """Explain why aggregate clone counts are not external-adoption counts."""
    clone_count = clones.get("count") if isinstance(clones, dict) else None
    action_run_count = (
        repository_actions.get("total_count")
        if isinstance(repository_actions, dict)
        else None
    )
    if not isinstance(action_run_count, int) or action_run_count < 0:
        action_run_count = None

    confounded = (
        isinstance(clone_count, int)
        and clone_count > 0
        and isinstance(action_run_count, int)
        and action_run_count > 0
    )
    return {
        "repository_action_runs": action_run_count,
        "repository_action_runs_error": repository_actions_error,
        "clone_signal_state": (
            "confounded_by_repository_actions"
            if confounded
            else "external_attribution_unavailable"
        ),
        "external_unique_cloners": None,
        "note": (
            "GitHub's aggregate clone endpoint does not identify clone "
            "sources. Repository-owned workflow runs can check out the "
            "repository, so clone totals and uniques are not treated as "
            "external visitors, installs, users, or adoption. They remain "
            "directional infrastructure diagnostics only."
        ),
    }


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


def optional_profile_card_references(
    token: str | None,
) -> tuple[int | None, str | None]:
    query = urlencode({"q": PROFILE_CARD_REFERENCE_QUERY, "per_page": 1})
    try:
        value = github_url_json(f"{API_ROOT}/search/code?{query}", token)
        return code_search_total_count(value), None
    except GrowthError as exc:
        return None, str(exc)


def external_text(
    url: str,
    max_bytes: int = MAX_EXTERNAL_STATUS_BYTES,
) -> str:
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
            body = response.read(max_bytes + 1)
    except (HTTPError, URLError, TimeoutError) as exc:
        raise GrowthError(f"External status request failed: {exc}") from exc
    if len(body) > max_bytes:
        raise GrowthError(
            f"External status response exceeded {max_bytes} bytes"
        )
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
    try:
        agent_skills = json.loads(documents.get("agent_skills", ""))
    except json.JSONDecodeError:
        agent_skills = {}
    skills = (
        agent_skills.get("skills", [])
        if isinstance(agent_skills, dict)
        else []
    )
    skill = skills[0] if len(skills) == 1 else {}
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
        "agent_skills_exposes_digest_bound_archive": (
            isinstance(agent_skills, dict)
            and agent_skills.get("$schema")
            == "https://schemas.agentskills.io/discovery/0.2.0/schema.json"
            and isinstance(skill, dict)
            and skill.get("name") == "find-complementary-founders"
            and skill.get("type") == "archive"
            and skill.get("url") == "find-complementary-founders.zip"
            and isinstance(skill.get("digest"), str)
            and re.fullmatch(r"sha256:[0-9a-f]{64}", skill["digest"])
            is not None
        ),
    }
    return {
        "site_url": FINDMATE_SITE_URL,
        "endpoint_urls": WEB_DISCOVERY_URLS,
        "live": all(checks.values()) if not errors else None,
        "checks": checks,
        "errors": errors,
        "note": (
            "Live means only that five bounded public documents expose the "
            "expected canonical, own-owner, and digest-bound Agent Skills "
            "discovery contract. It does not prove indexing, a visit, an "
            "agent read, an install, a profile submission, or a star."
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


def summarize_agent_plugins_directory(
    issue: object | None,
    issue_error: str | None,
    pull_request: object | None,
    pull_request_error: str | None,
    catalog: object | None,
    catalog_error: str | None,
) -> dict:
    summary = {
        "repository": AGENT_PLUGINS_REPOSITORY,
        "submission_issue": AGENT_PLUGINS_SUBMISSION_ISSUE,
        "submission_url": (
            f"https://github.com/{AGENT_PLUGINS_REPOSITORY}/issues/"
            f"{AGENT_PLUGINS_SUBMISSION_ISSUE}"
        ),
        "submission_state": "unavailable",
        "integration_pull_request": AGENT_PLUGINS_PULL_REQUEST,
        "integration_pull_request_url": (
            f"https://github.com/{AGENT_PLUGINS_REPOSITORY}/pull/"
            f"{AGENT_PLUGINS_PULL_REQUEST}"
        ),
        "integration_pull_request_state": "unavailable",
        "integration_pull_request_merged_at": None,
        "catalog_url": AGENT_PLUGINS_CATALOG_URL,
        "catalog_skill_count": None,
        "listed": None,
        "state": "unavailable",
        "source_commit_sha": None,
        "errors": [
            error
            for error in (
                issue_error,
                pull_request_error,
                catalog_error,
            )
            if isinstance(error, str)
        ],
        "note": (
            "A submission issue is not a listing. Listed means the public "
            "daily catalog contains the exact skill name, canonical FindMate "
            "repository, expected skill path, and a 40-character source "
            "commit. It does not prove an install, agent read, owner opt-in, "
            "profile, match, or star."
        ),
    }
    if isinstance(issue, dict):
        issue_state = issue.get("state")
        if issue_state in {"open", "closed"}:
            summary["submission_state"] = issue_state
    if isinstance(pull_request, dict):
        pull_request_state = pull_request.get("state")
        merged_at = pull_request.get("merged_at")
        if isinstance(merged_at, str) and merged_at:
            summary["integration_pull_request_state"] = "merged"
            summary["integration_pull_request_merged_at"] = merged_at
        elif pull_request_state in {"open", "closed"}:
            summary["integration_pull_request_state"] = pull_request_state

    if not isinstance(catalog, dict):
        return summary
    skills = catalog.get("skills")
    if not isinstance(skills, list):
        summary["errors"].append(
            "Agent Plugins catalog lacks a skills array"
        )
        return summary
    summary["catalog_skill_count"] = len(skills)
    named_entries = [
        item
        for item in skills
        if isinstance(item, dict)
        and item.get("name") == "find-complementary-founders"
    ]
    expected_source = AGENT_PLUGINS_EXPECTED_SOURCE.rstrip("/").casefold()
    canonical_entry = None
    for item in named_entries:
        source = item.get("source")
        source_repo = source.get("repo") if isinstance(source, dict) else None
        normalized_source = (
            source_repo.rstrip("/").removesuffix(".git").casefold()
            if isinstance(source_repo, str)
            else None
        )
        if normalized_source == expected_source:
            canonical_entry = item
            break

    if canonical_entry is None:
        summary["listed"] = False
        if named_entries:
            summary["state"] = "name_conflict"
        elif summary["integration_pull_request_state"] == "merged":
            summary["state"] = "merged_pending_catalog"
        elif summary["integration_pull_request_state"] == "open":
            summary["state"] = "integration_pr_open"
        elif summary["integration_pull_request_state"] == "closed":
            summary["state"] = "integration_pr_closed_not_listed"
        elif summary["submission_state"] == "open":
            summary["state"] = "submission_open"
        elif summary["submission_state"] == "closed":
            summary["state"] = "submission_closed_not_listed"
        else:
            summary["state"] = "not_listed"
        return summary

    source = canonical_entry.get("source")
    source_path = source.get("path") if isinstance(source, dict) else None
    source_sha = (
        source.get("commit_sha") if isinstance(source, dict) else None
    )
    if isinstance(source_sha, str):
        summary["source_commit_sha"] = source_sha
    valid_sha = (
        isinstance(source_sha, str)
        and re.fullmatch(r"[0-9a-fA-F]{40}", source_sha) is not None
    )
    if source_path == AGENT_PLUGINS_EXPECTED_PATH and valid_sha:
        summary["listed"] = True
        summary["state"] = "listed_expected_source"
    else:
        summary["listed"] = False
        summary["state"] = "canonical_source_unverified"
    return summary


def optional_agent_plugins_directory(
    issue: object | None,
    issue_error: str | None,
    pull_request: object | None,
    pull_request_error: str | None,
) -> dict:
    try:
        catalog = external_json(
            AGENT_PLUGINS_CATALOG_URL,
            MAX_AGENT_PLUGINS_CATALOG_BYTES,
        )
        return summarize_agent_plugins_directory(
            issue,
            issue_error,
            pull_request,
            pull_request_error,
            catalog,
            None,
        )
    except GrowthError as exc:
        return summarize_agent_plugins_directory(
            issue,
            issue_error,
            pull_request,
            pull_request_error,
            None,
            str(exc),
        )


def summarize_agent_skill_index(
    readme: str | None,
    error: str | None,
) -> dict:
    listed = (
        AGENT_SKILL_INDEX_EXPECTED_LINK in readme
        if isinstance(readme, str)
        else None
    )
    return {
        "repository": "heilcheng/awesome-agent-skills",
        "readme_url": AGENT_SKILL_INDEX_README_URL,
        "listed": listed,
        "state": (
            "listed_expected_source"
            if listed is True
            else "not_listed"
            if listed is False
            else "unavailable"
        ),
        "error": error,
        "note": (
            "Listed means the upstream main README contains the exact "
            "canonical FindMate skill link. An open or mergeable pull request "
            "is not a listing, install, owner opt-in, profile, match, or star."
        ),
    }


def optional_agent_skill_index() -> dict:
    try:
        readme = external_text(
            AGENT_SKILL_INDEX_README_URL,
            MAX_AGENT_SKILL_INDEX_BYTES,
        )
        return summarize_agent_skill_index(readme, None)
    except GrowthError as exc:
        return summarize_agent_skill_index(None, str(exc))


def summarize_aas_core_release(
    release: object | None,
    release_error: str | None,
    skill_file: object | None,
    skill_error: str | None,
) -> dict:
    summary = {
        "repository": AAS_CORE_REPOSITORY,
        "skill_path": AAS_CORE_SKILL_PATH,
        "latest_tag": None,
        "latest_url": None,
        "included": None,
        "state": "unavailable",
        "error": release_error,
        "note": (
            "A merged catalog pull request is not counted as released "
            "availability. Included means the exact canonical-source "
            "attribution exists at the latest published AAS release tag."
        ),
    }
    if not isinstance(release, dict):
        return summary
    tag = release.get("tag_name")
    url = release.get("html_url")
    if not isinstance(tag, str) or not tag:
        summary["error"] = "AAS latest release lacks tag_name"
        return summary
    summary["latest_tag"] = tag
    if isinstance(url, str):
        summary["latest_url"] = url

    if skill_error:
        if "HTTP Error 404" in skill_error:
            summary["included"] = False
            summary["state"] = "not_in_latest_release"
            summary["error"] = None
        else:
            summary["error"] = skill_error
        return summary
    if not isinstance(skill_file, dict):
        summary["error"] = "AAS release skill response must be an object"
        return summary
    if skill_file.get("type") != "file":
        summary["error"] = "AAS release skill path is not a file"
        return summary
    size = skill_file.get("size")
    encoded = skill_file.get("content")
    if (
        not isinstance(size, int)
        or size < 0
        or size > MAX_AAS_SKILL_BYTES
    ):
        summary["error"] = "AAS release skill size is invalid"
        return summary
    if skill_file.get("encoding") != "base64" or not isinstance(encoded, str):
        summary["error"] = "AAS release skill content is not base64"
        return summary
    try:
        decoded = base64.b64decode(
            encoded.replace("\n", ""),
            validate=True,
        ).decode("utf-8")
    except (binascii.Error, UnicodeError, ValueError) as exc:
        summary["error"] = f"AAS release skill content is invalid: {exc}"
        return summary
    if len(decoded.encode("utf-8")) != size:
        summary["error"] = "AAS release skill size does not match content"
        return summary

    canonical = (
        "name: find-complementary-founders" in decoded
        and AAS_CORE_EXPECTED_SOURCE in decoded
    )
    summary["included"] = canonical
    summary["state"] = (
        "included_expected_source"
        if canonical
        else "unexpected_source"
    )
    summary["error"] = None
    return summary


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


def moltbook_comment_nodes(response: object) -> tuple[list[dict], bool]:
    if not isinstance(response, dict):
        return [], False
    comments = response.get("comments")
    if not isinstance(comments, list):
        return [], False

    nodes: list[dict] = []
    seen_ids: set[str] = set()
    stack = list(reversed(comments))
    truncated = False
    while stack:
        if len(nodes) >= MAX_MOLTBOOK_COMMENT_NODES:
            truncated = True
            break
        node = stack.pop()
        if not isinstance(node, dict):
            continue
        comment_id = node.get("id")
        if not isinstance(comment_id, str) or not comment_id:
            continue
        if comment_id in seen_ids:
            continue
        seen_ids.add(comment_id)
        nodes.append(node)
        replies = node.get("replies")
        if isinstance(replies, list):
            stack.extend(reversed(replies))
    return nodes, truncated


def summarize_moltbook_owner_pool(
    response: object | None,
    error: str | None,
) -> dict:
    summary = {
        "thread_url": MOLTBOOK_THREAD_URL,
        "available": None,
        "state": "unavailable",
        "comment_nodes": None,
        "marked_own_owner_submissions": None,
        "external_current_marked_own_owner_submissions": None,
        "external_rejected_or_expired_markers": None,
        "eligible_external_profiles": None,
        "truncated": False,
        "error": error,
        "note": (
            "The monitor reads only the fixed canonical thread, treats all "
            "content as untrusted data, and discards comment text, authors, "
            "profile URLs, and hashes after aggregate classification. A "
            "current external marker is not called eligible until its linked "
            "profile passes local schema, hash, consent, and expiry validation."
        ),
    }
    if not isinstance(response, dict):
        return summary
    if response.get("success") is not True:
        summary["error"] = "Moltbook response did not report success"
        return summary

    nodes, truncated = moltbook_comment_nodes(response)
    if not isinstance(response.get("comments"), list):
        summary["error"] = "Moltbook response lacks a comments array"
        return summary

    today = datetime.now(timezone.utc).date()
    marked = 0
    external_current = 0
    external_rejected = 0
    for node in nodes:
        content = node.get("content")
        if (
            not isinstance(content, str)
            or not content.startswith(f"{PROFILE_REPLY_MARKER}\n")
        ):
            continue
        author = node.get("author")
        author_id = author.get("id") if isinstance(author, dict) else None
        is_external = (
            isinstance(author_id, str)
            and author_id
            and author_id != MOLTBOOK_HOST_AGENT_ID
        )
        structurally_marked = (
            "I represent my own owner." in content
            and "I ran FindMate only on that owner" in content
            and "the owner approved this expiring public profile" in content
            and MOLTBOOK_PROFILE_URL_PATTERN.search(content) is not None
            and MOLTBOOK_PROFILE_HASH_PATTERN.search(content) is not None
        )
        expiry_match = MOLTBOOK_PROFILE_EXPIRY_PATTERN.search(content)
        expires_on = None
        if expiry_match:
            try:
                expires_on = datetime.strptime(
                    expiry_match.group(1),
                    "%Y-%m-%d",
                ).date()
            except ValueError:
                expires_on = None
        current = (
            structurally_marked
            and expires_on is not None
            and expires_on >= today
            and node.get("is_deleted") is not True
            and node.get("is_spam") is not True
        )
        if structurally_marked:
            marked += 1
        if not is_external:
            continue
        if current:
            external_current += 1
        else:
            external_rejected += 1

    summary.update(
        {
            "available": True,
            "state": (
                "empty"
                if external_current == 0
                else "external_markers_require_local_validation"
            ),
            "comment_nodes": len(nodes),
            "marked_own_owner_submissions": marked,
            "external_current_marked_own_owner_submissions": external_current,
            "external_rejected_or_expired_markers": external_rejected,
            "eligible_external_profiles": 0 if external_current == 0 else None,
            "truncated": truncated,
            "error": None,
        }
    )
    if truncated:
        summary["state"] = "truncated"
        summary["eligible_external_profiles"] = None
    return summary


def optional_moltbook_owner_pool() -> dict:
    try:
        response = external_json(
            MOLTBOOK_THREAD_API_URL,
            MAX_MOLTBOOK_THREAD_BYTES,
        )
        return summarize_moltbook_owner_pool(response, None)
    except GrowthError as exc:
        return summarize_moltbook_owner_pool(None, str(exc))


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
    repository_actions: object | None = None,
    repository_actions_error: str | None = None,
    github_thread_comments: list | None = None,
    github_thread_error: str | None = None,
    moltbook_owner_pool: dict | None = None,
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
            "provenance": summarize_traffic_provenance(
                clones,
                repository_actions,
                repository_actions_error,
            ),
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
            "moltbook": (
                moltbook_owner_pool
                if moltbook_owner_pool is not None
                else summarize_moltbook_owner_pool(
                    None,
                    "Moltbook measurement was not supplied",
                )
            ),
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
        actions_window_start = (
            datetime.now(timezone.utc).date() - timedelta(days=13)
        ).isoformat()
        repository_actions, repository_actions_error = optional_github_json(
            args.repository,
            (
                "/actions/runs?per_page=1&created="
                f"{quote(f'>={actions_window_start}', safe='')}"
            ),
            token,
        )
        github_comments, github_thread_error = optional_github_json(
            args.repository,
            "/issues/2/comments?per_page=100",
            token,
        )
        moltbook_owner_pool = optional_moltbook_owner_pool()
        skills_sh_listed, skills_sh_error = optional_skills_sh_listing()
        skill_search_indexed, skill_search_error = optional_skill_search_index(
            token
        )
        action_references, action_references_error = (
            optional_github_action_references(token)
        )
        card_references, card_references_error = (
            optional_profile_card_references(token)
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
        agent_plugins_issue, agent_plugins_issue_error = optional_github_json(
            AGENT_PLUGINS_REPOSITORY,
            f"/issues/{AGENT_PLUGINS_SUBMISSION_ISSUE}",
            token,
        )
        agent_plugins_pr, agent_plugins_pr_error = optional_github_json(
            AGENT_PLUGINS_REPOSITORY,
            f"/pulls/{AGENT_PLUGINS_PULL_REQUEST}",
            token,
        )
        agent_plugins_directory = optional_agent_plugins_directory(
            agent_plugins_issue,
            agent_plugins_issue_error,
            agent_plugins_pr,
            agent_plugins_pr_error,
        )
        agent_skill_index = optional_agent_skill_index()
        aas_release, aas_release_error = optional_github_json(
            AAS_CORE_REPOSITORY,
            "/releases/latest",
            token,
        )
        aas_skill_file: object | None = None
        aas_skill_error: str | None = None
        if isinstance(aas_release, dict):
            aas_tag = aas_release.get("tag_name")
            if isinstance(aas_tag, str) and aas_tag:
                aas_skill_file, aas_skill_error = optional_github_json(
                    AAS_CORE_REPOSITORY,
                    (
                        f"/contents/{AAS_CORE_SKILL_PATH}"
                        f"?ref={quote(aas_tag, safe='')}"
                    ),
                    token,
                )
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
            repository_actions=repository_actions,
            repository_actions_error=repository_actions_error,
            github_thread_comments=(
                github_comments if isinstance(github_comments, list) else None
            ),
            github_thread_error=github_thread_error,
            moltbook_owner_pool=moltbook_owner_pool,
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
                "public_profile_card_references": {
                    "count": card_references,
                    "query": PROFILE_CARD_REFERENCE_QUERY,
                    "error": card_references_error,
                    "note": (
                        "Aggregate public markers in the documented Markdown "
                        "card output only, so copied generator source is not "
                        "counted. Code-search items, repository names, owner "
                        "identities, card contents, and profile data are "
                        "discarded."
                    ),
                },
                "release_supply_chain": summarize_release_supply_chain(
                    latest_release,
                    latest_release_error,
                    repository_rulesets,
                    repository_rulesets_error,
                ),
                "claude_community": claude_community,
                "agent_plugins_directory": agent_plugins_directory,
                "agent_skill_index": agent_skill_index,
                "aas_core_release": summarize_aas_core_release(
                    aas_release,
                    aas_release_error,
                    aas_skill_file,
                    aas_skill_error,
                ),
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
