#!/usr/bin/env python3
"""Typed, deterministic matter-plan graph validation and compilation."""

from __future__ import annotations

import hashlib
import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

try:
    from .skill_context import build_skill_context, normalize_inputs
    from .skill_spec_v2 import MODE_IDS
except ImportError:  # pragma: no cover
    from skill_context import build_skill_context, normalize_inputs
    from skill_spec_v2 import MODE_IDS

PLAN_SCHEMA_VERSION = "1.0"
NODE_TYPES = {"skill", "attorney-gate"}
CONDITION_OPERATORS = {
    "always",
    "present",
    "equals",
    "contains-any",
    "artifact-present",
    "gate-approved",
}
NODE_STATES = {
    "ready",
    "blocked",
    "unresolved",
    "not-selected",
    "completed",
    "approved",
    "rejected",
}
INPUT_TYPES = {
    "text",
    "document",
    "document-set",
    "enum",
    "date",
    "datetime",
    "boolean",
    "integer",
    "number",
    "jurisdiction",
    "object",
    "string-list",
}
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9-]*\Z")


class MatterPlanError(ValueError):
    """Raised when a matter plan cannot be validated or built safely."""


def _is_slug(value: Any) -> bool:
    return isinstance(value, str) and _SLUG_RE.fullmatch(value) is not None


def _duplicates_after_casefold(records: Any) -> list[str]:
    if not isinstance(records, list):
        return []
    seen: set[str] = set()
    duplicates: list[str] = []
    for record in records:
        value = record.get("id") if isinstance(record, dict) else record
        if not isinstance(value, str):
            continue
        normalized = value.strip().casefold()
        if normalized in seen:
            duplicates.append(value)
        seen.add(normalized)
    return duplicates


