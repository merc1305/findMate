"""Build and verify the portable FindMate Agent Skill archive.

The archive is deliberately stored rather than compressed so its bytes are
reproducible across zlib versions. It contains one top-level skill directory
and an explicit allowlist of public, tracked files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = REPOSITORY_ROOT / "skills" / "find-complementary-founders"
ARCHIVE_ROOT = "find-complementary-founders"
FIXED_ZIP_TIME = (1980, 1, 1, 0, 0, 0)
MAX_ARCHIVE_BYTES = 512 * 1024
EXPECTED_FILES = (
    "LICENSE.txt",
    "SKILL.md",
    "agents/openai.yaml",
    "references/community-growth.md",
    "references/evidence-model.md",
    "references/moltbook.md",
    "references/owner-onboarding.ru.md",
    "references/privacy-safety.md",
    "references/profile-schema.md",
    "scripts/assess_profile.py",
    "scripts/github_thread.py",
    "scripts/match_profiles.py",
    "scripts/moltbook_publish.py",
    "scripts/private_report.py",
    "scripts/profile_card.py",
    "scripts/validate_profile.py",
    "scripts/verify_github_submission.py",
)
IGNORED_DIRECTORY_NAMES = {"__pycache__"}


class ArchiveError(ValueError):
    """Raised when a skill source or archive violates the package contract."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(64 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _source_files(source: Path) -> dict[str, Path]:
    if not source.is_dir():
        raise ArchiveError(f"Skill source is not a directory: {source}")

    discovered: dict[str, Path] = {}
    for path in sorted(source.rglob("*")):
        relative = path.relative_to(source)
        if any(part in IGNORED_DIRECTORY_NAMES for part in relative.parts):
            continue
        if path.is_symlink():
            raise ArchiveError(f"Symlinks are not allowed in the archive: {relative}")
        if path.is_dir():
            continue
        if not path.is_file():
            raise ArchiveError(f"Unsupported source entry: {relative}")
        discovered[relative.as_posix()] = path

    expected = set(EXPECTED_FILES)
    actual = set(discovered)
    missing = sorted(expected - actual)
    unexpected = sorted(actual - expected)
    if missing or unexpected:
        details = []
        if missing:
            details.append(f"missing={missing}")
        if unexpected:
            details.append(f"unexpected={unexpected}")
        raise ArchiveError("Skill package allowlist mismatch: " + ", ".join(details))
    return discovered


def _safe_member_name(name: str) -> bool:
    path = PurePosixPath(name)
    return (
        not path.is_absolute()
        and ".." not in path.parts
        and len(path.parts) >= 2
        and path.parts[0] == ARCHIVE_ROOT
        and not name.endswith("/")
    )


def verify_archive(archive: Path, source: Path = DEFAULT_SOURCE) -> dict[str, object]:
    if not archive.is_file():
        raise ArchiveError(f"Archive does not exist: {archive}")
    archive_size = archive.stat().st_size
    if archive_size > MAX_ARCHIVE_BYTES:
        raise ArchiveError(f"Archive exceeds {MAX_ARCHIVE_BYTES} bytes: {archive_size}")

    source_files = _source_files(source)
    expected_members = {f"{ARCHIVE_ROOT}/{relative}" for relative in EXPECTED_FILES}
    with zipfile.ZipFile(archive, "r") as bundle:
        entries = bundle.infolist()
        names = [entry.filename for entry in entries]
        if len(names) != len(set(names)):
            raise ArchiveError("Archive contains duplicate member names")
        if any(not _safe_member_name(name) for name in names):
            raise ArchiveError("Archive contains an unsafe member path")
        if set(names) != expected_members:
            raise ArchiveError("Archive member allowlist does not match the skill")

        for entry in entries:
            mode = entry.external_attr >> 16
            if stat.S_IFMT(mode) != stat.S_IFREG or stat.S_IMODE(mode) != 0o644:
                raise ArchiveError(
                    f"Archive member must be a regular 0644 file: {entry.filename}"
                )
            if entry.date_time != FIXED_ZIP_TIME:
                raise ArchiveError(
                    f"Archive member has a non-deterministic timestamp: {entry.filename}"
                )
            if entry.compress_type != zipfile.ZIP_STORED:
                raise ArchiveError(
                    f"Archive member must use deterministic stored mode: {entry.filename}"
                )
            relative = PurePosixPath(entry.filename).relative_to(ARCHIVE_ROOT)
            source_bytes = source_files[relative.as_posix()].read_bytes()
            if bundle.read(entry) != source_bytes:
                raise ArchiveError(
                    f"Archive member differs from canonical source: {entry.filename}"
                )

    return {
        "archive": str(archive),
        "bytes": archive_size,
        "files": len(expected_members),
        "sha256": sha256_file(archive),
        "verified": True,
    }


def build_archive(source: Path, output: Path) -> dict[str, object]:
    source_files = _source_files(source)
    output = output.resolve()
    output.parent.mkdir(parents=True, exist_ok=True)

    descriptor, temporary_name = tempfile.mkstemp(
        prefix=f".{output.name}.",
        suffix=".tmp",
        dir=output.parent,
    )
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        with zipfile.ZipFile(
            temporary,
            "w",
            compression=zipfile.ZIP_STORED,
            allowZip64=False,
        ) as bundle:
            for relative in EXPECTED_FILES:
                info = zipfile.ZipInfo(
                    f"{ARCHIVE_ROOT}/{relative}",
                    date_time=FIXED_ZIP_TIME,
                )
                info.create_system = 3
                info.compress_type = zipfile.ZIP_STORED
                info.external_attr = (stat.S_IFREG | 0o644) << 16
                bundle.writestr(info, source_files[relative].read_bytes())
        os.replace(temporary, output)
    finally:
        temporary.unlink(missing_ok=True)

    return verify_archive(output, source)


def write_checksum(path: Path, digest: str, archive_name: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(f"{digest}  {archive_name}\n", encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Build or verify the portable FindMate Agent Skill archive."
    )
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument("--output", type=Path, help="Archive path to build")
    action.add_argument("--verify", type=Path, help="Existing archive to verify")
    parser.add_argument(
        "--source",
        type=Path,
        default=DEFAULT_SOURCE,
        help="Canonical skill directory",
    )
    parser.add_argument(
        "--checksum-output",
        type=Path,
        help="Optional sha256sum-compatible checksum file",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    if args.output:
        result = build_archive(args.source, args.output)
        archive = args.output.resolve()
    else:
        result = verify_archive(args.verify, args.source)
        archive = args.verify.resolve()

    if args.checksum_output:
        write_checksum(args.checksum_output, str(result["sha256"]), archive.name)
        result["checksum"] = str(args.checksum_output.resolve())
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
