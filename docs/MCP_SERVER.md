# AgentCounsel MCP Server

AgentCounsel can be exposed to MCP-compatible AI clients through the lightweight server in [`mcp_server.py`](../mcp_server.py).

The server keeps the Markdown skill library as the source of human-readable workflow guidance. It uses:

- `metadata/index.json` and `metadata/router.json` for discovery and task routing;
- `metadata/skill_specs.json` for typed inputs, outputs, execution modes, evidence contracts, safety gates, modules, and quality checks.

It does not duplicate each skill as an individual MCP tool. Clients can identify the narrowest relevant workflow, gather typed missing inputs, apply the compiled gates, and load only the contract or Markdown content they actually need.

The standard-library service in [`agentcounsel_mcp.py`](../agentcounsel_mcp.py) contains all catalog, contract, and routing logic. `mcp_server.py` is only the FastMCP transport adapter.

## Available tools

| Tool | Purpose |
|---|---|
| `list_practice_areas` | List practice areas and generated skill counts. |
| `search_skills` | Search compact skill cards using stable IDs, titles, descriptions, use-when triggers, tags, inputs, and outputs. |
| `route_legal_task` | Return a structured route with typed missing inputs, execution modes, gates, quality checks, and escalation behavior. |
| `get_skill_card` | Retrieve compact discovery metadata, spec version, custom-spec status, and available modes without loading the full workflow. |
| `get_skill_spec` | Retrieve the complete typed Skill Specification v2 execution contract. |
| `get_skill_context` | Build the deterministic core-plus-modules bundle for a mode and typed input set, with selection reasons, unresolved conditions, token estimates, a compiled-contract fingerprint, and a reproducibility fingerprint. |
| `get_skill` | Retrieve the canonical core Markdown workflow for one skill. For a modularized skill, use `get_skill_context` for execution. |
| `get_core_rules` | Retrieve AgentCounsel's global operating and legal-safety rules. |

The server also exposes the read-only resource `agentcounsel://catalog`, which contains a compact catalog of all available skills.

## Stable identifiers and compatibility

Canonical skill IDs use the generated `<practice-area>/<skill-slug>` format, such as `contracts/nda-review`. `get_skill`, `get_skill_card`, `get_skill_spec`, and `get_skill_context` also accept a unique folder slug, title, or canonical repository path for backward compatibility. Returned records always use the stable generated ID.

## Typed contracts

Every canonical skill has a compiled v2 contract, even when it does not have a hand-authored `SPEC.json` sidecar. The contract includes:

- baseline inherited safety rules;
- normalized missing-input, jurisdiction, deadline, attorney-review, and escalation gates;
- `quick-triage`, `standard`, and `deep-review` modes;
- typed and non-inferable required inputs;
- typed output artifacts that require attorney review;
- a claim-support evidence record;
- selectively loadable reference, template, profile, connector, quality-check, and workflow modules;
- generated and sidecar-supplied quality checks.

The compiler rejects contracts that weaken attorney review, permit deadline calculation, continue through missing required inputs, infer required legal inputs, remove baseline evidence fields, or remove baseline inherited safety rules. See [`SKILL_SPEC_V2.md`](SKILL_SPEC_V2.md).

## Structured routing response

`route_legal_task` returns:

- `status`: `matched` or `no_match`;
- `route_type`: normally `one-off skill`, or `matter workspace` when canonical workspace triggers are present;
- `confidence`: `high`, `medium`, `low`, or `none`;
- `primary_route` and `alternative_routes` as compact skill cards;
- `why_selected` with the matched metadata fields and deterministic score;
- `spec_version` for the compiled contract;
- `missing_required_inputs` as typed input records;
- `missing_input_labels` as a compact compatibility list;
- `execution_modes` with enabled status, purpose, output detail, and mode-specific checks;
- `custom_gates` from the selected skill contract;
- `mandatory_quality_checks` from the compiled contract;
- `gates` for jurisdiction, deadlines, and attorney review;
- `deadline_calculation_allowed`, which remains false for current legal workflows;
- `escalation_minimum` and `escalation_required` from the compiled contract.

