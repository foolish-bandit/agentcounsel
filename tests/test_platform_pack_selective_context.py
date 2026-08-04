#!/usr/bin/env python3
"""Tests that platform packs preserve selectively loaded skill resources."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_platform_packs as packs  # noqa: E402


class TestSelectiveContextPacks(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        packs.errors.clear()
        cls.areas = packs.load_areas()
        cls.ip_info = cls.areas["ip"]
        cls.infringement = next(
            skill
            for skill in cls.ip_info["skills"]
            if skill["slug"] == "infringement-triage"
        )

    def test_archive_module_ids_must_be_flat_upload_safe_slugs(self):
        self.assertTrue(packs.is_safe_module_id("expanded-verification"))
        self.assertFalse(packs.is_safe_module_id("../expanded-verification"))
        self.assertFalse(packs.is_safe_module_id("module/name"))
        self.assertFalse(packs.is_safe_module_id("Module Name"))

    def test_loader_resolves_spec_and_all_declared_modules(self):
        self.assertEqual(
            self.infringement["spec_path"],
            "skills/ip/infringement-triage/SPEC.json",
        )
        self.assertEqual(
            [module["id"] for module in self.infringement["module_resources"]],
            [
                "factor-method",
                "trademark",
                "copyright",
                "patent",
                "trade-secret",
                "defenses-routing-output",
                "expanded-verification",
            ],
        )
        self.assertTrue(
            all(module["content"] for module in self.infringement["module_resources"])
        )

    def test_chatgpt_pack_contains_contract_activation_and_module_content(self):
        text = packs.chatgpt_pack("ip", self.ip_info, {})
        self.assertIn("Selective execution contracts and modules", text)
        self.assertIn('"operator": "contains-any"', text)
        self.assertIn("Missing activation inputs fail closed", text)
        self.assertIn("Modules without `activation` are not auto-selected", text)
        self.assertIn("true prompt-size reduction requires", text)
        self.assertIn("#" * 4 + " Module: patent", text)
        self.assertIn("preliminary read only, not formal claim construction", text)

    def test_gemini_source_contains_contract_and_modules(self):
        text = packs.gemini_skills_source(
            packs.area_name("ip"),
            self.ip_info,
        )
        self.assertIn("Contract: Infringement Triage", text)
        self.assertIn("Module: trade-secret", text)
        self.assertIn('"ip-rights-at-issue"', text)

    def test_claude_members_use_unique_descriptive_basenames(self):
        members = packs.claude_selective_context_members(self.infringement)
        names = [path.rsplit("/", 1)[-1] for path, _ in members]
        self.assertEqual(len(names), len(set(names)))
        self.assertIn("infringement-triage--SPEC.json", names)
        self.assertIn("infringement-triage--patent.md", names)
        self.assertIn("infringement-triage--expanded-verification.md", names)

    def test_pack_manifest_lists_specs_and_modules(self):
        registry = packs.build_pack_registry(self.areas)
        ip_pack = next(
            pack for pack in registry["packs"] if pack["pack_id"] == "chatgpt/ip"
        )
        self.assertIn(
            "skills/ip/infringement-triage/SPEC.json",
            ip_pack["included_skill_specs"],
        )
        self.assertIn(
            "skills/ip/infringement-triage/modules/patent.md",
            ip_pack["included_spec_resources"],
        )
        self.assertEqual(registry["schema_version"], "1.1")


if __name__ == "__main__":
    unittest.main()
