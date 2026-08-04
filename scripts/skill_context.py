#!/usr/bin/env python3
"""Build deterministic, selectively loaded AgentCounsel context bundles.

This module is deliberately standard-library-only. It evaluates only explicit
Skill Specification v2 activation records; human-readable ``load_when`` prose
is never interpreted as executable routing logic.
"""

from __future__ import annotations

import hashlib
import json
import math
from copy import deepcopy
from pathlib import Path
from typing import Any

try:  # Support both ``scripts.skill_context`` and direct script-path imports.
    from .skill_spec_v2 import MODE_IDS
except ImportError:  # pragma: no cover - exercised by the repository test layout.
    from skill_spec_v2 import MODE_IDS


class SkillContextError(ValueError):
    """Raised when a requested context bundle cannot be built safely."""


def estimate_tokens(text: str) -> int:
    """Return the repository's deterministic four-characters-per-token estimate."""
    return (len(text) + 3) // 4


def _is_missing(value: Any) -> bool:
    return value is None or value == "" or value == [] or value == {}


def _canonical_controlled_value(
    field_id: str, value: Any, allowed: list[str]
) -> str:
    if not isinstance(value, str):
        raise SkillContextError(f"input {field_id} values must be strings")
    stripped = value.strip()
    if not stripped:
        raise SkillContextError(f"input {field_id} values may not be empty")
    canonical = {item.casefold(): item for item in allowed}
    match = canonical.get(stripped.casefold())
    if match is None:
        raise SkillContextError(
            f"invalid value for input {field_id}: {value!r}; allowed values: "
            + ", ".join(allowed)
        )
    return match


def _normalize_json_value(field_id: str, value: Any) -> Any:
    """Normalize one JSON-compatible object input for stable hashing."""
    if value is None or isinstance(value, (str, bool)):
        return value
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        if not math.isfinite(value):
            raise SkillContextError(f"input {field_id} numbers must be finite")
        return value
    if isinstance(value, (list, tuple)):
        return [_normalize_json_value(field_id, item) for item in value]
    if isinstance(value, dict):
        normalized: dict[str, Any] = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise SkillContextError(
                    f"input {field_id} object keys must be strings"
                )
            normalized[key] = _normalize_json_value(field_id, item)
        return normalized
    raise SkillContextError(
        f"input {field_id} values must be JSON-compatible"
    )