def _repo_path(root: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or not relative:
        return None
    root_resolved = root.resolve()
    target = (root_resolved / relative).resolve()
    if not target.is_relative_to(root_resolved):
        return None
    return target


def load_skill_spec_registry(root: Path) -> dict[str, dict[str, Any]]:
    path = root / "metadata" / "skill_specs.json"
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatterPlanError(f"Could not load skill spec registry: {exc}") from exc
    skills = data.get("skills") if isinstance(data, dict) else None
    if not isinstance(skills, list):
        raise MatterPlanError("metadata/skill_specs.json must contain a skills list")
    registry: dict[str, dict[str, Any]] = {}
    for spec in skills:
        if not isinstance(spec, dict) or not isinstance(spec.get("skill_id"), str):
            raise MatterPlanError("skill spec registry contains an invalid record")
        registry[spec["skill_id"]] = spec
    return registry


def load_matter_plan(root: Path, plan_id: str) -> dict[str, Any]:
    if not _is_slug(plan_id):
        raise MatterPlanError(f"invalid matter plan ID: {plan_id}")
    path = root / "matter-plans" / f"{plan_id}.json"
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise MatterPlanError(f"Could not load matter plan {plan_id}: {exc}") from exc
    if not isinstance(plan, dict):
        raise MatterPlanError(f"Matter plan {plan_id} must be an object")
    return plan


def _topological_order(nodes: list[dict[str, Any]]) -> tuple[list[str], list[str]]:
    node_ids = [node.get("id") for node in nodes if isinstance(node.get("id"), str)]
    existing = set(node_ids)
    dependencies: dict[str, set[str]] = {}
    children: dict[str, set[str]] = {node_id: set() for node_id in node_ids}
    for node in nodes:
        node_id = node.get("id")
        if not isinstance(node_id, str):
            continue
        deps = {
            dep
            for dep in node.get("depends_on", [])
            if isinstance(dep, str) and dep in existing and dep != node_id
        }
        dependencies[node_id] = deps
        for dep in deps:
            children.setdefault(dep, set()).add(node_id)
    ready = sorted(node_id for node_id in node_ids if not dependencies.get(node_id))
    order: list[str] = []
    while ready:
        current = ready.pop(0)
        order.append(current)
        for child in sorted(children.get(current, set())):
            dependencies[child].discard(current)
            if not dependencies[child] and child not in order and child not in ready:
                ready.append(child)
                ready.sort()
    remaining = sorted(existing - set(order))
    return order, remaining


def _enabled_modes(spec: dict[str, Any]) -> set[str]:
    return {
        mode.get("id")
        for mode in spec.get("execution_modes", [])
        if isinstance(mode, dict) and mode.get("enabled") is True and isinstance(mode.get("id"), str)
    }


def _non_finite_paths(value: Any, path: str = "plan") -> list[str]:
    """Return stable paths for every non-finite float in a JSON-like value."""
    found: list[str] = []
    if isinstance(value, float) and not math.isfinite(value):
        return [path]
    if isinstance(value, dict):
        for key in sorted(value):
            found.extend(_non_finite_paths(value[key], f"{path}.{key}"))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            found.extend(_non_finite_paths(item, f"{path}[{index}]"))
    return found


def _children_by_node(nodes: dict[str, dict[str, Any]]) -> dict[str, set[str]]:
    children = {node_id: set() for node_id in nodes}
    for node_id, node in nodes.items():
        for dependency in node.get("depends_on", []):
            if dependency in children:
                children[dependency].add(node_id)
    return children


def _can_reach(start: str, target: str, children: dict[str, set[str]]) -> bool:
    pending = [start]
    seen: set[str] = set()
    while pending:
        current = pending.pop()
        if current == target:
            return True
        if current in seen:
            continue
        seen.add(current)
        pending.extend(sorted(children.get(current, set()), reverse=True))
    return False


def validate_matter_plan(
    root: Path,
    plan: dict[str, Any],
    skill_specs: dict[str, dict[str, Any]],
) -> list[str]:
    errors: list[str] = []
    if not isinstance(plan, dict):
        return ["matter plan must be an object"]
    if plan.get("schema_version") != PLAN_SCHEMA_VERSION:
        errors.append(f"schema_version must be {PLAN_SCHEMA_VERSION}")
    if not _is_slug(plan.get("plan_id")):
        errors.append("plan_id must be a lowercase slug")
    for field in ("title", "description"):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            errors.append(f"{field} must be a non-empty string")

    source_path = plan.get("source_path")
    resolved_source = _repo_path(root, source_path)
    if resolved_source is None or not resolved_source.is_file():
        errors.append(f"source path does not resolve inside repository: {source_path}")
    elif not (
        isinstance(source_path, str)
        and source_path.endswith(".md")
        and source_path.startswith(("playbooks/", "matter-packs/"))
    ):
        errors.append("source path must reference a playbook or matter pack Markdown file")

    for non_finite_path in _non_finite_paths(plan):
        errors.append(f"non-finite value at {non_finite_path}")

    tags = plan.get("tags", [])
    if not isinstance(tags, list) or any(not isinstance(tag, str) or not tag.strip() for tag in tags):
        errors.append("tags must be a list of non-empty strings")

    inputs = plan.get("required_inputs")
    if not isinstance(inputs, list):
        errors.append("required_inputs must be a list")
        inputs = []
    if _duplicates_after_casefold(inputs):
        errors.append("matter input IDs must be unique after normalization")
    input_by_id: dict[str, dict[str, Any]] = {}
    for field in inputs:
        if not isinstance(field, dict):
            errors.append("matter inputs must be objects")
            continue
        field_id = field.get("id")
        if not _is_slug(field_id):
            errors.append(f"matter input needs a slug-form id: {field_id}")
            continue
        input_by_id[field_id] = field
        if field.get("type") not in INPUT_TYPES:
            errors.append(f"matter input {field_id} has invalid type")
        for bool_field in ("required", "may_infer", "sensitive"):
            if not isinstance(field.get(bool_field), bool):
                errors.append(f"matter input {field_id} {bool_field} must be boolean")
        if field.get("required") is True and field.get("may_infer") is True:
            errors.append(f"required matter input {field_id} may not be inferable")
        allowed = field.get("enum") if field.get("type") == "enum" else field.get("items")
        if allowed is not None:
            if not isinstance(allowed, list) or not allowed or any(not isinstance(v, str) or not v.strip() for v in allowed):
                errors.append(f"matter input {field_id} controlled values must be non-empty strings")
            elif len({v.strip().casefold() for v in allowed}) != len(allowed):
                errors.append(f"matter input {field_id} controlled values must be unique after normalization")

    nodes = plan.get("nodes")
    if not isinstance(nodes, list) or not nodes:
        errors.append("nodes must be a non-empty list")
        nodes = []
    if _duplicates_after_casefold(nodes):
        errors.append("node IDs must be unique after normalization")
    node_by_id: dict[str, dict[str, Any]] = {}
    for node in nodes:
        if not isinstance(node, dict):
            errors.append("nodes must be objects")
            continue
        node_id = node.get("id")
        if not _is_slug(node_id):
            errors.append(f"node needs a slug-form id: {node_id}")
            continue
        node_by_id[node_id] = node

    artifacts = plan.get("artifacts")
    if not isinstance(artifacts, list):
        errors.append("artifacts must be a list")
        artifacts = []
    if _duplicates_after_casefold(artifacts):
        errors.append("artifact IDs must be unique after normalization")
    artifact_by_id: dict[str, dict[str, Any]] = {}
    producers: dict[str, list[str]] = {}
    for artifact in artifacts:
        if not isinstance(artifact, dict):
            errors.append("artifacts must be objects")
            continue
        artifact_id = artifact.get("id")
        if not _is_slug(artifact_id):
            errors.append(f"artifact needs a slug-form id: {artifact_id}")
            continue
        artifact_by_id[artifact_id] = artifact
        producer = artifact.get("produced_by")
        if isinstance(producer, str):
            producers.setdefault(artifact_id, []).append(producer)
        else:
            errors.append(f"artifact {artifact_id} needs a producer")
        if artifact.get("type") not in {"document", "document-set", "memo", "table", "checklist", "tracker", "timeline", "matrix", "structured-data", "section", "letter"}:
            errors.append(f"artifact {artifact_id} has invalid type")
        for bool_field in ("attorney_review_required", "sensitive"):
            if not isinstance(artifact.get(bool_field), bool):
                errors.append(f"artifact {artifact_id} {bool_field} must be boolean")

    valid_node_ids = set(node_by_id)
    for node_id, node in node_by_id.items():
        node_type = node.get("type")
        if node_type not in NODE_TYPES:
            errors.append(f"node {node_id} has invalid type")
        depends_on = node.get("depends_on", [])
        if not isinstance(depends_on, list) or any(not isinstance(dep, str) for dep in depends_on):
            errors.append(f"node {node_id} depends_on must be a string list")
            depends_on = []
        if node_id in depends_on:
            errors.append(f"node {node_id} may not depend on itself")
        for dep in depends_on:
            if dep not in valid_node_ids:
                errors.append(f"node {node_id} has unknown dependency {dep}")

        condition = node.get("condition", {"operator": "always"})
        if not isinstance(condition, dict):
            errors.append(f"node {node_id} condition must be an object")
        else:
            operator = condition.get("operator")
            if operator not in CONDITION_OPERATORS:
                errors.append(f"node {node_id} has invalid condition operator {operator}")
            if operator in {"present", "equals", "contains-any"}:
                input_id = condition.get("input_id")
                if input_id not in input_by_id:
                    errors.append(f"node {node_id} condition references unknown matter input {input_id}")
                input_field = input_by_id.get(input_id)
                if operator in {"equals", "contains-any"} and input_field is not None:
                    if input_field.get("sensitive") is True or input_field.get("type") not in {"enum", "string-list", "boolean"}:
                        errors.append(
                            f"node {node_id} routing conditions require a non-sensitive controlled matter input"
                        )
                if operator == "equals" and (not isinstance(condition.get("value"), str) or not condition.get("value")):
                    errors.append(f"node {node_id} equals condition needs a value")
                if operator == "contains-any" and (
                    not isinstance(condition.get("values"), list)
                    or not condition.get("values")
                    or any(not isinstance(value, str) or not value for value in condition.get("values", []))
                ):
                    errors.append(f"node {node_id} contains-any condition needs values")
                if input_field is not None and operator in {"equals", "contains-any"}:
                    allowed = input_field.get("enum") or input_field.get("items")
                    configured = [condition.get("value")] if operator == "equals" else condition.get("values", [])
                    if isinstance(allowed, list):
                        unknown_values = [value for value in configured if value not in allowed]
                        if unknown_values:
                            errors.append(
                                f"node {node_id} condition values are not allowed by matter input {input_id}: "
                                + ", ".join(str(value) for value in unknown_values)
                            )
            if operator == "artifact-present" and condition.get("artifact_id") not in artifact_by_id:
                errors.append(f"node {node_id} condition references unknown artifact {condition.get('artifact_id')}")
            if operator == "gate-approved":
                gate_id = condition.get("gate_id")
                gate = node_by_id.get(gate_id)
                if not gate or gate.get("type") != "attorney-gate":
                    errors.append(f"node {node_id} condition references unknown attorney gate {gate_id}")
                elif gate_id not in depends_on:
                    errors.append(
                        f"node {node_id} must depend directly on attorney gate {gate_id} used by gate-approved condition"
                    )

        declared_produces = node.get("produces", [])
        if node_type == "skill":
            skill_id = node.get("skill_id")
            mode = node.get("mode")
            if mode not in MODE_IDS:
                errors.append(f"node {node_id} uses unknown mode {mode}")
            spec = skill_specs.get(skill_id)
            if spec is None:
                errors.append(f"node {node_id} references unknown skill {skill_id}")
            else:
                if mode in MODE_IDS and mode not in _enabled_modes(spec):
                    errors.append(f"node {node_id} uses disabled mode {mode}")
                target_fields = {
                    field.get("id"): field
                    for field in spec.get("input_schema", [])
                    if isinstance(field, dict) and isinstance(field.get("id"), str)
                }
                bindings = node.get("input_bindings", [])
                if not isinstance(bindings, list):
                    errors.append(f"node {node_id} input_bindings must be a list")
                    bindings = []
                bound_targets: set[str] = set()
                for binding in bindings:
                    if not isinstance(binding, dict):
                        errors.append(f"node {node_id} bindings must be objects")
                        continue
                    target_id = binding.get("target_input_id")
                    if target_id not in target_fields:
                        errors.append(f"node {node_id} binding references unknown target input {target_id}")
                        continue
                    if target_id in bound_targets:
                        errors.append(f"node {node_id} target input {target_id} has multiple bindings")
                    bound_targets.add(target_id)
                    if not isinstance(binding.get("required"), bool):
                        errors.append(
                            f"node {node_id} binding {target_id} required must be boolean"
                        )
                    source = binding.get("source")
                    if not isinstance(source, dict):
                        errors.append(f"node {node_id} binding {target_id} needs a source")
                        continue
                    kind = source.get("kind")
                    source_id = source.get("id")
                    if kind == "matter-input" and source_id not in input_by_id:
                        errors.append(f"node {node_id} binding {target_id} references unknown matter input {source_id}")
                    elif kind == "artifact" and source_id not in artifact_by_id:
                        errors.append(f"node {node_id} binding {target_id} references unknown artifact {source_id}")
                    elif kind == "constant" and "value" not in source:
                        errors.append(f"node {node_id} binding {target_id} constant needs a value")
                    elif kind == "gate-decision":
                        gate = node_by_id.get(source_id)
                        if not gate or gate.get("type") != "attorney-gate":
                            errors.append(
                                f"node {node_id} binding {target_id} references unknown attorney gate {source_id}"
                            )
                        elif source_id not in depends_on:
                            errors.append(
                                f"node {node_id} gate-decision binding {target_id} must depend directly on attorney gate {source_id}"
                            )
                    elif kind not in {"matter-input", "artifact", "constant", "gate-decision"}:
                        errors.append(f"node {node_id} binding {target_id} has invalid source kind {kind}")
                    transform = binding.get("transform", "identity")
                    if transform not in {"identity", "json-text", "join-text", "as-document-set", "artifact-ref"}:
                        errors.append(f"node {node_id} binding {target_id} has invalid transform {transform}")
                for target_id, field in target_fields.items():
                    if field.get("required") is True:
                        matching = [
                            binding
                            for binding in bindings
                            if isinstance(binding, dict)
                            and binding.get("target_input_id") == target_id
                        ]
                        if not matching:
                            errors.append(
                                f"node {node_id} required target input {target_id} has no binding"
                            )
                        elif matching[0].get("required") is not True:
                            errors.append(
                                f"node {node_id} required target input {target_id} must use a required binding"
                            )
        elif node_type == "attorney-gate":
            gate = node.get("gate")
            if not isinstance(gate, dict):
                errors.append(f"attorney gate {node_id} needs gate configuration")
            else:
                if gate.get("severity") not in {"required", "immediate"}:
                    errors.append(f"attorney gate {node_id} has invalid severity")
                if not isinstance(gate.get("instruction"), str) or not gate.get("instruction", "").strip():
                    errors.append(f"attorney gate {node_id} needs an instruction")
                for artifact_id in gate.get("required_artifacts", []):
                    if artifact_id not in artifact_by_id:
                        errors.append(f"attorney gate {node_id} references unknown artifact {artifact_id}")

        if declared_produces is not None:
            if not isinstance(declared_produces, list):
                errors.append(f"node {node_id} produces must be a list")
            else:
                for artifact_id in declared_produces:
                    if artifact_id not in artifact_by_id:
                        errors.append(f"node {node_id} produces unknown artifact {artifact_id}")
                    elif artifact_by_id[artifact_id].get("produced_by") != node_id:
                        errors.append(f"artifact {artifact_id} producer does not match node {node_id}")

    for artifact_id, artifact in artifact_by_id.items():
        producer = artifact.get("produced_by")
        if producer not in node_by_id:
            errors.append(f"artifact {artifact_id} references unknown producer {producer}")
        declarations = [
            node_id
            for node_id, node in node_by_id.items()
            if artifact_id in node.get("produces", [])
        ]
        if len(declarations) != 1:
            errors.append(f"artifact {artifact_id} must have exactly one producer declaration")
        if len(producers.get(artifact_id, [])) != 1:
            errors.append(f"artifact {artifact_id} must have exactly one producer")

    order, remaining = _topological_order(list(node_by_id.values()))
    if remaining:
        errors.append("graph contains a cycle involving: " + ", ".join(remaining))

    children = _children_by_node(node_by_id)
    terminal_nodes = sorted(
        node_id
        for node_id, node in node_by_id.items()
        if not children.get(node_id)
        and node.get("condition", {"operator": "always"}).get("operator") == "always"
    )
    terminal_gates = [
        node_id
        for node_id in terminal_nodes
        if node_by_id.get(node_id, {}).get("type") == "attorney-gate"
    ]
    final_gate_id: str | None = None
    if len(terminal_nodes) != 1 or node_by_id.get(terminal_nodes[0], {}).get("type") != "attorney-gate":
        errors.append("matter plan must have exactly one terminal attorney gate")
    if len(terminal_gates) == 1:
        final_gate_id = terminal_gates[0]

    final_outputs = plan.get("final_outputs")
    if not isinstance(final_outputs, list) or not final_outputs:
        errors.append("final_outputs must be a non-empty list")
    else:
        for artifact_id in final_outputs:
            if artifact_id not in artifact_by_id:
                errors.append(f"final output references unknown artifact {artifact_id}")
            elif final_gate_id is not None:
                producer = artifact_by_id[artifact_id].get("produced_by")
                if not isinstance(producer, str) or not _can_reach(
                    producer, final_gate_id, children
                ):
                    errors.append(
                        f"final output {artifact_id} is not upstream of final attorney gate {final_gate_id}"
                    )

    budget = plan.get("budget")
    if not isinstance(budget, dict):
        errors.append("budget must be an object")
    else:
        for field in (
            "max_graph_depth",
            "max_parallel_width",
            "max_ready_nodes",
            "max_total_estimated_tokens",
        ):
            value = budget.get(field)
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
            ):
                errors.append(f"budget {field} must be a positive finite number")

    return sorted(set(errors))


