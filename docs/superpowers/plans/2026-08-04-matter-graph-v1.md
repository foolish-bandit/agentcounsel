# Matter Graph v1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Compile recurring multi-skill legal matters into deterministic, privacy-conscious DAGs with typed handoffs, explicit attorney gates, lazy context loading, replayable receipts, MCP/CLI access, and CI-enforced complexity budgets.

**Architecture:** Add declarative `matter-plans/*.json` sidecars validated against canonical Skill Specification v2 contracts. A standard-library planner resolves conditions, dependencies, artifacts, gates, execution waves, and ready-node selective contexts, then emits a redacted receipt that can be verified against repository state. Generated metadata, MCP tools, CLI commands, reports, and static-site pages expose the same deterministic model.

**Tech Stack:** Python 3.12 standard library, JSON, Markdown, `unittest`, existing AgentCounsel metadata builders, existing MCP adapter, Node.js static-site generator, GitHub Actions.

## Global Constraints

- Existing playbooks and matter packs remain canonical human-readable guidance.
- No model calls, embeddings, vector database, connector execution, hosted backend, or third-party runtime dependency.
- Missing non-inferable inputs and missing gate approvals fail closed.
- No legal deadline is calculated.
- Every skill and plan output remains draft legal work product requiring attorney review.
- Raw sensitive matter input values never appear in exported plan receipts.
- Graphs must be acyclic, deterministic, repository-contained, and fully validated before registration.
- Existing skill routing, `get_skill`, `get_skill_spec`, and `get_skill_context` interfaces remain backward compatible.
- Only four pilot plans are added in this release.

---

### Task 1: Define Matter Plan Specification v1

**Files:**
- Create: `specs/matter-plan-v1.schema.json`
- Create: `scripts/matter_plan.py`
- Create: `tests/test_matter_plan_schema.py`
- Create: `matter-plans/README.md`

**Interfaces:**
- Produces `MatterPlanError`.
- Produces `load_skill_spec_registry(root: Path) -> dict[str, dict[str, Any]]`.
- Produces `validate_matter_plan(root: Path, plan: dict[str, Any], skill_specs: dict[str, dict[str, Any]]) -> list[str]`.
- Produces `assert_valid_matter_plan(root: Path, plan: dict[str, Any], skill_specs: dict[str, dict[str, Any]]) -> None`.

- [ ] **Step 1: Write failing schema tests**

Create fixtures with one matter input, one skill node, one attorney gate, and one artifact. Add tests for:

```python
def test_valid_minimal_plan_compiles(self):
    errors = validate_matter_plan(self.root, self.plan(), self.skill_specs)
    self.assertEqual(errors, [])


def test_rejects_cycle(self):
    plan = self.plan()
    plan["nodes"][0]["depends_on"] = ["final-gate"]
    self.assertIn("cycle", "\n".join(validate_matter_plan(...)).lower())


def test_rejects_unknown_skill_and_mode(self):
    plan = self.plan()
    plan["nodes"][0]["skill_id"] = "missing/skill"
    plan["nodes"][0]["mode"] = "turbo"
    errors = validate_matter_plan(...)
    self.assertTrue(any("unknown skill" in item for item in errors))


def test_rejects_binding_to_unknown_target_input(self):
    plan = self.plan()
    plan["nodes"][0]["input_bindings"][0]["target_input_id"] = "ghost"
    self.assertTrue(any("target input" in item for item in validate_matter_plan(...)))
```

Also cover duplicate IDs after case folding, unsafe slug IDs, unknown condition operators, non-finite budgets, multiple artifact producers, missing artifact producers, unknown dependencies, self-dependencies, path traversal in `source_path`, final outputs with no producer, and required skill inputs with no possible binding.

- [ ] **Step 2: Run tests and observe import failure**

Run:

```bash
python -m unittest tests.test_matter_plan_schema -v
```

Expected: FAIL because `scripts/matter_plan.py` and the schema do not exist.

- [ ] **Step 3: Implement plan constants and structural validation**

Add:

