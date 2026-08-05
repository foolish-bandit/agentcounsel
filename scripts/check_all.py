#!/usr/bin/env python3
"""Run the full local validation suite AgentCounsel's CI runs.

Mirrors .github/workflows/validate.yml step for step, in order, stopping at
the first failure. Standard library only — no third-party packages. Each
step is invoked as a subprocess (via sys.executable), matching how CI shells
out to the same sibling scripts; that is acceptable here since this is a
dev entry point, not a library module other scripts import.

    python scripts/check_all.py            # full suite, same order as CI
    python scripts/check_all.py --quick     # the three core structural checks

Exit code 0 if every step run passes, 1 on the first failing step.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

# Mirrors .github/workflows/validate.yml, in the same order. Each entry is
# (label, argv) where argv[0] is a script under scripts/ (or a repo-relative
# command) run with sys.executable / node as appropriate.
FULL_SUITE = [
    ("Check plugin bundle is in sync with canonical skills",
     [sys.executable, "scripts/sync_plugin_skills.py", "--check"]),
    ("Validate repository",
     [sys.executable, "scripts/validate_repo.py"]),
    ("Run tooling unit tests",
     [sys.executable, "-m", "unittest", "discover", "-s", "tests"]),
    ("Check skill metadata and router are up to date",
     [sys.executable, "scripts/build_skill_index.py", "--check"]),
    ("Check typed skill contract registry is up to date",
     [sys.executable, "scripts/build_skill_specs.py", "--check"]),
    ("Check selective context metrics and budgets",
     [sys.executable, "scripts/generate_selective_context_metrics.py", "--check"]),
    ("Check matter-plan registry and budgets",
     [sys.executable, "scripts/build_matter_plans.py", "--check"]),
    ("Evaluate matter plans and mutation sensitivity",
     [sys.executable, "scripts/evaluate_matter_plans.py", "--check"]),
    ("Check platform pack manifest is up to date",
     [sys.executable, "scripts/build_platform_packs.py", "--check"]),
    ("Check context metrics are up to date",
     [sys.executable, "scripts/generate_context_metrics.py", "--check"]),
    ("Check skill readiness reports are up to date",
     [sys.executable, "scripts/generate_skill_health_report.py", "--check"]),
    ("Validate skill eval framework",
     [sys.executable, "scripts/check_evals.py"]),
    ("Run skill eval candidates (static, --strict)",
     [sys.executable, "scripts/run_evals.py", "--strict", "--quiet"]),
    ("Check legal prose of repository-owned work-product samples",
     [sys.executable, "scripts/check_legal_prose.py"]),
    ("Check eval coverage report is up to date",
     [sys.executable, "scripts/generate_eval_report.py", "--check"]),
    ("Check skill-improvement reports are up to date",
     [sys.executable, "scripts/generate_skill_improvement_prompts.py", "--check"]),
    ("Check generated cold-start interviews are in sync",
     [sys.executable, "scripts/generate_cold_start_interviews.py", "--check"]),
    ("Build static site (verification only)",
     ["node", "site/generate.mjs"]),
]

# The minimum trio a contributor should run before any commit — the same
# three AGENTS.md calls "Done means validation passes".
QUICK_SUITE_LABELS = {
    "Check plugin bundle is in sync with canonical skills",
    "Validate repository",
    "Validate skill eval framework",
}


def run_step(label: str, argv: list[str]) -> bool:
    print(f"==> {label}")
    print(f"    $ {' '.join(argv)}")
    result = subprocess.run(argv, cwd=REPO_ROOT)
    print()
    return result.returncode == 0


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run the full local validation suite (same steps and "
                    "order as .github/workflows/validate.yml), or just the "
                    "quick core trio with --quick. Stops at the first "
                    "failing step.",
    )
    parser.add_argument(
        "--quick", action="store_true",
        help="Run only the three core checks: sync_plugin_skills --check, "
             "validate_repo, and check_evals.",
    )
    args = parser.parse_args()

    steps = (
        [(label, argv) for label, argv in FULL_SUITE if label in QUICK_SUITE_LABELS]
        if args.quick else FULL_SUITE
    )

    print(f"AgentCounsel check_all — {'quick (3 core checks)' if args.quick else 'full CI-equivalent suite'}")
    print()

    passed = 0
    for label, argv in steps:
        if not run_step(label, argv):
            print(f"FAILED at step {passed + 1}/{len(steps)}: {label}")
            return 1
        passed += 1

    print(f"All {passed} checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