def assert_valid_matter_plan(root: Path, plan: dict[str, Any], skill_specs: dict[str, dict[str, Any]]) -> None:
    errors = validate_matter_plan(root, plan, skill_specs)
    if errors:
        raise MatterPlanError("Invalid matter plan:\n- " + "\n- ".join(errors))


def _normalize_matter_inputs(plan: dict[str, Any], matter_inputs: dict[str, Any] | None) -> dict[str, Any]:
    pseudo_spec = {"input_schema": plan.get("required_inputs", [])}
    try:
        return normalize_inputs(pseudo_spec, matter_inputs)
    except Exception as exc:
        raise MatterPlanError(f"Invalid matter inputs: {exc}") from exc


def _normalize_available_artifacts(
    plan: dict[str, Any], available_artifacts: dict[str, dict[str, Any]] | None
) -> dict[str, dict[str, Any]]:
    if available_artifacts is None:
        return {}
    if not isinstance(available_artifacts, dict):
        raise MatterPlanError("available_artifacts must be an object")
    known = {artifact["id"] for artifact in plan.get("artifacts", []) if isinstance(artifact, dict) and isinstance(artifact.get("id"), str)}
    unknown = sorted(set(available_artifacts) - known)
    if unknown:
        raise MatterPlanError("Unknown artifact ID(s): " + ", ".join(unknown))
    normalized: dict[str, dict[str, Any]] = {}
    for artifact_id, record in available_artifacts.items():
        if not isinstance(record, dict):
            raise MatterPlanError(f"artifact {artifact_id} metadata must be an object")
        unexpected = sorted(set(record) - {"digest"})
        if unexpected:
            raise MatterPlanError(
                f"artifact {artifact_id} has unexpected metadata field(s): "
                + ", ".join(unexpected)
            )
        digest = record.get("digest")
        if digest is not None and (
            not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
        ):
            raise MatterPlanError(f"artifact {artifact_id} digest must be a lowercase SHA-256 hex string")
        normalized[artifact_id] = {"digest": digest} if digest is not None else {}
    return normalized