```python
PLAN_SCHEMA_VERSION = "1.0"
NODE_TYPES = {"skill", "attorney-gate"}
CONDITION_OPERATORS = {
    "always", "present", "equals", "contains-any",
    "artifact-present", "gate-approved",
}
NODE_STATES = {
    "ready", "blocked", "unresolved", "not-selected",
    "completed", "approved", "rejected",
}
```

Validate slug IDs with `r"[a-z0-9][a-z0-9-]*"`, repository-contained source paths, unique matter inputs/nodes/artifacts/final outputs, canonical skill IDs, enabled modes, declared dependencies, target skill input IDs, artifact producers, and positive finite budgets.

Use Kahn's algorithm to detect cycles and return deterministic cycle errors listing the remaining node IDs.

- [ ] **Step 4: Add the JSON Schema**

Define strict object shapes with `additionalProperties: false` for the top-level plan, required inputs, nodes, conditions, bindings, artifacts, gates, and budgets. Keep the Python validator authoritative for cross-record checks that JSON Schema cannot express.

- [ ] **Step 5: Document authoring rules**

`matter-plans/README.md` must explain node types, supported conditions, artifact lineage, gate semantics, fail-closed behavior, privacy boundaries, and the rule that plans reference legal skills rather than restating law.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.test_matter_plan_schema -v
```

Expected: PASS.

- [ ] **Step 7: Commit**

```bash
git add specs/matter-plan-v1.schema.json scripts/matter_plan.py tests/test_matter_plan_schema.py matter-plans/README.md
git commit -m "feat: define Matter Plan Specification v1"
```

---

### Task 2: Resolve graph states and execution waves

**Files:**
- Modify: `scripts/matter_plan.py`
- Create: `tests/test_matter_plan_builder.py`

**Interfaces:**
- Consumes `validate_matter_plan` and existing `scripts.skill_context.build_skill_context`.
- Produces:

```python
build_matter_plan(
    root: Path,
    plan: dict[str, Any],
    matter_inputs: dict[str, Any] | None = None,
    available_artifacts: dict[str, dict[str, Any]] | None = None,
    gate_decisions: dict[str, str] | None = None,
    explicit_node_ids: list[str] | None = None,
) -> dict[str, Any]
```

- [ ] **Step 1: Write failing state-resolution tests**

Cover:

```python
def test_first_skill_is_ready_and_downstream_is_blocked(self): ...
def test_missing_required_input_is_unresolved(self): ...
def test_false_condition_is_not_selected(self): ...
def test_missing_condition_input_is_unresolved_not_eager(self): ...
def test_supplied_artifact_marks_producer_completed(self): ...
def test_gate_requires_explicit_approved_or_rejected_value(self): ...
def test_rejected_gate_blocks_descendants(self): ...
def test_parallel_nodes_share_one_execution_wave(self): ...
def test_ready_nodes_only_load_their_skill_context(self): ...
def test_explicit_node_cannot_bypass_dependencies_or_gates(self): ...
```

Assert blocked nodes do not contain a `context` field.

- [ ] **Step 2: Run tests and observe missing builder**

```bash
python -m unittest tests.test_matter_plan_builder -v
```

Expected: FAIL because `build_matter_plan` is not implemented.

- [ ] **Step 3: Implement matter-input normalization**

Reuse Skill Specification v2 input types and the normalization behavior from `scripts.skill_context` where possible. Return matter-input records with:

```python
{
    "id": input_id,
    "present": True,
    "type": field_type,
    "sensitive": bool(field.get("sensitive")),
}
```

Keep normalized raw values only in the in-memory builder state, never in the receipt object.

- [ ] **Step 4: Implement condition resolution**

Return `(status, reason)` where status is `matched`, `not-matched`, or `unresolved`. `artifact-present` checks only artifact identity availability. `gate-approved` requires the exact decision `approved`. Unknown decisions reject before graph resolution.

- [ ] **Step 5: Implement deterministic node-state resolution**

Process nodes in stable topological order. Resolve completed producers from `available_artifacts`, then gates, conditions, dependencies, required bindings, and ready state. A node may not become ready when any dependency is blocked, unresolved, rejected, or not selected unless the plan declares an alternate dependency path.

- [ ] **Step 6: Implement execution waves**

Group ready nodes by dependency depth and emit:

```python
"execution_waves": [
    {
        "wave": 1,
        "node_ids": ["source-validation", "assumption-audit"],
        "estimated_tokens": 3200,
    }
]
```

Sort node IDs within each wave. Enforce plan caps on ready-node count, width, depth, and total ready-context tokens.

- [ ] **Step 7: Build lazy contexts and handoff manifests**

For each ready skill node, resolve structurally available bindings and call:

```python
context = build_skill_context(
    root,
    skill_spec,
    node["mode"],
    bound_inputs,
    node.get("module_ids"),
)
```

Emit bindings separately from content:

```python
{
    "target_input_id": "authorities",
    "source_kind": "artifact",
    "source_id": "authority-synthesis",
    "producer_node_id": "synthesize-authorities",
    "attorney_review_required": True,
}
```

- [ ] **Step 8: Run tests**

```bash
python -m unittest tests.test_matter_plan_builder -v
```

Expected: PASS.

- [ ] **Step 9: Commit**

```bash
git add scripts/matter_plan.py tests/test_matter_plan_builder.py
git commit -m "feat: build deterministic matter execution waves"
```

---

### Task 3: Add privacy-conscious plan receipts and verification

**Files:**
- Modify: `scripts/matter_plan.py`
- Create: `tests/test_matter_plan_receipts.py`

**Interfaces:**
- Produces `build_matter_plan(...)["receipt"]`.
- Produces `verify_matter_plan_receipt(root: Path, receipt: dict[str, Any]) -> dict[str, Any]`.

- [ ] **Step 1: Write failing receipt tests**

Cover:

```python
def test_receipt_contains_no_sensitive_raw_value(self):
    result = build_matter_plan(..., matter_inputs={"legal-question": "secret"})
    serialized = json.dumps(result["receipt"])
    self.assertNotIn("secret", serialized)


