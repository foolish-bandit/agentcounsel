#!/usr/bin/env python3
"""Unit tests for the new structural checks in scripts/validate_repo.py.

Each test builds a tiny synthetic repo layout under a tempfile directory and
points validate_repo.REPO_ROOT at it, so these run against fixtures rather
than the real library. Standard library only (unittest); no network.

    python -m unittest discover -s tests        # from the repo root
"""

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import validate_repo as vr  # noqa: E402


class _FixtureTestCase(unittest.TestCase):
    """Points vr.REPO_ROOT at a scratch directory and resets vr.errors."""

    def setUp(self):
        self._tmpdir = tempfile.TemporaryDirectory()
        self.tmp = Path(self._tmpdir.name)
        self._orig_repo_root = vr.REPO_ROOT
        self._orig_errors = vr.errors
        vr.REPO_ROOT = self.tmp
        vr.errors = []

    def tearDown(self):
        vr.REPO_ROOT = self._orig_repo_root
        vr.errors = self._orig_errors
        self._tmpdir.cleanup()


MATTER_PACK_OK = """# Sample Matter Packs

## 1. Sample Matter Pack

**When to use:** a sample situation.

**Required starting materials:** the sample facts.

**Recommended skill sequence:** `skills/sample/one/SKILL.md`.

**Expected outputs:** a sample memo.

**Do-not-use boundaries:** do not use for anything real.

**Handoff notes:** none.
"""


class TestCheckMatterPacks(_FixtureTestCase):
    def test_passes_when_all_labels_present(self):
        (self.tmp / "matter-packs").mkdir()
        (self.tmp / "matter-packs" / "sample.md").write_text(
            MATTER_PACK_OK, encoding="utf-8")
        orig_min = vr.MATTER_PACKS_MIN_COUNT
        vr.MATTER_PACKS_MIN_COUNT = 1
        try:
            vr.check_matter_packs()
        finally:
            vr.MATTER_PACKS_MIN_COUNT = orig_min
        self.assertEqual(vr.errors, [])

    def test_flags_missing_label(self):
        broken = MATTER_PACK_OK.replace(
            "**Do-not-use boundaries:** do not use for anything real.\n\n", "")
        (self.tmp / "matter-packs").mkdir()
        (self.tmp / "matter-packs" / "sample.md").write_text(
            broken, encoding="utf-8")
        orig_min = vr.MATTER_PACKS_MIN_COUNT
        vr.MATTER_PACKS_MIN_COUNT = 1
        try:
            vr.check_matter_packs()
        finally:
            vr.MATTER_PACKS_MIN_COUNT = orig_min
        self.assertTrue(
            any("Do-not-use boundaries" in e for e in vr.errors), vr.errors)

    def test_flags_too_few_packs(self):
        (self.tmp / "matter-packs").mkdir()
        (self.tmp / "matter-packs" / "sample.md").write_text(
            MATTER_PACK_OK, encoding="utf-8")
        vr.check_matter_packs()  # MATTER_PACKS_MIN_COUNT unmodified (9)
        self.assertTrue(any("expected at least" in e for e in vr.errors), vr.errors)


CONNECTOR_OK = """# Sample Connector

## 1. Source

Sample source.

## 2. In scope — what Sample can verify

Sample scope.

## 3. Out of scope — what Sample does not cover

Sample out-of-scope note.

## 4. Surface — where to hit

Sample surface.

## 5. Calling pattern from a skill

Sample calling pattern.

## 6. Fallback behavior

Sample fallback.

## 7. Limits and known failure modes

Sample limits.
"""


class TestCheckConnectors(_FixtureTestCase):
    def test_passes_when_all_headings_present(self):
        (self.tmp / "connectors").mkdir()
        (self.tmp / "connectors" / "sample.md").write_text(
            CONNECTOR_OK, encoding="utf-8")
        vr.check_connectors()
        self.assertEqual(vr.errors, [])

    def test_flags_missing_heading(self):
        broken = CONNECTOR_OK.replace("## 6. Fallback behavior\n\n"
                                       "Sample fallback.\n\n", "")
        (self.tmp / "connectors").mkdir()
        (self.tmp / "connectors" / "sample.md").write_text(
            broken, encoding="utf-8")
        vr.check_connectors()
        self.assertTrue(
            any("Fallback behavior" in e for e in vr.errors), vr.errors)

    def test_skips_readme(self):
        (self.tmp / "connectors").mkdir()
        (self.tmp / "connectors" / "README.md").write_text(
            "# not a connector doc\n", encoding="utf-8")
        vr.check_connectors()
        self.assertEqual(vr.errors, [])


class TestCheckPracticeAreaDocSync(_FixtureTestCase):
    def _write_doc(self, values: str) -> None:
        (self.tmp / "docs").mkdir()
        (self.tmp / "docs" / "SKILL_METADATA_STANDARD.md").write_text(
            "### `practice_area`\n\n"
            "The practice area the skill belongs to. Current\n"
            f"values: {values}.\n", encoding="utf-8")

    def test_passes_when_sets_match(self):
        self._write_doc("`alpha`, `beta`")
        (self.tmp / "skills" / "alpha").mkdir(parents=True)
        (self.tmp / "skills" / "beta").mkdir(parents=True)
        vr.check_practice_area_doc_sync()
        self.assertEqual(vr.errors, [])

    def test_flags_skill_dir_missing_from_doc(self):
        self._write_doc("`alpha`")
        (self.tmp / "skills" / "alpha").mkdir(parents=True)
        (self.tmp / "skills" / "beta").mkdir(parents=True)
        vr.check_practice_area_doc_sync()
        self.assertTrue(any("beta" in e for e in vr.errors), vr.errors)

    def test_flags_stale_doc_entry(self):
        self._write_doc("`alpha`, `beta`")
        (self.tmp / "skills" / "alpha").mkdir(parents=True)
        vr.check_practice_area_doc_sync()
        self.assertTrue(any("beta" in e for e in vr.errors), vr.errors)


class TestExpectedDirectories(unittest.TestCase):
    def test_matter_plans_is_required_repository_surface(self):
        self.assertIn("matter-plans", vr.EXPECTED_DIRS)


if __name__ == "__main__":
    unittest.main()