The router uses metadata fields designed for discovery. It does not rank skills by counting repeated words in complete skill bodies, so common safety boilerplate cannot dominate task-specific routing signals. Once a route is selected, its gates and inputs come from the validated typed contract rather than being reconstructed from routing metadata.

## Selective context bundles

`get_skill_context` is the recommended execution surface for modularized
skills. It accepts:

- `skill_id`: any stable or unique compatible identifier;
- `mode`: `quick-triage`, `standard`, or `deep-review`;
- `inputs`: values keyed by the compiled input IDs;
- optional `module_ids`: explicit module IDs when a client intentionally needs
  a module that is not auto-activated.

The response contains:

- normalized typed inputs and missing required input IDs;
- the canonical core `SKILL.md` content;
- selected module contents in deterministic specification order;
- a human-readable reason for every selected module;
- `selection_trace`, with a selected, not-selected, or unresolved decision and reason for every declared module;
- unresolved conditional modules when an activation input is absent;
- estimated core, module, and total tokens;
- SHA-256 hashes for each content file, dependency hashes for every inherited
  rule, `contract_sha256` for the complete compiled contract, and `bundle_sha256`
  for the complete selection decision;
- `complete`, which is false when a required input is missing or a required
  conditional module cannot be resolved.

Selection fails closed. The service never interprets `load_when` prose and
never loads all right-, posture-, or mode-specific modules merely because an
activation input is absent. Unknown input IDs, invalid controlled values,
unknown modes, disabled modes, and unknown explicit module IDs are rejected.
The ordered selection trace makes skipped modules inspectable rather than silently absent. `contract_sha256` fingerprints the complete compiled contract, including gates, types, modes, quality checks, and module declarations. The bundle fingerprint covers that contract hash, inherited-rule hashes, the trace, normalized inputs, and selected content, so contract, global-rule, or routing changes remain distinguishable even when selected Markdown does not change. These hashes support deterministic replay and audit comparison; they are not legal-validity or approval signals.

### Retrieval choices

| Need | Tool |
|---|---|
| Discover a likely workflow without loading instructions | `get_skill_card` or `search_skills` |
| Inspect types, gates, modes, and module declarations | `get_skill_spec` |
| Execute a modularized workflow with the narrowest applicable context | `get_skill_context` |
| Read the canonical core workflow directly | `get_skill` |

## Legal-safety model

AgentCounsel supplies structured workflows for draft legal work product. It does not provide legal advice or create an attorney-client relationship. Outputs must be reviewed and adopted by a qualified licensed attorney before reliance. A routing confidence score measures metadata fit only; it does not measure legal correctness. A valid typed contract measures structural and repository-policy compliance, not the substantive correctness of work produced from it.

## Run locally

Requires Python 3.10 or newer.

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python mcp_server.py
```

The remote Streamable HTTP MCP endpoint is served at:

```text
http://localhost:8000/mcp
```

Set `PORT` to use a different port.

## Manufact deployment settings

Use these settings when deploying the repository to Manufact Cloud:

```text
Repository: zgbrenner/agentcounsel
Branch: main
Build command: pip install -r requirements.txt
Start command: python mcp_server.py
Port: 8000
Region: US
```

The Manufact GitHub App must have access to the repository before the initial deployment can be created.

## Example client flow

1. Call `route_legal_task` with a task such as `Review a mutual NDA for a software vendor relationship`.
2. Inspect the primary route, typed missing inputs, modes, custom gates, quality checks, and escalation requirements.
3. Gather every required input; never silently infer a required legal field.
4. Call `get_skill_spec` when the client needs to inspect the complete typed execution contract or present mode/module choices to a user.
5. Call `get_skill_context` with the selected mode and gathered typed inputs. Stop if the bundle is incomplete; resolve missing inputs and required unresolved modules rather than guessing.
6. Use the selected core and module content, preserving every returned gate and quality check. Store both `contract_sha256` and `bundle_sha256` with any audit or replay record.
7. Call `get_skill` only when the canonical core workflow itself is needed outside the selective execution flow.
8. Use `get_core_rules` when the client has not already loaded AgentCounsel's global safety rules.
9. Require qualified attorney review and adoption before reliance.