def test_receipt_is_deterministic(self): ...
def test_plan_file_drift_fails_verification(self): ...
def test_skill_contract_drift_fails_verification(self): ...
def test_artifact_lineage_tampering_fails_verification(self): ...
def test_node_state_tampering_fails_verification(self): ...
def test_token_arithmetic_tampering_fails_verification(self): ...
def test_unsafe_receipt_path_fails_verification(self): ...
```

- [ ] **Step 2: Run tests and observe missing receipt support**

```bash
python -m unittest tests.test_matter_plan_receipts -v
```

- [ ] **Step 3: Implement canonical receipt payloads**

Receipt structure:

```python
{
    "receipt_version": "1.0",
    "plan_id": plan["plan_id"],
    "plan_path": plan_path,
    "plan_sha256": sha256(plan_bytes),
    "input_presence": [...],
    "node_states": [...],
    "execution_waves": [...],
    "artifact_lineage": [...],
    "gate_decisions": [...],
    "ready_contexts": [
        {
            "node_id": node_id,
            "skill_id": skill_id,
            "contract_sha256": context["contract_sha256"],
            "bundle_sha256": context["bundle_sha256"],
            "estimated_tokens": context["estimated_tokens"]["total"],
        }
    ],
    "budget": {...},
    "receipt_sha256": digest,
}
```

Do not include raw matter inputs, bound artifact content, document text, or free-text gate notes.

- [ ] **Step 4: Implement strict verification**

Recompute plan hash, registry contract hashes, node states, artifact lineage, ready contexts, budgets, and receipt digest. Return:

```python
{
    "valid": False,
    "errors": ["plan source changed", "node state mismatch: draft-memo"],
}
```

Never stop after the first mismatch; return a stable sorted error list.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_matter_plan_receipts -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/matter_plan.py tests/test_matter_plan_receipts.py
git commit -m "feat: add verifiable privacy-conscious plan receipts"
```

---

### Task 4: Create plan registry, search, metrics, and CI drift gates

