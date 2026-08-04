#!/usr/bin/env python3
"""Compile and validate AgentCounsel Skill Specification v2 contracts.

Existing ``SKILL.md`` files remain canonical human-readable workflows. An
optional ``SPEC.json`` beside a skill can refine the typed execution contract.
The compiler always preserves baseline legal-safety controls.
"""

from __future__ import annotations

import json
import math
import re
from copy import deepcopy
from pathlib import Path
from typing import Any

SCHEMA_VERSION = "2.0"
SPEC_FILENAME = "SPEC.json"

BASELINE_INHERITS = (
    "core/legal-work-product.md",
    "core/source-and-citation-discipline.md",
    "core/output-format-rules.md",
    "core/attorney-review-checklist.md",
)
DEADLINE_GATE_PATH = "core/jurisdiction-and-deadline-gates.md"

BASELINE_EVIDENCE_FIELDS = (
    "claim_id",
    "source_document_id",
    "locator",
    "support_type",
    "verification_status",
)

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
OUTPUT_TYPES = {
    "section",
    "table",
    "checklist",
    "memo",
    "letter",
    "tracker",
    "timeline",
    "matrix",
    "structured-data",
}
MODE_IDS = ("quick-triage", "standard", "deep-review")
OUTPUT_DETAIL_LEVELS = {"minimal", "standard", "expanded"}
MODULE_KINDS = {
    "reference",
    "template",
    "profile",
    "connector",
    "quality-check",
    "workflow-module",
}
CUSTOM_GATE_ACTIONS = {
    "flag",
    "stop-and-ask",
    "stop-and-escalate",
    "require-attorney-confirmation",
}
MODULE_ACTIVATION_OPERATORS = {"always", "present", "equals", "contains-any"}


class SpecValidationError(ValueError):
    """Raised when a custom or compiled Skill Specification is invalid."""


def _slug(value: str) -> str:
    value = value.strip().lower().replace("'", "")
    value = re.sub(r"^(the|a|an)\s+", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value).strip("-")
    return value or "field"


def _clean_legacy_label(value: str) -> tuple[str, bool]:
    value = value.strip().strip('"').strip("'")
    required = True
    if value.lower().startswith("optional:"):
        required = False
        value = value.split(":", 1)[1].strip()
    if value:
        value = value[0].lower() + value[1:]
    return value, required


def _infer_input_type(label: str) -> str:
    low = label.lower()
    if "jurisdiction" in low or "governing law" in low:
        return "jurisdiction"
    if "date and time" in low or "timestamp" in low or "date/time" in low:
        return "datetime"
    if "date" in low:
        return "date"
    plural_document_terms = (
        "document set",
        "agreements",
        "contracts",
        "policies",
        "reports",
        "authorities",
        "files",
    )
    if any(term in low for term in plural_document_terms):
        return "document-set"
    document_terms = (
        "document",
        "agreement",
        "contract",
        "policy",
        "memo",
        "report",
        "text",
        "notice",
        "complaint",
        "brief",
    )
    if any(term in low for term in document_terms):
        return "document"
    return "text"


def _infer_output_type(label: str) -> str:
    low = label.lower()
    if "table" in low:
        return "table"
    if "checklist" in low:
        return "checklist"
    if "memo" in low or "memorandum" in low:
        return "memo"
    if "letter" in low or "notice" in low:
        return "letter"
    if "tracker" in low or "register" in low:
        return "tracker"
    if "chronology" in low or "timeline" in low:
        return "timeline"
    if "matrix" in low:
        return "matrix"
    if any(term in low for term in ("json", "csv", "structured data")):
        return "structured-data"
    return "section"


