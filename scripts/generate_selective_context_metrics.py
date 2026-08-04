#!/usr/bin/env python3
"""Generate and enforce deterministic selective-context scenario budgets.

The estimates use AgentCounsel's existing one-token-per-four-characters
approximation. They are context-planning signals, not provider token counts,
latency measurements, or billing data.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from skill_context import build_skill_context

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_OUTPUT = Path("metadata/selective_context_metrics.json")
MARKDOWN_OUTPUT = Path("reports/selective-context.md")


def _read_registry(root: Path) -> dict[str, Any]:
    path = root / "metadata" / "skill_specs.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"Could not read {path}: {exc}") from exc
    if not isinstance(data, dict) or not isinstance(data.get("skills"), list):
        raise RuntimeError(f"Expected a skill-spec registry object in {path}")
    return data


def collect_metrics(root: Path | str = REPO_ROOT) -> dict[str, Any]:
    """Build every declared scenario and return deterministic measurements."""
    root = Path(root).resolve()
    registry = _read_registry(root)
    records: list[dict[str, Any]] = []

    specs = [spec for spec in registry["skills"] if isinstance(spec, dict)]
    specs.sort(key=lambda item: str(item.get("skill_id", "")))
    for spec in specs:
        skill_id = spec.get("skill_id")
        scenarios = spec.get("context_scenarios", [])
        if not isinstance(skill_id, str) or not isinstance(scenarios, list):
            continue
        for scenario in scenarios:
            if not isinstance(scenario, dict):
                continue
            bundle = build_skill_context(
                root,
                spec,
                str(scenario["mode"]),
                scenario.get("inputs", {}),
            )
            baseline = int(scenario["baseline_estimated_tokens"])
            total = int(bundle["estimated_tokens"]["total"])
            raw_ratio = total / baseline
            max_ratio = float(scenario["max_ratio"])
            records.append(
                {
                    "skill_id": skill_id,
                    "scenario_id": str(scenario["id"]),
                    "mode": str(scenario["mode"]),
                    "selected_module_ids": [
                        str(module["id"]) for module in bundle["modules"]
                    ],
                    "selection_trace": [
                        {
                            "id": str(item["id"]),
                            "status": str(item["status"]),
                            "reason": str(item["reason"]),
                        }
                        for item in bundle["selection_trace"]
                    ],
                    "unresolved_module_ids": [
                        str(module["id"])
                        for module in bundle["unresolved_modules"]
                    ],
                    "missing_required_inputs": list(
                        bundle["missing_required_inputs"]
                    ),
                    "core_estimated_tokens": int(
                        bundle["estimated_tokens"]["core"]
                    ),
                    "module_estimated_tokens": int(
                        bundle["estimated_tokens"]["modules"]
                    ),
                    "total_estimated_tokens": total,
                    "baseline_estimated_tokens": baseline,
                    "ratio": round(raw_ratio, 4),
                    "max_ratio": max_ratio,
                    "within_budget": raw_ratio <= max_ratio,
                    "complete": bool(bundle["complete"]),
                    "contract_sha256": str(bundle["contract_sha256"]),
                    "inherited_rule_hashes": {
                        str(record["path"]): str(record["sha256"])
                        for record in bundle["inherited_rules"]
                    },
                    "bundle_sha256": str(bundle["bundle_sha256"]),
                }
            )

    records.sort(key=lambda item: (item["skill_id"], item["scenario_id"]))
    skill_ids = sorted({record["skill_id"] for record in records})
    return {
        "schema_version": "1.0",
        "approximation": "one token per four characters, rounded up",
        "skill_count": len(skill_ids),
        "scenario_count": len(records),
        "within_budget_count": sum(
            1 for record in records if record["within_budget"]
        ),
        "complete_count": sum(1 for record in records if record["complete"]),
        "all_within_budget": all(
            record["within_budget"] for record in records
        ),
        "all_complete": all(record["complete"] for record in records),
        "scenarios": records,
    }


def violation_messages(data: dict[str, Any]) -> list[str]:
    """Return stable, actionable budget and completeness violations."""
    messages: list[str] = []
    for record in data.get("scenarios", []):
        label = f"{record['skill_id']}::{record['scenario_id']}"
        if not record.get("complete"):
            details: list[str] = []
            missing = record.get("missing_required_inputs", [])
            unresolved = record.get("unresolved_module_ids", [])
            if missing:
                details.append("missing inputs " + ", ".join(missing))
            if unresolved:
                details.append("unresolved modules " + ", ".join(unresolved))
            suffix = "; ".join(details) or "unresolved required context"
            messages.append(f"{label} is incomplete: {suffix}")
        if not record.get("within_budget"):
            messages.append(
                f"{label} is over budget: ratio {record['ratio']:.4f} "
                f"exceeds {float(record['max_ratio']):.4f}"
            )
    return messages


def budgets_pass(data: dict[str, Any]) -> bool:
    """Return whether every scenario is complete and within its declared cap."""
    return not violation_messages(data)


def render_markdown(data: dict[str, Any]) -> str:
    """Render the human-readable selective-context scorecard."""
    lines = [
        "# AgentCounsel Selective Context Metrics",
        "",
        "Generated by `scripts/generate_selective_context_metrics.py`. Do not edit by hand.",
        "",
        "These are deterministic context-planning estimates, not provider token counts, "
        "latency measurements, or billing data. The approximation is one token per four "
        "characters, rounded up.",
        "",
        f"- Modularized skills measured: {data.get('skill_count', 0)}",
        f"- Scenarios measured: {data.get('scenario_count', 0)}",
        f"- Complete scenarios: {data.get('complete_count', 0)} / {data.get('scenario_count', 0)}",
        f"- Scenarios within budget: {data.get('within_budget_count', 0)} / {data.get('scenario_count', 0)}",
        "",
        "## Scenario results",
        "",
        "| Skill | Scenario | Mode | Selected modules | Core | Modules | Total | Baseline | Ratio | Limit | Complete | Budget |",
        "|---|---|---|---|---:|---:|---:|---:|---:|---:|---|---|",
    ]
    for record in data.get("scenarios", []):
        modules = ", ".join(f"`{item}`" for item in record["selected_module_ids"])
        if not modules:
            modules = "core only"
        lines.append(
            f"| `{record['skill_id']}` | `{record['scenario_id']}` | "
            f"{record['mode']} | {modules} | {record['core_estimated_tokens']:,} | "
            f"{record['module_estimated_tokens']:,} | {record['total_estimated_tokens']:,} | "
            f"{record['baseline_estimated_tokens']:,} | {record['ratio']:.1%} | "
            f"{float(record['max_ratio']):.1%} | "
            f"{'yes' if record['complete'] else 'no'} | "
            f"{'pass' if record['within_budget'] else 'fail'} |"
        )

    violations = violation_messages(data)
    lines.extend(["", "## Gate status", ""])
    if violations:
        lines.append("The generated gate fails for the following reasons:")
        lines.append("")
        lines.extend(f"- {message}" for message in violations)
    else:
        lines.append("All declared scenarios are complete and within budget.")
    lines.extend(
        [
            "",
            "Each JSON record also stores the complete module-selection trace, the "
            "selected module IDs, inherited-rule hashes, the compiled-contract SHA-256 "
            "fingerprint, and the deterministic bundle SHA-256 fingerprint for audit "
            "and replay.",
            "",
        ]
    )
    return "\n".join(lines)


def _expected_outputs(root: Path) -> tuple[dict[str, Any], dict[Path, str]]:
    data = collect_metrics(root)
    outputs = {
        root / JSON_OUTPUT: json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        root / MARKDOWN_OUTPUT: render_markdown(data),
    }
    return data, outputs


def write_outputs(root: Path | str = REPO_ROOT, check: bool = False) -> bool:
    """Write scorecards, or check both artifact drift and budget validity."""
    root = Path(root).resolve()
    data, outputs = _expected_outputs(root)
    if check:
        current = all(
            path.is_file() and path.read_text(encoding="utf-8") == content
            for path, content in outputs.items()
        )
        return current and budgets_pass(data)
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return budgets_pass(data)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail on artifact drift, incomplete scenarios, or exceeded budgets",
    )
    args = parser.parse_args()

    data, outputs = _expected_outputs(REPO_ROOT)
    current = all(
        path.is_file() and path.read_text(encoding="utf-8") == content
        for path, content in outputs.items()
    )
    if not args.check:
        for path, content in outputs.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
        print(f"Wrote {JSON_OUTPUT} and {MARKDOWN_OUTPUT}")

    failed = False
    if args.check and not current:
        print("Selective context metrics are missing or out of date.", file=sys.stderr)
        failed = True
    for message in violation_messages(data):
        print(message, file=sys.stderr)
        failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
