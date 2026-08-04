#!/usr/bin/env python3
"""Tests for generated selective-context measurements and budget gates."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import generate_selective_context_metrics as metrics  # noqa: E402


class SelectiveMetricsFixture:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "metadata").mkdir()
        core = self.root / "skills" / "ip" / "test" / "SKILL.md"
        module = self.root / "skills" / "ip" / "test" / "modules" / "trademark.md"
        module.parent.mkdir(parents=True)
        core.write_text("# Test\n\nCore context.\n", encoding="utf-8")
        module.write_text("# Trademark\n\nSelected detail.\n", encoding="utf-8")
        inherited = self.root / "core" / "legal-work-product.md"
        inherited.parent.mkdir(parents=True)
        inherited.write_text("# Legal work product\n", encoding="utf-8")
        self.spec = {
            "schema_version": "2.0",
            "skill_id": "ip/test",
            "skill_path": "skills/ip/test/SKILL.md",
            "inherits": ["core/legal-work-product.md"],
            "execution_modes": [
                {"id": "quick-triage", "enabled": True},
                {"id": "standard", "enabled": True},
                {"id": "deep-review", "enabled": True},
            ],
            "input_schema": [
                {
                    "id": "rights",
                    "type": "string-list",
                    "required": True,
                    "items": ["trademark"],
                }
            ],
            "modules": [
                {
                    "id": "trademark",
                    "kind": "workflow-module",
                    "path": "skills/ip/test/modules/trademark.md",
                    "required": False,
                    "activation": {
                        "modes": ["standard", "deep-review"],
                        "input_id": "rights",
                        "operator": "contains-any",
                        "values": ["trademark"],
                    },
                }
            ],
            "context_scenarios": [
                {
                    "id": "standard-trademark",
                    "mode": "standard",
                    "inputs": {"rights": ["trademark"]},
                    "baseline_estimated_tokens": 100,
                    "max_ratio": 0.5,
                }
            ],
        }
        self.write_registry(self.spec)

    def write_registry(self, spec: dict) -> None:
        registry = {
            "schema_version": "2.0",
            "skill_count": 1,
            "skills": [spec],
        }
        (self.root / "metadata" / "skill_specs.json").write_text(
            json.dumps(registry), encoding="utf-8"
        )

    def close(self) -> None:
        self.tempdir.cleanup()


class TestSelectiveContextMetrics(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = SelectiveMetricsFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_collects_deterministic_ratio_and_selection_evidence(self):
        first = metrics.collect_metrics(self.fixture.root)
        second = metrics.collect_metrics(self.fixture.root)
        self.assertEqual(first, second)
        record = first["scenarios"][0]
        self.assertEqual(record["skill_id"], "ip/test")
        self.assertEqual(record["scenario_id"], "standard-trademark")
        self.assertEqual(record["selected_module_ids"], ["trademark"])
        self.assertEqual(
            record["selection_trace"],
            [
                {
                    "id": "trademark",
                    "status": "selected",
                    "reason": "activation input rights contains trademark",
                }
            ],
        )
        self.assertEqual(
            record["ratio"],
            round(record["total_estimated_tokens"] / 100, 4),
        )
        self.assertTrue(record["within_budget"])
        self.assertTrue(record["complete"])
        self.assertEqual(len(record["contract_sha256"]), 64)
        self.assertEqual(
            set(record["inherited_rule_hashes"]),
            {"core/legal-work-product.md"},
        )
        self.assertEqual(
            len(record["inherited_rule_hashes"]["core/legal-work-product.md"]),
            64,
        )
        self.assertEqual(len(record["bundle_sha256"]), 64)

    def test_budget_violation_fails_the_gate(self):
        spec = deepcopy(self.fixture.spec)
        spec["context_scenarios"][0]["max_ratio"] = 0.01
        self.fixture.write_registry(spec)
        data = metrics.collect_metrics(self.fixture.root)
        self.assertFalse(data["scenarios"][0]["within_budget"])
        self.assertFalse(metrics.budgets_pass(data))
        self.assertIn("over budget", metrics.violation_messages(data)[0])

    def test_incomplete_bundle_fails_the_gate(self):
        spec = deepcopy(self.fixture.spec)
        spec["context_scenarios"][0]["inputs"] = {}
        self.fixture.write_registry(spec)
        data = metrics.collect_metrics(self.fixture.root)
        record = data["scenarios"][0]
        self.assertFalse(record["complete"])
        self.assertEqual(record["missing_required_inputs"], ["rights"])
        self.assertFalse(metrics.budgets_pass(data))
        self.assertIn("incomplete", metrics.violation_messages(data)[0])

    def test_render_and_check_mode_detect_drift(self):
        data = metrics.collect_metrics(self.fixture.root)
        report = metrics.render_markdown(data)
        self.assertIn("Selective Context Metrics", report)
        self.assertIn("standard-trademark", report)
        self.assertIn("planning estimates", report)
        self.assertFalse(metrics.write_outputs(self.fixture.root, check=True))
        self.assertTrue(metrics.write_outputs(self.fixture.root, check=False))
        self.assertTrue(metrics.write_outputs(self.fixture.root, check=True))


if __name__ == "__main__":
    unittest.main()
