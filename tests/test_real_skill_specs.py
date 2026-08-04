#!/usr/bin/env python3
"""Repository-level coverage for real Skill Specification v2 contracts."""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import build_skill_specs  # noqa: E402
from skill_spec_v2 import BASELINE_EVIDENCE_FIELDS, BASELINE_INHERITS  # noqa: E402


class TestRealSkillContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.data = build_skill_specs.collect_skill_specs(REPO_ROOT)
        cls.by_id = {item["skill_id"]: item for item in cls.data["skills"]}

    def test_every_canonical_skill_has_a_compiled_contract(self):
        self.assertEqual(self.data["skill_count"], 212)
        self.assertEqual(len(self.by_id), 212)
        self.assertEqual(self.data["custom_spec_count"], 5)
        self.assertEqual(self.data["legacy_compiled_count"], 207)
        self.assertEqual(
            self.data["custom_specs_by_practice_area"],
            {
                "contracts": 1,
                "ip": 1,
                "legal-research": 1,
                "litigation": 1,
                "privacy": 1,
            },
        )

    def test_all_contracts_preserve_baseline_safety_controls(self):
        for skill_id, spec in self.by_id.items():
            with self.subTest(skill_id=skill_id):
                self.assertEqual(spec["schema_version"], "2.0")
                self.assertTrue(set(BASELINE_INHERITS).issubset(spec["inherits"]))
                self.assertEqual(
                    spec["gates"]["missing_inputs"]["behavior"], "stop-and-ask"
                )
                self.assertTrue(spec["gates"]["attorney_review"]["required"])
                self.assertFalse(
                    spec["gates"]["deadline"]["calculation_allowed"]
                )
                self.assertTrue(
                    set(BASELINE_EVIDENCE_FIELDS).issubset(
                        spec["evidence_schema"]["required_fields"]
                    )
                )

    def test_custom_contracts_are_domain_specific(self):
        nda = self.by_id["contracts/nda-review"]
        research = self.by_id["legal-research/legal-research-memo"]
        breach = self.by_id["privacy/breach-response-workflow"]
        infringement = self.by_id["ip/infringement-triage"]
        opposition = self.by_id["litigation/motion-opposition-drafter"]

        for spec in (nda, research, breach, infringement, opposition):
            self.assertTrue(spec["has_custom_spec"])
            self.assertTrue(spec["spec_path"].endswith("/SPEC.json"))

        nda_inputs = {item["id"]: item for item in nda["input_schema"]}
        self.assertEqual(
            nda_inputs["clients-role-disclosing-receiving-or-mutual"]["type"],
            "enum",
        )
        self.assertIn("transaction-context", nda_inputs)
        self.assertTrue(
            any(module["id"] == "nda-risk-table-template" for module in nda["modules"])
        )

        research_outputs = {item["id"]: item for item in research["output_schema"]}
        self.assertEqual(
            research_outputs[
                "structured-legal-research-memo-using-irac-discipline-for-attorney-review"
            ]["type"],
            "memo",
        )
        self.assertIn("claim-authority-map", research_outputs)
        self.assertTrue(
            any(module["id"] == "courtlistener-connector-guide" for module in research["modules"])
        )

        self.assertEqual(
            breach["gates"]["escalation"]["minimum"],
            "immediate-attorney-attention",
        )
        breach_gate_ids = {gate["id"] for gate in breach["gates"]["custom"]}
        self.assertIn("reportability-conclusion-prohibited", breach_gate_ids)
        self.assertIn("deadline-calculation-prohibited", breach_gate_ids)
        self.assertFalse(breach["gates"]["deadline"]["calculation_allowed"])

        rights = {item["id"]: item for item in infringement["input_schema"]}
        self.assertEqual(rights["ip-rights-at-issue"]["type"], "string-list")
        self.assertEqual(len(infringement["context_scenarios"]), 6)
        self.assertEqual(len(opposition["context_scenarios"]), 3)
        self.assertTrue(
            any(module.get("activation") for module in infringement["modules"])
        )
        self.assertTrue(
            any(module.get("activation") for module in opposition["modules"])
        )

    def test_generated_registry_matches_live_compilation(self):
        generated = json.loads(
            (REPO_ROOT / "metadata" / "skill_specs.json").read_text(encoding="utf-8")
        )
        self.assertEqual(generated, self.data)


if __name__ == "__main__":
    unittest.main()
