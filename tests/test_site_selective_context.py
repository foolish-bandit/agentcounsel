#!/usr/bin/env python3
"""Catalog coverage for skills with selectable execution resources."""

from __future__ import annotations

import html
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SITE_PUBLIC = REPO_ROOT / "site" / "public"


class TestSiteSelectiveContext(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        subprocess.run(
            ["node", "site/generate.mjs"],
            cwd=REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
        )

    def _page(self, area: str, slug: str) -> str:
        return (SITE_PUBLIC / "skills" / area / f"{slug}.html").read_text(
            encoding="utf-8"
        )

    def test_modularized_skill_page_exposes_complete_execution_package(self):
        page = html.unescape(self._page("ip", "infringement-triage"))
        self.assertIn("Selective execution package", page)
        self.assertIn("Copy Core Skill", page)
        self.assertIn("Copy Full Package", page)
        self.assertIn("skills/ip/infringement-triage/SPEC.json", page)
        self.assertIn("Module: trademark", page)
        self.assertIn("BEGIN AGENTCOUNSEL SPEC", page)
        self.assertIn("BEGIN AGENTCOUNSEL MODULE: trademark", page)
        self.assertIn(
            "evaluate each module's machine-readable activation object exactly",
            page,
        )

    def test_one_off_prompt_for_custom_skill_includes_contract_and_resources(self):
        page = html.unescape(self._page("litigation", "motion-opposition-drafter"))
        self.assertIn("BEGIN AGENTCOUNSEL SPEC", page)
        self.assertIn("BEGIN AGENTCOUNSEL MODULE: motion-deconstruction", page)
        self.assertIn("Missing activation inputs fail closed", page)

    def test_legacy_skill_keeps_simple_copy_experience(self):
        page = html.unescape(self._page("corporate", "board-minutes"))
        self.assertIn("Copy Full Skill", page)
        self.assertNotIn("Copy Full Package", page)
        self.assertNotIn("Selective execution package", page)

    def test_platform_guidance_distinguishes_core_from_complete_package(self):
        page = html.unescape(
            (SITE_PUBLIC / "platforms" / "chatgpt-projects.html").read_text(
                encoding="utf-8"
            )
        )
        self.assertIn("Copy Full Package", page)
        self.assertIn("Copy Core Skill", page)
        self.assertIn("quick triage", page)


if __name__ == "__main__":
    unittest.main()
