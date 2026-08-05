#!/usr/bin/env python3
"""Evaluate Matter Graph v1 scenarios and adversarial mutation sensitivity."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from .build_matter_plans import build_registry
    from .matter_plan import build_matter_plan, load_skill_spec_registry, validate_matter_plan, verify_matter_plan_receipt
except ImportError:  # pragma: no cover
    from build_matter_plans import build_registry
    from matter_plan import build_matter_plan, load_skill_spec_registry, validate_matter_plan, verify_matter_plan_receipt

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_OUTPUT = Path("metadata/matter_plan_evals.json")
MARKDOWN_OUTPUT = Path("reports/matter-plan-evals.md")


def _hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def _rehash_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    result = deepcopy(receipt)
    result.pop("receipt_sha256", None)
    result["receipt_sha256"] = _hash(result)
    return result


def _digest(artifact_id: str) -> str:
    return hashlib.sha256(artifact_id.encode()).hexdigest()


def _inputs(plan_id: str) -> dict[str, Any]:
    if plan_id == "legal-research-memo":
        return {
            "legal-question": "What is the rule?",
            "known-facts": {"fact": "fictional fixture"},
            "jurisdiction": "California",
            "existing-authorities": ["authority.pdf"],
            "relevant-date": "2026-08-04",
            "time-and-scope": "Scoped review",
        }
    if plan_id == "commercial-contract-review":
        return {
            "agreement": "agreement.pdf", "client-role": "customer",
            "business-context": "software purchase", "has-sow": "no",
            "has-prior-redline": "no", "review-date": "2026-08-04",
            "jurisdiction": "California", "distribution-plan": "internal",
            "matter-context": "workspace",
        }
    if plan_id == "litigation-motion-opposition":
        return {
            "legal-question": "What is the opposition standard?", "known-facts": "fictional facts",
            "jurisdiction": "California", "existing-authorities": ["authority.pdf"],
            "relevant-date": "2026-08-04", "time-and-scope": "Scoped review",
            "motion-record": "motion.pdf", "case-theory": "oppose the requested relief",
            "record-materials": ["record.pdf"], "response-deadline-as-stated": "[user-supplied docket date]",
        }
    return {
        "incident-summary": "incident currently contained", "discovery-date": "2026-08-04",
        "affected-data": "fictional data categories", "privilege-posture-text": "counsel directed",
        "incident-description": {"status": "fictional"}, "trigger-dates": {"discovery": "2026-08-04"},
        "privilege-posture": {"counsel_directed": True}, "incident-records": ["incident.pdf"],
        "chronology-date-range": "2026-08-04", "preservation-trigger-date": "2026-08-04",
        "preservation-scope": "systems and custodians", "custodians-and-systems": "fictional custodians",
        "published-policy": "privacy-policy.pdf", "actual-practices": "fictional practices",
        "processing-context": "product context",
    }


def _all_artifacts(plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {artifact["id"]: {"digest": _digest(artifact["id"])} for artifact in plan["artifacts"]}


def _gates(plan: dict[str, Any], through_first: bool = False) -> dict[str, str]:
    ids = [node["id"] for node in plan["nodes"] if node["type"] == "attorney-gate"]
    return {gate_id: "approved" for gate_id in (ids[:1] if through_first else ids)}


def _continuation_artifacts(plan_id: str, plan: dict[str, Any]) -> dict[str, dict[str, Any]]:
    if plan_id in {"legal-research-memo", "litigation-motion-opposition"}:
        return {"research-roadmap": {"digest": _digest("research-roadmap")}}
    if plan_id == "commercial-contract-review":
        ids = ["contract-risk-matrix", "source-validation-report", "assumption-audit-report", "privilege-check-report"]
        return {item: {"digest": _digest(item)} for item in ids}
    return {"breach-response-package": {"digest": _digest("breach-response-package")}}


def _scenario_record(plan_id: str, scenario_id: str, result: dict[str, Any], receipt_valid: bool) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for node in result["nodes"]:
        counts[node["state"]] = counts.get(node["state"], 0) + 1
    return {
        "plan_id": plan_id,
        "scenario_id": scenario_id,
        "node_state_counts": dict(sorted(counts.items())),
        "ready_node_ids": [node["id"] for node in result["nodes"] if node["state"] == "ready"],
        "execution_wave_count": len(result["execution_waves"]),
        "ready_context_tokens": result["budget"]["ready_context_tokens"],
        "max_total_estimated_tokens": result["budget"]["limits"]["max_total_estimated_tokens"],
        "within_budget": result["budget"]["ready_context_tokens"] <= result["budget"]["limits"]["max_total_estimated_tokens"],
        "receipt_valid": receipt_valid,
    }


def _detect_plan_mutation(plan: dict[str, Any], baseline_hash: str, root: Path, specs: dict[str, dict[str, Any]]) -> tuple[bool, str]:
    errors = validate_matter_plan(root, plan, specs)
    if errors:
        return True, "validator: " + errors[0]
    if _hash(plan) != baseline_hash:
        return True, "registered plan hash mismatch"
    return False, ""


def _blocked_context_leak(result: dict[str, Any]) -> tuple[bool, str]:
    leaked = [node["id"] for node in result["nodes"] if node["state"] != "ready" and "context" in node]
    return (bool(leaked), "blocked node carried context: " + ", ".join(leaked) if leaked else "")


def evaluate(root: Path | str = REPO_ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    specs = load_skill_spec_registry(root)
    registry = build_registry(root)
    cards = {card["plan_id"]: card for card in registry["plans"]}
    plans = {
        plan_id: json.loads((root / card["path"]).read_text(encoding="utf-8"))
        for plan_id, card in cards.items()
    }
    scenarios: list[dict[str, Any]] = []
    baseline_results: dict[str, dict[str, Any]] = {}
    for plan_id in sorted(plans):
        plan = plans[plan_id]
        cases = [
            ("missing-inputs", {}, {}, {}),
            ("first-ready-wave", _inputs(plan_id), {}, {}),
            ("first-gate-approved", _inputs(plan_id), _continuation_artifacts(plan_id, plan), _gates(plan, through_first=True)),
            ("completed-final", _inputs(plan_id), _all_artifacts(plan), _gates(plan)),
        ]
        for scenario_id, inputs, artifacts, gates in cases:
            result = build_matter_plan(root, plan, inputs, artifacts, gates, skill_specs=specs)
            verification = verify_matter_plan_receipt(root, result["receipt"])
            scenarios.append(_scenario_record(plan_id, scenario_id, result, verification["valid"]))
            if scenario_id == "first-ready-wave":
                baseline_results[plan_id] = result

    mutations: list[dict[str, Any]] = []
    legal = plans["legal-research-memo"]
    baseline_hash = cards["legal-research-memo"]["plan_sha256"]

    mutated = deepcopy(legal)
    mutated["nodes"][0]["depends_on"] = ["final-attorney-review"]
    detected, signal = _detect_plan_mutation(mutated, baseline_hash, root, specs)
    mutations.append({"mutation_id": "cycle-injection", "detected": detected, "signal": signal})

    mutated = deepcopy(legal)
    next(node for node in mutated["nodes"] if node["id"] == "authority-synthesis")["depends_on"] = []
    detected, signal = _detect_plan_mutation(mutated, baseline_hash, root, specs)
    mutations.append({"mutation_id": "gate-bypass", "detected": detected, "signal": signal})

    mutated = deepcopy(legal)
    next(node for node in mutated["nodes"] if node["id"] == "source-validation")["depends_on"] = []
    detected, signal = _detect_plan_mutation(mutated, baseline_hash, root, specs)
    mutations.append({"mutation_id": "dependency-removal", "detected": detected, "signal": signal})

    mutated = deepcopy(legal)
    next(artifact for artifact in mutated["artifacts"] if artifact["id"] == "research-memo")["produced_by"] = "research-plan"
    detected, signal = _detect_plan_mutation(mutated, baseline_hash, root, specs)
    mutations.append({"mutation_id": "artifact-producer-swap", "detected": detected, "signal": signal})

    receipt = deepcopy(baseline_results["legal-research-memo"]["receipt"])
    receipt["raw_inputs"] = {"legal-question": "private matter text"}
    verification = verify_matter_plan_receipt(root, _rehash_receipt(receipt))
    mutations.append({"mutation_id": "raw-input-receipt-injection", "detected": not verification["valid"], "signal": verification["errors"][0] if verification["errors"] else ""})

    receipt = deepcopy(baseline_results["legal-research-memo"]["receipt"])
    receipt["budget"]["ready_context_tokens"] += 1
    verification = verify_matter_plan_receipt(root, _rehash_receipt(receipt))
    mutations.append({"mutation_id": "token-arithmetic-tamper", "detected": not verification["valid"], "signal": verification["errors"][0] if verification["errors"] else ""})

    mutated = deepcopy(legal)
    next(node for node in mutated["nodes"] if node["type"] == "skill")["mode"] = "turbo"
    detected, signal = _detect_plan_mutation(mutated, baseline_hash, root, specs)
    mutations.append({"mutation_id": "skill-mode-swap", "detected": detected, "signal": signal})

    leaked = deepcopy(baseline_results["legal-research-memo"])
    blocked = next(node for node in leaked["nodes"] if node["state"] == "blocked")
    blocked["context"] = {"injected": True}
    detected, signal = _blocked_context_leak(leaked)
    mutations.append({"mutation_id": "blocked-node-context-leak", "detected": detected, "signal": signal})

    scenarios.sort(key=lambda item: (item["plan_id"], item["scenario_id"]))
    mutations.sort(key=lambda item: item["mutation_id"])
    return {
        "schema_version": "1.0",
        "plan_count": len(plans),
        "scenario_count": len(scenarios),
        "mutation_count": len(mutations),
        "detected_mutation_count": sum(item["detected"] for item in mutations),
        "all_scenarios_within_budget": all(item["within_budget"] for item in scenarios),
        "all_receipts_valid": all(item["receipt_valid"] for item in scenarios),
        "all_mutations_detected": all(item["detected"] for item in mutations),
        "scenarios": scenarios,
        "mutations": mutations,
    }


def render_report(data: dict[str, Any]) -> str:
    lines = [
        "# Matter Plan Evaluation and Mutation Sensitivity",
        "",
        "Generated by `scripts/evaluate_matter_plans.py`. Do not edit by hand.",
        "",
        f"- Plans: {data['plan_count']}",
        f"- Scenarios: {data['scenario_count']}",
        f"- Valid receipts: {'yes' if data['all_receipts_valid'] else 'no'}",
        f"- Scenarios within budget: {'yes' if data['all_scenarios_within_budget'] else 'no'}",
        f"- Mutation detection: {data['detected_mutation_count']} / {data['mutation_count']}",
        "",
        "## Scenarios",
        "",
        "| Plan | Scenario | Ready | Waves | Tokens | Limit | Receipt |",
        "|---|---|---|---:|---:|---:|---|",
    ]
    for item in data["scenarios"]:
        lines.append(
            f"| `{item['plan_id']}` | `{item['scenario_id']}` | "
            f"{', '.join(item['ready_node_ids']) or 'none'} | {item['execution_wave_count']} | "
            f"{item['ready_context_tokens']:,} | {item['max_total_estimated_tokens']:,} | "
            f"{'pass' if item['receipt_valid'] else 'fail'} |"
        )
    lines.extend(["", "## Mutation probes", "", "| Mutation | Detected | Signal |", "|---|---|---|"])
    for item in data["mutations"]:
        lines.append(f"| `{item['mutation_id']}` | {'yes' if item['detected'] else 'no'} | {item['signal']} |")
    lines.extend(["", "These checks establish structural and integrity sensitivity, not substantive legal correctness.", ""])
    return "\n".join(lines)


def _outputs(root: Path) -> dict[Path, str]:
    data = evaluate(root)
    return {
        root / JSON_OUTPUT: json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        root / MARKDOWN_OUTPUT: render_report(data),
    }


def write_outputs(root: Path | str = REPO_ROOT, check: bool = False) -> bool:
    root = Path(root).resolve()
    outputs = _outputs(root)
    data = evaluate(root)
    healthy = data["all_scenarios_within_budget"] and data["all_receipts_valid"] and data["all_mutations_detected"]
    if check:
        return healthy and all(path.is_file() and path.read_text(encoding="utf-8") == content for path, content in outputs.items())
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return healthy


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    ok = write_outputs(REPO_ROOT, check=args.check)
    if not ok:
        print("Matter-plan evaluations are stale or a scenario/mutation gate failed.", file=sys.stderr)
        return 1
    if not args.check:
        data = evaluate(REPO_ROOT)
        print(f"Wrote matter-plan evals: {data['scenario_count']} scenarios, {data['detected_mutation_count']}/{data['mutation_count']} mutations detected.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
