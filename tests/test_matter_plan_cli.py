#!/usr/bin/env python3
"""CLI behavior for Matter Graph v1."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CLI = ROOT / "scripts" / "matter_plan_cli.py"


class TestMatterPlanCLI(unittest.TestCase):
    def run_cli(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(CLI), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
        )

    def test_list_and_show(self):
        listed = self.run_cli("list")
        self.assertEqual(listed.returncode, 0, listed.stderr)
        data = json.loads(listed.stdout)
        self.assertEqual(data["plan_count"], 4)
        shown = self.run_cli("show", "legal-research-memo")
        self.assertEqual(shown.returncode, 0, shown.stderr)
        self.assertEqual(json.loads(shown.stdout)["plan_id"], "legal-research-memo")

    def test_show_markdown_summary(self):
        result = self.run_cli("show", "legal-research-memo", "--markdown")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("# Legal Research Memo", result.stdout)
        self.assertIn("## Nodes", result.stdout)
        self.assertIn("`approve-research-scope`", result.stdout)
        self.assertIn("attorney-gate", result.stdout)

    def test_build_and_verify(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp = Path(tmp)
            inputs = tmp / "inputs.json"
            inputs.write_text(json.dumps({
                "legal-question": "What is the rule?",
                "known-facts": {"fact": "provided"},
                "jurisdiction": "California",
                "existing-authorities": ["authority.pdf"],
                "relevant-date": "2026-08-04",
                "time-and-scope": "Scoped review",
            }), encoding="utf-8")
            receipt = tmp / "receipt.json"
            built = self.run_cli("build", "legal-research-memo", "--inputs", str(inputs), "--receipt-output", str(receipt))
            self.assertEqual(built.returncode, 0, built.stderr)
            self.assertTrue(receipt.is_file())
            verified = self.run_cli("verify", str(receipt))
            self.assertEqual(verified.returncode, 0, verified.stderr)
            self.assertTrue(json.loads(verified.stdout)["valid"])

    def test_markdown_run_sheet(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "inputs.json"
            path.write_text(json.dumps({
                "agreement": "agreement.pdf", "client-role": "customer",
                "business-context": "software", "has-sow": "no",
                "has-prior-redline": "no", "review-date": "2026-08-04",
                "jurisdiction": "California", "distribution-plan": "internal",
                "matter-context": "workspace",
            }), encoding="utf-8")
            result = self.run_cli("build", "commercial-contract-review", "--inputs", str(path), "--markdown")
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("# Commercial Contract Review", result.stdout)
            self.assertIn("Ready", result.stdout)
            self.assertIn("Blocked", result.stdout)

    def test_invalid_json_unknown_plan_and_gate_decision_fail(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / "bad.json"
            bad.write_text("{", encoding="utf-8")
            self.assertNotEqual(self.run_cli("build", "legal-research-memo", "--inputs", str(bad)).returncode, 0)
        self.assertNotEqual(self.run_cli("show", "missing-plan").returncode, 0)
        with tempfile.TemporaryDirectory() as tmp:
            gates = Path(tmp) / "gates.json"
            gates.write_text(json.dumps({"approve-research-scope": "maybe"}), encoding="utf-8")
            self.assertNotEqual(self.run_cli("build", "legal-research-memo", "--gates", str(gates)).returncode, 0)


if __name__ == "__main__":
    unittest.main()
