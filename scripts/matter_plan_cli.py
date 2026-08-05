#!/usr/bin/env python3
"""List, inspect, build, and verify AgentCounsel Matter Plan v1 graphs."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from agentcounsel_mcp import CatalogService, CatalogLoadError  # noqa: E402
from scripts.matter_plan import MatterPlanError  # noqa: E402


def read_json(path: str | None) -> dict[str, Any]:
    if not path:
        return {}
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"Could not read JSON file {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return value


def render_markdown(result: dict[str, Any]) -> str:
    groups = {
        "ready": "Ready",
        "blocked": "Blocked",
        "unresolved": "Unresolved",
        "completed": "Completed",
        "approved": "Approved",
        "rejected": "Rejected",
        "not-selected": "Not selected",
    }
    lines = [
        f"# {result['title']}",
        "",
        "Draft legal workflow plan for attorney supervision. This run sheet organizes work; it does not execute legal analysis or calculate deadlines.",
        "",
    ]
    for state, title in groups.items():
        matches = [node for node in result["nodes"] if node["state"] == state]
        lines.extend([f"## {title}", ""])
        if not matches:
            lines.append("None.")
        else:
            for node in matches:
                lines.append(f"- `{node['id']}`: {node['reason']}")
        lines.append("")
    lines.extend([
        "## Execution waves",
        "",
    ])
    if not result["execution_waves"]:
        lines.append("No skill node is currently ready to run.")
    else:
        for wave in result["execution_waves"]:
            lines.append(
                f"- Wave {wave['wave']}: {', '.join(f'`{node}`' for node in wave['node_ids'])} "
                f"({wave['estimated_tokens']:,} estimated context tokens)"
            )
    return "\n".join(lines) + "\n"



def render_plan_markdown(plan: dict[str, Any]) -> str:
    lines = [
        f"# {plan['title']}",
        "",
        plan.get("description", ""),
        "",
        f"- Plan ID: `{plan['plan_id']}`",
        f"- Human guidance: `{plan['source_path']}`",
        f"- Schema: `{plan['schema_version']}`",
        "",
        "## Required inputs",
        "",
    ]
    for field in plan.get("required_inputs", []):
        requirement = "required" if field.get("required") else "optional"
        sensitivity = "sensitive" if field.get("sensitive") else "non-sensitive"
        lines.append(
            f"- `{field['id']}`: `{field['type']}`; {requirement}; {sensitivity}"
        )
    lines.extend(["", "## Nodes", ""])
    for node in plan.get("nodes", []):
        dependencies = ", ".join(f"`{item}`" for item in node.get("depends_on", [])) or "none"
        if node.get("type") == "skill":
            detail = f"skill `{node['skill_id']}` in `{node['mode']}` mode"
        else:
            detail = "attorney-gate"
        lines.append(
            f"- `{node['id']}`: {detail}; depends on {dependencies}"
        )
    lines.extend(["", "## Artifacts", ""])
    for artifact in plan.get("artifacts", []):
        review = "attorney review required" if artifact.get("attorney_review_required") else "no plan-level attorney-review flag"
        lines.append(
            f"- `{artifact['id']}`: `{artifact['type']}` from `{artifact['produced_by']}`; {review}"
        )
    lines.extend([
        "",
        "This is a workflow specification, not legal advice or legal analysis. Attorney gates never auto-complete.",
        "",
    ])
    return "\n".join(lines)

def write_or_print(text: str, output: str | None) -> None:
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    list_parser = sub.add_parser("list")
    list_parser.add_argument("--output")
    show_parser = sub.add_parser("show")
    show_parser.add_argument("plan_id")
    show_parser.add_argument("--output")
    show_parser.add_argument("--markdown", action="store_true")
    build_parser = sub.add_parser("build")
    build_parser.add_argument("plan_id")
    build_parser.add_argument("--inputs")
    build_parser.add_argument("--artifacts")
    build_parser.add_argument("--gates")
    build_parser.add_argument("--nodes")
    build_parser.add_argument("--markdown", action="store_true")
    build_parser.add_argument("--output")
    build_parser.add_argument("--receipt-output")
    verify_parser = sub.add_parser("verify")
    verify_parser.add_argument("receipt")
    verify_parser.add_argument("--output")
    args = parser.parse_args()

    try:
        service = CatalogService.from_root(REPO_ROOT)
        if args.command == "list":
            registry = service.matter_plans
            write_or_print(json.dumps(registry, indent=2, ensure_ascii=False) + "\n", args.output)
            return 0
        if args.command == "show":
            plan = service.get_matter_plan(args.plan_id)
            text = render_plan_markdown(plan) if args.markdown else json.dumps(plan, indent=2, ensure_ascii=False) + "\n"
            write_or_print(text, args.output)
            return 0
        if args.command == "build":
            node_ids = None
            if args.nodes:
                node_ids = [item.strip() for item in args.nodes.split(",") if item.strip()]
            result = service.build_matter_plan(
                args.plan_id,
                matter_inputs=read_json(args.inputs),
                available_artifacts=read_json(args.artifacts),
                gate_decisions=read_json(args.gates),
                node_ids=node_ids,
            )
            if args.receipt_output:
                Path(args.receipt_output).write_text(
                    json.dumps(result["receipt"], indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8",
                )
            text = render_markdown(result) if args.markdown else json.dumps(result, indent=2, ensure_ascii=False) + "\n"
            write_or_print(text, args.output)
            return 0
        receipt = read_json(args.receipt)
        verification = service.verify_matter_plan_receipt(receipt)
        write_or_print(json.dumps(verification, indent=2) + "\n", args.output)
        return 0 if verification["valid"] else 1
    except (ValueError, KeyError, CatalogLoadError, MatterPlanError) as exc:
        print(str(exc), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
