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
GROWTH = ROOT / "growth"
EXAMPLES = ROOT / "examples"
RUSSIAN_ONBOARDING = ROOT / "docs" / "locales" / "ru" / "owner-onboarding.md"


def load_module(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, SCRIPTS / filename)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


assess = load_module("assess_profile", "assess_profile.py")
matcher = load_module("match_profiles", "match_profiles.py")
publisher = load_module("moltbook_publish", "moltbook_publish.py")
profile_card = load_module("profile_card", "profile_card.py")


def load_path_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


growth = load_path_module("growth_measure", GROWTH / "measure.py")
demo = load_path_module("synthetic_demo", EXAMPLES / "run_synthetic_demo.py")


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

    def test_profile_reply_is_explicitly_self_published(self):
        profile, _ = assess.build_profiles(owner_input())
        content = publisher.render_profile_reply(
            profile,
            "https://github.com/example/project/profile.public.json",
        )
        self.assertTrue(content.startswith("FINDMATE_OWNER_PROFILE_V1\n"))
        self.assertIn("I represent my own owner", content)
        self.assertIn("the owner approved", content)
        self.assertIn("https://github.com/merc1305/findMate", content)
        self.assertRegex(content, r"Canonical profile SHA-256: [0-9a-f]{64}")
        self.assertNotIn("Private detail", content)

    def test_general_moltbook_search_is_not_a_matching_command(self):
        self.assertFalse(hasattr(publisher, "search"))
        self.assertTrue(hasattr(publisher, "read_thread"))

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


class ProfileCardTests(unittest.TestCase):
    def test_card_is_deterministic_and_omits_contact_and_evidence(self):
        profile, _ = assess.build_profiles(owner_input())
        first = profile_card.render_card(profile)
        second = profile_card.render_card(profile)
        self.assertEqual(first, second)
        self.assertIn(profile_card.CARD_MARKER, first)
        self.assertIn("owner-one", first)
        self.assertIn("0→1", first)
        self.assertIn("go-to-market", first)
        self.assertIn("Canonical profile SHA-256", first)
        self.assertIn(profile_card.PROTOCOL_URL, first)
        self.assertNotIn(profile["contact"]["url"], first)
        self.assertNotIn("Published a working developer tool", first)

    def test_secret_like_text_is_rejected(self):
        profile, _ = assess.build_profiles(owner_input())
        profile["alias"] = "ghp_1234567890abcdefghijkl"
        with self.assertRaises(profile_card.CardError):
            profile_card.render_card(profile)

    def test_expired_profile_is_rejected(self):
        profile, _ = assess.build_profiles(owner_input())
        profile["expires_on"] = "2000-01-01"
        with self.assertRaises(profile_card.CardError):
            profile_card.render_card(profile)


class GrowthLoopTests(unittest.TestCase):
    def test_active_promotion_stops_only_above_one_hundred(self):
        self.assertTrue(growth.promotion_state(100, 100)["active_promotion"])
        state = growth.promotion_state(101, 100)
        self.assertFalse(state["active_promotion"])
        self.assertTrue(state["stopped"])
        self.assertEqual(state["stars_until_stop"], 0)

    def test_strategy_portfolio_is_valid_and_nontrivial(self):
        config = growth.read_object(GROWTH / "strategies.json")
        growth.validate_strategy_config(config)
        self.assertGreaterEqual(len(config["experiments"]), 10)
        self.assertIn(
            "Never star the repository before the authenticated owner explicitly authorizes that public action.",
            config["guardrails"],
        )
        observation_log = growth.read_object(GROWTH / "observations.json")
        observations = observation_log["observations"]
        self.assertGreaterEqual(len(observations), 2)
        self.assertEqual(observations[0]["metric"]["delta"], 1)
        self.assertIn("not_supported", observations[0])

    def test_synthetic_demo_produces_reciprocal_match(self):
        result = demo.run_demo()
        self.assertEqual(result["owner_alias"], "synthetic-builder")
        self.assertGreater(result["match"]["score"], 70)
        self.assertIn(
            "covers capability gap: go_to_market",
            result["match"]["reasons"],
        )
        self.assertIn("synthetic; no owner data", result["demo"])


class LocaleDocsTests(unittest.TestCase):
    def test_russian_onboarding_preserves_protocol_and_consent_boundaries(self):
        content = RUSSIAN_ONBOARDING.read_text(encoding="utf-8")
        self.assertIn("FINDMATE_OWNER_PROFILE_V1", content)
        self.assertIn("да, оба действия", content)
        self.assertIn("только публикация", content)
        self.assertIn("отмена", content)
        self.assertIn("yes to both", content)
        self.assertIn("publish only", content)
        self.assertIn("cancel", content)
        self.assertIn("только своего владельца", content)
        self.assertIn("отдельное согласие обоих людей", content)
        self.assertIn("101 и более звёздах", content)


if __name__ == "__main__":
    unittest.main()