def _normalize_gate_decisions(
    plan: dict[str, Any], gate_decisions: dict[str, str] | None
) -> dict[str, str]:
    if gate_decisions is None:
        return {}
    if not isinstance(gate_decisions, dict):
        raise MatterPlanError("gate_decisions must be an object")
    gates = {
        node["id"]
        for node in plan.get("nodes", [])
        if isinstance(node, dict) and node.get("type") == "attorney-gate"
    }
    unknown = sorted(set(gate_decisions) - gates)
    if unknown:
        raise MatterPlanError("Unknown attorney gate ID(s): " + ", ".join(unknown))
    normalized: dict[str, str] = {}
    for gate_id, decision in gate_decisions.items():
        if decision not in {"approved", "rejected"}:
            raise MatterPlanError(
                f"gate {gate_id} decision must be approved or rejected"
            )
        normalized[gate_id] = decision
    return normalized


def _condition_result(
    condition: dict[str, Any],
    matter_inputs: dict[str, Any],
    available_artifacts: dict[str, dict[str, Any]],
    gate_decisions: dict[str, str],
) -> tuple[str, str]:
    operator = condition.get("operator", "always")
    if operator == "always":
        return "matched", "condition always applies"
    if operator in {"present", "equals", "contains-any"}:
        input_id = condition.get("input_id")
        if input_id not in matter_inputs or matter_inputs.get(input_id) in (None, "", [], {}):
            return "unresolved", f"condition input {input_id} was not supplied"
        value = matter_inputs[input_id]
        if operator == "present":
            return "matched", f"condition input {input_id} is present"
        values = value if isinstance(value, (list, tuple, set)) else [value]
        actual = {str(item).strip().casefold() for item in values}
        if operator == "equals":
            expected = str(condition.get("value", "")).strip().casefold()
            matched = len(actual) == 1 and expected in actual
            return (
                ("matched", f"condition input {input_id} equals {condition.get('value')}")
                if matched
                else ("not-matched", f"condition input {input_id} does not equal {condition.get('value')}")
            )
        configured = condition.get("values", [])
        expected = {str(item).strip().casefold() for item in configured}
        matched_values = sorted(actual & expected)
        return (
            ("matched", f"condition input {input_id} contains {', '.join(matched_values)}")
            if matched_values
            else ("not-matched", f"condition input {input_id} contains none of the configured values")
        )
    if operator == "artifact-present":
        artifact_id = condition.get("artifact_id")
        if artifact_id in available_artifacts:
            return "matched", f"artifact {artifact_id} is available"
        return "not-matched", f"artifact {artifact_id} is not available"
    if operator == "gate-approved":
        gate_id = condition.get("gate_id")
        if gate_id not in gate_decisions:
            return "unresolved", f"attorney gate {gate_id} has no decision"
        if gate_decisions[gate_id] == "approved":
            return "matched", f"attorney gate {gate_id} is approved"
        return "not-matched", f"attorney gate {gate_id} was rejected"
    raise MatterPlanError(f"Unsupported condition operator: {operator}")


def _node_depths(nodes: list[dict[str, Any]], order: list[str]) -> dict[str, int]:
    by_id = {node["id"]: node for node in nodes}
    depths: dict[str, int] = {}
    for node_id in order:
        dependencies = by_id[node_id].get("depends_on", [])
        depths[node_id] = 0 if not dependencies else 1 + max(depths[dep] for dep in dependencies)
    return depths


def _source_value(
    source: dict[str, Any],
    matter_inputs: dict[str, Any],
    available_artifacts: dict[str, dict[str, Any]],
    gate_decisions: dict[str, str],
) -> tuple[bool, Any, str]:
    kind = source.get("kind")
    source_id = source.get("id")
    if kind == "matter-input":
        if source_id not in matter_inputs or matter_inputs.get(source_id) in (None, "", [], {}):
            return False, None, f"matter input {source_id} is missing"
        return True, matter_inputs[source_id], f"matter input {source_id}"
    if kind == "artifact":
        if source_id not in available_artifacts:
            return False, None, f"artifact {source_id} is not available"
        return True, f"artifact://{source_id}", f"artifact {source_id}"
    if kind == "constant":
        return True, source.get("value"), "declared constant"
    if kind == "gate-decision":
        if source_id not in gate_decisions:
            return False, None, f"attorney gate {source_id} has no decision"
        return True, gate_decisions[source_id], f"attorney gate {source_id} decision"
    return False, None, f"unsupported source kind {kind}"