**Files:**
- Create: `scripts/build_matter_plans.py`
- Create: `metadata/matter_plans.json`
- Create: `reports/matter-plans.md`
- Create: `tests/test_matter_plan_registry.py`
- Modify: `scripts/check_all.py`
- Modify: `.github/workflows/validate.yml`

**Interfaces:**
- Consumes all `matter-plans/*.json` files.
- Produces `build_registry(root: Path) -> dict[str, Any]`.
- Produces `search_plan_cards(registry: dict[str, Any], query: str, limit: int) -> list[dict[str, Any]]`.

- [ ] **Step 1: Write failing registry tests**

Test deterministic plan ordering, unique IDs, source-path hashes, graph depth, maximum width, practice-area extraction from skill IDs, node/gate/artifact counts, search ranking, generated drift detection, and over-budget fixture rejection.

- [ ] **Step 2: Run tests and observe missing generator**

```bash
python -m unittest tests.test_matter_plan_registry -v
```

- [ ] **Step 3: Implement registry generation**

Generate cards containing:

```python
{
    "plan_id": plan_id,
    "title": title,
    "description": description,
    "source_path": source_path,
    "source_sha256": source_sha256,
    "tags": tags,
    "required_inputs": required_inputs,
    "node_count": 7,
    "skill_node_count": 5,
    "gate_node_count": 2,
    "artifact_count": 6,
    "practice_areas": ["legal-research", "legal-methodology"],
    "graph_depth": 5,
    "max_parallel_width": 3,
    "validation_status": "valid",
}
```

- [ ] **Step 4: Implement deterministic lexical search**

Weight exact plan ID/title matches highest, then tags, description, source path, and included skill titles. Return relevance score and matched fields.

- [ ] **Step 5: Render the Markdown report**

Include one summary table and one section per plan with nodes, edges, gates, artifacts, complexity caps, and declared scenario results.

- [ ] **Step 6: Wire drift checks**

Add to `scripts/check_all.py` and `.github/workflows/validate.yml`:

```yaml
- name: Check matter-plan registry and budgets
  run: python scripts/build_matter_plans.py --check
```

- [ ] **Step 7: Run focused tests and checks**

```bash
python -m unittest tests.test_matter_plan_registry -v
python scripts/build_matter_plans.py
python scripts/build_matter_plans.py --check
```

- [ ] **Step 8: Commit**

```bash
git add scripts/build_matter_plans.py metadata/matter_plans.json reports/matter-plans.md tests/test_matter_plan_registry.py scripts/check_all.py .github/workflows/validate.yml
git commit -m "feat: register and budget typed matter plans"
```

---

### Task 5: Author four pilot matter plans

**Files:**
- Create: `matter-plans/legal-research-memo.json`
- Create: `matter-plans/commercial-contract-review.json`
- Create: `matter-plans/litigation-motion-opposition.json`
- Create: `matter-plans/privacy-incident-response.json`
- Create: `tests/test_pilot_matter_plans.py`

**Interfaces:**
- Produces four valid Matter Plan v1 records.

- [ ] **Step 1: Write failing pilot preservation tests**

Assert every plan source path exists, every primary skill named in the source playbook or pack is represented, all quality checks are downstream of the primary draft, every plan ends at an attorney gate, privacy incident response contains an immediate reportability gate, and motion opposition uses `deep-review` only after a research-scope gate.

- [ ] **Step 2: Author Legal Research Memo plan**

Nodes:

```text
research-plan -> approve-research-scope -> authority-synthesis
-> legal-research-memo
-> [source-validation, citation-integrity-check, assumption-audit]
-> final-attorney-review
```

Artifacts include `research-roadmap`, `authority-synthesis`, `research-memo`, three quality reports, and `reviewed-research-package`.

- [ ] **Step 3: Author Commercial Contract Review plan**

Required controlled inputs include `has-sow` and `has-prior-redline`. Conditional nodes use `equals` against `yes`. Quality checks run in parallel after `contract-risk-review`. The contract-review panel is represented as an attorney gate requiring the risk matrix and quality reports.