def normalize_inputs(
    spec: dict[str, Any], inputs: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Validate and normalize inputs against a compiled skill contract.

    Controlled enum and string-list values are canonicalized case-insensitively.
    Unknown fields fail rather than being silently ignored because input values
    can determine which legal workflow modules enter the context bundle.
    """
    if inputs is None:
        return {}
    if not isinstance(inputs, dict):
        raise SkillContextError("inputs must be an object")

    fields = {
        field["id"]: field
        for field in spec.get("input_schema", [])
        if isinstance(field, dict) and isinstance(field.get("id"), str)
    }
    unknown = sorted(set(inputs) - set(fields))
    if unknown:
        raise SkillContextError("unknown input ID(s): " + ", ".join(unknown))

    normalized: dict[str, Any] = {}
    for field_id, value in inputs.items():
        field = fields[field_id]
        field_type = field.get("type")
        if value is None:
            normalized[field_id] = None
            continue

        if field_type == "string-list":
            if isinstance(value, str):
                raw_values = [value]
            elif isinstance(value, (list, tuple)):
                raw_values = list(value)
            else:
                raise SkillContextError(
                    f"input {field_id} must be a string or list of strings"
                )
            allowed = field.get("items")
            result: list[str] = []
            seen: set[str] = set()
            for raw in raw_values:
                if isinstance(allowed, list):
                    item = _canonical_controlled_value(field_id, raw, allowed)
                else:
                    if not isinstance(raw, str):
                        raise SkillContextError(
                            f"input {field_id} values must be strings"
                        )
                    item = raw.strip()
                    if not item:
                        raise SkillContextError(
                            f"input {field_id} values may not be empty"
                        )
                if item not in seen:
                    seen.add(item)
                    result.append(item)
            normalized[field_id] = result
            continue

        if field_type == "enum":
            allowed = field.get("enum")
            if not isinstance(allowed, list):
                raise SkillContextError(f"input {field_id} has no enum values")
            normalized[field_id] = _canonical_controlled_value(
                field_id, value, allowed
            )
            continue

        if field_type in {
            "text",
            "document",
            "date",
            "datetime",
            "jurisdiction",
        }:
            if not isinstance(value, str):
                raise SkillContextError(f"input {field_id} must be a string")
            normalized[field_id] = value.strip()
            continue

        if field_type == "document-set":
            if isinstance(value, str):
                normalized[field_id] = value.strip()
                continue
            if not isinstance(value, (list, tuple)):
                raise SkillContextError(
                    f"input {field_id} must be a string or list of strings"
                )
            documents: list[str] = []
            seen_documents: set[str] = set()
            for document in value:
                if not isinstance(document, str):
                    raise SkillContextError(
                        f"input {field_id} values must be strings"
                    )
                normalized_document = document.strip()
                if not normalized_document:
                    raise SkillContextError(
                        f"input {field_id} values may not be empty"
                    )
                if normalized_document not in seen_documents:
                    seen_documents.add(normalized_document)
                    documents.append(normalized_document)
            normalized[field_id] = documents
            continue

        if field_type == "object":
            if not isinstance(value, dict):
                raise SkillContextError(f"input {field_id} must be an object")
            normalized[field_id] = _normalize_json_value(field_id, value)
            continue

        if field_type == "boolean" and not isinstance(value, bool):
            raise SkillContextError(f"input {field_id} must be boolean")
        if field_type == "integer" and (
            isinstance(value, bool) or not isinstance(value, int)
        ):
            raise SkillContextError(f"input {field_id} must be an integer")
        if field_type == "number":
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                raise SkillContextError(f"input {field_id} must be a number")
            if not math.isfinite(value):
                raise SkillContextError(f"input {field_id} must be finite")

        normalized[field_id] = value
    return normalized


def _mode_record(spec: dict[str, Any], mode: str) -> dict[str, Any]:
    if mode not in MODE_IDS:
        raise SkillContextError(f"unknown execution mode: {mode}")
    for record in spec.get("execution_modes", []):
        if isinstance(record, dict) and record.get("id") == mode:
            if record.get("enabled") is not True:
                raise SkillContextError(f"execution mode is disabled: {mode}")
            return record
    raise SkillContextError(f"unknown execution mode: {mode}")


def _normalized_comparison_values(value: Any) -> list[str]:
    values = value if isinstance(value, (list, tuple, set)) else [value]
    result: list[str] = []
    for item in values:
        if isinstance(item, str):
            result.append(item.strip().casefold())
        else:
            result.append(str(item).casefold())
    return result


def _trace_record(
    module: dict[str, Any], status: str, reason: str
) -> dict[str, Any]:
    """Return a compact, serializable decision record for one module."""
    return {
        "id": module.get("id"),
        "kind": module.get("kind"),
        "path": module.get("path"),
        "required": module.get("required") is True,
        "status": status,
        "reason": reason,
    }


def _mode_reason(allowed_modes: list[Any], requested_mode: str) -> str:
    modes = [str(item) for item in allowed_modes]
    if len(modes) == 1:
        return (
            f"activation applies to mode {modes[0]} only; "
            f"requested mode was {requested_mode}"
        )
    return (
        "activation applies to modes " + ", ".join(modes)
        + f"; requested mode was {requested_mode}"
    )


def select_modules(
    spec: dict[str, Any],
    mode: str,
    inputs: dict[str, Any] | None = None,
    explicit_module_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Select modules and explain every module decision deterministically.

    Selection follows the order of ``spec["modules"]``. Modules with only
    human-readable ``load_when`` prose are not auto-selected unless required.
    Missing activation inputs fail closed and are returned as unresolved rather
    than causing all conditional modules to load.
    """
    _mode_record(spec, mode)
    normalized_inputs = normalize_inputs(spec, inputs)

    modules = [
        module for module in spec.get("modules", []) if isinstance(module, dict)
    ]
    modules_by_id = {
        module.get("id"): module
        for module in modules
        if isinstance(module.get("id"), str)
    }

    explicit_ids: list[str] = []
    for module_id in explicit_module_ids or []:
        if not isinstance(module_id, str) or not module_id:
            raise SkillContextError("explicit module IDs must be non-empty strings")
        if module_id not in modules_by_id:
            raise SkillContextError(f"unknown module ID: {module_id}")
        if module_id not in explicit_ids:
            explicit_ids.append(module_id)
    explicit = set(explicit_ids)

    selected: list[dict[str, Any]] = []
    unresolved: list[dict[str, Any]] = []
    selection_trace: list[dict[str, Any]] = []

    for module in modules:
        module_id = module.get("id")
        if module_id in explicit:
            reason = "explicitly requested by module ID"
            selected.append({"module": deepcopy(module), "reason": reason})
            selection_trace.append(_trace_record(module, "selected", reason))
            continue

        activation = module.get("activation")
        if not isinstance(activation, dict):
            if module.get("required") is True:
                reason = "required module without conditional activation"
                selected.append({"module": deepcopy(module), "reason": reason})
                selection_trace.append(_trace_record(module, "selected", reason))
            else:
                reason = (
                    "optional module has no machine-readable activation and was "
                    "not explicitly requested"
                )
                selection_trace.append(
                    _trace_record(module, "not-selected", reason)
                )
            continue

        allowed_modes = activation.get("modes", [])
        if mode not in allowed_modes:
            selection_trace.append(
                _trace_record(
                    module,
                    "not-selected",
                    _mode_reason(allowed_modes, mode),
                )
            )
            continue

        operator = activation.get("operator")
        if operator == "always":
            reason = f"activation matched execution mode {mode}"
            selected.append({"module": deepcopy(module), "reason": reason})
            selection_trace.append(_trace_record(module, "selected", reason))
            continue

        input_id = activation.get("input_id")
        input_value = normalized_inputs.get(input_id)
        if input_id not in normalized_inputs or _is_missing(input_value):
            reason = f"activation input {input_id} was not supplied"
            unresolved.append({"module": deepcopy(module), "reason": reason})
            selection_trace.append(_trace_record(module, "unresolved", reason))
            continue

        if operator == "present":
            reason = f"activation input {input_id} is present"
            selected.append({"module": deepcopy(module), "reason": reason})
            selection_trace.append(_trace_record(module, "selected", reason))
            continue

        actual = _normalized_comparison_values(input_value)
        if operator == "equals":
            expected_raw = activation.get("value")
            expected = str(expected_raw or "").strip().casefold()
            matched = len(actual) == 1 and actual[0] == expected
            if matched:
                reason = f"activation input {input_id} equals {expected_raw}"
            else:
                reason = (
                    f"activation input {input_id} did not equal {expected_raw}"
                )
        elif operator == "contains-any":
            configured = activation.get("values", [])
            expected_values = [
                str(value).strip().casefold() for value in configured
            ]
            actual_set = set(actual)
            matches = [
                value
                for value in configured
                if str(value).strip().casefold() in actual_set
            ]
            matched = bool(actual_set.intersection(expected_values))
            if matched:
                reason = (
                    f"activation input {input_id} contains "
                    + ", ".join(str(value) for value in matches)
                )
            else:
                reason = (
                    f"activation input {input_id} matched none of: "
                    + ", ".join(str(value) for value in configured)
                )
        else:
            raise SkillContextError(
                f"module {module_id} has unsupported activation operator: {operator}"
            )

        if matched:
            selected.append({"module": deepcopy(module), "reason": reason})
            selection_trace.append(_trace_record(module, "selected", reason))
        else:
            selection_trace.append(
                _trace_record(module, "not-selected", reason)
            )

    return {
        "mode": mode,
        "normalized_inputs": normalized_inputs,
        "selected": selected,
        "unresolved": unresolved,
        "selection_trace": selection_trace,
    }


def _read_repo_text(root: Path, relative_path: str) -> str:
    if not isinstance(relative_path, str) or not relative_path:
        raise SkillContextError("context path must be a non-empty string")
    root = root.resolve()
    target = (root / relative_path).resolve()
    if not target.is_relative_to(root):
        raise SkillContextError(f"context path is outside repository root: {relative_path}")
    if not target.is_file():
        raise SkillContextError(f"context path does not resolve: {relative_path}")
    try:
        return target.read_text(encoding="utf-8")
    except OSError as exc:
        raise SkillContextError(f"could not read context path {relative_path}: {exc}") from exc


def _content_record(path: str, content: str) -> dict[str, Any]:
    return {
        "path": path,
        "content": content,
        "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
        "estimated_tokens": estimate_tokens(content),
    }


def _canonical_sha256(payload: Any) -> str:
    """Hash a JSON-compatible value using one canonical serialization."""
    return hashlib.sha256(
        json.dumps(
            payload,
            sort_keys=True,
            separators=(",", ":"),
            ensure_ascii=False,
        ).encode("utf-8")
    ).hexdigest()


def build_skill_context(
    root: Path,
    spec: dict[str, Any],
    mode: str,
    inputs: dict[str, Any] | None = None,
    explicit_module_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Build a complete, inspectable context bundle for one compiled skill."""
    root = Path(root)
    normalized_inputs = normalize_inputs(spec, inputs)
    selection = select_modules(
        spec,
        mode,
        normalized_inputs,
        explicit_module_ids,
    )

    missing_required_inputs = [
        field["id"]
        for field in spec.get("input_schema", [])
        if isinstance(field, dict)
        and field.get("required") is True
        and isinstance(field.get("id"), str)
        and (
            field["id"] not in normalized_inputs
            or _is_missing(normalized_inputs.get(field["id"]))
        )
    ]

    core_path = spec.get("skill_path")
    core_content = _read_repo_text(root, core_path)
    core = _content_record(core_path, core_content)

    inherited_rules: list[dict[str, str]] = []
    inherits = spec.get("inherits", [])
    if not isinstance(inherits, list):
        raise SkillContextError("inherits must be a list")
    for inherited_path in inherits:
        content = _read_repo_text(root, inherited_path)
        inherited_rules.append(
            {
                "path": inherited_path,
                "sha256": hashlib.sha256(content.encode("utf-8")).hexdigest(),
            }
        )

    module_records: list[dict[str, Any]] = []
    for item in selection["selected"]:
        module = item["module"]
        path = module.get("path")
        content = _read_repo_text(root, path)
        record = {
            "id": module.get("id"),
            "kind": module.get("kind"),
            "required": module.get("required") is True,
            "reason": item["reason"],
            **_content_record(path, content),
        }
        module_records.append(record)

    unresolved_modules = [
        {
            "id": item["module"].get("id"),
            "kind": item["module"].get("kind"),
            "path": item["module"].get("path"),
            "required": item["module"].get("required") is True,
            "reason": item["reason"],
        }
        for item in selection["unresolved"]
    ]

    module_tokens = sum(record["estimated_tokens"] for record in module_records)
    complete = not missing_required_inputs and not any(
        record["required"] for record in unresolved_modules
    )
    contract_sha256 = _canonical_sha256(spec)

    fingerprint_payload = {
        "skill_id": spec.get("skill_id"),
        "schema_version": spec.get("schema_version"),
        "contract_sha256": contract_sha256,
        "mode": mode,
        "normalized_inputs": normalized_inputs,
        "core": {"path": core["path"], "sha256": core["sha256"]},
        "inherited_rules": inherited_rules,
        "modules": [
            {
                "id": record["id"],
                "path": record["path"],
                "sha256": record["sha256"],
                "reason": record["reason"],
            }
            for record in module_records
        ],
        "unresolved_modules": unresolved_modules,
        "selection_trace": selection["selection_trace"],
    }
    fingerprint = _canonical_sha256(fingerprint_payload)

    return {
        "skill_id": spec.get("skill_id"),
        "schema_version": spec.get("schema_version"),
        "mode": mode,
        "normalized_inputs": normalized_inputs,
        "missing_required_inputs": missing_required_inputs,
        "core": core,
        "inherited_rules": inherited_rules,
        "modules": module_records,
        "unresolved_modules": unresolved_modules,
        "selection_trace": selection["selection_trace"],
        "estimated_tokens": {
            "core": core["estimated_tokens"],
            "modules": module_tokens,
            "total": core["estimated_tokens"] + module_tokens,
        },
        "complete": complete,
        "contract_sha256": contract_sha256,
        "bundle_sha256": fingerprint,
    }
