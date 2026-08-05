# Matter Graph v1 Design

## Status

Approved for implementation by the maintainer's instruction to continue improving AgentCounsel autonomously using best judgment after the v0.3.0 selective-context release.

## Problem

AgentCounsel can now route and execute one skill with typed inputs, deterministic selective context, provenance hashes, and CI-enforced context budgets. Whole matters remain less rigorous:

- playbooks and matter packs describe sequences only in prose and Markdown tables;
- handoffs between skills are human-readable but not machine-validated;
- conditional steps, parallel quality checks, and attorney checkpoints are not represented as typed graph structure;
- clients cannot ask for a complete matter plan, identify which steps are ready or blocked, or load only the context for the next executable wave;
- there is no deterministic receipt proving which plan, contracts, gates, and handoffs produced a proposed execution order.

The result is a strong single-skill substrate with a comparatively informal multi-skill layer.

## Goals

1. Compile recurring legal matters into validated directed acyclic graphs whose nodes are canonical AgentCounsel skills or explicit attorney-review gates.
2. Preserve Markdown playbooks and matter packs as the human-readable guidance while adding sidecar plan specifications for machine execution.
3. Make every dependency, input binding, conditional branch, parallel lane, artifact handoff, and review checkpoint inspectable.
4. Build matter plans without model calls, embeddings, a database, or a hosted runtime.
5. Load only the context for nodes that are actually ready to run.
6. Emit privacy-conscious plan receipts that support audit, replay, cache invalidation, and change detection without copying matter facts into the receipt.
7. Prove the architecture with four materially different pilot plans.
8. Keep every legal output a draft requiring attorney review, never calculate deadlines, and never infer missing non-inferable legal inputs.

## Non-goals

- Executing an LLM or connector.
- Automatically parsing arbitrary prose playbooks into graphs.
- Replacing the supervising attorney's sequencing or strategy decisions.
- Persisting confidential matter facts in a server or database.
- Implementing an asynchronous job runner, retries, timers, or background workers.
- Computing legal deadlines or deciding whether an escalation condition is legally satisfied.
- Converting all existing playbooks and matter packs in this release.
- Claiming that graph validation establishes substantive legal correctness.

## Considered approaches

### A. Modularize more large skills

This would continue the v0.3.0 efficiency program and reduce context in more individual workflows. It does not solve whole-matter coordination, typed handoffs, or plan-level auditability.

### B. Add a claim-to-evidence verification layer

This would improve output review and is a high-value future phase. It depends on knowing which artifacts and quality checks a matter plan is supposed to produce. Building the graph substrate first gives the evidence layer explicit attachment points.

### C. Typed matter graphs with lazy context loading — selected

Add declarative plan sidecars, a strict compiler, deterministic graph planning, privacy-conscious receipts, MCP and CLI retrieval, generated registries, graph visualization, and CI gates. This converts existing multi-skill prose into an executable specification without requiring a model runtime.

## Research-informed principles

The design adapts structural ideas rather than dependencies or copied implementations:

- **Typed state and subgraph interfaces:** graph nodes communicate through explicit input/output schemas, and reusable subgraphs remain independently understandable.
- **Typed handoffs:** a destination and its handoff payload are declared separately from model conversation history.
- **Asset lineage:** outputs are first-class artifacts with upstream dependencies rather than incidental text passed between steps.
- **Deterministic replay:** plan identity depends on the plan definition, node contracts, selected contexts, and decision trace.
- **Append-only execution events:** future runtimes can reconstruct state from an event history, but v1 provides validation and receipt formats without a server.
- **Cache safety:** a node cache key is derived from its contract, selected context, binding structure, and upstream artifact identities, not merely its display name.
- **Human interruption points:** attorney checkpoints are graph nodes and cannot be hidden in prose.

## Architecture

### Canonical directories