- [ ] **Step 4: Author Litigation Motion Opposition plan**

Use research planning, scope approval, authority synthesis, `litigation/motion-opposition-drafter` in `deep-review`, parallel methodology checks, a litigation-risk gate, and final attorney review.

- [ ] **Step 5: Author Privacy Incident Response plan**

Use `privacy/breach-response-workflow`, an immediate attorney reportability gate, parallel `litigation/litigation-chronology`, `litigation/legal-hold`, and `privacy/privacy-policy-gap-review`, then regulatory-risk and external-communication gates before final attorney review. Every date field is user-supplied and marked sensitive; no node computes a deadline.

- [ ] **Step 6: Run pilot tests and registry generation**

```bash
python -m unittest tests.test_pilot_matter_plans -v
python scripts/build_matter_plans.py
python scripts/build_matter_plans.py --check
```

- [ ] **Step 7: Commit**

```bash
git add matter-plans tests/test_pilot_matter_plans.py metadata/matter_plans.json reports/matter-plans.md
git commit -m "feat: add four typed legal matter graphs"
```

---

### Task 6: Expose matter plans through MCP and CLI

**Files:**
- Modify: `agentcounsel_mcp.py`
- Modify: `mcp_server.py`
- Create: `scripts/matter_plan_cli.py`
- Create: `tests/test_matter_plan_mcp.py`
- Create: `tests/test_matter_plan_cli.py`
- Modify: `docs/MCP_SERVER.md`
- Modify: `docs/CLI.md`

**Interfaces:**
- Adds `CatalogService.list_matter_plans()`.
- Adds `CatalogService.search_matter_plans(query, limit=10)`.
- Adds `CatalogService.get_matter_plan(plan_id)`.
- Adds `CatalogService.build_matter_plan(...)`.
- Adds `CatalogService.verify_matter_plan_receipt(receipt)`.

- [ ] **Step 1: Write failing MCP service tests**

Assert alias resolution by plan ID/title, deterministic search ranking, correct ready/blocked states, no blocked-node context, gate approval transitions, and verification error propagation.

- [ ] **Step 2: Extend `CatalogService.from_root`**

Load `metadata/matter_plans.json` and build unique aliases from plan ID, title, and source path. Preserve constructor compatibility by making the registry optional only in direct test fixtures; `from_root` requires it.

- [ ] **Step 3: Add MCP transport tools**

Expose compact JSON-safe signatures and document that these tools plan work but do not execute legal analysis.

- [ ] **Step 4: Write failing CLI tests**

Test:

```text
matter_plan_cli.py list
matter_plan_cli.py show legal-research-memo
matter_plan_cli.py build legal-research-memo --inputs inputs.json
matter_plan_cli.py verify receipt.json
```

Assert nonzero exit for malformed JSON, unknown plan, invalid gate decision, and invalid receipt.

- [ ] **Step 5: Implement the CLI**

Use `argparse`, UTF-8 JSON files, stable sorted output, `--output`, and `--markdown`. The Markdown run sheet lists ready, blocked, unresolved, completed, approved, rejected, and not-selected nodes with reasons.

- [ ] **Step 6: Run focused tests**

```bash
python -m unittest tests.test_matter_plan_mcp tests.test_matter_plan_cli -v
```

- [ ] **Step 7: Update docs and commit**

```bash
git add agentcounsel_mcp.py mcp_server.py scripts/matter_plan_cli.py tests/test_matter_plan_mcp.py tests/test_matter_plan_cli.py docs/MCP_SERVER.md docs/CLI.md
git commit -m "feat: expose matter graphs through MCP and CLI"
```

---

### Task 7: Add matter-plan catalog pages and accessible graph visualization

**Files:**
- Modify: `site/generate.mjs`
- Modify: `site/assets/style.css`
- Modify: `site/assets/app.js`
- Create: `tests/test_site_matter_plans.py`

**Interfaces:**
- Produces `site/public/matter-plans/index.html` and one page per registered plan.

- [ ] **Step 1: Write failing site tests**

