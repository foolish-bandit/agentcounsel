#!/usr/bin/env python3
"""Static-site coverage for accessible Matter Graph v1 pages."""

from __future__ import annotations

import json
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PUBLIC = ROOT / "site" / "public" / "matter-plans"


class TestSiteMatterPlans(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        result = subprocess.run(["node", "site/generate.mjs"], cwd=ROOT, text=True, capture_output=True)
        if result.returncode:
            raise RuntimeError(result.stderr)
        cls.registry = json.loads((ROOT / "metadata" / "matter_plans.json").read_text(encoding="utf-8"))

    def test_index_lists_every_registered_plan(self):
        html = (PUBLIC / "index.html").read_text(encoding="utf-8")
        for card in self.registry["plans"]:
            self.assertIn(card["title"], html)
            self.assertIn(f'{card["plan_id"]}.html', html)

    def test_each_plan_has_accessible_svg_and_complete_text_edge_list(self):
        for card in self.registry["plans"]:
            plan = json.loads((ROOT / card["path"]).read_text(encoding="utf-8"))
            html = (PUBLIC / f'{card["plan_id"]}.html').read_text(encoding="utf-8")
            with self.subTest(plan_id=card["plan_id"]):
                self.assertIn('<svg class="matter-graph" role="img"', html)
                self.assertIn('aria-labelledby="graph-title graph-desc"', html)
                for node in plan["nodes"]:
                    for dep in node.get("depends_on", []):
                        self.assertIn(f'{dep} → {node["id"]}', html)

    def test_skill_nodes_link_to_canonical_skill_pages_and_gates_are_labeled(self):
        plan = json.loads((ROOT / "matter-plans" / "litigation-motion-opposition.json").read_text(encoding="utf-8"))
        html = (PUBLIC / "litigation-motion-opposition.html").read_text(encoding="utf-8")
        for node in plan["nodes"]:
            if node["type"] == "skill":
                area, slug = node["skill_id"].split("/", 1)
                self.assertIn(f'../skills/{area}/{slug}.html', html)
            else:
                self.assertIn(f'Attorney gate: {node["id"]}', html)

    def test_raw_json_is_copyable_and_no_graph_dependency_is_bundled(self):
        html = (PUBLIC / "legal-research-memo.html").read_text(encoding="utf-8")
        self.assertIn('data-copy="matter-plan-json"', html)
        self.assertIn('id="matter-plan-json"', html)
        combined = html + (ROOT / "site" / "assets" / "app.js").read_text(encoding="utf-8")
        for dependency in ("mermaid", "d3.js", "dagre", "cytoscape"):
            self.assertNotIn(dependency, combined.lower())

    def test_shared_navigation_links_matter_plans(self):
        home = (ROOT / "site" / "public" / "index.html").read_text(encoding="utf-8")
        self.assertIn('matter-plans/index.html', home)
        self.assertIn('Matter plans', home)


if __name__ == "__main__":
    unittest.main()
