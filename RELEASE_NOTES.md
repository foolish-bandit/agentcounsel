# AgentCounsel v0.4.0: Typed Matter Graphs

**Release date:** 2026-08-04
**License:** MIT

> AgentCounsel produces **draft legal work product for attorney review**. It does not provide legal advice, replace a licensed attorney, compute legal deadlines, or create an attorney-client relationship.

AgentCounsel v0.4.0 adds a deterministic whole-matter planning layer on top of the 212 typed legal skills released in v0.3.0. The new Matter Plan v1 format turns selected playbooks and matter packs into validated dependency graphs with typed artifact handoffs, explicit attorney gates, parallel review lanes, lazy context loading, and privacy-conscious receipts. It plans work; it does not execute an AI model or decide legal strategy.

## Highlights

### Four typed legal matter graphs

The first pilots cover:

- **Legal Research Memo:** research planning, attorney scope approval, authority synthesis, negative-treatment review, memo drafting, three parallel methodology checks, and final attorney review.
- **Commercial Contract Review:** core risk review, optional SOW and prior-redline branches, parallel source/assumption/privilege checks, a contract-review gate, and final attorney review.
- **Litigation Motion Opposition:** research planning and scope approval, authority synthesis, the selectively loaded deep-review opposition workflow, parallel methodology checks, litigation-risk review, and final attorney review.
- **Privacy Incident Response:** breach-response intake, immediate reportability escalation, parallel chronology, preservation, and policy-gap work, regulatory and external-communication gates, and final attorney review.

Together the pilots contain **34 nodes**, including **23 canonical skill nodes**, **11 attorney gates**, and **23 typed artifact identities**.

### Deterministic graph states and execution waves

Every node receives exactly one visible state: `ready`, `blocked`, `unresolved`, `not-selected`, `completed`, `approved`, or `rejected`. Missing non-inferable inputs, artifacts, dependencies, and attorney approvals fail closed. Safely skipped optional branches do not block downstream completion, while unresolved or rejected branches do.

The planner computes stable topological order and groups dependency-independent work into parallel waves. It loads Skill Specification v2 context only for genuinely ready nodes. Blocked nodes carry no skill content, avoiding whole-matter prompt inflation.

### Typed artifact handoffs

Plan artifacts are first-class identities with one producer, declared consumers, target skill inputs, sensitivity metadata, and attorney-review requirements. The plan returns handoff manifests rather than copying document content between nodes. Actual legal documents and drafts remain in the user's matter workspace.

### Privacy-conscious, verifiable receipts

Each plan build can emit a deterministic receipt containing:

- plan and human-guidance hashes;
- node states and reasons;
- execution waves and budget arithmetic;
- attorney-gate decisions;
- artifact lineage and optional caller-supplied content digests;
- selected skill contract hashes and ready-context fingerprints; and
- a final receipt SHA-256.

Raw sensitive matter inputs, document text, draft work product, artifact paths, and free-text gate notes are excluded. Verification detects plan, source, contract inventory, context resources, state, lineage, gate, and arithmetic drift. Receipts are deterministic integrity and self-consistency records, not digital signatures or proof of who approved a gate; approval identity and authority remain the caller's responsibility.

### MCP and CLI access

The MCP catalog adds:

- `list_matter_plans`
- `search_matter_plans`
- `get_matter_plan`
- `build_matter_plan`
- `verify_matter_plan_receipt`

The standard-library CLI supports `list`, `show`, `build`, and `verify` commands with JSON or Markdown output. No model provider, account, database, or third-party runtime is required.

### Accessible plan catalog

The static catalog now includes a matter-plan index and one page per pilot. Each page has an accessible dependency SVG, a complete text edge alternative, canonical skill links, clearly labeled attorney gates, artifact and binding tables, raw plan JSON, and copyable CLI commands. No graph visualization dependency was added.

### Adversarial graph evaluation

Sixteen representative lifecycle scenarios exercise missing-input, first-ready-wave, gate-approved continuation, optional-branch, and completed-final states. Eight destructive mutations prove the validators and receipt verifier detect:

- cycle injection;
- gate bypass;
- dependency removal;
- artifact producer substitution;
- raw sensitive input injected into a receipt;
- token arithmetic tampering;
- skill mode substitution; and
- context attached to a blocked node.

All scenarios stay within declared graph and ready-context budgets.

## Repository state

- 212 canonical legal skills and typed Skill Specification v2 contracts.
- 4 Matter Plan v1 pilots.
- 34 plan nodes: 23 skills and 11 attorney gates.
- 23 typed plan artifacts.
- 16 lifecycle scenarios and 8/8 detected mutations.
- 170 standard-library unit tests.
- 587 existing skill eval cases remain intact.
- 292 generated catalog pages.
- No new runtime dependency.

## Safety boundaries

- Matter graphs organize work; they do not determine legal strategy or certify legal correctness.
- Attorney gates never auto-complete.
- Required legal inputs are not inferred.
- Legal deadlines are never calculated.
- Blocked nodes do not load context.
- Graph validity does not establish that authority is current, a claim is supported, or a draft may be relied upon.
- Every final artifact remains draft legal work product requiring independent attorney review.

## Validation

The release gate remains:

```bash
python scripts/check_all.py
```

It now includes 18 stages covering repository structure, 186 unit tests, generated skill and matter registries, selective-context and matter-plan budgets, privacy-conscious receipt verification, adversarial graph mutations, platform packs, 587 skill eval cases, legal-prose checks, and the static site.

## Open-source research

Matter Graph v1 was independently implemented after reviewing typed-state and subgraph patterns in LangGraph, typed handoffs and traceability in the OpenAI Agents SDK, deterministic replay concepts from Temporal, state and cache-key concepts from Prefect, asset-lineage concepts from Dagster, and the emerging MCP Tasks surface as a future compatibility target. AgentCounsel imports none of those runtimes and copies no code, schema, prompts, or examples. The research record is in `docs/OSS_BORROWING_MAP.md`.

## Upgrade notes

Existing Markdown skills, platform packs, Skill Specification v2 clients, and `get_skill_context` calls remain compatible. New clients may adopt matter plans incrementally. Run `python scripts/build_matter_plans.py --check` and `python scripts/evaluate_matter_plans.py --check` when adding or editing a plan.