Assert the index lists all four plans, each page includes an SVG with `role="img"`, a text alternative listing every edge, node links to canonical skill pages, gate nodes are labeled as attorney gates, raw JSON is copyable, and no graph library is bundled.

- [ ] **Step 2: Implement graph layout**

Use deterministic depth columns and stable node ordering. Render simple SVG rectangles, paths, and labels. Cap visual width with horizontal scrolling while keeping the complete edge list in adjacent HTML.

- [ ] **Step 3: Add plan detail tables**

Render required inputs, node states/types, conditions, dependencies, artifacts, handoff bindings, gates, budgets, and CLI examples. Link the human source playbook or matter pack.

- [ ] **Step 4: Add navigation and copy actions**

Add `Matter plans` to shared navigation. Add buttons for raw plan JSON and a starter CLI command; reuse existing copy behavior rather than adding a dependency.

- [ ] **Step 5: Run tests and build**

```bash
python -m unittest tests.test_site_matter_plans -v
node site/generate.mjs
```

- [ ] **Step 6: Commit**

```bash
git add site/generate.mjs site/assets/style.css site/assets/app.js tests/test_site_matter_plans.py
git commit -m "feat: visualize typed matter plans in the catalog"
```

---

### Task 8: Add scenario budgets and adversarial plan mutations

**Files:**
- Create: `scripts/evaluate_matter_plans.py`
- Create: `metadata/matter_plan_evals.json`
- Create: `reports/matter-plan-evals.md`
- Create: `tests/test_matter_plan_evals.py`
- Modify: `scripts/check_all.py`
- Modify: `.github/workflows/validate.yml`

**Interfaces:**
- Produces deterministic plan scenario and mutation results.

- [ ] **Step 1: Write failing evaluator tests**

Require mutation probes that remove a dependency, bypass a gate, add a cycle, swap an artifact producer, inject raw sensitive input into a receipt, alter token arithmetic, change a skill mode, and make a blocked node carry context. Every mutation must be detected.

- [ ] **Step 2: Implement representative scenarios**

For each pilot plan include at least:

- missing-input scenario;
- first-ready-wave scenario;
- one gate-approved continuation;
- one condition-false branch where applicable;
- completed final scenario using artifact identities only.

- [ ] **Step 3: Implement mutation evaluation**

Deep-copy valid plans/results, apply one mutation at a time, and record the exact validator or verifier signal that caught it. Fail when any mutation escapes.

- [ ] **Step 4: Generate JSON and Markdown reports**

Record scenario states, ready contexts, token totals, maximum width/depth, receipt validity, and mutation detection rate.

- [ ] **Step 5: Wire CI**

Add:

```yaml
- name: Evaluate matter plans and mutation sensitivity
  run: python scripts/evaluate_matter_plans.py --check
```

- [ ] **Step 6: Run tests and checks**

```bash
python -m unittest tests.test_matter_plan_evals -v
python scripts/evaluate_matter_plans.py
python scripts/evaluate_matter_plans.py --check
```

- [ ] **Step 7: Commit**

```bash
git add scripts/evaluate_matter_plans.py metadata/matter_plan_evals.json reports/matter-plan-evals.md tests/test_matter_plan_evals.py scripts/check_all.py .github/workflows/validate.yml
git commit -m "test: prove matter-plan gate and receipt sensitivity"
```

---

### Task 9: Documentation, borrowing map, and v0.4.0 preparation

**Files:**
- Modify: `README.md`
- Modify: `QUICKSTART.md`
- Modify: `VALIDATION.md`
- Modify: `docs/PROJECT_STATUS.md`
- Modify: `docs/IMPLEMENTATION_SEQUENCE.md`
- Modify: `docs/OSS_BORROWING_MAP.md`
- Modify: `docs/RELEASE_CHECKLIST.md`
- Modify: `CHANGELOG.md`
- Modify: `RELEASE_NOTES.md`
- Modify: `adapters/claude-code-plugin/plugin.json`
- Modify: `gemini-extension.json`
- Modify: `site/package.json`