def _unique(values: list[str] | tuple[str, ...]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def _merge_records(base: list[dict[str, Any]], overlay: Any) -> list[dict[str, Any]]:
    if overlay is None:
        return deepcopy(base)
    if not isinstance(overlay, list):
        return deepcopy(base)
    order: list[str] = []
    records: dict[str, dict[str, Any]] = {}
    anonymous: list[dict[str, Any]] = []
    for item in base:
        item_copy = deepcopy(item)
        item_id = item_copy.get("id")
        if isinstance(item_id, str):
            order.append(item_id)
            records[item_id] = item_copy
        else:
            anonymous.append(item_copy)
    for item in overlay:
        if not isinstance(item, dict):
            anonymous.append(deepcopy(item))
            continue
        item_id = item.get("id")
        if isinstance(item_id, str) and item_id in records:
            records[item_id].update(deepcopy(item))
        elif isinstance(item_id, str):
            order.append(item_id)
            records[item_id] = deepcopy(item)
        else:
            anonymous.append(deepcopy(item))
    return [records[item_id] for item_id in order] + anonymous


def load_custom_spec(skill_dir: Path) -> dict[str, Any] | None:
    """Load an optional ``SPEC.json`` sidecar as a JSON object."""
    path = skill_dir / SPEC_FILENAME
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise SpecValidationError(f"{path}: invalid JSON: {exc}") from exc
    if not isinstance(data, dict):
        raise SpecValidationError(f"{path}: top level must be a JSON object")
    return data


def _legacy_inputs(items: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in items if isinstance(items, list) else []:
        if not isinstance(raw, str):
            continue
        label, required = _clean_legacy_label(raw)
        field_type = _infer_input_type(label)
        result.append(
            {
                "id": _slug(label),
                "label": label,
                "type": field_type,
                "required": required,
                "description": label,
                "source_requirement": (
                    "provided-document"
                    if field_type in {"document", "document-set"}
                    else "user-provided"
                ),
                "may_infer": False,
                "sensitive": False,
            }
        )
    return result


def _legacy_outputs(items: Any) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for raw in items if isinstance(items, list) else []:
        if not isinstance(raw, str):
            continue
        label = raw.strip().strip('"').strip("'")
        result.append(
            {
                "id": _slug(label),
                "label": label,
                "type": _infer_output_type(label),
                "required": True,
                "description": label,
                "attorney_review_required": True,
            }
        )
    return result


def _default_modes(quality_checks: list[str], deadline_or_jurisdiction: bool) -> list[dict[str, Any]]:
    quick_checks = ["attorney-review-gate"]
    if deadline_or_jurisdiction:
        quick_checks.append("jurisdiction-deadline-gates")
    deep_checks = _unique(
        quality_checks
        + [
            "assumption-audit",
            "hallucination-red-team",
            "output-format-compliance-check",
        ]
    )
    return [
        {
            "id": "quick-triage",
            "enabled": True,
            "purpose": "Confirm applicability, missing inputs, top issues, and escalation without producing the full deliverable.",
            "output_detail": "minimal",
            "quality_checks": quick_checks,
        },
        {
            "id": "standard",
            "enabled": True,
            "purpose": "Produce the default attorney-ready draft work product defined by the skill.",
            "output_detail": "standard",
            "quality_checks": list(quality_checks),
        },
        {
            "id": "deep-review",
            "enabled": True,
            "purpose": "Run the full workflow, load applicable references and modules, and apply expanded verification checks.",
            "output_detail": "expanded",
            "quality_checks": deep_checks,
        },
    ]


def _default_evidence_schema() -> dict[str, Any]:
    field_types = {
        "claim_id": "text",
        "source_document_id": "text",
        "locator": "text",
        "support_text": "text",
        "support_type": "enum",
        "verification_status": "enum",
        "confidence": "enum",
        "reviewer": "text",
        "reviewed_at": "datetime",
    }
    return {
        "record_type": "claim-support",
        "required_fields": list(BASELINE_EVIDENCE_FIELDS),
        "fields": [
            {
                "id": field_id,
                "type": field_type,
                "description": field_id.replace("_", " "),
            }
            for field_id, field_type in field_types.items()
        ],
    }


def _default_contract(
    skill_dir: Path,
    metadata: dict[str, Any],
    derived: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    area = str(metadata.get("practice_area", skill_dir.parent.name))
    skill_id = f"{area}/{skill_dir.name}"
    requires_jurisdiction = bool(derived.get("requires_jurisdiction"))
    requires_deadline = bool(derived.get("requires_deadline_check"))
    quality_checks = _unique(
        [
            item
            for item in derived.get("recommended_quality_checks", [])
            if isinstance(item, str)
        ]
    )
    inherits = list(BASELINE_INHERITS)
    if requires_jurisdiction or requires_deadline:
        inherits.append(DEADLINE_GATE_PATH)
    risk_level = str(metadata.get("risk_level", "medium"))
    escalation = {
        "minimum": (
            "immediate-attorney-attention"
            if risk_level == "critical"
            else "attorney-escalation"
            if risk_level == "high"
            else "attorney-review"
        )
    }
    return {
        "schema_version": SCHEMA_VERSION,
        "skill_id": skill_id,
        "title": metadata.get("name") or skill_dir.name.replace("-", " ").title(),
        "skill_path": (skill_dir / "SKILL.md").relative_to(root).as_posix(),
        "spec_path": None,
        "has_custom_spec": False,
        "inherits": inherits,
        "gates": {
            "missing_inputs": {"behavior": "stop-and-ask"},
            "attorney_review": {
                "required": bool(metadata.get("requires_attorney_review", True))
            },
            "jurisdiction": {"required": requires_jurisdiction},
            "deadline": {
                "required": requires_deadline,
                "calculation_allowed": False,
            },
            "escalation": escalation,
            "custom": [],
        },
        "execution_modes": _default_modes(
            quality_checks, requires_jurisdiction or requires_deadline
        ),
        "input_schema": _legacy_inputs(metadata.get("inputs")),
        "output_schema": _legacy_outputs(metadata.get("outputs")),
        "evidence_schema": _default_evidence_schema(),
        "modules": [],
        "quality_checks": quality_checks,
    }


def _merge_custom(
    base: dict[str, Any], custom: dict[str, Any], root: Path, skill_dir: Path
) -> dict[str, Any]:
    result = deepcopy(base)
    if "schema_version" in custom:
        result["schema_version"] = custom["schema_version"]
    if "skill_id" in custom:
        result["skill_id"] = custom["skill_id"]
    result["has_custom_spec"] = True
    result["spec_path"] = (skill_dir / SPEC_FILENAME).relative_to(root).as_posix()

    custom_inherits = custom.get("inherits", [])
    if isinstance(custom_inherits, list):
        result["inherits"] = _unique(result["inherits"] + custom_inherits)

    custom_gates = custom.get("gates")
    if isinstance(custom_gates, dict):
        for gate_id in (
            "missing_inputs",
            "attorney_review",
            "jurisdiction",
            "deadline",
            "escalation",
        ):
            if gate_id in custom_gates and isinstance(custom_gates[gate_id], dict):
                result["gates"][gate_id].update(deepcopy(custom_gates[gate_id]))
        if "custom" in custom_gates:
            result["gates"]["custom"] = _merge_records(
                result["gates"].get("custom", []), custom_gates.get("custom")
            )

    result["execution_modes"] = _merge_records(
        result["execution_modes"], custom.get("execution_modes")
    )
    result["input_schema"] = _merge_records(
        result["input_schema"], custom.get("input_schema")
    )
    result["output_schema"] = _merge_records(
        result["output_schema"], custom.get("output_schema")
    )
    result["modules"] = _merge_records(result["modules"], custom.get("modules"))
    if "context_scenarios" in custom:
        result["context_scenarios"] = _merge_records(
            result.get("context_scenarios", []), custom.get("context_scenarios")
        )

    evidence = custom.get("evidence_schema")
    if isinstance(evidence, dict):
        if evidence.get("replace_required_fields") is True:
            result["evidence_schema"]["required_fields"] = list(
                evidence.get("required_fields", [])
            )
        elif isinstance(evidence.get("required_fields"), list):
            result["evidence_schema"]["required_fields"] = _unique(
                result["evidence_schema"]["required_fields"]
                + evidence["required_fields"]
            )
        result["evidence_schema"]["fields"] = _merge_records(
            result["evidence_schema"]["fields"], evidence.get("fields")
        )

    if isinstance(custom.get("quality_checks"), list):
        result["quality_checks"] = _unique(
            result["quality_checks"] + custom["quality_checks"]
        )
    return result


def _duplicate_ids(records: Any) -> list[str]:
    if not isinstance(records, list):
        return []
    seen: set[str] = set()
    duplicates: list[str] = []
    for record in records:
        if not isinstance(record, dict) or not isinstance(record.get("id"), str):
            continue
        record_id = record["id"]
        if record_id in seen:
            duplicates.append(record_id)
        seen.add(record_id)
    return duplicates


def _casefold_duplicates(values: Any) -> list[str]:
    """Return later values that collide after runtime normalization."""
    if not isinstance(values, list):
        return []
    seen: set[str] = set()
    duplicates: list[str] = []
    for value in values:
        if not isinstance(value, str):
            continue
        normalized = value.strip().casefold()
        if normalized in seen:
            duplicates.append(value)
        seen.add(normalized)
    return duplicates


def validate_compiled_spec(spec: dict[str, Any], root: Path) -> list[str]:
    """Return all validation errors for one compiled contract."""
    errors: list[str] = []
    if spec.get("schema_version") != SCHEMA_VERSION:
        errors.append(f"schema_version must be {SCHEMA_VERSION}")
    skill_id = spec.get("skill_id")
    if not isinstance(skill_id, str) or not re.fullmatch(
        r"[a-z0-9][a-z0-9-]*/[a-z0-9][a-z0-9-]*", skill_id
    ):
        errors.append("skill_id must use <practice-area>/<skill-slug>")

    inherits = spec.get("inherits")
    if not isinstance(inherits, list):
        errors.append("inherits must be a list")
        inherits = []
    missing_baseline = [path for path in BASELINE_INHERITS if path not in inherits]
    if missing_baseline:
        errors.append(
            "inherits may not remove baseline safety paths: "
            + ", ".join(missing_baseline)
        )
    for path in inherits:
        if not isinstance(path, str) or not (root / path).is_file():
            errors.append(f"inherits path does not resolve: {path}")

    gates = spec.get("gates")
    if not isinstance(gates, dict):
        errors.append("gates must be an object")
        gates = {}
    if gates.get("missing_inputs", {}).get("behavior") != "stop-and-ask":
        errors.append("missing_inputs behavior must remain stop-and-ask")
    if gates.get("attorney_review", {}).get("required") is not True:
        errors.append("attorney_review.required must remain true")
    if gates.get("deadline", {}).get("calculation_allowed") is not False:
        errors.append("deadline.calculation_allowed must remain false")
    custom_gates = gates.get("custom", [])
    duplicates = _duplicate_ids(custom_gates)
    if duplicates:
        errors.append("duplicate custom gate ids: " + ", ".join(duplicates))
    if isinstance(custom_gates, list):
        for gate in custom_gates:
            if not isinstance(gate, dict):
                errors.append("custom gates must be objects")
                continue
            for field in ("id", "condition", "action", "reason"):
                if not isinstance(gate.get(field), str) or not gate[field].strip():
                    errors.append(f"custom gate missing non-empty {field}")
            if gate.get("action") not in CUSTOM_GATE_ACTIONS:
                errors.append(f"invalid custom gate action: {gate.get('action')}")

    modes = spec.get("execution_modes")
    if not isinstance(modes, list):
        errors.append("execution_modes must be a list")
        modes = []
    mode_duplicates = _duplicate_ids(modes)
    if mode_duplicates:
        errors.append("duplicate execution mode ids: " + ", ".join(mode_duplicates))
    mode_ids = [mode.get("id") for mode in modes if isinstance(mode, dict)]
    for required_mode in MODE_IDS:
        if required_mode not in mode_ids:
            errors.append(f"missing execution mode: {required_mode}")
    for mode in modes:
        if not isinstance(mode, dict):
            errors.append("execution modes must be objects")
            continue
        if mode.get("id") not in MODE_IDS:
            errors.append(f"invalid execution mode id: {mode.get('id')}")
        if not isinstance(mode.get("enabled"), bool):
            errors.append(f"execution mode {mode.get('id')} enabled must be boolean")
        if mode.get("output_detail") not in OUTPUT_DETAIL_LEVELS:
            errors.append(
                f"execution mode {mode.get('id')} has invalid output_detail"
            )
        if not isinstance(mode.get("purpose"), str) or not mode["purpose"].strip():
            errors.append(f"execution mode {mode.get('id')} needs a purpose")
        if not isinstance(mode.get("quality_checks"), list):
            errors.append(
                f"execution mode {mode.get('id')} quality_checks must be a list"
            )

    inputs = spec.get("input_schema")
    if not isinstance(inputs, list):
        errors.append("input_schema must be a list")
        inputs = []
    input_duplicates = _duplicate_ids(inputs)
    if input_duplicates:
        errors.append("duplicate input ids: " + ", ".join(input_duplicates))
    for field in inputs:
        if not isinstance(field, dict):
            errors.append("input fields must be objects")
            continue
        for required_field in (
            "id",
            "label",
            "type",
            "required",
            "description",
            "source_requirement",
            "may_infer",
            "sensitive",
        ):
            if required_field not in field:
                errors.append(
                    f"input {field.get('id', '<unknown>')} missing {required_field}"
                )
        if field.get("type") not in INPUT_TYPES:
            errors.append(f"invalid input type: {field.get('type')}")
        if field.get("required") is True and field.get("may_infer") is not False:
            errors.append(
                f"required input {field.get('id')} must set may_infer to false"
            )
        if field.get("type") == "enum":
            enum = field.get("enum")
            if not isinstance(enum, list) or not enum or any(
                not isinstance(item, str) or not item.strip() for item in enum
            ):
                errors.append(f"enum input {field.get('id')} needs string values")
            elif _casefold_duplicates(enum):
                errors.append(
                    f"enum input {field.get('id')} values must be unique after normalization"
                )
        if field.get("type") == "string-list" and "items" in field:
            items = field.get("items")
            if not isinstance(items, list) or not items or any(
                not isinstance(item, str) or not item.strip() for item in items
            ):
                errors.append(
                    f"string-list input {field.get('id')} items must be non-empty strings"
                )
            elif _casefold_duplicates(items):
                errors.append(
                    f"string-list input {field.get('id')} items must be unique after normalization"
                )

    outputs = spec.get("output_schema")
    if not isinstance(outputs, list):
        errors.append("output_schema must be a list")
        outputs = []
    output_duplicates = _duplicate_ids(outputs)
    if output_duplicates:
        errors.append("duplicate output ids: " + ", ".join(output_duplicates))
    for artifact in outputs:
        if not isinstance(artifact, dict):
            errors.append("output artifacts must be objects")
            continue
        for required_field in (
            "id",
            "label",
            "type",
            "required",
            "description",
            "attorney_review_required",
        ):
            if required_field not in artifact:
                errors.append(
                    f"output {artifact.get('id', '<unknown>')} missing {required_field}"
                )
        if artifact.get("type") not in OUTPUT_TYPES:
            errors.append(f"invalid output type: {artifact.get('type')}")
        if artifact.get("attorney_review_required") is not True:
            errors.append(
                f"output {artifact.get('id')} must require attorney review"
            )

    evidence = spec.get("evidence_schema")
    if not isinstance(evidence, dict):
        errors.append("evidence_schema must be an object")
        evidence = {}
    required_evidence = evidence.get("required_fields")
    if not isinstance(required_evidence, list):
        errors.append("evidence_schema.required_fields must be a list")
        required_evidence = []
    missing_evidence = [
        field for field in BASELINE_EVIDENCE_FIELDS if field not in required_evidence
    ]
    if missing_evidence:
        errors.append(
            "evidence schema may not remove baseline fields: "
            + ", ".join(missing_evidence)
        )

    modules = spec.get("modules")
    if not isinstance(modules, list):
        errors.append("modules must be a list")
        modules = []
    module_duplicates = _duplicate_ids(modules)
    if module_duplicates:
        errors.append("duplicate module ids: " + ", ".join(module_duplicates))
    input_fields = {
        field.get("id"): field
        for field in inputs
        if isinstance(field, dict) and isinstance(field.get("id"), str)
    }
    for module in modules:
        if not isinstance(module, dict):
            errors.append("modules must be objects")
            continue
        for field in ("id", "kind", "path", "required", "load_when"):
            if field not in module:
                errors.append(
                    f"module {module.get('id', '<unknown>')} missing {field}"
                )
        module_id = module.get("id")
        if not isinstance(module_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]*", module_id
        ):
            errors.append("module needs a slug-form id")
        if module.get("kind") not in MODULE_KINDS:
            errors.append(f"invalid module kind: {module.get('kind')}")
        path = module.get("path")
        if not isinstance(path, str) or not path:
            errors.append(f"module path does not resolve: {path}")
        else:
            resolved_path = (root / path).resolve()
            if not resolved_path.is_relative_to(root.resolve()):
                errors.append(f"module path escapes repository root: {path}")
            elif not resolved_path.is_file():
                errors.append(f"module path does not resolve: {path}")
        if not isinstance(module.get("required"), bool):
            errors.append(f"module {module.get('id')} required must be boolean")
        activation = module.get("activation")
        if activation is not None:
            if not isinstance(activation, dict):
                errors.append(
                    f"module {module.get('id')} activation must be an object"
                )
                continue
            modes = activation.get("modes")
            if not isinstance(modes, list) or not modes or any(
                not isinstance(mode, str) or mode not in MODE_IDS for mode in modes
            ):
                errors.append(
                    f"module {module.get('id')} activation modes must be known modes"
                )
            elif len(modes) != len(set(modes)):
                errors.append(
                    f"module {module.get('id')} activation modes must be unique"
                )

            operator = activation.get("operator")
            if operator not in MODULE_ACTIVATION_OPERATORS:
                errors.append(
                    f"module {module.get('id')} has invalid activation operator: {operator}"
                )
                continue

            has_input_id = "input_id" in activation
            has_value = "value" in activation
            has_values = "values" in activation
            input_id = activation.get("input_id")

            if operator == "always":
                if has_input_id or has_value or has_values:
                    errors.append(
                        f"module {module.get('id')} always activation may not declare input fields"
                    )
                continue

            if not isinstance(input_id, str) or not input_id:
                errors.append(
                    f"module {module.get('id')} activation needs a non-empty input_id"
                )
                continue
            if input_id not in input_fields:
                errors.append(
                    f"module {module.get('id')} activation references unknown input: {input_id}"
                )
                continue

            if operator == "present":
                if has_value or has_values:
                    errors.append(
                        f"module {module.get('id')} present activation may not declare values"
                    )
                continue

            if operator == "equals":
                value = activation.get("value")
                if not isinstance(value, str) or not value or has_values:
                    errors.append(
                        f"module {module.get('id')} equals activation needs one non-empty value"
                    )
                    continue
                activation_values = [value]
            else:
                values = activation.get("values")
                if (
                    not isinstance(values, list)
                    or not values
                    or any(not isinstance(value, str) or not value.strip() for value in values)
                    or has_value
                ):
                    errors.append(
                        f"module {module.get('id')} contains-any activation needs non-empty string values"
                    )
                    continue
                if _casefold_duplicates(values):
                    errors.append(
                        f"module {module.get('id')} activation values must be unique after normalization"
                    )
                activation_values = values

            input_field = input_fields[input_id]
            allowed_values = input_field.get("enum") or input_field.get("items")
            if isinstance(allowed_values, list):
                unknown_values = [
                    value for value in activation_values if value not in allowed_values
                ]
                if unknown_values:
                    errors.append(
                        f"module {module.get('id')} activation values are not allowed by input {input_id}: "
                        + ", ".join(unknown_values)
                    )

    context_scenarios = spec.get("context_scenarios", [])
    if not isinstance(context_scenarios, list):
        errors.append("context_scenarios must be a list")
        context_scenarios = []
    scenario_duplicates = _duplicate_ids(context_scenarios)
    if scenario_duplicates:
        errors.append(
            "duplicate context scenario ids: " + ", ".join(scenario_duplicates)
        )
    for scenario in context_scenarios:
        if not isinstance(scenario, dict):
            errors.append("context scenarios must be objects")
            continue
        scenario_id = scenario.get("id")
        if not isinstance(scenario_id, str) or not re.fullmatch(
            r"[a-z0-9][a-z0-9-]*", scenario_id
        ):
            errors.append("context scenario needs a slug-form id")
        if scenario.get("mode") not in MODE_IDS:
            errors.append(
                f"context scenario {scenario_id or '<unknown>'} has invalid mode"
            )
        scenario_inputs = scenario.get("inputs")
        if not isinstance(scenario_inputs, dict):
            errors.append(
                f"context scenario {scenario_id or '<unknown>'} inputs must be an object"
            )
        else:
            unknown_inputs = sorted(set(scenario_inputs) - set(input_fields))
            if unknown_inputs:
                errors.append(
                    f"context scenario {scenario_id or '<unknown>'} references unknown inputs: "
                    + ", ".join(unknown_inputs)
                )
        baseline = scenario.get("baseline_estimated_tokens")
        if isinstance(baseline, bool) or not isinstance(baseline, int) or baseline <= 0:
            errors.append(
                f"context scenario {scenario_id or '<unknown>'} baseline_estimated_tokens must be a positive integer"
            )
        max_ratio = scenario.get("max_ratio")
        if (
            isinstance(max_ratio, bool)
            or not isinstance(max_ratio, (int, float))
            or not math.isfinite(max_ratio)
            or max_ratio <= 0
        ):
            errors.append(
                f"context scenario {scenario_id or '<unknown>'} max_ratio must be positive"
            )

    quality_checks = spec.get("quality_checks")
    if not isinstance(quality_checks, list) or any(
        not isinstance(item, str) or not item for item in quality_checks
    ):
        errors.append("quality_checks must be a list of non-empty strings")
    return errors



def _raw_overlay_duplicate_errors(custom: dict[str, Any]) -> list[str]:
    """Detect duplicate stable IDs before merge normalization collapses them."""
    groups: list[tuple[str, Any]] = [
        ("execution mode", custom.get("execution_modes")),
        ("input", custom.get("input_schema")),
        ("output", custom.get("output_schema")),
        ("module", custom.get("modules")),
        ("context scenario", custom.get("context_scenarios")),
    ]
    gates = custom.get("gates")
    if isinstance(gates, dict):
        groups.append(("custom gate", gates.get("custom")))
    evidence = custom.get("evidence_schema")
    if isinstance(evidence, dict):
        groups.append(("evidence field", evidence.get("fields")))
    errors: list[str] = []
    for label, records in groups:
        duplicates = _duplicate_ids(records)
        if duplicates:
            errors.append(
                f"duplicate {label} ids in custom spec: " + ", ".join(duplicates)
            )
    return errors

def compile_skill_spec(
    skill_dir: Path,
    metadata: dict[str, Any],
    body: str,
    derived: dict[str, Any],
    root: Path,
) -> dict[str, Any]:
    """Compile one legacy skill and optional sidecar into a validated v2 contract."""
    del body  # Reserved for later module extraction; metadata and derived fields suffice now.
    root = Path(root)
    skill_dir = Path(skill_dir)
    expected_id = f"{metadata.get('practice_area', skill_dir.parent.name)}/{skill_dir.name}"
    result = _default_contract(skill_dir, metadata, derived, root)
    custom = load_custom_spec(skill_dir)
    if custom is not None:
        duplicate_errors = _raw_overlay_duplicate_errors(custom)
        if duplicate_errors:
            raise SpecValidationError(
                f"{skill_dir / SPEC_FILENAME}: invalid Skill Specification v2:\n- "
                + "\n- ".join(duplicate_errors)
            )
        result = _merge_custom(result, custom, root, skill_dir)
        explicit_version = custom.get("schema_version")
        if explicit_version is not None and explicit_version != SCHEMA_VERSION:
            raise SpecValidationError(
                f"{skill_dir / SPEC_FILENAME}: schema_version must be {SCHEMA_VERSION}"
            )
        explicit_id = custom.get("skill_id")
        if explicit_id is not None and explicit_id != expected_id:
            raise SpecValidationError(
                f"{skill_dir / SPEC_FILENAME}: skill_id must be {expected_id}"
            )
    errors = validate_compiled_spec(result, root)
    if errors:
        location = skill_dir / SPEC_FILENAME if custom is not None else skill_dir / "SKILL.md"
        raise SpecValidationError(
            f"{location}: invalid Skill Specification v2:\n- " + "\n- ".join(errors)
        )
    return result
