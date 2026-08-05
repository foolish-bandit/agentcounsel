"""AgentCounsel MCP server.

Exposes the repository's Markdown-native legal workflow library over MCP.
All returned material is draft workflow guidance for licensed-attorney review,
not legal advice.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from agentcounsel_mcp import CatalogService

ROOT = Path(__file__).resolve().parent
CATALOG = CatalogService.from_root(ROOT)

mcp = FastMCP(
    "AgentCounsel",
    instructions=(
        "AgentCounsel provides structured legal workflows for draft work product. "
        "Use the narrowest relevant skill, preserve uncertainty, gather required "
        "inputs, apply the returned typed gates, execution modes, and quality checks, "
        "and require review and adoption by a qualified licensed attorney before "
        "reliance. It does not provide legal advice or create an attorney-client "
        "relationship."
    ),
    host="0.0.0.0",
    port=int(os.getenv("PORT", "8000")),
)


@mcp.tool()
def list_practice_areas() -> list[dict[str, Any]]:
    """List available AgentCounsel practice areas and generated skill counts."""
    return CATALOG.list_practice_areas()


@mcp.tool()
def search_skills(
    query: str,
    practice_area: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    """Search compact skill cards using canonical routing metadata."""
    return CATALOG.search_skills(query, practice_area=practice_area, limit=limit)


@mcp.tool()
def route_legal_task(task: str, limit: int = 5) -> dict[str, Any]:
    """Return a structured route, typed inputs, modes, gates, and checks."""
    return CATALOG.route_task(task, limit=limit)


@mcp.tool()
def get_skill_card(skill_id: str) -> dict[str, Any]:
    """Return compact metadata for one skill without loading its Markdown body."""
    return CATALOG.get_skill_card(skill_id)


@mcp.tool()
def get_skill_spec(skill_id: str) -> dict[str, Any]:
    """Return the complete typed Skill Specification v2 execution contract."""
    return CATALOG.get_skill_spec(skill_id)


@mcp.tool()
def get_skill_context(
    skill_id: str,
    mode: str = "standard",
    inputs: dict[str, Any] | None = None,
    module_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Return a deterministic selective context bundle with selection reasons."""
    return CATALOG.get_skill_context(
        skill_id,
        mode=mode,
        inputs=inputs,
        module_ids=module_ids,
    )


@mcp.tool()
def list_matter_plans() -> list[dict[str, Any]]:
    """List validated typed matter plans without executing legal work."""
    return CATALOG.list_matter_plans()


@mcp.tool()
def search_matter_plans(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """Search recurring multi-skill legal matter plans."""
    return CATALOG.search_matter_plans(query, limit=limit)


@mcp.tool()
def get_matter_plan(plan_id: str) -> dict[str, Any]:
    """Return one complete typed matter graph and its attorney gates."""
    return CATALOG.get_matter_plan(plan_id)


@mcp.tool()
def build_matter_plan(
    plan_id: str,
    matter_inputs: dict[str, Any] | None = None,
    available_artifacts: dict[str, dict[str, Any]] | None = None,
    gate_decisions: dict[str, str] | None = None,
    node_ids: list[str] | None = None,
) -> dict[str, Any]:
    """Plan the next legal-work waves; this does not execute any legal analysis."""
    return CATALOG.build_matter_plan(
        plan_id,
        matter_inputs=matter_inputs,
        available_artifacts=available_artifacts,
        gate_decisions=gate_decisions,
        node_ids=node_ids,
    )


@mcp.tool()
def verify_matter_plan_receipt(receipt: dict[str, Any]) -> dict[str, Any]:
    """Verify graph, lineage, gate, contract, context, and budget integrity."""
    return CATALOG.verify_matter_plan_receipt(receipt)


@mcp.tool()
def get_skill(skill_id: str) -> dict[str, Any]:
    """Return the complete Markdown workflow for one AgentCounsel skill."""
    return CATALOG.get_skill(skill_id)


@mcp.tool()
def get_core_rules() -> dict[str, str]:
    """Return AgentCounsel's global operating and legal-safety rules."""
    return CATALOG.get_core_rules()


@mcp.resource("agentcounsel://catalog")
def catalog_resource() -> str:
    """A compact Markdown catalog of every available AgentCounsel skill."""
    return CATALOG.catalog_markdown()


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