def _transform_binding(value: Any, transform: str, target_type: str) -> Any:
    if transform == "identity":
        return value
    if transform == "json-text":
        return json.dumps(value, sort_keys=True, ensure_ascii=False)
    if transform == "join-text":
        if isinstance(value, (list, tuple)):
            return "\n".join(str(item) for item in value)
        return str(value)
    if transform == "as-document-set":
        return list(value) if isinstance(value, (list, tuple)) else [str(value)]
    if transform == "artifact-ref":
        if target_type == "document-set":
            return [str(value)]
        if target_type == "object":
            return {"artifact_ref": str(value)}
        return str(value)
    raise MatterPlanError(f"Unsupported binding transform: {transform}")


def build_matter_plan(
    root: Path,
    plan: dict[str, Any],
    matter_inputs: dict[str, Any] | None = None,
    available_artifacts: dict[str, dict[str, Any]] | None = None,
    gate_decisions: dict[str, str] | None = None,
    explicit_node_ids: list[str] | None = None,
    *,
    skill_specs: dict[str, dict[str, Any]] | None = None,
    _include_receipt: bool = True,
) -> dict[str, Any]:
    """Resolve one validated matter graph without executing legal work."""
    root = Path(root).resolve()
    specs = skill_specs or load_skill_spec_registry(root)
    assert_valid_matter_plan(root, plan, specs)
    normalized_inputs = _normalize_matter_inputs(plan, matter_inputs)
    artifacts_available = _normalize_available_artifacts(plan, available_artifacts)
    decisions = _normalize_gate_decisions(plan, gate_decisions)

    nodes = [deepcopy(node) for node in plan.get("nodes", [])]
    node_by_id = {node["id"]: node for node in nodes}
    order, remaining = _topological_order(nodes)
    if remaining:
        raise MatterPlanError("Matter plan contains a cycle: " + ", ".join(remaining))
    depths = _node_depths(nodes, order)

    if explicit_node_ids is not None:
        if not isinstance(explicit_node_ids, list) or any(not isinstance(item, str) for item in explicit_node_ids):
            raise MatterPlanError("explicit_node_ids must be a list of strings")
        unknown = sorted(set(explicit_node_ids) - set(node_by_id))
        if unknown:
            raise MatterPlanError("Unknown explicit node ID(s): " + ", ".join(unknown))
        requested_ids = set(explicit_node_ids)
    else:
        requested_ids = None

    artifact_by_id = {artifact["id"]: artifact for artifact in plan.get("artifacts", [])}
    state_by_id: dict[str, str] = {}
    result_by_id: dict[str, dict[str, Any]] = {}

    for node_id in order:
        node = node_by_id[node_id]
        record: dict[str, Any] = {
            "id": node_id,
            "type": node["type"],
            "depth": depths[node_id],
        }
        condition_status, condition_reason = _condition_result(
            node.get("condition", {"operator": "always"}),
            normalized_inputs,
            artifacts_available,
            decisions,
        )
        if condition_status == "unresolved":
            record.update(state="unresolved", reason=condition_reason)
            state_by_id[node_id] = "unresolved"
            result_by_id[node_id] = record
            continue
        if condition_status == "not-matched":
            record.update(state="not-selected", reason=condition_reason)
            state_by_id[node_id] = "not-selected"
            result_by_id[node_id] = record
            continue

        dependency_states = {dep: state_by_id[dep] for dep in node.get("depends_on", [])}
        unsatisfied = [
            dep for dep, state in dependency_states.items() if state not in {"completed", "approved", "not-selected"}
        ]
        if unsatisfied:
            if node["type"] == "attorney-gate" and node_id in decisions:
                raise MatterPlanError(
                    f"attorney gate {node_id} cannot be decided before its dependencies are satisfied"
                )
            details = ", ".join(f"{dep}={dependency_states[dep]}" for dep in unsatisfied)
            record.update(state="blocked", reason="waiting on dependencies: " + details)
            state_by_id[node_id] = "blocked"
            result_by_id[node_id] = record
            continue

        if node["type"] == "attorney-gate":
            required_artifacts = node.get("gate", {}).get("required_artifacts", [])
            missing_artifacts = [item for item in required_artifacts if item not in artifacts_available]
            if missing_artifacts:
                if node_id in decisions:
                    raise MatterPlanError(
                        f"attorney gate {node_id} cannot be decided before required artifacts are available"
                    )
                record.update(
                    state="blocked",
                    reason="waiting on required artifacts: " + ", ".join(missing_artifacts),
                )
            elif decisions.get(node_id) == "approved":
                record.update(state="approved", reason="attorney gate explicitly approved")
            elif decisions.get(node_id) == "rejected":
                record.update(state="rejected", reason="attorney gate explicitly rejected")
            else:
                record.update(state="blocked", reason="waiting on explicit attorney approval")
            state_by_id[node_id] = record["state"]
            result_by_id[node_id] = record
            continue

        produced = node.get("produces", [])
        if produced and all(item in artifacts_available for item in produced):
            record.update(
                state="completed",
                reason="dependencies are satisfied and all declared output artifacts are available",
            )
            state_by_id[node_id] = "completed"
            result_by_id[node_id] = record
            continue

        spec = specs[node["skill_id"]]
        fields = {
            field["id"]: field
            for field in spec.get("input_schema", [])
            if isinstance(field, dict) and isinstance(field.get("id"), str)
        }
        bound_inputs: dict[str, Any] = {}
        binding_manifest: list[dict[str, Any]] = []
        unresolved_bindings: list[str] = []
        blocked_bindings: list[str] = []
        for binding in node.get("input_bindings", []):
            target_id = binding["target_input_id"]
            source = binding["source"]
            available, value, source_reason = _source_value(
                source, normalized_inputs, artifacts_available, decisions
            )
            if not available:
                if binding.get("required") is not True:
                    binding_manifest.append(
                        {
                            "target_input_id": target_id,
                            "source_kind": source.get("kind"),
                            "source_id": source.get("id"),
                            "transform": binding.get("transform", "identity"),
                            "required": False,
                            "available": False,
                            "reason": source_reason,
                        }
                    )
                    continue
                message = f"{target_id}: {source_reason}"
                if source.get("kind") in {"matter-input", "gate-decision"}:
                    unresolved_bindings.append(message)
                else:
                    blocked_bindings.append(message)
                continue
            transform = binding.get("transform", "identity")
            value = _transform_binding(value, transform, str(fields[target_id].get("type")))
            bound_inputs[target_id] = value
            manifest = {
                "target_input_id": target_id,
                "source_kind": source.get("kind"),
                "source_id": source.get("id"),
                "transform": transform,
                "required": binding.get("required") is True,
                "available": True,
                "reason": source_reason,
            }
            if source.get("kind") == "artifact":
                artifact = artifact_by_id[source.get("id")]
                manifest["producer_node_id"] = artifact.get("produced_by")
                manifest["attorney_review_required"] = artifact.get("attorney_review_required") is True
            binding_manifest.append(manifest)

        if unresolved_bindings:
            record.update(state="unresolved", reason="unresolved bindings: " + "; ".join(unresolved_bindings))
        elif blocked_bindings:
            record.update(state="blocked", reason="waiting on bindings: " + "; ".join(blocked_bindings))
        else:
            record.update(state="ready", reason="dependencies, condition, and bindings are satisfied")
            record["bindings"] = binding_manifest
        state_by_id[node_id] = record["state"]
        result_by_id[node_id] = record

    ready_ids = [node_id for node_id in order if state_by_id[node_id] == "ready"]
    if requested_ids is not None:
        not_ready = sorted(requested_ids - set(ready_ids))
        if not_ready:
            raise MatterPlanError(
                "Explicit node selection cannot bypass dependencies, conditions, or gates: "
                + ", ".join(not_ready)
            )
        context_ids = [node_id for node_id in ready_ids if node_id in requested_ids]
    else:
        context_ids = ready_ids

    for node_id in context_ids:
        node = node_by_id[node_id]
        record = result_by_id[node_id]
        bound_inputs: dict[str, Any] = {}
        spec = specs[node["skill_id"]]
        fields = {field["id"]: field for field in spec.get("input_schema", []) if isinstance(field, dict) and isinstance(field.get("id"), str)}
        for binding in node.get("input_bindings", []):
            available, value, _ = _source_value(binding["source"], normalized_inputs, artifacts_available, decisions)
            if not available:
                if binding.get("required") is not True:
                    continue
                raise MatterPlanError(f"ready node {node_id} lost binding availability")
            target_id = binding["target_input_id"]
            bound_inputs[target_id] = _transform_binding(
                value,
                binding.get("transform", "identity"),
                str(fields[target_id].get("type")),
            )
        try:
            record["context"] = build_skill_context(
                root,
                spec,
                node["mode"],
                bound_inputs,
                node.get("module_ids"),
            )
        except Exception as exc:
            raise MatterPlanError(f"could not build context for node {node_id}: {exc}") from exc

    result_nodes = [result_by_id[node_id] for node_id in order]
    wave_groups: dict[int, list[str]] = {}
    for node_id in context_ids:
        wave_groups.setdefault(depths[node_id], []).append(node_id)
    execution_waves: list[dict[str, Any]] = []
    for wave_number, depth in enumerate(sorted(wave_groups), start=1):
        node_ids = sorted(wave_groups[depth])
        tokens = sum(result_by_id[node_id]["context"]["estimated_tokens"]["total"] for node_id in node_ids)
        execution_waves.append(
            {"wave": wave_number, "depth": depth, "node_ids": node_ids, "estimated_tokens": tokens}
        )

    graph_depth = 1 + max(depths.values(), default=-1)
    width_by_depth: dict[int, int] = {}
    for depth in depths.values():
        width_by_depth[depth] = width_by_depth.get(depth, 0) + 1
    max_width = max(width_by_depth.values(), default=0)
    total_tokens = sum(wave["estimated_tokens"] for wave in execution_waves)
    budget = plan["budget"]
    violations: list[str] = []
    if graph_depth > budget["max_graph_depth"]:
        violations.append(f"graph depth {graph_depth} exceeds {budget['max_graph_depth']}")
    if max_width > budget["max_parallel_width"]:
        violations.append(f"parallel width {max_width} exceeds {budget['max_parallel_width']}")
    if len(context_ids) > budget["max_ready_nodes"]:
        violations.append(f"ready nodes {len(context_ids)} exceeds {budget['max_ready_nodes']}")
    if total_tokens > budget["max_total_estimated_tokens"]:
        violations.append(f"ready context tokens {total_tokens} exceeds {budget['max_total_estimated_tokens']}")
    if violations:
        raise MatterPlanError("Matter plan budget violation: " + "; ".join(violations))

    input_status = [
        {
            "id": field["id"],
            "type": field.get("type"),
            "required": field.get("required") is True,
            "sensitive": field.get("sensitive") is True,
            "present": field["id"] in normalized_inputs and normalized_inputs.get(field["id"]) not in (None, "", [], {}),
        }
        for field in plan.get("required_inputs", [])
    ]
    result = {
        "schema_version": PLAN_SCHEMA_VERSION,
        "plan_id": plan["plan_id"],
        "title": plan["title"],
        "input_status": input_status,
        "nodes": result_nodes,
        "topological_order": order,
        "execution_waves": execution_waves,
        "artifacts": [
            {
                "id": artifact["id"],
                "produced_by": artifact["produced_by"],
                "available": artifact["id"] in artifacts_available,
                "digest": artifacts_available.get(artifact["id"], {}).get("digest"),
                "attorney_review_required": artifact.get("attorney_review_required") is True,
                "sensitive": artifact.get("sensitive") is True,
            }
            for artifact in plan.get("artifacts", [])
        ],
        "budget": {
            "graph_depth": graph_depth,
            "max_parallel_width": max_width,
            "ready_node_count": len(context_ids),
            "ready_context_tokens": total_tokens,
            "limits": deepcopy(budget),
        },
    }
    if _include_receipt:
        result["receipt"] = _build_matter_plan_receipt(
            root, plan, result, normalized_inputs, artifacts_available, decisions, specs
        )
    return result


