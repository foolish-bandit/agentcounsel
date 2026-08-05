#!/usr/bin/env python3
"""Matter Plan Specification v1 structural validation tests."""

from __future__ import annotations

import json
import math
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.matter_plan import validate_matter_plan


class MatterPlanSchemaFixture:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "playbooks").mkdir()
        (self.root / "playbooks" / "sample.md").write_text("# Sample\n", encoding="utf-8")
        (self.root / "skills" / "test" / "first").mkdir(parents=True)
        (self.root / "skills" / "test" / "first" / "SKILL.md").write_text("# First\n", encoding="utf-8")
        self.skill_specs = {
            "test/first": {
                "skill_id": "test/first",
                "skill_path": "skills/test/first/SKILL.md",
                "schema_version": "2.0",
                "input_schema": [
                    {"id": "question", "type": "text", "required": True, "may_infer": False},
                    {"id": "jurisdiction", "type": "jurisdiction", "required": True, "may_infer": False},
                ],
                "output_schema": [{"id": "draft", "type": "memo"}],
                "execution_modes": [
                    {"id": "quick-triage", "enabled": True},
                    {"id": "standard", "enabled": True},
                    {"id": "deep-review", "enabled": True},
                ],
                "modules": [],
                "inherits": [],
            }
        }

    def close(self) -> None:
        self.tmp.cleanup()

    def plan(self) -> dict:
        return {
            "schema_version": "1.0",
            "plan_id": "sample-plan",
            "title": "Sample Plan",
            "source_path": "playbooks/sample.md",
            "description": "A valid sample plan.",
            "tags": ["sample"],
            "required_inputs": [
                {"id": "question", "type": "text", "required": True, "may_infer": False, "sensitive": True},
                {"id": "jurisdiction", "type": "jurisdiction", "required": True, "may_infer": False, "sensitive": False},
            ],
            "nodes": [
                {
                    "id": "draft",
                    "type": "skill",
                    "skill_id": "test/first",
                    "mode": "standard",
                    "depends_on": [],
                    "condition": {"operator": "always"},
                    "input_bindings": [
                        {"target_input_id": "question", "source": {"kind": "matter-input", "id": "question"}, "required": True},
                        {"target_input_id": "jurisdiction", "source": {"kind": "matter-input", "id": "jurisdiction"}, "required": True},
                    ],
                    "produces": ["draft-output"],
                },
                {
                    "id": "final-gate",
                    "type": "attorney-gate",
                    "depends_on": ["draft"],
                    "condition": {"operator": "always"},
                    "gate": {
                        "severity": "required",
                        "instruction": "Attorney reviews the draft.",
                        "required_artifacts": ["draft-output"],
                    },
                },
            ],
            "artifacts": [
                {"id": "draft-output", "type": "document", "produced_by": "draft", "attorney_review_required": True, "sensitive": True}
            ],
            "final_outputs": ["draft-output"],
            "budget": {
                "max_graph_depth": 3,
                "max_parallel_width": 2,
                "max_ready_nodes": 2,
                "max_total_estimated_tokens": 10000,
            },
        }


