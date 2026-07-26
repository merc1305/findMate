from __future__ import annotations

import importlib.util
import shutil
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PACKAGER_PATH = ROOT / "tools" / "build_skill_archive.py"
CANONICAL_SKILL = ROOT / "skills" / "find-complementary-founders"
PROJECT_SKILL = ROOT / ".agents" / "skills" / "find-complementary-founders"

spec = importlib.util.spec_from_file_location("build_skill_archive", PACKAGER_PATH)
packager = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(packager)


class SkillArchiveTests(unittest.TestCase):
    def test_build_is_deterministic_and_matches_canonical_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            directory = Path(temporary)
            first = directory / "first.skill.zip"
            second = directory / "second.skill.zip"

            first_result = packager.build_archive(CANONICAL_SKILL, first)
            second_result = packager.build_archive(CANONICAL_SKILL, second)

            self.assertEqual(first.read_bytes(), second.read_bytes())
            self.assertEqual(first_result["sha256"], second_result["sha256"])
            self.assertEqual(first_result["files"], len(packager.EXPECTED_FILES))
            self.assertLess(first_result["bytes"], packager.MAX_ARCHIVE_BYTES)

            with zipfile.ZipFile(first, "r") as bundle:
                self.assertEqual(
                    bundle.namelist(),
                    [
                        f"{packager.ARCHIVE_ROOT}/{name}"
                        for name in packager.EXPECTED_FILES
                    ],
                )
                self.assertNotIn("__pycache__", "\n".join(bundle.namelist()))

    def test_unexpected_source_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as temporary:
            copied = Path(temporary) / "skill"
            shutil.copytree(CANONICAL_SKILL, copied)
            (copied / "owner.private.json").write_text(
                '{"must_not_ship": true}\n',
                encoding="utf-8",
            )

            with self.assertRaisesRegex(
                packager.ArchiveError,
                "unexpected=.*owner.private.json",
            ):
                packager.build_archive(copied, Path(temporary) / "blocked.zip")

    def test_project_entry_points_to_one_canonical_skill_directory(self):
        self.assertTrue(PROJECT_SKILL.is_symlink())
        self.assertEqual(PROJECT_SKILL.resolve(), CANONICAL_SKILL.resolve())


if __name__ == "__main__":
    unittest.main()
