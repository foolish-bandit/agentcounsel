#!/usr/bin/env python3
"""Tests for deterministic selective skill context bundles."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from tests.test_skill_spec_v2 import BASELINE_INHERITS

import sys

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from skill_context import (  # noqa: E402
    SkillContextError,
    build_skill_context,
    normalize_inputs,
    select_modules,
)


class ContextFixture:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        skill_dir = self.root / "skills" / "ip" / "test-skill"
        modules_dir = skill_dir / "modules"
        modules_dir.mkdir(parents=True)
        (skill_dir / "SKILL.md").write_text("# Core\n\nUniversal rules.\n", encoding="utf-8")
        for inherited_path in BASELINE_INHERITS:
            target = self.root / inherited_path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(
                f"# {target.stem}\n\nInherited rule.\n", encoding="utf-8"
            )
        for name in (
            "required",
            "common",
            "trademark",
            "copyright",
            "deep",
            "prose-only",
        ):
            (modules_dir / f"{name}.md").write_text(
                f"# {name.title()}\n\n{name} detail.\n", encoding="utf-8"
            )
        self.spec = {
            "schema_version": "2.0",
            "skill_id": "ip/test-skill",
            "skill_path": "skills/ip/test-skill/SKILL.md",
            "inherits": list(BASELINE_INHERITS),
            "execution_modes": [
                {
                    "id": "quick-triage",
                    "enabled": True,
                    "purpose": "Quick.",
                    "output_detail": "minimal",
                    "quality_checks": [],
                },
                {
                    "id": "standard",
                    "enabled": True,
                    "purpose": "Standard.",
                    "output_detail": "standard",
                    "quality_checks": [],
                },
                {
                    "id": "deep-review",
                    "enabled": True,
                    "purpose": "Deep.",
                    "output_detail": "expanded",
                    "quality_checks": [],
                },
            ],
            "input_schema": [
                {
                    "id": "rights",
                    "label": "Rights",
                    "type": "string-list",
                    "required": True,
                    "description": "Rights at issue.",
                    "source_requirement": "user-provided",
                    "may_infer": False,
                    "sensitive": False,
                    "items": ["trademark", "copyright"],
                },
                {
                    "id": "posture",
                    "label": "Posture",
                    "type": "enum",
                    "required": False,
                    "description": "Matter posture.",
                    "source_requirement": "user-provided",
                    "may_infer": False,
                    "sensitive": False,
                    "enum": ["claimant", "respondent"],
                },
                {
                    "id": "record",
                    "label": "Record",
                    "type": "document-set",
                    "required": False,
                    "description": "Record materials.",
                    "source_requirement": "provided-document",
                    "may_infer": False,
                    "sensitive": True,
                },
            ],
            "modules": [
                {
                    "id": "required",
                    "kind": "reference",
                    "path": "skills/ip/test-skill/modules/required.md",
                    "required": True,
                    "load_when": "Always required.",
                },
                {
                    "id": "common",
                    "kind": "workflow-module",
                    "path": "skills/ip/test-skill/modules/common.md",
                    "required": False,
                    "load_when": "Standard and deep modes.",
                    "activation": {
                        "modes": ["standard", "deep-review"],
                        "operator": "always",
                    },
                },
                {
                    "id": "trademark",
                    "kind": "workflow-module",
                    "path": "skills/ip/test-skill/modules/trademark.md",
                    "required": False,
                    "load_when": "Trademark is present.",
                    "activation": {
                        "modes": ["standard", "deep-review"],
                        "input_id": "rights",
                        "operator": "contains-any",
                        "values": ["trademark"],
                    },
                },
                {
                    "id": "copyright",
                    "kind": "workflow-module",
                    "path": "skills/ip/test-skill/modules/copyright.md",
                    "required": False,
                    "load_when": "Copyright is present.",
                    "activation": {
                        "modes": ["standard", "deep-review"],
                        "input_id": "rights",
                        "operator": "contains-any",
                        "values": ["copyright"],
                    },
                },
                {
                    "id": "deep",
                    "kind": "quality-check",
                    "path": "skills/ip/test-skill/modules/deep.md",
                    "required": False,
                    "load_when": "Deep mode only.",
                    "activation": {
                        "modes": ["deep-review"],
                        "operator": "always",
                    },
                },
                {
                    "id": "prose-only",
                    "kind": "reference",
                    "path": "skills/ip/test-skill/modules/prose-only.md",
                    "required": False,
                    "load_when": "When prose says so.",
                },
            ],
        }

    def close(self) -> None:
        self.tempdir.cleanup()


class TestInputNormalization(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_controlled_values_are_canonicalized_and_deduplicated(self):
        normalized = normalize_inputs(
            self.fixture.spec,
            {"rights": [" Copyright ", "TRADEMARK", "copyright"], "posture": " Claimant "},
        )
        self.assertEqual(normalized["rights"], ["copyright", "trademark"])
        self.assertEqual(normalized["posture"], "claimant")

    def test_unknown_inputs_and_invalid_controlled_values_fail(self):
        with self.assertRaisesRegex(SkillContextError, "unknown input"):
            normalize_inputs(self.fixture.spec, {"other": "value"})
        with self.assertRaisesRegex(SkillContextError, "invalid value"):
            normalize_inputs(self.fixture.spec, {"rights": ["patent"]})
        with self.assertRaisesRegex(SkillContextError, "must be a string or list"):
            normalize_inputs(self.fixture.spec, {"rights": {"trademark": True}})

    def test_typed_inputs_reject_wrong_json_shapes(self):
        self.fixture.spec["input_schema"].extend(
            [
                {
                    "id": "question",
                    "label": "Question",
                    "type": "text",
                    "required": False,
                },
                {
                    "id": "facts",
                    "label": "Facts",
                    "type": "object",
                    "required": False,
                },
                {
                    "id": "confirmed",
                    "label": "Confirmed",
                    "type": "boolean",
                    "required": False,
                },
            ]
        )
        normalized = normalize_inputs(
            self.fixture.spec,
            {
                "question": "  issue  ",
                "record": [" doc-1 ", "doc-1", "doc-2"],
                "facts": {"source": "provided"},
                "confirmed": True,
            },
        )
        self.assertEqual(normalized["question"], "issue")
        self.assertEqual(normalized["record"], ["doc-1", "doc-2"])
        self.assertEqual(normalized["facts"], {"source": "provided"})

        self.fixture.spec["input_schema"].append(
            {
                "id": "confidence",
                "label": "Confidence",
                "type": "number",
                "required": False,
            }
        )
        invalid = [
            ({"question": ["not", "text"]}, "must be a string"),
            ({"record": {"doc": "one"}}, "string or list of strings"),
            ({"record": ["doc-1", 2]}, "values must be strings"),
            ({"facts": ["not", "an", "object"]}, "must be an object"),
            ({"facts": {1: "non-string key"}}, "keys must be strings"),
            ({"facts": {"tags": {"not-json"}}}, "JSON-compatible"),
            ({"facts": {"score": float("inf")}}, "must be finite"),
            ({"confirmed": "yes"}, "must be boolean"),
            ({"confidence": float("nan")}, "must be finite"),
            ({"confidence": float("inf")}, "must be finite"),
        ]
        for inputs, message in invalid:
            with self.subTest(inputs=inputs):
                with self.assertRaisesRegex(SkillContextError, message):
                    normalize_inputs(self.fixture.spec, inputs)


class TestModuleSelection(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_mode_and_multi_value_selection_is_deterministic(self):
        result = select_modules(
            self.fixture.spec,
            "standard",
            {"rights": ["trademark", "copyright"]},
        )
        self.assertEqual(
            [item["module"]["id"] for item in result["selected"]],
            ["required", "common", "trademark", "copyright"],
        )
        self.assertEqual(result["unresolved"], [])
        self.assertNotIn("prose-only", [item["module"]["id"] for item in result["selected"]])
        self.assertEqual(
            [(item["id"], item["status"]) for item in result["selection_trace"]],
            [
                ("required", "selected"),
                ("common", "selected"),
                ("trademark", "selected"),
                ("copyright", "selected"),
                ("deep", "not-selected"),
                ("prose-only", "not-selected"),
            ],
        )
        self.assertIn(
            "mode deep-review only",
            result["selection_trace"][4]["reason"],
        )
        self.assertIn(
            "no machine-readable activation",
            result["selection_trace"][5]["reason"],
        )

    def test_missing_activation_input_fails_closed(self):
        result = select_modules(self.fixture.spec, "standard", {})
        self.assertEqual(
            [item["module"]["id"] for item in result["selected"]],
            ["required", "common"],
        )
        self.assertEqual(
            [item["module"]["id"] for item in result["unresolved"]],
            ["trademark", "copyright"],
        )
        self.assertTrue(
            all("rights" in item["reason"] for item in result["unresolved"])
        )

    def test_present_and_equals_operators(self):
        extra = [
            {
                "id": "record-present",
                "kind": "workflow-module",
                "path": "skills/ip/test-skill/modules/common.md",
                "required": False,
                "load_when": "Record present.",
                "activation": {
                    "modes": ["standard"],
                    "input_id": "record",
                    "operator": "present",
                },
            },
            {
                "id": "claimant",
                "kind": "workflow-module",
                "path": "skills/ip/test-skill/modules/common.md",
                "required": False,
                "load_when": "Claimant posture.",
                "activation": {
                    "modes": ["standard"],
                    "input_id": "posture",
                    "operator": "equals",
                    "value": "claimant",
                },
            },
        ]
        self.fixture.spec["modules"].extend(extra)
        result = select_modules(
            self.fixture.spec,
            "standard",
            {"rights": ["trademark"], "record": ["doc-1"], "posture": "claimant"},
        )
        selected = [item["module"]["id"] for item in result["selected"]]
        self.assertEqual(selected[-2:], ["record-present", "claimant"])

    def test_explicit_selection_is_transparent(self):
        result = select_modules(
            self.fixture.spec,
            "quick-triage",
            {},
            explicit_module_ids=["prose-only"],
        )
        selected = result["selected"]
        self.assertEqual([item["module"]["id"] for item in selected], ["required", "prose-only"])
        self.assertEqual(selected[-1]["reason"], "explicitly requested by module ID")

    def test_unknown_disabled_mode_and_module_fail(self):
        with self.assertRaisesRegex(SkillContextError, "unknown execution mode"):
            select_modules(self.fixture.spec, "turbo", {})
        self.fixture.spec["execution_modes"][0]["enabled"] = False
        with self.assertRaisesRegex(SkillContextError, "disabled"):
            select_modules(self.fixture.spec, "quick-triage", {})
        with self.assertRaisesRegex(SkillContextError, "unknown module ID"):
            select_modules(
                self.fixture.spec,
                "standard",
                {"rights": ["trademark"]},
                explicit_module_ids=["missing"],
            )


class TestBundleBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = ContextFixture()

    def tearDown(self) -> None:
        self.fixture.close()

    def test_bundle_contains_content_reasons_hashes_and_stable_fingerprint(self):
        first = build_skill_context(
            self.fixture.root,
            self.fixture.spec,
            "standard",
            {"rights": ["TRADEMARK"]},
        )
        second = build_skill_context(
            self.fixture.root,
            self.fixture.spec,
            "standard",
            {"rights": ["trademark"]},
        )
        self.assertEqual(first["normalized_inputs"], {"rights": ["trademark"]})
        self.assertEqual(
            [module["id"] for module in first["modules"]],
            ["required", "common", "trademark"],
        )
        self.assertIn("Universal rules", first["core"]["content"])
        self.assertRegex(first["core"]["sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(first["contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(
            [record["path"] for record in first["inherited_rules"]],
            list(BASELINE_INHERITS),
        )
        self.assertTrue(
            all(len(record["sha256"]) == 64 for record in first["inherited_rules"])
        )
        self.assertRegex(first["bundle_sha256"], r"^[0-9a-f]{64}$")
        self.assertEqual(first["bundle_sha256"], second["bundle_sha256"])
        self.assertEqual(len(first["selection_trace"]), len(self.fixture.spec["modules"]))
        self.assertEqual(
            {item["id"]: item["status"] for item in first["selection_trace"]}["copyright"],
            "not-selected",
        )
        self.assertEqual(
            first["estimated_tokens"]["total"],
            first["estimated_tokens"]["core"]
            + first["estimated_tokens"]["modules"],
        )
        self.assertTrue(first["complete"])

        changed_spec = dict(self.fixture.spec)
        changed_spec["quality_checks"] = ["new-check"]
        changed = build_skill_context(
            self.fixture.root,
            changed_spec,
            "standard",
            {"rights": ["trademark"]},
        )
        self.assertNotEqual(first["contract_sha256"], changed["contract_sha256"])
        self.assertNotEqual(first["bundle_sha256"], changed["bundle_sha256"])

        inherited = self.fixture.root / BASELINE_INHERITS[0]
        inherited.write_text("# Changed inherited rule\n", encoding="utf-8")
        changed_rule = build_skill_context(
            self.fixture.root,
            self.fixture.spec,
            "standard",
            {"rights": ["trademark"]},
        )
        self.assertEqual(first["contract_sha256"], changed_rule["contract_sha256"])
        self.assertNotEqual(first["bundle_sha256"], changed_rule["bundle_sha256"])

    def test_missing_required_input_and_required_unresolved_module_are_incomplete(self):
        bundle = build_skill_context(self.fixture.root, self.fixture.spec, "standard", {})
        self.assertEqual(bundle["missing_required_inputs"], ["rights"])
        self.assertTrue(bundle["unresolved_modules"])
        self.assertFalse(bundle["complete"])

        self.fixture.spec["modules"][2]["required"] = True
        bundle = build_skill_context(self.fixture.root, self.fixture.spec, "standard", {})
        unresolved = {item["id"]: item for item in bundle["unresolved_modules"]}
        self.assertTrue(unresolved["trademark"]["required"])
        self.assertFalse(bundle["complete"])

    def test_repository_path_escape_is_rejected(self):
        self.fixture.spec["skill_path"] = "../outside.md"
        with self.assertRaisesRegex(SkillContextError, "outside repository root"):
            build_skill_context(
                self.fixture.root,
                self.fixture.spec,
                "standard",
                {"rights": ["trademark"]},
            )


if __name__ == "__main__":
    unittest.main()
