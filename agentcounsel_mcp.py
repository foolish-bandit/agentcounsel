"""Canonical metadata-backed service for AgentCounsel MCP adapters.

This module is standard-library only so routing and retrieval can be tested
without installing the MCP transport package. Markdown remains the canonical
source of workflow content; generated metadata is the canonical discovery,
routing, and typed execution-contract surface.
"""

from __future__ import annotations

import json
import re
from copy import deepcopy
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.skill_context import build_skill_context


class CatalogLoadError(RuntimeError):
    """Raised when generated AgentCounsel catalog metadata cannot be loaded."""


_WORD_RE = re.compile(r"[a-z0-9]+")
_STOP_WORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "before",
    "by",
    "for",
    "from",
    "help",
    "i",
    "in",
    "is",
    "it",
    "me",
    "my",
    "of",
    "on",
    "or",
    "please",
    "that",
    "the",
    "this",
    "to",
    "we",
    "with",
}


def _normalize(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple, set)):
        return " ".join(_normalize(item) for item in value)
    return " ".join(_WORD_RE.findall(str(value).lower()))


def _tokens(value: Any) -> set[str]:
    return {
        token
        for token in _WORD_RE.findall(_normalize(value))
        if len(token) > 1 and token not in _STOP_WORDS
    }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise CatalogLoadError(f"Required generated metadata file not found: {path}")
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise CatalogLoadError(f"Could not load generated metadata file {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise CatalogLoadError(f"Generated metadata must be a JSON object: {path}")
    return data


def _as_list(value: Any) -> list[Any]:
    return list(value) if isinstance(value, list) else []


def _compact_skill(skill: dict[str, Any]) -> dict[str, Any]:
    """Return a stable, transport-friendly skill card without Markdown content."""
    fields = (
        "id",
        "title",
        "name",
        "path",
        "summary",
        "description",
        "use_when",
        "required_inputs",
        "expected_outputs",
        "practice_area",
        "task_type",
        "risk_level",
        "requires_jurisdiction",
        "requires_deadline_check",
        "requires_attorney_review",
        "recommended_quality_checks",
        "tags",
        "related_skills",
        "eval_status",
    )
    card = {field: skill.get(field) for field in fields if field in skill}
    card.setdefault("title", skill.get("name", skill.get("id", "")))
    card.setdefault("name", card["title"])
    card.setdefault("summary", skill.get("description", ""))
    card.setdefault("description", card["summary"])
    for field in (
        "use_when",
        "required_inputs",
        "expected_outputs",
        "recommended_quality_checks",
        "tags",
        "related_skills",
    ):
        card[field] = _as_list(card.get(field))
    return card


@dataclass(frozen=True)
class _RankedSkill:
    score: int
    card: dict[str, Any]
    matched_fields: tuple[str, ...]


class CatalogService:
    """Read-only discovery, retrieval, and routing over generated metadata."""

    def __init__(
        self,
        root: Path,
        index: dict[str, Any],
        router: dict[str, Any],
        skill_specs: dict[str, Any],
    ) -> None:
        self.root = root
        self.index = index
        self.router = router
        self.skill_specs = skill_specs

        raw_skills = index.get("skills")
        if not isinstance(raw_skills, list) or not raw_skills:
            raise CatalogLoadError("metadata/index.json must contain a non-empty 'skills' list")

        self._skills: dict[str, dict[str, Any]] = {}
        alias_candidates: dict[str, set[str]] = {}
        for raw in raw_skills:
            if not isinstance(raw, dict):
                raise CatalogLoadError("metadata/index.json contains a non-object skill record")
            skill_id = raw.get("id")
            path = raw.get("path")
            if not isinstance(skill_id, str) or not skill_id.strip():
                raise CatalogLoadError("Every generated skill record must have a stable string 'id'")
            if not isinstance(path, str) or not path.strip():
                raise CatalogLoadError(f"Skill '{skill_id}' is missing a canonical 'path'")
            if skill_id in self._skills:
                raise CatalogLoadError(f"Duplicate generated skill id: {skill_id}")
            skill = dict(raw)
            self._skills[skill_id] = skill

            title = str(skill.get("title") or skill.get("name") or "")
            slug = skill_id.rsplit("/", 1)[-1]
            aliases = {skill_id, slug, path, title}
            for alias in aliases:
                normalized = alias.strip().lower()
                if normalized:
                    alias_candidates.setdefault(normalized, set()).add(skill_id)

        self._aliases = {
            alias: next(iter(ids))
            for alias, ids in alias_candidates.items()
            if len(ids) == 1
        }

        raw_specs = skill_specs.get("skills")
        if not isinstance(raw_specs, list) or not raw_specs:
            raise CatalogLoadError(
                "metadata/skill_specs.json must contain a non-empty 'skills' list"
            )
        self._specs: dict[str, dict[str, Any]] = {}
        for raw in raw_specs:
            if not isinstance(raw, dict):
                raise CatalogLoadError(
                    "metadata/skill_specs.json contains a non-object contract record"
                )
            skill_id = raw.get("skill_id")
            if not isinstance(skill_id, str) or not skill_id:
                raise CatalogLoadError("Every typed skill contract must have a skill_id")
            if skill_id in self._specs:
                raise CatalogLoadError(f"Duplicate typed skill contract id: {skill_id}")
            if skill_id not in self._skills:
                raise CatalogLoadError(
                    f"Typed skill contract has no matching catalog skill: {skill_id}"
                )
            self._specs[skill_id] = dict(raw)

        missing_specs = sorted(set(self._skills) - set(self._specs))
        if missing_specs:
            raise CatalogLoadError(
                "metadata/skill_specs.json is missing contracts for: "
                + ", ".join(missing_specs[:10])
            )

    @classmethod
    def from_root(cls, root: Path | str) -> "CatalogService":
        root_path = Path(root).resolve()
        index = _read_json(root_path / "metadata" / "index.json")
        router = _read_json(root_path / "metadata" / "router.json")
        skill_specs = _read_json(root_path / "metadata" / "skill_specs.json")
        return cls(root_path, index, router, skill_specs)

    def list_practice_areas(self) -> list[dict[str, Any]]:
        counts = self.index.get("practice_areas")
        if not isinstance(counts, dict):
            calculated: dict[str, int] = {}
            for skill in self._skills.values():
                area = str(skill.get("practice_area", "unknown"))
                calculated[area] = calculated.get(area, 0) + 1
            counts = calculated
        return [
            {"practice_area": str(area), "skill_count": int(count)}
            for area, count in sorted(counts.items())
        ]

    def _resolve_id(self, identifier: str) -> str:
        normalized = identifier.strip().lower()
        if not normalized:
            raise KeyError("Skill identifier must not be empty")
        if normalized in self._aliases:
            return self._aliases[normalized]
        raise KeyError(f"Unknown or ambiguous skill identifier: {identifier}")

    def get_skill_card(self, skill_id: str) -> dict[str, Any]:
        stable_id = self._resolve_id(skill_id)
        card = _compact_skill(self._skills[stable_id])
        spec = self._specs[stable_id]
        card["spec_version"] = spec.get("schema_version")
        card["has_custom_spec"] = bool(spec.get("has_custom_spec"))
        card["available_modes"] = [
            mode.get("id")
            for mode in _as_list(spec.get("execution_modes"))
            if isinstance(mode, dict) and mode.get("enabled") is True
        ]
        return card

    def get_skill_spec(self, skill_id: str) -> dict[str, Any]:
        """Return the complete typed execution contract for one skill."""
        stable_id = self._resolve_id(skill_id)
        return deepcopy(self._specs[stable_id])

    def get_skill_context(
        self,
        skill_id: str,
        mode: str = "standard",
        inputs: dict[str, Any] | None = None,
        module_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """Return the deterministic core-plus-modules context for one skill."""
        stable_id = self._resolve_id(skill_id)
        return build_skill_context(
            self.root,
            self._specs[stable_id],
            mode,
            inputs,
            module_ids,
        )

    def get_skill(self, skill_id: str) -> dict[str, Any]:
        card = self.get_skill_card(skill_id)
        path = self.root / str(card["path"])
        if not path.is_file():
            raise CatalogLoadError(f"Canonical skill file not found for {card['id']}: {path}")
        record = dict(card)
        record["content"] = path.read_text(encoding="utf-8")
        return record

    @staticmethod
    def _field_score(
        query_normalized: str,
        query_tokens: set[str],
        value: Any,
        token_weight: int,
        phrase_weight: int,
    ) -> tuple[int, bool]:
        normalized = _normalize(value)
        if not normalized:
            return 0, False
        overlap = query_tokens & _tokens(normalized)
        score = len(overlap) * token_weight
        phrase_match = bool(query_normalized and query_normalized in normalized)
        if phrase_match:
            score += phrase_weight
        return score, bool(overlap or phrase_match)

    def _rank_skill(
        self,
        skill: dict[str, Any],
        query: str,
        query_normalized: str,
        query_tokens: set[str],
    ) -> _RankedSkill:
        skill_id = str(skill.get("id", ""))
        title = str(skill.get("title") or skill.get("name") or "")
        slug = skill_id.rsplit("/", 1)[-1]
        path = str(skill.get("path", ""))

        score = 0
        matched_fields: list[str] = []
        exact_candidates = {skill_id.lower(), title.lower(), slug.lower(), path.lower()}
        if query.strip().lower() in exact_candidates:
            score += 250
            matched_fields.append("exact_identifier")

        weighted_fields: tuple[tuple[str, Any, int, int], ...] = (
            ("id", skill_id, 18, 80),
            ("title", title, 16, 70),
            ("description", skill.get("description") or skill.get("summary"), 10, 45),
            ("use_when", skill.get("use_when"), 9, 40),
            ("tags", skill.get("tags"), 10, 35),
            ("task_type", skill.get("task_type") or skill.get("category"), 6, 24),
            ("practice_area", skill.get("practice_area"), 5, 20),
            ("required_inputs", skill.get("required_inputs") or skill.get("inputs"), 3, 12),
            ("expected_outputs", skill.get("expected_outputs") or skill.get("outputs"), 3, 12),
        )
        for field, value, token_weight, phrase_weight in weighted_fields:
            field_score, matched = self._field_score(
                query_normalized, query_tokens, value, token_weight, phrase_weight
            )
            score += field_score
            if matched:
                matched_fields.append(field)

        card = _compact_skill(skill)
        return _RankedSkill(score, card, tuple(dict.fromkeys(matched_fields)))

    def search_skills(
        self,
        query: str,
        practice_area: str | None = None,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        query = query.strip()
        if not query:
            raise ValueError("query must not be empty")
        if not isinstance(limit, int) or limit < 1 or limit > 50:
            raise ValueError("limit must be an integer between 1 and 50")

        query_normalized = _normalize(query)
        query_tokens = _tokens(query)
        ranked: list[_RankedSkill] = []
        for skill in self._skills.values():
            if practice_area and str(skill.get("practice_area", "")).lower() != practice_area.lower():
                continue
            candidate = self._rank_skill(skill, query, query_normalized, query_tokens)
            if candidate.score > 0:
                ranked.append(candidate)

        ranked.sort(key=lambda item: (-item.score, str(item.card.get("id", ""))))
        results: list[dict[str, Any]] = []
        for item in ranked[:limit]:
            result = dict(item.card)
            spec = self._specs[str(result["id"])]
            result["spec_version"] = spec.get("schema_version")
            result["has_custom_spec"] = bool(spec.get("has_custom_spec"))
            result["relevance_score"] = item.score
            result["matched_fields"] = list(item.matched_fields)
            results.append(result)
        return results

    @staticmethod
    def _confidence(primary_score: int, alternative_score: int | None) -> str:
        if primary_score >= 100:
            return "high"
        if alternative_score is None:
            return "high" if primary_score >= 35 else "medium"
        if primary_score >= 45 and primary_score >= alternative_score * 2:
            return "high"
        if primary_score >= 20:
            return "medium"
        return "low"

    def _workspace_triggered(self, task: str) -> bool:
        normalized_task = _normalize(task)
        for trigger in _as_list(self.router.get("workspace_triggers")):
            normalized_trigger = _normalize(trigger)
            if normalized_trigger and normalized_trigger in normalized_task:
                return True
        return False

    def route_task(self, task: str, limit: int = 5) -> dict[str, Any]:
        results = self.search_skills(task, limit=limit)
        if not results:
            return {
                "status": "no_match",
                "task": task,
                "route_type": None,
                "confidence": "none",
                "primary_route": None,
                "alternative_routes": [],
                "why_selected": "No generated skill metadata matched the task terms.",
                "spec_version": None,
                "missing_required_inputs": [],
                "missing_input_labels": [],
                "execution_modes": [],
                "custom_gates": [],
                "mandatory_quality_checks": [],
                "gates": {
                    "jurisdiction": False,
                    "deadline": False,
                    "attorney_review": True,
                },
                "deadline_calculation_allowed": False,
                "escalation_minimum": "immediate-attorney-attention",
                "escalation_required": True,
            }

        primary = results[0]
        alternatives = results[1:]
        alternative_score = alternatives[0]["relevance_score"] if alternatives else None
        confidence = self._confidence(primary["relevance_score"], alternative_score)
        matched_fields = primary.get("matched_fields", [])
        reason_fields = ", ".join(matched_fields) if matched_fields else "generated metadata"
        spec = self._specs[str(primary["id"])]
        gates = spec.get("gates") if isinstance(spec.get("gates"), dict) else {}
        deadline_gate = gates.get("deadline") if isinstance(gates.get("deadline"), dict) else {}
        jurisdiction_gate = gates.get("jurisdiction") if isinstance(gates.get("jurisdiction"), dict) else {}
        attorney_gate = gates.get("attorney_review") if isinstance(gates.get("attorney_review"), dict) else {}
        escalation_gate = gates.get("escalation") if isinstance(gates.get("escalation"), dict) else {}
        escalation_minimum = str(escalation_gate.get("minimum", "attorney-review"))
        required_inputs = [
            deepcopy(field)
            for field in _as_list(spec.get("input_schema"))
            if isinstance(field, dict) and field.get("required") is True
        ]

        return {
            "status": "matched",
            "task": task,
            "route_type": "matter workspace" if self._workspace_triggered(task) else "one-off skill",
            "confidence": confidence,
            "primary_route": primary,
            "alternative_routes": alternatives,
            "why_selected": (
                f"Selected {primary['id']} from matches in {reason_fields}; "
                f"metadata relevance score {primary['relevance_score']}."
            ),
            "spec_version": spec.get("schema_version"),
            "missing_required_inputs": required_inputs,
            "missing_input_labels": [str(field.get("label", field.get("id", ""))) for field in required_inputs],
            "execution_modes": deepcopy(_as_list(spec.get("execution_modes"))),
            "custom_gates": deepcopy(_as_list(gates.get("custom"))),
            "mandatory_quality_checks": deepcopy(_as_list(spec.get("quality_checks"))),
            "gates": {
                "jurisdiction": bool(jurisdiction_gate.get("required")),
                "deadline": bool(deadline_gate.get("required")),
                "attorney_review": bool(attorney_gate.get("required", True)),
            },
            "deadline_calculation_allowed": bool(
                deadline_gate.get("calculation_allowed", False)
            ),
            "escalation_minimum": escalation_minimum,
            "escalation_required": escalation_minimum
            in {"attorney-escalation", "immediate-attorney-attention"},
        }

    def get_core_rules(self) -> dict[str, str]:
        core_root = self.root / "core"
        if not core_root.is_dir():
            return {}
        return {
            path.relative_to(self.root).as_posix(): path.read_text(encoding="utf-8")
            for path in sorted(core_root.glob("*.md"))
        }

    def catalog_markdown(self) -> str:
        lines = ["# AgentCounsel Skill Catalog", ""]
        for skill_id in sorted(self._skills):
            card = self.get_skill_card(skill_id)
            lines.append(
                f"- `{card['id']}` — **{card['title']}** "
                f"({card.get('practice_area', 'unknown')}): {card.get('description', '')}"
            )
        return "\n".join(lines)
