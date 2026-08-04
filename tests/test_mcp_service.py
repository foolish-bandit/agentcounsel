#!/usr/bin/env python3
"""Tests for the standard-library AgentCounsel MCP catalog service."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from agentcounsel_mcp import CatalogLoadError, CatalogService


class CatalogFixture:
    def __init__(self) -> None:
        self.tempdir = tempfile.TemporaryDirectory()
        self.root = Path(self.tempdir.name)
        (self.root / "metadata").mkdir()
        (self.root / "core").mkdir()

        skills = [
            {
                "id": "contracts/nda-review",
                "title": "NDA Review",
                "name": "NDA Review",
                "path": "skills/contracts/nda-review/SKILL.md",
                "summary": "Use when reviewing a non-disclosure or confidentiality agreement.",
                "description": "Use when reviewing a non-disclosure or confidentiality agreement.",
                "use_when": [
                    "Review a mutual NDA before signature.",
                    "Identify confidentiality and non-use risks.",
                ],
                "required_inputs": ["Full NDA text", "Client role"],
                "expected_outputs": ["Triage rating", "Risk table"],
                "practice_area": "contracts",
                "task_type": "review",
                "risk_level": "medium",
                "requires_jurisdiction": True,
                "requires_deadline_check": False,
                "requires_attorney_review": True,
                "recommended_quality_checks": [
                    "attorney-review-gate",
                    "source-validation-check",
                ],
                "tags": ["nda", "confidentiality", "contract-review"],
                "related_skills": ["skills/contracts/contract-risk-review/SKILL.md"],
                "eval_status": "scored",
            },
            {
                "id": "contracts/contract-risk-review",
                "title": "Contract Risk Review",
                "name": "Contract Risk Review",
                "path": "skills/contracts/contract-risk-review/SKILL.md",
                "summary": "Use when reviewing a general commercial agreement for legal and business risk.",
                "description": "Use when reviewing a general commercial agreement for legal and business risk.",
                "use_when": ["Review a services agreement, SaaS agreement, or other commercial contract."],
                "required_inputs": ["Full agreement text", "Client role"],
                "expected_outputs": ["Risk summary", "Issue list"],
                "practice_area": "contracts",
                "task_type": "review",
                "risk_level": "high",
                "requires_jurisdiction": True,
                "requires_deadline_check": True,
                "requires_attorney_review": True,
                "recommended_quality_checks": [
                    "attorney-review-gate",
                    "assumption-audit",
                    "source-validation-check",
                ],
                "tags": ["commercial-contract", "risk-review"],
                "related_skills": ["skills/contracts/nda-review/SKILL.md"],
                "eval_status": "manual-eval-ready",
            },
            {
                "id": "privacy/breach-response-workflow",
                "title": "Breach Response Workflow",
                "name": "Breach Response Workflow",
                "path": "skills/privacy/breach-response-workflow/SKILL.md",
                "summary": "Use when a privacy or security incident is suspected or confirmed.",
                "description": "Use when a privacy or security incident is suspected or confirmed.",
                "use_when": ["Organize ransomware, unauthorized access, or exposed personal data."],
                "required_inputs": ["Incident description", "Discovery date", "Privilege posture"],
                "expected_outputs": ["Incident facts record", "Notification question set"],
                "practice_area": "privacy",
                "task_type": "intake",
                "risk_level": "critical",
                "requires_jurisdiction": True,
                "requires_deadline_check": True,
                "requires_attorney_review": True,
                "recommended_quality_checks": [
                    "attorney-review-gate",
                    "jurisdiction-deadline-gates",
                    "privilege-confidentiality-check",
                ],
                "tags": ["breach-response", "incident-response", "privacy"],
                "related_skills": [],
                "eval_status": "manual-eval-ready",
            },
        ]
        index = {
            "skill_count": len(skills),
            "practice_areas": {"contracts": 2, "privacy": 1},
            "skills": skills,
        }
        router = {
            "workspace_triggers": [
                "multi-step",
                "document-heavy",
                "high-risk",
                "ongoing",
                "deadline-sensitive",
            ],
            "route_types": ["one-off skill", "matter workspace", "quality check"],
        }
        specs = {
            "schema_version": "2.0",
            "skill_count": 3,
            "custom_spec_count": 2,
            "legacy_compiled_count": 1,
            "custom_specs_by_practice_area": {"contracts": 1, "privacy": 1},
            "skills": [
                self._spec(
                    "contracts/nda-review",
                    custom=True,
                    required_inputs=[
                        self._input("full-nda-text", "Full NDA text", "document"),
                        self._input(
                            "client-role",
                            "Client role",
                            "enum",
                            enum=["disclosing", "receiving", "mutual"],
                        ),
                    ],
                    deadline=False,
                    escalation="attorney-review",
                    custom_gates=[
                        {
                            "id": "specialist-context",
                            "condition": "The NDA is part of a specialist transaction.",
                            "action": "stop-and-escalate",
                            "reason": "Specialist review is required.",
                        }
                    ],
                    checks=["attorney-review-gate", "source-validation-check"],
                ),
                self._spec(
                    "contracts/contract-risk-review",
                    custom=False,
                    required_inputs=[
                        self._input("full-agreement-text", "Full agreement text", "document"),
                        self._input("client-role", "Client role", "text"),
                    ],
                    deadline=True,
                    escalation="attorney-escalation",
                    custom_gates=[],
                    checks=[
                        "attorney-review-gate",
                        "assumption-audit",
                        "source-validation-check",
                    ],
                ),
                self._spec(
                    "privacy/breach-response-workflow",
                    custom=True,
                    required_inputs=[
                        self._input("incident-description", "Incident description", "object", sensitive=True),
                        self._input("discovery-date", "Discovery date", "date", sensitive=True),
                        self._input("privilege-posture", "Privilege posture", "object", sensitive=True),
                    ],
                    deadline=True,
                    escalation="immediate-attorney-attention",
                    custom_gates=[
                        {
                            "id": "deadline-calculation-prohibited",
                            "condition": "A due date is requested.",
                            "action": "stop-and-escalate",
                            "reason": "The workflow never calculates legal deadlines.",
                        }
                    ],
                    checks=[
                        "attorney-review-gate",
                        "jurisdiction-deadline-gates",
                        "privilege-confidentiality-check",
                    ],
                ),
            ],
        }
        nda_spec = specs["skills"][0]
        nda_spec["modules"] = [
            {
                "id": "common-review",
                "kind": "workflow-module",
                "path": "skills/contracts/nda-review/modules/common-review.md",
                "required": False,
                "load_when": "Standard and deep review modes.",
                "activation": {
                    "modes": ["standard", "deep-review"],
                    "operator": "always",
                },
            },
            {
                "id": "receiving-party",
                "kind": "workflow-module",
                "path": "skills/contracts/nda-review/modules/receiving-party.md",
                "required": False,
                "load_when": "The client is receiving information.",
                "activation": {
                    "modes": ["standard", "deep-review"],
                    "input_id": "client-role",
                    "operator": "equals",
                    "value": "receiving",
                },
            },
            {
                "id": "expanded-verification",
                "kind": "quality-check",
                "path": "skills/contracts/nda-review/modules/expanded-verification.md",
                "required": False,
                "load_when": "Deep review mode.",
                "activation": {
                    "modes": ["deep-review"],
                    "operator": "always",
                },
            },
        ]
        (self.root / "metadata" / "index.json").write_text(
            json.dumps(index), encoding="utf-8"
        )
        (self.root / "metadata" / "router.json").write_text(
            json.dumps(router), encoding="utf-8"
        )
        (self.root / "metadata" / "skill_specs.json").write_text(
            json.dumps(specs), encoding="utf-8"
        )
        (self.root / "core" / "legal-work-product.md").write_text(
            "# Legal Work Product\n\nDraft for attorney review.\n", encoding="utf-8"
        )

        for skill in skills:
            path = self.root / skill["path"]
            path.parent.mkdir(parents=True, exist_ok=True)
            repeated = "\n".join(["NDA confidentiality boilerplate." for _ in range(40)])
            body = repeated if skill["id"] == "contracts/contract-risk-review" else "Specific body."
            path.write_text(
                f"---\nname: {skill['title']}\n---\n# {skill['title']}\n\n{body}\n",
                encoding="utf-8",
            )

        nda_modules = self.root / "skills" / "contracts" / "nda-review" / "modules"
        nda_modules.mkdir()
        (nda_modules / "common-review.md").write_text(
            "# Common Review\n\nReview scope and confidentiality definitions.\n",
            encoding="utf-8",
        )
        (nda_modules / "receiving-party.md").write_text(
            "# Receiving Party\n\nReview use restrictions and residuals.\n",
            encoding="utf-8",
        )
        (nda_modules / "expanded-verification.md").write_text(
            "# Expanded Verification\n\nVerify every material issue.\n",
            encoding="utf-8",
        )

    @staticmethod
    def _input(
        field_id: str,
        label: str,
        field_type: str,
        *,
        sensitive: bool = False,
        enum: list[str] | None = None,
    ) -> dict:
        field = {
            "id": field_id,
            "label": label,
            "type": field_type,
            "required": True,
            "description": label,
            "source_requirement": "user-provided",
            "may_infer": False,
            "sensitive": sensitive,
        }
        if enum is not None:
            field["enum"] = enum
        return field

    @staticmethod
    def _spec(
        skill_id: str,
        *,
        custom: bool,
        required_inputs: list[dict],
        deadline: bool,
        escalation: str,
        custom_gates: list[dict],
        checks: list[str],
    ) -> dict:
        return {
            "schema_version": "2.0",
            "skill_id": skill_id,
            "title": skill_id.rsplit("/", 1)[-1].replace("-", " ").title(),
            "skill_path": f"skills/{skill_id}/SKILL.md",
            "spec_path": f"skills/{skill_id}/SPEC.json" if custom else None,
            "has_custom_spec": custom,
            "inherits": ["core/legal-work-product.md"],
            "gates": {
                "missing_inputs": {"behavior": "stop-and-ask"},
                "attorney_review": {"required": True},
                "jurisdiction": {"required": True},
                "deadline": {
                    "required": deadline,
                    "calculation_allowed": False,
                },
                "escalation": {"minimum": escalation},
                "custom": custom_gates,
            },
            "execution_modes": [
                {
                    "id": "quick-triage",
                    "enabled": True,
                    "purpose": "Triage only.",
                    "output_detail": "minimal",
                    "quality_checks": ["attorney-review-gate"],
                },
                {
                    "id": "standard",
                    "enabled": True,
                    "purpose": "Standard work product.",
                    "output_detail": "standard",
                    "quality_checks": checks,
                },
                {
                    "id": "deep-review",
                    "enabled": True,
                    "purpose": "Expanded verification.",
                    "output_detail": "expanded",
                    "quality_checks": checks,
                },
            ],
            "input_schema": required_inputs,
            "output_schema": [],
            "evidence_schema": {
                "record_type": "claim-support",
                "required_fields": [
                    "claim_id",
                    "source_document_id",
                    "locator",
                    "support_type",
                    "verification_status",
                ],
                "fields": [],
            },
            "modules": [],
            "quality_checks": checks,
        }

    def close(self) -> None:
        self.tempdir.cleanup()


class TestCatalogService(unittest.TestCase):
    def setUp(self) -> None:
        self.fixture = CatalogFixture()
        self.service = CatalogService.from_root(self.fixture.root)

    def tearDown(self) -> None:
        self.fixture.close()

    def test_loads_generated_metadata_and_preserves_lists(self):
        card = self.service.get_skill_card("contracts/nda-review")
        self.assertEqual(card["id"], "contracts/nda-review")
        self.assertEqual(card["required_inputs"], ["Full NDA text", "Client role"])
        self.assertEqual(card["tags"], ["nda", "confidentiality", "contract-review"])

    def test_list_practice_areas_uses_generated_counts(self):
        self.assertEqual(
            self.service.list_practice_areas(),
            [
                {"practice_area": "contracts", "skill_count": 2},
                {"practice_area": "privacy", "skill_count": 1},
            ],
        )

    def test_search_returns_stable_ids_and_exact_id_first(self):
        results = self.service.search_skills("contracts/nda-review")
        self.assertEqual(results[0]["id"], "contracts/nda-review")
        self.assertGreater(results[0]["relevance_score"], 0)

    def test_trigger_metadata_outweighs_repeated_body_boilerplate(self):
        results = self.service.search_skills("review NDA confidentiality")
        self.assertEqual(results[0]["id"], "contracts/nda-review")

    def test_practice_area_filter(self):
        results = self.service.search_skills("incident", practice_area="privacy")
        self.assertEqual([item["id"] for item in results], ["privacy/breach-response-workflow"])

    def test_get_skill_accepts_slug_title_and_path_aliases(self):
        for alias in (
            "nda-review",
            "NDA Review",
            "skills/contracts/nda-review/SKILL.md",
        ):
            record = self.service.get_skill(alias)
            self.assertEqual(record["id"], "contracts/nda-review")
            self.assertIn("# NDA Review", record["content"])

    def test_compact_card_omits_content(self):
        card = self.service.get_skill_card("nda-review")
        self.assertNotIn("content", card)
        self.assertEqual(card["id"], "contracts/nda-review")

    def test_get_skill_spec_uses_existing_alias_resolution(self):
        for alias in ("contracts/nda-review", "nda-review", "NDA Review"):
            spec = self.service.get_skill_spec(alias)
            self.assertEqual(spec["skill_id"], "contracts/nda-review")
            self.assertEqual(spec["schema_version"], "2.0")
            self.assertTrue(spec["has_custom_spec"])
            self.assertEqual(spec["input_schema"][0]["id"], "full-nda-text")

    def test_get_skill_context_selects_modules_and_returns_reproducible_bundle(self):
        bundle = self.service.get_skill_context(
            "nda-review",
            mode="standard",
            inputs={
                "full-nda-text": "Fictional NDA text",
                "client-role": "receiving",
            },
        )
        self.assertEqual(bundle["skill_id"], "contracts/nda-review")
        self.assertEqual(
            [module["id"] for module in bundle["modules"]],
            ["common-review", "receiving-party"],
        )
        self.assertTrue(all(module["reason"] for module in bundle["modules"]))
        self.assertEqual(
            {item["id"]: item["status"] for item in bundle["selection_trace"]},
            {
                "common-review": "selected",
                "receiving-party": "selected",
                "expanded-verification": "not-selected",
            },
        )
        self.assertGreater(bundle["estimated_tokens"]["total"], 0)
        self.assertRegex(bundle["contract_sha256"], r"^[0-9a-f]{64}$")
        self.assertRegex(bundle["bundle_sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(bundle["complete"])

    def test_get_skill_context_missing_activation_input_fails_closed(self):
        bundle = self.service.get_skill_context(
            "contracts/nda-review",
            mode="standard",
            inputs={"full-nda-text": "Fictional NDA text"},
        )
        self.assertEqual(
            [module["id"] for module in bundle["modules"]],
            ["common-review"],
        )
        self.assertEqual(
            [module["id"] for module in bundle["unresolved_modules"]],
            ["receiving-party"],
        )
        self.assertEqual(bundle["missing_required_inputs"], ["client-role"])
        self.assertFalse(bundle["complete"])

    def test_route_uses_typed_contract_inputs_modes_and_gates(self):
        route = self.service.route_task("Review this NDA before signature", limit=2)
        self.assertEqual(route["status"], "matched")
        self.assertEqual(route["primary_route"]["id"], "contracts/nda-review")
        self.assertEqual(route["route_type"], "one-off skill")
        self.assertEqual(route["spec_version"], "2.0")
        self.assertEqual(
            [item["id"] for item in route["missing_required_inputs"]],
            ["full-nda-text", "client-role"],
        )
        self.assertEqual(
            route["missing_input_labels"], ["Full NDA text", "Client role"]
        )
        self.assertEqual(
            [mode["id"] for mode in route["execution_modes"]],
            ["quick-triage", "standard", "deep-review"],
        )
        self.assertEqual(route["custom_gates"][0]["id"], "specialist-context")
        self.assertIn("attorney-review-gate", route["mandatory_quality_checks"])
        self.assertTrue(route["gates"]["jurisdiction"])
        self.assertFalse(route["gates"]["deadline"])
        self.assertTrue(route["gates"]["attorney_review"])
        self.assertFalse(route["escalation_required"])
        self.assertEqual(len(route["alternative_routes"]), 1)
        self.assertIn(route["confidence"], {"low", "medium", "high"})
        self.assertTrue(route["why_selected"])

    def test_critical_skill_uses_compiled_escalation_and_deadline_gate(self):
        route = self.service.route_task("Organize a ransomware breach incident")
        self.assertEqual(route["primary_route"]["id"], "privacy/breach-response-workflow")
        self.assertTrue(route["escalation_required"])
        self.assertEqual(
            route["escalation_minimum"], "immediate-attorney-attention"
        )
        self.assertTrue(route["gates"]["deadline"])
        self.assertFalse(route["deadline_calculation_allowed"])
        self.assertEqual(
            route["custom_gates"][0]["id"], "deadline-calculation-prohibited"
        )

    def test_workspace_trigger_changes_route_type(self):
        route = self.service.route_task(
            "This is an ongoing multi-step document-heavy contract matter"
        )
        self.assertEqual(route["route_type"], "matter workspace")

    def test_no_match_is_explicit(self):
        route = self.service.route_task("quantum gardening telescope")
        self.assertEqual(route["status"], "no_match")
        self.assertIsNone(route["primary_route"])
        self.assertEqual(route["alternative_routes"], [])
        self.assertEqual(route["missing_required_inputs"], [])

    def test_empty_query_and_invalid_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.service.search_skills("   ")
        with self.assertRaises(ValueError):
            self.service.search_skills("nda", limit=0)

    def test_unknown_skill_raises_key_error(self):
        with self.assertRaises(KeyError):
            self.service.get_skill_card("missing/skill")
        with self.assertRaises(KeyError):
            self.service.get_skill_spec("missing/skill")


class TestCatalogLoadErrors(unittest.TestCase):
    def test_missing_metadata_raises_descriptive_error(self):
        with tempfile.TemporaryDirectory() as tempdir:
            with self.assertRaises(CatalogLoadError) as ctx:
                CatalogService.from_root(Path(tempdir))
        self.assertIn("metadata/index.json", str(ctx.exception))

    def test_missing_skill_spec_registry_is_rejected(self):
        fixture = CatalogFixture()
        try:
            (fixture.root / "metadata" / "skill_specs.json").unlink()
            with self.assertRaises(CatalogLoadError) as ctx:
                CatalogService.from_root(fixture.root)
            self.assertIn("metadata/skill_specs.json", str(ctx.exception))
        finally:
            fixture.close()


if __name__ == "__main__":
    unittest.main()
