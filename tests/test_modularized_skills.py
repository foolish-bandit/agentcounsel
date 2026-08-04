#!/usr/bin/env python3
"""Regression tests for the first selectively modularized legal skills."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from build_skill_specs import collect_skill_specs  # noqa: E402
from skill_context import build_skill_context  # noqa: E402


class TestModularizedSkills(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        registry = collect_skill_specs(REPO_ROOT)
        cls.specs = {spec["skill_id"]: spec for spec in registry["skills"]}

    def _bundle(
        self,
        skill_id: str,
        mode: str,
        inputs: dict | None = None,
    ) -> dict:
        return build_skill_context(
            REPO_ROOT,
            self.specs[skill_id],
            mode,
            inputs or {},
        )

    @staticmethod
    def _module_ids(bundle: dict) -> list[str]:
        return [module["id"] for module in bundle["modules"]]

    @staticmethod
    def _deep_text(bundle: dict) -> str:
        parts = [bundle["core"]["content"]]
        parts.extend(module["content"] for module in bundle["modules"])
        return "\n".join(parts).casefold()

    def test_motion_opposition_loads_modules_by_mode(self):
        quick = self._bundle("litigation/motion-opposition-drafter", "quick-triage")
        standard = self._bundle("litigation/motion-opposition-drafter", "standard")
        deep = self._bundle("litigation/motion-opposition-drafter", "deep-review")

        self.assertEqual(self._module_ids(quick), [])
        self.assertEqual(
            self._module_ids(standard),
            ["motion-deconstruction", "opposition-drafting"],
        )
        self.assertEqual(
            self._module_ids(deep),
            [
                "motion-deconstruction",
                "opposition-drafting",
                "expanded-verification",
            ],
        )

    def test_motion_opposition_deep_bundle_preserves_material_obligations(self):
        text = self._deep_text(
            self._bundle("litigation/motion-opposition-drafter", "deep-review")
        )
        required_fragments = [
            "never invent counter-authority",
            "confirm current treatment",
            "every factual statement",
            "provided record",
            "never calculates",
            "do not file unreviewed",
            "flag weak counter-arguments honestly",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)

    def test_infringement_standard_loads_only_the_requested_right(self):
        bundle = self._bundle(
            "ip/infringement-triage",
            "standard",
            {"ip-rights-at-issue": ["trademark"]},
        )
        self.assertEqual(
            self._module_ids(bundle),
            ["factor-method", "trademark", "defenses-routing-output"],
        )

    def test_infringement_supports_multiple_rights_in_stable_order(self):
        bundle = self._bundle(
            "ip/infringement-triage",
            "standard",
            {"ip-rights-at-issue": ["trade-secret", "patent"]},
        )
        self.assertEqual(
            self._module_ids(bundle),
            [
                "factor-method",
                "patent",
                "trade-secret",
                "defenses-routing-output",
            ],
        )

    def test_infringement_missing_rights_fails_closed(self):
        bundle = self._bundle("ip/infringement-triage", "standard")
        self.assertEqual(
            self._module_ids(bundle),
            ["factor-method", "defenses-routing-output"],
        )
        self.assertEqual(
            [module["id"] for module in bundle["unresolved_modules"]],
            ["trademark", "copyright", "patent", "trade-secret"],
        )
        self.assertIn("ip-rights-at-issue", bundle["missing_required_inputs"])
        self.assertFalse(bundle["complete"])

    def test_infringement_deep_bundle_preserves_material_obligations(self):
        bundle = self._bundle(
            "ip/infringement-triage",
            "deep-review",
            {
                "ip-rights-at-issue": [
                    "trademark",
                    "copyright",
                    "patent",
                    "trade-secret",
                ]
            },
        )
        self.assertEqual(
            self._module_ids(bundle),
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
        text = self._deep_text(bundle)
        required_fragments = [
            "not a legal opinion on whether infringement",
            "does not perform a registry or docket search",
            "factor frameworks applied in this memo must be confirmed",
            "preliminary read only, not formal claim construction",
            "do not decide any affirmative defense",
            "no clock is computed",
            "routing signal, not an infringement finding",
        ]
        for fragment in required_fragments:
            with self.subTest(fragment=fragment):
                self.assertIn(fragment, text)


if __name__ == "__main__":
    unittest.main()
