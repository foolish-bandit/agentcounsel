#!/usr/bin/env python3
"""Generated matter-plan registry, metrics, search, and drift tests."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.build_matter_plans import build_registry, search_plan_cards, write_outputs
from scripts.matter_plan import MatterPlanError
from tests.test_matter_plan_builder import MatterPlanBuilderFixture


class TestMatterPlanRegistry(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = MatterPlanBuilderFixture()
        self.root = self.fixture.root
        (self.root / "matter-plans").mkdir()
        self.plan = self.fixture.plan()
        self.plan["title"] = "Sample Research Plan"
        self.plan["description"] = "Research and validate a sample question."
        self.plan["tags"] = ["research", "sample"]
        (self.root / "matter-plans" / "sample-plan.json").write_text(
            json.dumps(self.plan, indent=2) + "\n", encoding="utf-8"
        )
        (self.root / "metadata").mkdir()
        (self.root / "metadata" / "skill_specs.json").write_text(
            json.dumps({"skills": list(self.fixture.skill_specs.values())}, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def test_registry_is_deterministic_and_measures_graph(self):
        first = build_registry(self.root)
        second = build_registry(self.root)
        self.assertEqual(first, second)
        self.assertEqual(first["plan_count"], 1)
        card = first["plans"][0]
        self.assertEqual(card["plan_id"], "sample-plan")
        self.assertEqual(card["node_count"], 5)
        self.assertEqual(card["skill_node_count"], 4)
        self.assertEqual(card["gate_node_count"], 1)
        self.assertEqual(card["artifact_count"], 4)
        self.assertEqual(card["practice_areas"], ["test"])
        self.assertEqual(card["graph_depth"], 3)
        self.assertEqual(card["max_parallel_width"], 2)
        self.assertRegex(card["plan_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(card["source_sha256"], r"^[0-9a-f]{64}$")

    def test_search_prioritizes_exact_and_tag_matches(self):
        registry = build_registry(self.root)
        exact = search_plan_cards(registry, "sample-plan", 10)
        self.assertEqual(exact[0]["plan_id"], "sample-plan")
        tagged = search_plan_cards(registry, "research", 10)
        self.assertEqual(tagged[0]["plan_id"], "sample-plan")
        self.assertIn("tags", tagged[0]["matched_fields"])

    def test_generated_drift_detection(self):
        self.assertTrue(write_outputs(self.root, check=False))
        self.assertTrue(write_outputs(self.root, check=True))
        path = self.root / "metadata" / "matter_plans.json"
        path.write_text("{}\n", encoding="utf-8")
        self.assertFalse(write_outputs(self.root, check=True))

    def test_duplicate_plan_ids_fail(self):
        second = dict(self.plan)
        (self.root / "matter-plans" / "another.json").write_text(
            json.dumps(second, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaises(MatterPlanError):
            build_registry(self.root)

    def test_static_budget_violation_fails_registry(self):
        self.plan["budget"]["max_graph_depth"] = 1
        (self.root / "matter-plans" / "sample-plan.json").write_text(
            json.dumps(self.plan, indent=2) + "\n", encoding="utf-8"
        )
        with self.assertRaises(MatterPlanError):
            build_registry(self.root)


if __name__ == "__main__":
    unittest.main()