```text
matter-plans/
  README.md
  legal-research-memo.json
  commercial-contract-review.json
  litigation-motion-opposition.json
  privacy-incident-response.json
specs/
  matter-plan-v1.schema.json
metadata/
  matter_plans.json
reports/
  matter-plans.md
```

Existing playbooks and matter packs remain canonical human guidance. Each plan sidecar links to its source Markdown with `source_path` and does not duplicate substantive legal instructions.

### Matter Plan Specification v1

Each plan is a JSON object:

```json
{
  "schema_version": "1.0",
  "plan_id": "legal-research-memo",
  "title": "Legal Research Memo",
  "source_path": "playbooks/legal-research-memo.md",
  "description": "Compile a scoped, authority-grounded research memo workflow.",
  "tags": ["legal-research", "memo", "citations"],
  "required_inputs": [
    {
      "id": "legal-question",
      "type": "text",
      "required": true,
      "may_infer": false,
      "sensitive": true
    }
  ],
  "nodes": [],
  "artifacts": [],
  "final_outputs": [],
  "budget": {
    "max_ready_nodes": 6,
    "max_total_estimated_tokens": 24000
  }
}
```

Plan IDs, node IDs, artifact IDs, gate IDs, and binding IDs use lowercase slug form. Controlled values are unique after case folding.

### Node types

#### Skill node

```json
{
  "id": "research-plan",
  "type": "skill",
  "skill_id": "legal-research/research-plan",
  "mode": "standard",
  "depends_on": [],
  "condition": {"operator": "always"},
  "input_bindings": [
    {
      "target_input_id": "legal-question",
      "source": {"kind": "matter-input", "id": "legal-question"},
      "required": true
    }
  ],
  "produces": ["research-roadmap"]
}
```

A skill node references a canonical compiled Skill Specification v2 contract. The plan compiler validates its mode, target input IDs, and output declarations.

#### Gate node

```json
{
  "id": "approve-research-scope",
  "type": "attorney-gate",
  "depends_on": ["research-plan"],
  "gate": {
    "severity": "required",
    "instruction": "Attorney confirms the question, jurisdiction, date, and research scope.",
    "required_artifacts": ["research-roadmap"]
  }
}
```

Gate nodes never auto-complete. They are emitted as explicit human interruption points. A downstream node remains blocked until the caller records the gate as approved.

### Conditions

Conditions use a deliberately small declarative language:

- `always`
- `present`
- `equals`
- `contains-any`
- `artifact-present`
- `gate-approved`

Matter-input conditions may inspect only declared controlled fields. Arbitrary expressions and prose interpretation are prohibited. A missing condition input is unresolved and fails closed.

### Artifacts and handoffs

Artifacts are typed plan-level identities:

```json
{
  "id": "research-roadmap",
  "type": "document",
  "produced_by": "research-plan",
  "attorney_review_required": true,
  "sensitive": true
}
```

Bindings may source values from:

- a matter input;
- an upstream artifact reference;
- a controlled constant declared in the plan;
- a gate approval record.

The planner does not copy artifact content. It emits a handoff manifest describing the artifact ID, producer, consumer, target skill input, and review requirement. The actual content stays in the user's matter workspace.

### Deterministic graph compiler

A new standard-library module, `scripts/matter_plan.py`, provides:

```python
load_matter_plan(root: Path, plan_id: str) -> dict[str, Any]
validate_matter_plan(root: Path, plan: dict[str, Any], skill_specs: dict[str, Any]) -> list[str]
build_matter_plan(
    root: Path,
    plan: dict[str, Any],
    matter_inputs: dict[str, Any] | None = None,
    available_artifacts: dict[str, dict[str, Any]] | None = None,
    gate_decisions: dict[str, str] | None = None,
    explicit_node_ids: list[str] | None = None,
) -> dict[str, Any]
verify_matter_plan_receipt(root: Path, receipt: dict[str, Any]) -> dict[str, Any]
```

Validation rejects:

- missing or duplicate stable IDs;
- unknown skill IDs or disabled execution modes;
- cycles and self-dependencies;
- dependencies on conditionally unreachable nodes when no fallback exists;
- artifact producers that do not exist or multiple producers for one artifact;
- bindings to unknown matter inputs, artifacts, nodes, or target skill inputs;
- a required target input with no possible binding;
- paths outside the repository;
- unknown condition operators or invalid controlled values;
- budget values that are non-finite, non-positive, or structurally impossible;
- a final output that cannot be produced on any valid path.

### Plan states

Every node is assigned exactly one state:

- `ready`: dependencies and conditions are satisfied and required bound inputs are available;
- `blocked`: waiting on an upstream node, artifact, or attorney gate;
- `unresolved`: a required matter input or condition value is missing;
- `not-selected`: a condition evaluated false;
- `completed`: caller supplied the node's required artifact identities;
- `approved`: attorney gate explicitly approved;
- `rejected`: attorney gate explicitly rejected.

The builder returns deterministic topological order and execution waves. Nodes in the same wave have no dependency relationship and may be run in parallel by a future runtime. V1 itself does not execute them.

### Lazy node context

For each `ready` skill node, the builder calls the existing `build_skill_context` function using only structurally available bindings. Matter facts are not copied into the plan receipt. The response includes the ready node's exact core-plus-module bundle, contract hash, bundle fingerprint, token estimate, and binding manifest.

Blocked nodes do not load skill context. This prevents the plan from front-loading every skill in a multi-step matter.

### Privacy-conscious receipts

The plan receipt contains:

- plan ID, source path, source SHA-256, and schema version;
- deterministic graph structure and topological order;
- node states and reasons;
- matter-input presence/type metadata, never raw values;
- gate decision states;
- artifact identities, producer/consumer lineage, and optional caller-supplied content digests;
- selected skill contract hashes and ready-node bundle hashes;
- plan budget arithmetic;
- one deterministic receipt SHA-256.

Raw sensitive matter inputs are excluded. The fingerprint is computed from an internal canonical payload that may include normalized controlled routing values but is returned only as a digest. Free-text matter facts are represented by presence metadata unless the caller explicitly supplies an artifact digest.

`verify_matter_plan_receipt` re-reads the plan, skill contracts, core files, and ready-node contexts and fails on drift, unsafe paths, altered lineage, invalid state transitions, or arithmetic tampering.

### Registry and search

`scripts/build_matter_plans.py` validates all plans and generates `metadata/matter_plans.json`. Each registry card includes:

- plan ID, title, description, source path, tags;
- required matter inputs;
- node, skill-node, gate-node, and artifact counts;
- practice areas involved;
- graph depth, maximum parallel width, and estimated ready-context range;
- pilot maturity and validation status.

The MCP service adds:

```text
list_matter_plans()
search_matter_plans(query, limit=10)
get_matter_plan(plan_id)
build_matter_plan(plan_id, matter_inputs={}, available_artifacts={}, gate_decisions={}, node_ids=[])
verify_matter_plan_receipt(receipt)
```

Search is deterministic weighted lexical matching over plan IDs, titles, descriptions, tags, source paths, and included skill metadata.

### CLI

`scripts/matter_plan_cli.py` supports:

```text
list
show <plan-id>
build <plan-id> --inputs inputs.json --artifacts artifacts.json --gates gates.json
verify receipt.json
```

Output is JSON by default, with `--markdown` for a human-readable run sheet. No third-party package is required.

### Pilot plans

#### 1. Legal Research Memo

Graph:

```text
research-plan
  -> approve-research-scope [attorney gate]
  -> authority-synthesis
  -> legal-research-memo
  -> {source-validation, citation-integrity-check, assumption-audit} [parallel]
  -> attorney-review-gate
```

This proves explicit human interruption and parallel quality lanes.

#### 2. Commercial Contract Review

