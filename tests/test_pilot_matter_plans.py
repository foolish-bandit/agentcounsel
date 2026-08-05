#!/usr/bin/env python3
"""Static preservation and safety tests for the four Matter Graph v1 pilots."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.matter_plan import load_skill_spec_registry, validate_matter_plan

ROOT = Path(__file__).resolve().parent.parent
PLAN_IDS = (
    "legal-research-memo",
    "commercial-contract-review",
    "litigation-motion-opposition",
    "privacy-incident-response",
)


class TestPilotMatterPlans(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.specs = load_skill_spec_registry(ROOT)
        cls.plans = {
            plan_id: json.loads((ROOT / "matter-plans" / f"{plan_id}.json").read_text(encoding="utf-8"))
            for plan_id in PLAN_IDS
        }

    def test_all_pilots_compile_and_source_paths_exist(self):
        for plan_id, plan in self.plans.items():
            with self.subTest(plan_id=plan_id):
                self.assertTrue((ROOT / plan["source_path"]).is_file())
                self.assertEqual(validate_matter_plan(ROOT, plan, self.specs), [])

    def test_every_plan_has_artifact_handoffs_and_ends_at_attorney_gate(self):
        for plan_id, plan in self.plans.items():
            nodes = {node["id"]: node for node in plan["nodes"]}
            consumers = {
                binding["source"]["id"]
                for node in plan["nodes"]
                for binding in node.get("input_bindings", [])
                if binding.get("source", {}).get("kind") == "artifact"
            }
            with self.subTest(plan_id=plan_id):
                self.assertTrue(consumers)
                terminal = [node for node in plan["nodes"] if not any(node["id"] in other.get("depends_on", []) for other in plan["nodes"])]
                self.assertEqual(len(terminal), 1)
                self.assertEqual(terminal[0]["type"], "attorney-gate")

    def test_legal_research_plan_preserves_primary_and_quality_workflows(self):
        skills = {node.get("skill_id") for node in self.plans["legal-research-memo"]["nodes"]}
        required = {
            "legal-research/research-plan",
            "legal-research/authority-synthesis",
            "legal-research/negative-treatment-check",
            "legal-research/legal-research-memo",
            "legal-methodology/source-validation",
            "legal-methodology/citation-integrity-check",
            "legal-methodology/assumption-audit",
        }
        self.assertTrue(required <= skills)

    def test_contract_plan_has_controlled_optional_branches_and_parallel_checks(self):
        plan = self.plans["commercial-contract-review"]
        nodes = {node["id"]: node for node in plan["nodes"]}
        self.assertEqual(nodes["sow-review"]["condition"]["operator"], "equals")
        self.assertEqual(nodes["redline-summary"]["condition"]["operator"], "equals")
        quality = {"source-validation", "assumption-audit", "privilege-check"}
        self.assertTrue(all(nodes[node_id]["depends_on"] == ["contract-risk-review"] for node_id in quality))

    def test_motion_plan_uses_deep_selective_skill_only_after_scope_gate(self):
        plan = self.plans["litigation-motion-opposition"]
        nodes = {node["id"]: node for node in plan["nodes"]}
        motion = nodes["motion-opposition"]
        self.assertEqual(motion["skill_id"], "litigation/motion-opposition-drafter")
        self.assertEqual(motion["mode"], "deep-review")
        self.assertIn("approve-research-scope", nodes["authority-synthesis"]["depends_on"])
        self.assertIn("authority-synthesis", motion["depends_on"])

    def test_privacy_plan_has_immediate_reportability_gate_and_no_computed_deadline_node(self):
        plan = self.plans["privacy-incident-response"]
        nodes = {node["id"]: node for node in plan["nodes"]}
        gate = nodes["immediate-reportability-review"]
        self.assertEqual(gate["type"], "attorney-gate")
        self.assertEqual(gate["gate"]["severity"], "immediate")
        serialized = json.dumps(plan).lower()
        self.assertNotIn("calculate-deadline", serialized)
        self.assertNotIn("compute-deadline", serialized)

    def test_at_least_three_pilots_have_parallel_lanes(self):
        parallel = 0
        for plan in self.plans.values():
            sibling_groups: dict[tuple[str, ...], int] = {}
            for node in plan["nodes"]:
                deps = tuple(node.get("depends_on", []))
                sibling_groups[deps] = sibling_groups.get(deps, 0) + 1
            if any(count >= 2 and deps for deps, count in sibling_groups.items()):
                parallel += 1
        self.assertGreaterEqual(parallel, 3)


if __name__ == "__main__":
    unittest.main()