class TestMatterPlanSchema(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = MatterPlanSchemaFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def errors(self, plan: dict) -> list[str]:
        return validate_matter_plan(self.fixture.root, plan, self.fixture.skill_specs)

    def test_json_schema_is_valid_json(self):
        import json
        schema = Path(__file__).resolve().parent.parent / "specs" / "matter-plan-v1.schema.json"
        self.assertIsInstance(json.loads(schema.read_text(encoding="utf-8")), dict)

    def test_valid_minimal_plan_compiles(self):
        self.assertEqual(self.errors(self.fixture.plan()), [])

    def test_rejects_cycle(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["depends_on"] = ["final-gate"]
        self.assertIn("cycle", "\n".join(self.errors(plan)).lower())

    def test_rejects_unknown_skill_and_mode(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["skill_id"] = "missing/skill"
        plan["nodes"][0]["mode"] = "turbo"
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("unknown skill", errors)
        self.assertIn("mode", errors)

    def test_rejects_binding_to_unknown_target_input(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["input_bindings"][0]["target_input_id"] = "ghost"
        self.assertIn("target input", "\n".join(self.errors(plan)).lower())

    def test_rejects_duplicate_ids_after_casefold(self):
        plan = self.fixture.plan()
        plan["required_inputs"].append({"id": "Question", "type": "text", "required": False, "may_infer": False, "sensitive": False})
        self.assertIn("unique after normalization", "\n".join(self.errors(plan)).lower())

    def test_rejects_unsafe_ids_and_unknown_condition(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["id"] = "../draft"
        plan["nodes"][1]["condition"] = {"operator": "eval", "value": "true"}
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("slug", errors)
        self.assertIn("condition operator", errors)

    def test_rejects_non_finite_or_non_positive_budgets(self):
        for value in (0, -1, math.inf, math.nan, True):
            plan = self.fixture.plan()
            plan["budget"]["max_total_estimated_tokens"] = value
            with self.subTest(value=value):
                self.assertIn("budget", "\n".join(self.errors(plan)).lower())

    def test_rejects_multiple_artifact_producers(self):
        plan = self.fixture.plan()
        plan["nodes"].insert(1, deepcopy(plan["nodes"][0]))
        plan["nodes"][1]["id"] = "draft-two"
        self.assertIn("producer", "\n".join(self.errors(plan)).lower())

    def test_rejects_unknown_dependency_and_self_dependency(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["depends_on"] = ["draft", "ghost"]
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("itself", errors)
        self.assertIn("unknown dependency", errors)

    def test_rejects_source_path_traversal(self):
        plan = self.fixture.plan()
        plan["source_path"] = "../outside.md"
        self.assertIn("source path", "\n".join(self.errors(plan)).lower())

    def test_rejects_final_output_without_artifact(self):
        plan = self.fixture.plan()
        plan["final_outputs"] = ["ghost"]
        self.assertIn("final output", "\n".join(self.errors(plan)).lower())

    def test_rejects_required_skill_input_without_binding(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["input_bindings"] = plan["nodes"][0]["input_bindings"][:1]
        self.assertIn("required target input jurisdiction", "\n".join(self.errors(plan)).lower())

    def test_rejects_sensitive_or_uncontrolled_routing_input(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["condition"] = {"operator": "equals", "input_id": "question", "value": "secret"}
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("non-sensitive controlled", errors)

    def test_rejects_non_guidance_source_path(self):
        (self.fixture.root / "README.md").write_text("# Repo\n", encoding="utf-8")
        plan = self.fixture.plan()
        plan["source_path"] = "README.md"
        self.assertIn("playbook or matter pack", "\n".join(self.errors(plan)).lower())

    def test_rejects_multiple_terminal_nodes_or_non_gate_terminal(self):
        plan = self.fixture.plan()
        plan["nodes"].append({
            "id": "orphan",
            "type": "skill",
            "skill_id": "test/first",
            "mode": "standard",
            "depends_on": [],
            "condition": {"operator": "always"},
            "input_bindings": deepcopy(plan["nodes"][0]["input_bindings"]),
            "produces": [],
        })
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("one terminal attorney gate", errors)

    def test_rejects_final_output_not_upstream_of_final_gate(self):
        plan = self.fixture.plan()
        plan["nodes"][1]["depends_on"] = []
        self.assertIn("final output", "\n".join(self.errors(plan)).lower())

    def test_rejects_gate_condition_or_binding_without_gate_dependency(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["condition"] = {
            "operator": "gate-approved", "gate_id": "final-gate"
        }
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("depend directly", errors)

        plan = self.fixture.plan()
        plan["nodes"][0]["input_bindings"][0]["source"] = {
            "kind": "gate-decision", "id": "final-gate"
        }
        errors = "\n".join(self.errors(plan)).lower()
        self.assertIn("gate-decision", errors)

    def test_rejects_invalid_binding_required_policy(self):
        plan = self.fixture.plan()
        del plan["nodes"][0]["input_bindings"][0]["required"]
        self.assertIn("required must be boolean", "\n".join(self.errors(plan)).lower())

        plan = self.fixture.plan()
        plan["nodes"][0]["input_bindings"][0]["required"] = False
        self.assertIn("required target input question", "\n".join(self.errors(plan)).lower())

    def test_rejects_non_finite_values_anywhere_in_plan(self):
        plan = self.fixture.plan()
        plan["nodes"][0]["input_bindings"][0]["source"] = {
            "kind": "constant", "value": math.nan
        }
        self.assertIn("non-finite", "\n".join(self.errors(plan)).lower())


if __name__ == "__main__":
    unittest.main()