**Interfaces:**
- Produces synchronized release version `0.4.0` and user guidance.

- [ ] **Step 1: Document the end-user path**

README and Quickstart must explain the distinction between a skill, playbook, matter pack, matter plan, and matter workspace. Include one legal-research CLI/MCP walkthrough and emphasize that plans organize work but do not execute legal analysis or replace attorney judgment.

- [ ] **Step 2: Document validation boundaries**

State clearly that graph validation proves structure, references, gates, lineage, deterministic state resolution, and receipt integrity, not legal correctness or deadline accuracy.

- [ ] **Step 3: Record research provenance**

Add borrowing-map rows for LangGraph subgraph/state patterns, OpenAI Agents SDK typed handoffs and tracing, Temporal event-sourcing/replay concepts, Prefect cache-key/task-state concepts, Dagster asset lineage, and MCP Tasks as a deferred future compatibility target. State that no dependency or copied implementation was introduced.

- [ ] **Step 4: Update project status and roadmap**

Promote selective context to stable and mark Matter Graph v1 experimental but fully validated. Identify the next likely phase as claim-to-evidence ledgers attached to plan artifacts.

- [ ] **Step 5: Prepare release notes and versions**

Set `0.4.0` in all three manifests. Release notes must report measured graph counts, gates, artifacts, scenarios, mutation probes, tests, and site pages without claiming legal correctness.

- [ ] **Step 6: Run version and generated-artifact checks**

```bash
python scripts/build_skill_index.py
python scripts/build_skill_specs.py
python scripts/build_matter_plans.py
python scripts/evaluate_matter_plans.py
python scripts/build_platform_packs.py
node site/generate.mjs
python scripts/validate_repo.py
```

- [ ] **Step 7: Commit**

```bash
git add -A
git commit -m "docs: prepare AgentCounsel v0.4.0 matter graphs"
```

---

### Task 10: Full verification, review, merge, and release

**Files:**
- Review all changed files.

**Interfaces:**
- Produces merged `main` and release `v0.4.0` only after exact-head verification.

- [ ] **Step 1: Run the full local gate**

```bash
python scripts/check_all.py
```

Expected: every step passes.

- [ ] **Step 2: Run targeted smoke tests**

```bash
python scripts/matter_plan_cli.py list
python scripts/matter_plan_cli.py build legal-research-memo --inputs tests/fixtures/matter-plan/legal-research-inputs.json
python -m unittest tests.test_matter_plan_schema tests.test_matter_plan_builder tests.test_matter_plan_receipts tests.test_matter_plan_registry tests.test_pilot_matter_plans tests.test_matter_plan_mcp tests.test_matter_plan_cli tests.test_site_matter_plans tests.test_matter_plan_evals -v
node site/generate.mjs
```

- [ ] **Step 3: Review scope and safety**

Confirm no raw matter facts appear in generated registries, reports, receipts, or site pages; no deadline is computed; blocked nodes contain no context; all pilot final outputs pass through attorney gates; no temporary transport workflow remains; and no runtime dependency was added.

- [ ] **Step 4: Request independent code and security review**

Review the exact base-to-head diff for correctness, privacy leakage, path traversal, graph bypass, receipt tampering, cycle handling, archive/package regressions, and MCP backward compatibility. Fix every Critical or Important finding and rerun the full gate.

- [ ] **Step 5: Open the PR and wait for exact-head CI**

Summarize architecture, pilot graphs, measurements, safety boundaries, tests, and explicit non-goals. Mark ready only after the GitHub `Validate` workflow passes on the exact PR head.

- [ ] **Step 6: Merge and verify `main`**

Merge into `main`, then verify the merge commit's validation workflow and release manifest versions.

- [ ] **Step 7: Publish v0.4.0**

Create annotated tag `v0.4.0` on the verified merge commit and publish a non-draft, non-prerelease GitHub release titled:

```text
AgentCounsel v0.4.0: Typed Matter Graphs
```

Use `RELEASE_NOTES.md` as the release body and confirm the public release targets `main`.
