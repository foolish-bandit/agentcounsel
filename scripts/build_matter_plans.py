#!/usr/bin/env python3
"""Validate and generate AgentCounsel Matter Plan v1 registry and report."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any

try:
    from .matter_plan import (
        MatterPlanError,
        build_matter_plan,
        load_skill_spec_registry,
        validate_matter_plan,
    )
except ImportError:  # pragma: no cover
    from matter_plan import MatterPlanError, build_matter_plan, load_skill_spec_registry, validate_matter_plan

REPO_ROOT = Path(__file__).resolve().parent.parent
JSON_OUTPUT = Path("metadata/matter_plans.json")
MARKDOWN_OUTPUT = Path("reports/matter-plans.md")
_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "and", "for", "in", "of", "on", "or", "the", "to", "with"}


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _tokens(value: Any) -> set[str]:
    if isinstance(value, (list, tuple, set)):
        text = " ".join(str(item) for item in value)
    else:
        text = str(value or "")
    return {token for token in _WORD_RE.findall(text.lower()) if len(token) > 1 and token not in _STOP}


def _plan_files(root: Path) -> list[Path]:
    directory = root / "matter-plans"
    if not directory.is_dir():
        return []
    return sorted(path for path in directory.glob("*.json") if path.is_file())


def _load_plan(path: Path) -> dict[str, Any]:
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatterPlanError(f"Could not read matter plan {path}: {exc}") from exc
    if not isinstance(plan, dict):
        raise MatterPlanError(f"Matter plan must be a JSON object: {path}")
    return plan


def _card(root: Path, path: Path, plan: dict[str, Any], specs: dict[str, dict[str, Any]]) -> dict[str, Any]:
    errors = validate_matter_plan(root, plan, specs)
    if errors:
        raise MatterPlanError(f"Invalid matter plan {path}:\n- " + "\n- ".join(errors))
    result = build_matter_plan(root, plan, skill_specs=specs, _include_receipt=False)
    nodes = plan["nodes"]
    skill_ids = sorted({node["skill_id"] for node in nodes if node.get("type") == "skill"})
    source = root / plan["source_path"]
    return {
        "plan_id": plan["plan_id"],
        "title": plan["title"],
        "description": plan["description"],
        "path": path.relative_to(root).as_posix(),
        "plan_sha256": _canonical_sha256(plan),
        "source_path": plan["source_path"],
        "source_sha256": _file_sha256(source),
        "tags": list(plan.get("tags", [])),
        "required_inputs": [
            {
                "id": field["id"],
                "type": field.get("type"),
                "required": field.get("required") is True,
                "sensitive": field.get("sensitive") is True,
            }
            for field in plan.get("required_inputs", [])
        ],
        "node_count": len(nodes),
        "skill_node_count": sum(node.get("type") == "skill" for node in nodes),
        "gate_node_count": sum(node.get("type") == "attorney-gate" for node in nodes),
        "artifact_count": len(plan.get("artifacts", [])),
        "practice_areas": sorted({skill_id.split("/", 1)[0] for skill_id in skill_ids}),
        "included_skills": skill_ids,
        "graph_depth": result["budget"]["graph_depth"],
        "max_parallel_width": result["budget"]["max_parallel_width"],
        "budget_limits": dict(plan["budget"]),
        "validation_status": "valid",
    }


def build_registry(root: Path | str = REPO_ROOT) -> dict[str, Any]:
    root = Path(root).resolve()
    specs = load_skill_spec_registry(root)
    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for path in _plan_files(root):
        plan = _load_plan(path)
        plan_id = plan.get("plan_id")
        if plan_id in seen:
            raise MatterPlanError(f"Duplicate matter plan id: {plan_id}")
        seen.add(plan_id)
        cards.append(_card(root, path, plan, specs))
    cards.sort(key=lambda item: item["plan_id"])
    return {
        "schema_version": "1.0",
        "plan_count": len(cards),
        "skill_node_count": sum(card["skill_node_count"] for card in cards),
        "gate_node_count": sum(card["gate_node_count"] for card in cards),
        "artifact_count": sum(card["artifact_count"] for card in cards),
        "plans": cards,
    }


def search_plan_cards(registry: dict[str, Any], query: str, limit: int = 10) -> list[dict[str, Any]]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("query must not be empty")
    if not isinstance(limit, int) or limit < 1 or limit > 50:
        raise ValueError("limit must be between 1 and 50")
    q = query.strip().lower()
    qtokens = _tokens(q)
    ranked: list[tuple[int, str, dict[str, Any], list[str]]] = []
    fields = (
        ("plan_id", 30, 180),
        ("title", 25, 150),
        ("tags", 18, 80),
        ("description", 10, 45),
        ("source_path", 8, 35),
        ("included_skills", 8, 35),
        ("practice_areas", 6, 25),
    )
    for card in registry.get("plans", []):
        score = 0
        matched: list[str] = []
        if q in {str(card.get("plan_id", "")).lower(), str(card.get("title", "")).lower()}:
            score += 300
            matched.append("exact_identifier")
        for field, token_weight, phrase_weight in fields:
            value = card.get(field)
            tokens = _tokens(value)
            overlap = tokens & qtokens
            text = " ".join(str(item) for item in value) if isinstance(value, list) else str(value or "")
            phrase = q in text.lower()
            if overlap or phrase:
                score += len(overlap) * token_weight + (phrase_weight if phrase else 0)
                matched.append(field)
        if score:
            ranked.append((score, card["plan_id"], card, list(dict.fromkeys(matched))))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    results: list[dict[str, Any]] = []
    for score, _, card, matched in ranked[:limit]:
        result = dict(card)
        result["relevance_score"] = score
        result["matched_fields"] = matched
        results.append(result)
    return results


def render_report(registry: dict[str, Any]) -> str:
    lines = [
        "# AgentCounsel Matter Plans",
        "",
        "Generated by `scripts/build_matter_plans.py`. Do not edit by hand.",
        "",
        "Matter-plan validation proves graph structure, canonical references, typed handoffs, gate placement, and declared complexity limits. It does not establish legal correctness or calculate deadlines.",
        "",
        f"- Plans: {registry['plan_count']}",
        f"- Skill nodes: {registry['skill_node_count']}",
        f"- Attorney gates: {registry['gate_node_count']}",
        f"- Artifacts: {registry['artifact_count']}",
        "",
        "| Plan | Source | Nodes | Gates | Artifacts | Depth | Width | Practice areas |",
        "|---|---|---:|---:|---:|---:|---:|---|",
    ]
    for card in registry["plans"]:
        lines.append(
            f"| `{card['plan_id']}` | `{card['source_path']}` | {card['node_count']} | "
            f"{card['gate_node_count']} | {card['artifact_count']} | {card['graph_depth']} | "
            f"{card['max_parallel_width']} | {', '.join(card['practice_areas'])} |"
        )
    for card in registry["plans"]:
        lines.extend([
            "",
            f"## {card['title']}",
            "",
            card["description"],
            "",
            f"- Plan: `{card['path']}`",
            f"- Human guidance: `{card['source_path']}`",
            f"- Skills: {', '.join(f'`{item}`' for item in card['included_skills'])}",
            f"- Graph depth / width: {card['graph_depth']} / {card['max_parallel_width']}",
            f"- Validation: {card['validation_status']}",
        ])
    return "\n".join(lines) + "\n"


def _expected(root: Path) -> dict[Path, str]:
    registry = build_registry(root)
    return {
        root / JSON_OUTPUT: json.dumps(registry, indent=2, ensure_ascii=False) + "\n",
        root / MARKDOWN_OUTPUT: render_report(registry),
    }


def write_outputs(root: Path | str = REPO_ROOT, check: bool = False) -> bool:
    root = Path(root).resolve()
    outputs = _expected(root)
    if check:
        return all(path.is_file() and path.read_text(encoding="utf-8") == content for path, content in outputs.items())
    for path, content in outputs.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        current = write_outputs(REPO_ROOT, check=args.check)
    except MatterPlanError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    if args.check and not current:
        print("Matter-plan registry or report is missing or out of date.", file=sys.stderr)
        return 1
    if not args.check:
        registry = build_registry(REPO_ROOT)
        print(f"Wrote matter-plan registry: {registry['plan_count']} plans.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
