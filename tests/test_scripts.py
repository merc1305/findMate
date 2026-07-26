from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "find-complementary-founders" / "scripts"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


assess = load_module("assess_profile", "assess_profile.py")
matcher = load_module("match_profiles", "match_profiles.py")
publisher = load_module("moltbook_publish", "moltbook_publish.py")


def owner_input(alias: str = "owner-one") -> dict:
    today = datetime.now(timezone.utc).date()
    return {
        "alias": alias,
        "summary": "Technical product builder seeking a complementary operator.",
        "evidence": [
            {
                "id": "artifact-one",
                "kind": "shipped_artifact",
                "stages": ["zero_to_one"],
                "functions": ["product", "engineering"],
                "private_note": "Private detail that must not be published.",
                "share": True,
                "public_claim": "Published a working developer tool.",
                "public_proof": "https://github.com/example/tool-one",
            },
            {
                "id": "artifact-two",
                "kind": "shipped_artifact",
                "stages": ["zero_to_one"],
                "functions": ["product"],
                "private_note": "A second independent artifact.",
                "share": True,
                "public_claim": "Published a second working tool.",
                "public_proof": "https://github.com/example/tool-two",
            },
        ],
        "preferences": {
            "stages": ["zero_to_one"],
            "functions": ["product"],
        },
        "seeking": {
            "stages": ["one_to_ten"],
            "functions": ["go_to_market", "operations"],
            "project_themes": ["agent tools"],
            "collaboration_modes": ["project-partner"],
            "shared_principles": ["evidence over hype"],
        },
        "public_contact": {
            "type": "github_issues",
            "url": "https://github.com/example/project/issues",
        },
        "consent": {
            "public_profile": True,
            "approved_at": today.isoformat(),
            "expires_on": (today + timedelta(days=30)).isoformat(),
            "scope": "Public profile and inbound replies",
        },
    }


class AssessProfileTests(unittest.TestCase):
    def test_private_notes_do_not_enter_public_profile(self):
        public, private = assess.build_profiles(owner_input())
        self.assertEqual(
            public["stage_contributions"]["zero_to_one"]["level"], "strong"
        )
        self.assertNotIn("Private detail", json.dumps(public))
        self.assertIn("Private detail", json.dumps(private))

    def test_sensitive_public_text_is_rejected(self):
        value = owner_input()
        value["summary"] = "Contact me at owner@example.com"
        with self.assertRaises(assess.ProfileError):
            assess.build_profiles(value)

    def test_private_output_requires_private_suffix(self):
        public, private = assess.build_profiles(owner_input())
        self.assertIsNotNone(public)
        with (
            tempfile.TemporaryDirectory() as directory,
            self.assertRaises(assess.ProfileError),
        ):
            assess.write_json(Path(directory) / "private.json", private, private=True)


class MatchProfileTests(unittest.TestCase):
    def test_candidate_covering_gap_ranks_high(self):
        owner, _ = assess.build_profiles(owner_input())
        candidate_data = owner_input("operator-two")
        candidate_data["evidence"] = [
            {
                "id": "growth-outcome",
                "kind": "customer_outcome",
                "stages": ["one_to_ten"],
                "functions": ["go_to_market", "operations"],
                "private_note": "Built a repeatable sales and delivery loop.",
                "share": True,
                "public_claim": "Built a repeatable early-customer loop.",
                "public_proof": "https://github.com/example/operator-proof",
            },
            {
                "id": "ops-outcome",
                "kind": "operational_outcome",
                "stages": ["one_to_ten"],
                "functions": ["go_to_market", "operations"],
                "private_note": "Scaled reliable delivery.",
                "share": True,
                "public_claim": "Documented a reliable delivery system.",
                "public_proof": "https://github.com/example/ops-proof",
            },
        ]
        candidate_data["seeking"] = {
            "stages": ["zero_to_one"],
            "functions": ["product", "engineering"],
            "project_themes": ["agent tools"],
            "collaboration_modes": ["project-partner"],
            "shared_principles": ["evidence over hype"],
        }
        candidate, _ = assess.build_profiles(candidate_data)
        owner["_source_path"] = "owner.json"
        candidate["_source_path"] = "candidate.json"
        result = matcher.score_match(owner, candidate)
        self.assertGreater(result["score"], 70)
        self.assertIn("covers capability gap: go_to_market", result["reasons"])


class PublisherTests(unittest.TestCase):
    def test_exact_hash_approval(self):
        profile, _ = assess.build_profiles(owner_input())
        title, content = publisher.render_post(
            profile,
            "https://github.com/example/project/tree/agent/skill",
        )
        draft = publisher.build_draft(
            "create_post",
            "/posts",
            {"submolt": "founders", "title": title, "content": content},
        )
        publisher.validate_draft(draft, "create_post", draft["approval_hash"])
        with self.assertRaises(publisher.PublishError):
            publisher.validate_draft(draft, "create_post", "0" * 64)

    def test_local_socks_proxy_is_opt_in(self):
        with patch.dict("os.environ", {}, clear=True):
            self.assertIsNone(publisher.socks_proxy_from_env())
        with patch.dict(
            "os.environ",
            {"MOLTBOOK_SOCKS_PROXY": "socks5h://127.0.0.1:1080"},
            clear=True,
        ):
            self.assertEqual(
                publisher.socks_proxy_from_env(),
                ("127.0.0.1", 1080),
            )

    def test_non_loopback_proxy_is_rejected(self):
        unsafe_values = [
            "socks5h://proxy.example:1080",
            "socks5://127.0.0.1:1080",
            "socks5h://user:password@127.0.0.1:1080",
            "socks5h://127.0.0.1:99999",
        ]
        for value in unsafe_values:
            with (
                self.subTest(value=value),
                patch.dict(
                    "os.environ",
                    {"MOLTBOOK_SOCKS_PROXY": value},
                    clear=True,
                ),
                self.assertRaises(publisher.PublishError),
            ):
                publisher.socks_proxy_from_env()


if __name__ == "__main__":
    unittest.main()