def _canonical_sha256(value: Any) -> str:
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def _file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _plan_identity(root: Path, plan: dict[str, Any]) -> tuple[str, str]:
    relative = f"matter-plans/{plan['plan_id']}.json"
    candidate = _repo_path(root, relative)
    if candidate is not None and candidate.is_file():
        return relative, _canonical_sha256(json.loads(candidate.read_text(encoding="utf-8")))
    return f"inline:{plan['plan_id']}", _canonical_sha256(plan)


def _redacted_input_presence(plan: dict[str, Any], normalized_inputs: dict[str, Any]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for field in plan.get("required_inputs", []):
        input_id = field["id"]
        present = input_id in normalized_inputs and normalized_inputs.get(input_id) not in (None, "", [], {})
        record: dict[str, Any] = {
            "id": input_id,
            "type": field.get("type"),
            "required": field.get("required") is True,
            "sensitive": field.get("sensitive") is True,
            "present": present,
        }
        if present and field.get("sensitive") is not True and field.get("type") in {
            "enum", "string-list", "boolean", "integer", "number"
        }:
            record["routing_value"] = normalized_inputs[input_id]
        records.append(record)
    return records


def _context_receipt_record(node: dict[str, Any]) -> dict[str, Any]:
    context = node["context"]
    record = {
        "node_id": node["id"],
        "skill_id": context["skill_id"],
        "contract_sha256": context["contract_sha256"],
        "core": {
            "path": context["core"]["path"],
            "sha256": context["core"]["sha256"],
            "estimated_tokens": context["core"]["estimated_tokens"],
        },
        "modules": [
            {
                "id": module["id"],
                "path": module["path"],
                "sha256": module["sha256"],
                "reason": module["reason"],
                "estimated_tokens": module["estimated_tokens"],
            }
            for module in context["modules"]
        ],
        "inherited_rules": deepcopy(context["inherited_rules"]),
        "estimated_tokens": deepcopy(context["estimated_tokens"]),
    }
    # The runtime bundle fingerprint includes normalized inputs. Receipts must
    # not retain sensitive matter values, so they use a verifiable resource-
    # bundle fingerprint over contracts, files, selection reasons, and token
    # arithmetic only.
    record["bundle_sha256"] = _canonical_sha256(record)
    return record


def _build_matter_plan_receipt(
    root: Path,
    plan: dict[str, Any],
    result: dict[str, Any],
    normalized_inputs: dict[str, Any],
    artifacts_available: dict[str, dict[str, Any]],
    gate_decisions: dict[str, str],
    skill_specs: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    plan_path, plan_sha256 = _plan_identity(root, plan)
    source_path = plan["source_path"]
    source_file = _repo_path(root, source_path)
    source_sha256 = _file_sha256(source_file) if source_file and source_file.is_file() else ""
    skill_ids = sorted(
        {
            node["skill_id"]
            for node in plan.get("nodes", [])
            if isinstance(node, dict) and node.get("type") == "skill"
        }
    )
    result_states = {node["id"]: node["state"] for node in result["nodes"]}
    receipt: dict[str, Any] = {
        "receipt_version": "1.0",
        "plan_id": plan["plan_id"],
        "plan_path": plan_path,
        "plan_sha256": plan_sha256,
        "source_path": source_path,
        "source_sha256": source_sha256,
        "input_presence": _redacted_input_presence(plan, normalized_inputs),
        "node_states": [
            {
                "id": node["id"],
                "type": node["type"],
                "state": node["state"],
                "reason": node["reason"],
                "depth": node["depth"],
            }
            for node in result["nodes"]
        ],
        "execution_waves": deepcopy(result["execution_waves"]),
        "context_node_ids": [
            node["id"] for node in result["nodes"] if "context" in node
        ],
        "artifact_lineage": [
            {
                "id": artifact["id"],
                "produced_by": artifact["produced_by"],
                "available": artifact["available"],
                "digest": artifacts_available.get(artifact["id"], {}).get("digest"),
                "attorney_review_required": artifact["attorney_review_required"],
                "sensitive": artifact["sensitive"],
            }
            for artifact in result["artifacts"]
        ],
        "gate_decisions": [
            {
                "id": node["id"],
                "decision": (
                    result_states[node["id"]]
                    if result_states[node["id"]] in {"approved", "rejected"}
                    else "pending"
                ),
            }
            for node in result["nodes"]
            if node.get("type") == "attorney-gate"
        ],
        "skill_contracts": [
            {"skill_id": skill_id, "sha256": _canonical_sha256(skill_specs[skill_id])}
            for skill_id in skill_ids
        ],
        "ready_contexts": [
            _context_receipt_record(node) for node in result["nodes"] if "context" in node
        ],
        "budget": deepcopy(result["budget"]),
    }
    receipt["receipt_sha256"] = _canonical_sha256(receipt)
    return receipt


def _placeholder_input(field: dict[str, Any], record: dict[str, Any]) -> Any:
    if not record.get("present"):
        return None
    if "routing_value" in record:
        return deepcopy(record["routing_value"])
    field_type = field.get("type")
    if field_type in {"text", "document", "date", "datetime", "jurisdiction"}:
        return "[receipt-redacted]"
    if field_type == "document-set":
        return ["[receipt-redacted]"]
    if field_type == "object":
        return {"redacted": True}
    if field_type == "boolean":
        return True
    if field_type in {"integer", "number"}:
        return 1
    if field_type == "string-list":
        allowed = field.get("items", [])
        return [allowed[0]] if allowed else ["redacted"]
    if field_type == "enum":
        allowed = field.get("enum", [])
        return allowed[0] if allowed else "redacted"
    return "[receipt-redacted]"


def _safe_receipt_path(root: Path, relative: Any) -> Path | None:
    if not isinstance(relative, str) or relative.startswith("inline:"):
        return None
    return _repo_path(root, relative)


def verify_matter_plan_receipt(root: Path, receipt: dict[str, Any]) -> dict[str, Any]:
    """Verify receipt integrity, repository drift, graph state, lineage, and budgets.

    Matter-plan receipts are deterministic self-consistency records, not digital
    signatures and not proof of who approved an attorney gate. Approval identity
    and authorization must be authenticated by the caller's own system.
    """
    root = Path(root).resolve()
    errors: list[str] = []
    if not isinstance(receipt, dict):
        return {"valid": False, "errors": ["receipt must be an object"]}

    allowed_receipt_fields = {
        "receipt_version", "plan_id", "plan_path", "plan_sha256",
        "source_path", "source_sha256", "input_presence", "node_states",
        "execution_waves", "context_node_ids", "artifact_lineage",
        "gate_decisions", "skill_contracts", "ready_contexts", "budget",
        "receipt_sha256",
    }
    unexpected = sorted(set(receipt) - allowed_receipt_fields)
    if unexpected:
        errors.append("unexpected receipt field(s): " + ", ".join(unexpected))
    if receipt.get("receipt_version") != "1.0":
        errors.append("receipt version must be 1.0")

    supplied_digest = receipt.get("receipt_sha256")
    payload = deepcopy(receipt)
    payload.pop("receipt_sha256", None)
    if supplied_digest != _canonical_sha256(payload):
        errors.append("receipt digest mismatch")

    plan_path = receipt.get("plan_path")
    path = _safe_receipt_path(root, plan_path)
    if path is None or not path.is_file():
        errors.append("receipt plan path is unsafe or unavailable")
        return {"valid": False, "errors": sorted(set(errors))}
    try:
        plan = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"could not read current plan: {exc}")
        return {"valid": False, "errors": sorted(set(errors))}

    expected_plan_path = f"matter-plans/{plan.get('plan_id')}.json"
    if plan_path != expected_plan_path:
        errors.append("plan path does not match the canonical plan ID")
    if receipt.get("plan_id") != plan.get("plan_id"):
        errors.append("plan ID mismatch")
    if receipt.get("plan_sha256") != _canonical_sha256(plan):
        errors.append("plan source changed")

    expected_source_path = plan.get("source_path")
    if receipt.get("source_path") != expected_source_path:
        errors.append("source path does not match current plan")
    source = _safe_receipt_path(root, expected_source_path)
    if source is None or not source.is_file():
        errors.append("receipt source path is unsafe or unavailable")
    elif receipt.get("source_sha256") != _file_sha256(source):
        errors.append("human guidance source changed")

    try:
        specs = load_skill_spec_registry(root)
    except MatterPlanError as exc:
        errors.append(str(exc))
        return {"valid": False, "errors": sorted(set(errors))}

    skill_ids = sorted(
        {
            node.get("skill_id")
            for node in plan.get("nodes", [])
            if isinstance(node, dict)
            and node.get("type") == "skill"
            and isinstance(node.get("skill_id"), str)
        }
    )
    expected_contracts = [
        {"skill_id": skill_id, "sha256": _canonical_sha256(specs[skill_id])}
        for skill_id in skill_ids
        if skill_id in specs
    ]
    if receipt.get("skill_contracts") != expected_contracts:
        errors.append("skill contract inventory or hash changed")

    supplied_input_presence = receipt.get("input_presence")
    input_records: dict[str, dict[str, Any]] = {}
    allowed_input_fields = {
        "id", "type", "required", "sensitive", "present", "routing_value"
    }
    if not isinstance(supplied_input_presence, list):
        errors.append("input presence must be a list")
        supplied_input_presence = []
    for item in supplied_input_presence:
        if not isinstance(item, dict):
            errors.append("input presence records must be objects")
            continue
        extra = sorted(set(item) - allowed_input_fields)
        if extra:
            errors.append(
                "input presence record has unexpected field(s): "
                + ", ".join(extra)
            )
        input_id = item.get("id")
        if not isinstance(input_id, str) or input_id in input_records:
            errors.append("input presence IDs must be unique strings")
            continue
        input_records[input_id] = item

    replay_inputs: dict[str, Any] = {}
    for field in plan.get("required_inputs", []):
        record = input_records.get(field.get("id"))
        if record is None:
            errors.append(f"input presence record missing: {field.get('id')}")
            continue
        placeholder = _placeholder_input(field, record)
        if record.get("present"):
            replay_inputs[field["id"]] = placeholder

    receipt_lineage = receipt.get("artifact_lineage")
    if not isinstance(receipt_lineage, list):
        errors.append("artifact lineage must be a list")
        receipt_lineage = []
    replay_artifacts: dict[str, dict[str, Any]] = {}
    for record in receipt_lineage:
        if not isinstance(record, dict):
            errors.append("artifact lineage records must be objects")
            continue
        if record.get("available") is True and isinstance(record.get("id"), str):
            metadata: dict[str, Any] = {}
            if record.get("digest") is not None:
                metadata["digest"] = record.get("digest")
            replay_artifacts[record["id"]] = metadata

    supplied_gates = receipt.get("gate_decisions")
    if not isinstance(supplied_gates, list):
        errors.append("gate decisions must be a list")
        supplied_gates = []
    replay_gates: dict[str, str] = {}
    for item in supplied_gates:
        if not isinstance(item, dict) or set(item) != {"id", "decision"}:
            errors.append("gate decision records must contain only id and decision")
            continue
        if item.get("decision") in {"approved", "rejected"}:
            replay_gates[str(item.get("id"))] = str(item.get("decision"))
        elif item.get("decision") != "pending":
            errors.append(f"invalid gate decision: {item.get('decision')}")

    context_node_ids = receipt.get("context_node_ids")
    if (
        not isinstance(context_node_ids, list)
        or any(not isinstance(item, str) for item in context_node_ids)
        or len(context_node_ids) != len(set(context_node_ids))
    ):
        errors.append("context_node_ids must be a unique string list")
        context_node_ids = []

    try:
        replay = build_matter_plan(
            root,
            plan,
            matter_inputs=replay_inputs,
            available_artifacts=replay_artifacts,
            gate_decisions=replay_gates,
            explicit_node_ids=context_node_ids,
            skill_specs=specs,
            _include_receipt=False,
        )
    except MatterPlanError as exc:
        errors.append(f"could not replay receipt: {exc}")
        return {"valid": False, "errors": sorted(set(errors))}

    expected_input_presence = _redacted_input_presence(plan, replay_inputs)
    if supplied_input_presence != expected_input_presence:
        errors.append("input presence metadata mismatch")

    expected_states = [
        {key: node[key] for key in ("id", "type", "state", "reason", "depth")}
        for node in replay["nodes"]
    ]
    if receipt.get("node_states") != expected_states:
        errors.append("node state trace mismatch")
    if receipt.get("execution_waves") != replay.get("execution_waves"):
        errors.append("execution wave or token arithmetic mismatch")

    expected_context_ids = [node["id"] for node in replay["nodes"] if "context" in node]
    if context_node_ids != expected_context_ids:
        errors.append("context node selection mismatch")

    expected_lineage = [
        {
            "id": artifact["id"],
            "produced_by": artifact["produced_by"],
            "available": artifact["available"],
            "digest": artifact.get("digest"),
            "attorney_review_required": artifact["attorney_review_required"],
            "sensitive": artifact["sensitive"],
        }
        for artifact in replay["artifacts"]
    ]
    if receipt_lineage != expected_lineage:
        errors.append("artifact lineage mismatch")

    expected_gates = [
        {
            "id": node["id"],
            "decision": node["state"]
            if node["state"] in {"approved", "rejected"}
            else "pending",
        }
        for node in replay["nodes"]
        if node["type"] == "attorney-gate"
    ]
    if supplied_gates != expected_gates:
        errors.append("gate decision trace mismatch")

    if receipt.get("budget") != replay.get("budget"):
        errors.append("budget or token arithmetic mismatch")

    supplied_contexts = receipt.get("ready_contexts")
    if not isinstance(supplied_contexts, list):
        errors.append("ready contexts must be a list")
        supplied_contexts = []
    replay_contexts = [
        _context_receipt_record(node) for node in replay["nodes"] if "context" in node
    ]
    if supplied_contexts != replay_contexts:
        errors.append("ready context resources or contracts changed")

    return {"valid": not errors, "errors": sorted(set(errors))}
