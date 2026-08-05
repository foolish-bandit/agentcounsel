#!/usr/bin/env python3
"""MCP catalog service coverage for Matter Graph v1."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from agentcounsel_mcp import CatalogService

ROOT = Path(__file__).resolve().parent.parent


class TestMatterPlanMCP(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.service = CatalogService.from_root(ROOT)

    def test_lists_and_searches_matter_plans(self):
        plans = self.service.list_matter_plans()
        self.assertEqual([item["plan_id"] for item in plans], sorted(item["plan_id"] for item in plans))
        self.assertEqual(len(plans), 4)
        results = self.service.search_matter_plans("motion opposition")
        self.assertEqual(results[0]["plan_id"], "litigation-motion-opposition")

    def test_get_resolves_title_alias(self):
        plan = self.service.get_matter_plan("Legal Research Memo")
        self.assertEqual(plan["plan_id"], "legal-research-memo")
        self.assertGreater(len(plan["nodes"]), 1)

    def test_build_returns_ready_and_blocked_without_eager_context(self):
        result = self.service.build_matter_plan(
            "legal-research-memo",
            matter_inputs={
                "legal-question": "What is the rule?",
                "known-facts": {"fact": "provided"},
                "jurisdiction": "California",
                "existing-authorities": ["authority.pdf"],
                "relevant-date": "2026-08-04",
                "time-and-scope": "Two-hour scoped review",
            },
        )
        states = {node["id"]: node for node in result["nodes"]}
        self.assertEqual(states["research-plan"]["state"], "ready")
        self.assertIn("context", states["research-plan"])
        self.assertEqual(states["authority-synthesis"]["state"], "blocked")
        self.assertNotIn("context", states["authority-synthesis"])

    def test_receipt_verification_round_trip(self):
        built = self.service.build_matter_plan(
            "commercial-contract-review",
            matter_inputs={
                "agreement": "agreement.pdf",
                "client-role": "customer",
                "business-context": "software purchase",
                "has-sow": "no",
                "has-prior-redline": "no",
                "review-date": "2026-08-04",
                "jurisdiction": "California",
                "distribution-plan": "internal legal team",
                "matter-context": "matter workspace",
            },
        )
        verification = self.service.verify_matter_plan_receipt(built["receipt"])
        self.assertEqual(verification, {"valid": True, "errors": []})

    def test_transport_source_exposes_plan_tools(self):
        source = (ROOT / "mcp_server.py").read_text(encoding="utf-8")
        for name in (
            "list_matter_plans",
            "search_matter_plans",
            "get_matter_plan",
            "build_matter_plan",
            "verify_matter_plan_receipt",
        ):
            self.assertIn(f"def {name}(", source)


if __name__ == "__main__":
    unittest.main()
