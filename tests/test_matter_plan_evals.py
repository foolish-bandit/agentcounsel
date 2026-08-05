#!/usr/bin/env python3
"""Scenario budgets and adversarial mutation sensitivity for matter plans."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.evaluate_matter_plans import evaluate, write_outputs

ROOT = Path(__file__).resolve().parent.parent


class TestMatterPlanEvals(unittest.TestCase):
    def test_all_scenarios_are_bounded_and_receipts_verify(self):
        data = evaluate(ROOT)
        self.assertGreaterEqual(data["scenario_count"], 16)
        self.assertTrue(data["all_scenarios_within_budget"])
        self.assertTrue(data["all_receipts_valid"])
        for scenario in data["scenarios"]:
            self.assertLessEqual(
                scenario["ready_context_tokens"],
                scenario["max_total_estimated_tokens"],
            )

    def test_all_eight_mutations_are_detected(self):
        data = evaluate(ROOT)
        self.assertEqual(data["mutation_count"], 8)
        self.assertEqual(data["detected_mutation_count"], 8)
        self.assertTrue(data["all_mutations_detected"])
        expected = {
            "cycle-injection",
            "gate-bypass",
            "dependency-removal",
            "artifact-producer-swap",
            "raw-input-receipt-injection",
            "token-arithmetic-tamper",
            "skill-mode-swap",
            "blocked-node-context-leak",
        }
        self.assertEqual({item["mutation_id"] for item in data["mutations"]}, expected)
        self.assertTrue(all(item["detected"] and item["signal"] for item in data["mutations"]))
        gate_bypass = next(
            item for item in data["mutations"] if item["mutation_id"] == "gate-bypass"
        )
        self.assertTrue(gate_bypass["signal"].startswith("validator:"))

    def test_generated_outputs_do_not_contain_fixture_matter_text(self):
        data = evaluate(ROOT)
        serialized = json.dumps(data)
        for text in ("What is the rule?", "software purchase", "incident currently contained"):
            self.assertNotIn(text, serialized)

    def test_generated_drift_detection(self):
        self.assertTrue(write_outputs(ROOT, check=False))
        self.assertTrue(write_outputs(ROOT, check=True))
        path = ROOT / "metadata" / "matter_plan_evals.json"
        original = path.read_text(encoding="utf-8")
        try:
            path.write_text("{}\n", encoding="utf-8")
            self.assertFalse(write_outputs(ROOT, check=True))
        finally:
            path.write_text(original, encoding="utf-8")


if __name__ == "__main__":
    unittest.main()