Graph:

```text
contract-risk-review
  -> {sow-review [conditional], redline-summary [conditional], assumption-audit,
      source-validation, privilege-confidentiality-check}
  -> contract-review-panel gate
  -> attorney-review-gate
```

This proves controlled optional nodes and multiple parallel downstream checks.

#### 3. Litigation Motion Opposition

Graph:

```text
research-plan
  -> approve-research-scope [attorney gate]
  -> authority-synthesis
  -> motion-opposition-drafter
  -> {citation-integrity-check, source-validation, assumption-audit}
  -> litigation-risk gate
  -> attorney-review-gate
```

This proves reuse of a selectively modularized deep skill inside a whole-matter graph.

#### 4. Privacy Incident Response

Graph:

```text
breach-response-workflow
  -> immediate-reportability gate
  -> {litigation-chronology, legal-hold, privacy-policy-gap-review}
  -> {regulatory-risk gate, external-communication gate}
  -> attorney-review-gate
```

This proves high-severity gates, parallel preservation/policy work, and no deadline computation.

### Generated report and site

`reports/matter-plans.md` records each plan's nodes, edges, gates, depth, width, practice areas, and validation status. The static site adds:

- a matter-plan index;
- one page per plan;
- an accessible CSS/SVG dependency graph;
- node tables with skill links, conditions, artifacts, gates, and handoffs;
- copyable plan JSON and example CLI commands;
- explicit text alternatives for every graph.

No charting dependency is added.

### Context and complexity budgets

Each plan declares:

- maximum graph depth;
- maximum parallel width;
- maximum ready nodes in one wave;
- maximum total estimated tokens loaded for one ready wave.

CI builds each declared example scenario and fails if a plan exceeds its caps, becomes incomplete unexpectedly, or loads context for blocked nodes.

## Safety and error handling

- Missing non-inferable input: node is unresolved; no guessing.
- Missing condition input: conditional node is unresolved; no eager loading.
- Attorney gate without explicit approval: downstream nodes remain blocked.
- Rejected gate: dependent branch remains blocked and the receipt records rejection.
- Unknown artifact content: artifact identity may be present, but its legal sufficiency is never inferred.
- Deadline-related input: stored only as user-supplied metadata and marked for attorney verification.
- Graph cycle or ambiguous producer: compilation fails.
- Context path escapes repository root: compilation fails.
- Receipt mismatch or source drift: verification fails with exact reasons.
- Every skill output and final plan output remains draft legal work product for attorney review.

## Testing

1. Plan-schema and compiler tests for IDs, modes, cycles, artifacts, bindings, conditions, and budgets.
2. State-resolution tests for ready, blocked, unresolved, not-selected, completed, approved, and rejected nodes.
3. Deterministic topological-order and parallel-wave tests.
4. Lazy-context tests proving blocked nodes load no skill content.
5. Privacy tests proving receipts exclude raw sensitive inputs.
6. Tamper tests for plan files, contracts, contexts, lineage, states, and arithmetic.
7. MCP service and transport tests.
8. CLI tests using temporary repositories and JSON fixtures.
9. Four pilot-plan preservation tests against their source playbooks and matter packs.
10. Generated-registry, report, site, and drift tests.
11. Full existing validation, eval, pack, and site suites.

## Success criteria

- Four plans compile with no cycles, unresolved static references, or unsafe paths.
- Each plan exposes at least one human gate and one artifact handoff.
- At least three plans expose a parallel execution wave.
- Missing inputs and gates fail closed.
- Blocked nodes load zero skill context.
- Receipts contain no raw sensitive matter input values.
- A changed plan, skill contract, inherited rule, module, lineage edge, state, or budget invalidates verification.
- MCP clients can search, inspect, build, and verify matter plans without loading all 212 skills.
- Existing skill routing and selective-context APIs remain backward compatible.
- The repository remains standard-library-only at runtime.
