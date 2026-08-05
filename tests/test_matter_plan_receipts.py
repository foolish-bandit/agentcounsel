#!/usr/bin/env python3
"""Privacy, determinism, drift, and tamper tests for matter-plan receipts."""

from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path

from scripts.matter_plan import build_matter_plan, verify_matter_plan_receipt
from tests.test_matter_plan_builder import MatterPlanBuilderFixture


def rehash(receipt: dict) -> dict:
    updated = deepcopy(receipt)
    updated.pop("receipt_sha256", None)
    updated["receipt_sha256"] = hashlib.sha256(
        json.dumps(updated, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()
    return updated


class TestMatterPlanReceipts(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = MatterPlanBuilderFixture()
        (self.fixture.root / "matter-plans").mkdir()
        self.plan = self.fixture.plan()
        (self.fixture.root / "matter-plans" / "sample-plan.json").write_text(
            json.dumps(self.plan, indent=2) + "\n", encoding="utf-8"
        )
        (self.fixture.root / "metadata").mkdir()
        (self.fixture.root / "metadata" / "skill_specs.json").write_text(
            json.dumps({"skills": list(self.fixture.skill_specs.values())}, indent=2) + "\n",
            encoding="utf-8",
        )

    def tearDown(self) -> None:
        self.fixture.close()

    def receipt(self) -> dict:
        return build_matter_plan(
            self.fixture.root,
            self.plan,
            matter_inputs={
                "question": "Secret acquisition strategy and client facts",
                "jurisdiction": "California",
                "include-optional": "no",
            },
            skill_specs=self.fixture.skill_specs,
        )["receipt"]

    def test_receipt_contains_no_sensitive_raw_value(self):
        receipt = self.receipt()
        serialized = json.dumps(receipt)
        self.assertNotIn("Secret acquisition strategy", serialized)
        question = next(item for item in receipt["input_presence"] if item["id"] == "question")
        self.assertTrue(question["present"])
        self.assertNotIn("routing_value", question)

    def test_receipt_is_deterministic(self):
        first = self.receipt()
        second = self.receipt()
        self.assertEqual(first, second)
        self.assertRegex(first["receipt_sha256"], r"^[0-9a-f]{64}$")

    def test_plan_file_drift_fails_verification(self):
        receipt = self.receipt()
        self.plan["description"] = "Changed after execution"
        (self.fixture.root / "matter-plans" / "sample-plan.json").write_text(
            json.dumps(self.plan, indent=2) + "\n", encoding="utf-8"
        )
        result = verify_matter_plan_receipt(self.fixture.root, receipt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("plan" in error and "changed" in error for error in result["errors"]))

    def test_skill_contract_drift_fails_verification(self):
        receipt = self.receipt()
        registry = {"skills": list(self.fixture.skill_specs.values())}
        registry["skills"][0]["description"] = "drift"
        (self.fixture.root / "metadata" / "skill_specs.json").write_text(
            json.dumps(registry, indent=2) + "\n", encoding="utf-8"
        )
        result = verify_matter_plan_receipt(self.fixture.root, receipt)
        self.assertFalse(result["valid"])
        self.assertTrue(any("contract" in error and "changed" in error for error in result["errors"]))

    def test_artifact_lineage_tampering_fails_verification(self):
        receipt = self.receipt()
        receipt["artifact_lineage"][0]["produced_by"] = "optional"
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("lineage" in error for error in result["errors"]))

    def test_node_state_tampering_fails_verification(self):
        receipt = self.receipt()
        receipt["node_states"][0]["state"] = "completed"
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("node state" in error for error in result["errors"]))

    def test_token_arithmetic_tampering_fails_verification(self):
        receipt = self.receipt()
        receipt["budget"]["ready_context_tokens"] += 1
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("budget" in error or "token" in error for error in result["errors"]))

    def test_unsafe_receipt_path_fails_verification(self):
        receipt = self.receipt()
        receipt["plan_path"] = "../outside.json"
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("unsafe" in error or "path" in error for error in result["errors"]))

    def test_rehashed_receipt_with_raw_input_field_is_rejected(self):
        receipt = self.receipt()
        receipt["raw_inputs"] = {"question": "Secret acquisition strategy"}
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("unexpected receipt field" in error for error in result["errors"]))

    def test_nested_raw_input_injection_is_rejected(self):
        receipt = self.receipt()
        receipt["input_presence"][0]["raw"] = "Secret acquisition strategy"
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("input presence" in error for error in result["errors"]))

    def test_missing_skill_contract_record_is_rejected(self):
        receipt = self.receipt()
        receipt["skill_contracts"].pop()
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("skill contract" in error for error in result["errors"]))

    def test_bundle_fingerprint_tampering_is_rejected(self):
        receipt = self.receipt()
        receipt["ready_contexts"][0]["bundle_sha256"] = "0" * 64
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("ready context" in error for error in result["errors"]))

    def test_source_path_substitution_is_rejected(self):
        receipt = self.receipt()
        other = self.fixture.root / "playbooks" / "other.md"
        other.write_text("# Other\n", encoding="utf-8")
        receipt["source_path"] = "playbooks/other.md"
        receipt["source_sha256"] = hashlib.sha256(other.read_bytes()).hexdigest()
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("source path" in error for error in result["errors"]))

    def test_explicit_context_selection_receipt_round_trip(self):
        plan = self.fixture.plan()
        result = build_matter_plan(
            self.fixture.root,
            plan,
            matter_inputs={
                "question": "Secret acquisition strategy and client facts",
                "jurisdiction": "California",
                "include-optional": "yes",
            },
            explicit_node_ids=["draft"],
            skill_specs=self.fixture.skill_specs,
        )
        verification = verify_matter_plan_receipt(self.fixture.root, result["receipt"])
        self.assertTrue(verification["valid"], verification["errors"])
        self.assertEqual(result["receipt"]["context_node_ids"], ["draft"])

    def test_receipt_version_tampering_is_rejected(self):
        receipt = self.receipt()
        receipt["receipt_version"] = "9.9"
        result = verify_matter_plan_receipt(self.fixture.root, rehash(receipt))
        self.assertFalse(result["valid"])
        self.assertTrue(any("receipt version" in error for error in result["errors"]))


if __name__ == "__main__":
    unittest.main()
