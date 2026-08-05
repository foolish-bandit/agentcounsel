#!/usr/bin/env python3
"""Matter Graph v1 state resolution, waves, and lazy-context tests."""

from __future__ import annotations

import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.matter_plan import MatterPlanError, build_matter_plan


class MatterPlanBuilderFixture:
    def __init__(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "playbooks").mkdir()
        (self.root / "playbooks" / "sample.md").write_text("# Sample\n", encoding="utf-8")
        for slug in ("first", "check-a", "check-b", "optional"):
            path = self.root / "skills" / "test" / slug
            path.mkdir(parents=True)
            (path / "SKILL.md").write_text(
                f"# {slug}\n\nDraft legal work product for attorney review.\n",
                encoding="utf-8",
            )
        self.skill_specs = {
            "test/first": self.spec("first", [
                {"id": "question", "type": "text", "required": True, "may_infer": False},
                {"id": "jurisdiction", "type": "jurisdiction", "required": True, "may_infer": False},
            ]),
            "test/check-a": self.spec("check-a", [
                {"id": "draft", "type": "document", "required": True, "may_infer": False},
            ]),
            "test/check-b": self.spec("check-b", [
                {"id": "drafts", "type": "document-set", "required": True, "may_infer": False},
            ]),
            "test/optional": self.spec("optional", [
                {"id": "question", "type": "text", "required": True, "may_infer": False},
            ]),
        }

    def spec(self, slug: str, inputs: list[dict]) -> dict:
        return {
            "skill_id": f"test/{slug}",
            "skill_path": f"skills/test/{slug}/SKILL.md",
            "schema_version": "2.0",
            "input_schema": inputs,
            "output_schema": [{"id": "draft", "type": "memo", "attorney_review_required": True}],
            "execution_modes": [
                {"id": "quick-triage", "enabled": True},
                {"id": "standard", "enabled": True},
                {"id": "deep-review", "enabled": True},
            ],
            "modules": [],
            "inherits": [],
        }

    def close(self) -> None:
        self.tmp.cleanup()

    def plan(self) -> dict:
        return {
            "schema_version": "1.0",
            "plan_id": "sample-plan",
            "title": "Sample Plan",
            "source_path": "playbooks/sample.md",
            "description": "A graph state fixture.",
            "tags": ["sample"],
            "required_inputs": [
                {"id": "question", "type": "text", "required": True, "may_infer": False, "sensitive": True},
                {"id": "jurisdiction", "type": "jurisdiction", "required": True, "may_infer": False, "sensitive": False},
                {"id": "include-optional", "type": "enum", "enum": ["yes", "no"], "required": False, "may_infer": False, "sensitive": False},
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
                    "id": "optional",
                    "type": "skill",
                    "skill_id": "test/optional",
                    "mode": "quick-triage",
                    "depends_on": [],
                    "condition": {"operator": "equals", "input_id": "include-optional", "value": "yes"},
                    "input_bindings": [
                        {"target_input_id": "question", "source": {"kind": "matter-input", "id": "question"}, "required": True},
                    ],
                    "produces": ["optional-output"],
                },
                {
                    "id": "check-a",
                    "type": "skill",
                    "skill_id": "test/check-a",
                    "mode": "standard",
                    "depends_on": ["draft"],
                    "condition": {"operator": "always"},
                    "input_bindings": [
                        {"target_input_id": "draft", "source": {"kind": "artifact", "id": "draft-output"}, "transform": "artifact-ref", "required": True},
                    ],
                    "produces": ["check-a-output"],
                },
                {
                    "id": "check-b",
                    "type": "skill",
                    "skill_id": "test/check-b",
                    "mode": "standard",
                    "depends_on": ["draft"],
                    "condition": {"operator": "always"},
                    "input_bindings": [
                        {"target_input_id": "drafts", "source": {"kind": "artifact", "id": "draft-output"}, "transform": "as-document-set", "required": True},
                    ],
                    "produces": ["check-b-output"],
                },
                {
                    "id": "final-gate",
                    "type": "attorney-gate",
                    "depends_on": ["check-a", "check-b"],
                    "condition": {"operator": "always"},
                    "gate": {
                        "severity": "required",
                        "instruction": "Attorney reviews the complete package.",
                        "required_artifacts": ["check-a-output", "check-b-output"],
                    },
                    "produces": [],
                },
            ],
            "artifacts": [
                {"id": "draft-output", "type": "document", "produced_by": "draft", "attorney_review_required": True, "sensitive": True},
                {"id": "optional-output", "type": "document", "produced_by": "optional", "attorney_review_required": True, "sensitive": True},
                {"id": "check-a-output", "type": "document", "produced_by": "check-a", "attorney_review_required": True, "sensitive": True},
                {"id": "check-b-output", "type": "document", "produced_by": "check-b", "attorney_review_required": True, "sensitive": True},
            ],
            "final_outputs": ["check-a-output", "check-b-output"],
            "budget": {
                "max_graph_depth": 4,
                "max_parallel_width": 3,
                "max_ready_nodes": 3,
                "max_total_estimated_tokens": 20000,
            },
        }

    @staticmethod
    def inputs(include_optional: str | None = "no") -> dict:
        result = {"question": "What is the rule?", "jurisdiction": "California"}
        if include_optional is not None:
            result["include-optional"] = include_optional
        return result


class TestMatterPlanBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = MatterPlanBuilderFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def build(self, **kwargs):
        return build_matter_plan(
            self.fixture.root,
            self.fixture.plan(),
            skill_specs=self.fixture.skill_specs,
            **kwargs,
        )

    @staticmethod
    def states(result: dict) -> dict[str, str]:
        return {node["id"]: node["state"] for node in result["nodes"]}

    def test_first_skill_is_ready_and_downstream_is_blocked(self):
        result = self.build(matter_inputs=self.fixture.inputs())
        states = self.states(result)
        self.assertEqual(states["draft"], "ready")
        self.assertEqual(states["check-a"], "blocked")
        self.assertEqual(states["check-b"], "blocked")
        self.assertEqual(states["final-gate"], "blocked")
        self.assertIn("context", next(node for node in result["nodes"] if node["id"] == "draft"))
        self.assertNotIn("context", next(node for node in result["nodes"] if node["id"] == "check-a"))

    def test_missing_required_input_is_unresolved(self):
        result = self.build(matter_inputs={"jurisdiction": "California", "include-optional": "no"})
        draft = next(node for node in result["nodes"] if node["id"] == "draft")
        self.assertEqual(draft["state"], "unresolved")
        self.assertIn("question", draft["reason"])
        self.assertNotIn("context", draft)

    def test_false_condition_is_not_selected(self):
        result = self.build(matter_inputs=self.fixture.inputs("no"))
        optional = next(node for node in result["nodes"] if node["id"] == "optional")
        self.assertEqual(optional["state"], "not-selected")

    def test_not_selected_optional_dependency_does_not_block_downstream(self):
        plan = self.fixture.plan()
        plan["nodes"][-1]["depends_on"].append("optional")
        artifacts = {
            "draft-output": {"digest": "a" * 64},
            "check-a-output": {"digest": "b" * 64},
            "check-b-output": {"digest": "c" * 64},
        }
        result = build_matter_plan(
            self.fixture.root,
            plan,
            matter_inputs=self.fixture.inputs("no"),
            available_artifacts=artifacts,
            skill_specs=self.fixture.skill_specs,
        )
        gate = next(node for node in result["nodes"] if node["id"] == "final-gate")
        self.assertEqual(gate["state"], "blocked")
        self.assertEqual(gate["reason"], "waiting on explicit attorney approval")

    def test_missing_condition_input_is_unresolved_not_eager(self):
        result = self.build(matter_inputs=self.fixture.inputs(None))
        optional = next(node for node in result["nodes"] if node["id"] == "optional")
        self.assertEqual(optional["state"], "unresolved")
        self.assertNotIn("context", optional)

    def test_supplied_artifact_marks_producer_completed(self):
        result = self.build(
            matter_inputs=self.fixture.inputs(),
            available_artifacts={"draft-output": {"digest": "a" * 64}},
        )
        states = self.states(result)
        self.assertEqual(states["draft"], "completed")
        self.assertEqual(states["check-a"], "ready")
        self.assertEqual(states["check-b"], "ready")

    def test_gate_requires_explicit_approved_or_rejected_value(self):
        artifacts = {
            "draft-output": {"digest": "a" * 64},
            "check-a-output": {"digest": "b" * 64},
            "check-b-output": {"digest": "c" * 64},
        }
        pending = self.build(matter_inputs=self.fixture.inputs(), available_artifacts=artifacts)
        self.assertEqual(self.states(pending)["final-gate"], "blocked")
        approved = self.build(
            matter_inputs=self.fixture.inputs(),
            available_artifacts=artifacts,
            gate_decisions={"final-gate": "approved"},
        )
        self.assertEqual(self.states(approved)["final-gate"], "approved")

    def test_rejected_gate_blocks_descendants(self):
        plan = self.fixture.plan()
        plan["nodes"].insert(-1, {
            "id": "intermediate-gate",
            "type": "attorney-gate",
            "depends_on": ["draft"],
            "condition": {"operator": "always"},
            "gate": {
                "severity": "required",
                "instruction": "Attorney decides whether the branch may continue.",
                "required_artifacts": ["draft-output"],
            },
            "produces": [],
        })
        plan["nodes"].append({
            "id": "after-gate",
            "type": "skill",
            "skill_id": "test/optional",
            "mode": "standard",
            "depends_on": ["intermediate-gate"],
            "condition": {"operator": "always"},
            "input_bindings": [
                {"target_input_id": "question", "source": {"kind": "matter-input", "id": "question"}, "required": True},
            ],
            "produces": ["after-output"],
        })
        final_gate = next(node for node in plan["nodes"] if node["id"] == "final-gate")
        final_gate["depends_on"].append("after-gate")
        plan["artifacts"].append({"id": "after-output", "type": "document", "produced_by": "after-gate", "attorney_review_required": True, "sensitive": True})
        artifacts = {
            "draft-output": {"digest": "a" * 64},
            "check-a-output": {"digest": "b" * 64},
            "check-b-output": {"digest": "c" * 64},
        }
        result = build_matter_plan(
            self.fixture.root,
            plan,
            matter_inputs=self.fixture.inputs(),
            available_artifacts=artifacts,
            gate_decisions={"intermediate-gate": "rejected"},
            skill_specs=self.fixture.skill_specs,
        )
        states = self.states(result)
        self.assertEqual(states["intermediate-gate"], "rejected")
        self.assertEqual(states["after-gate"], "blocked")

    def test_parallel_nodes_share_one_execution_wave(self):
        result = self.build(
            matter_inputs=self.fixture.inputs(),
            available_artifacts={"draft-output": {"digest": "a" * 64}},
        )
        wave = next(item for item in result["execution_waves"] if set(item["node_ids"]) == {"check-a", "check-b"})
        self.assertEqual(wave["node_ids"], ["check-a", "check-b"])
        self.assertGreater(wave["estimated_tokens"], 0)

    def test_ready_nodes_only_load_their_skill_context(self):
        result = self.build(matter_inputs=self.fixture.inputs())
        contexts = [node["id"] for node in result["nodes"] if "context" in node]
        self.assertEqual(contexts, ["draft"])

    def test_explicit_node_cannot_bypass_dependencies_or_gates(self):
        with self.assertRaises(MatterPlanError):
            self.build(matter_inputs=self.fixture.inputs(), explicit_node_ids=["check-a"])

    def test_downstream_artifact_cannot_bypass_dependencies(self):
        result = self.build(
            matter_inputs=self.fixture.inputs(),
            available_artifacts={"check-a-output": {"digest": "b" * 64}},
        )
        states = self.states(result)
        self.assertEqual(states["check-a"], "blocked")
        self.assertNotIn("context", next(node for node in result["nodes"] if node["id"] == "check-a"))

    def test_gate_cannot_be_preapproved_before_prerequisites(self):
        with self.assertRaises(MatterPlanError):
            self.build(
                matter_inputs=self.fixture.inputs(),
                gate_decisions={"final-gate": "approved"},
            )

    def test_optional_binding_does_not_block_ready_node(self):
        plan = self.fixture.plan()
        self.fixture.skill_specs["test/first"]["input_schema"].append({
            "id": "optional-note", "type": "text", "required": False,
            "may_infer": False,
        })
        plan["required_inputs"].append({
            "id": "optional-note", "type": "text", "required": False,
            "may_infer": False, "sensitive": True,
        })
        plan["nodes"][0]["input_bindings"].append({
            "target_input_id": "optional-note",
            "source": {"kind": "matter-input", "id": "optional-note"},
            "required": False,
        })
        result = build_matter_plan(
            self.fixture.root, plan, matter_inputs=self.fixture.inputs(),
            skill_specs=self.fixture.skill_specs,
        )
        draft = next(node for node in result["nodes"] if node["id"] == "draft")
        self.assertEqual(draft["state"], "ready")
        omitted = next(item for item in draft["bindings"] if item["target_input_id"] == "optional-note")
        self.assertFalse(omitted["available"])

    def test_artifact_metadata_rejects_content_or_unknown_fields(self):
        with self.assertRaises(MatterPlanError):
            self.build(
                matter_inputs=self.fixture.inputs(),
                available_artifacts={
                    "draft-output": {"content_ref": "secret document text"}
                },
            )


if __name__ == "__main__":
    unittest.main()
