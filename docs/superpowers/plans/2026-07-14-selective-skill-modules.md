# Phase 2B Selective Skill Modules Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Decompose AgentCounsel's two largest skills into deterministic, selectively loaded Markdown modules and expose context bundles with enforceable token budgets.

**Architecture:** Extend Skill Specification v2 with optional declarative module activation and context scenarios. Add a pure standard-library selector/bundle builder, expose it through the MCP catalog service, migrate the two >6,000-token skills, and generate a CI-enforced selective-context report.

**Tech Stack:** Python 3.12 standard library, JSON, Markdown, `unittest`, GitHub Actions, existing AgentCounsel generators.

## Global Constraints

- `SKILL.md` remains the canonical human-readable core workflow.
- Module files are Markdown only and contain no executable instructions beyond the declared workflow.
- No third-party Python dependency.
- Missing required inputs are never inferred.
- Missing activation inputs fail closed and do not cause all conditional modules to load.
- Deadline calculation remains prohibited.
- Every output remains draft legal work product requiring attorney review.
- Existing Phase 2A specs compile without changes.
- Only `litigation/motion-opposition-drafter` and `ip/infringement-triage` are physically modularized in this PR.

---

### Task 1: Extend the compiled contract schema

**Files:**
- Modify: `scripts/skill_spec_v2.py`
- Modify: `specs/skill-spec-v2.schema.json`
- Modify: `docs/SKILL_SPEC_V2.md`
- Test: `tests/test_skill_spec_v2.py`

**Interfaces:**
- Produces: validated module `activation` objects, `string-list` inputs, and `context_scenarios` records in compiled specs.

- [ ] **Step 1: Write failing compiler tests**

Add tests that compile a sidecar containing:

```python
{
    "input_schema": [{
        "id": "rights",
        "label": "Rights",
        "type": "string-list",
        "required": True,
        "description": "Controlled right identifiers",
        "source_requirement": "user-provided",
        "may_infer": False,
        "sensitive": False,
        "items": ["trademark", "copyright"]
    }],
    "modules": [{
        "id": "trademark",
        "kind": "workflow-module",
        "path": "skills/ip/test/modules/trademark.md",
        "required": False,
        "load_when": "The rights input includes trademark.",
        "activation": {
            "modes": ["standard", "deep-review"],
            "input_id": "rights",
            "operator": "contains-any",
            "values": ["trademark"]
        }
    }],
    "context_scenarios": [{
        "id": "standard-trademark",
        "mode": "standard",
        "inputs": {"rights": ["trademark"]},
        "baseline_estimated_tokens": 1000,
        "max_ratio": 0.7
    }]
}
```

Also test rejection of invalid operators, unknown modes, missing activation values, duplicate scenario IDs, zero baselines, and non-positive ratios.

- [ ] **Step 2: Run focused tests and observe failure**

Run:

```bash
python -m unittest tests.test_skill_spec_v2 -v
```

Expected: failures for the unsupported `string-list`, activation, and scenario fields.

- [ ] **Step 3: Implement schema validation**

Add:

```python
INPUT_TYPES.add("string-list")
MODULE_ACTIVATION_OPERATORS = {"always", "present", "equals", "contains-any"}
```

Validate:

- `string-list.items` is a non-empty list of unique strings when present;
- `activation.modes` is a non-empty subset of `MODE_IDS`;
- `always` has no input fields;
- `present` requires `input_id` only;
- `equals` requires one non-empty `value`;
- `contains-any` requires non-empty unique `values`;
- `context_scenarios` have unique IDs, valid modes, object inputs, positive integer baselines, and positive numeric ratios.

Copy `context_scenarios` through `_merge_custom` with record merging by ID.

- [ ] **Step 4: Update JSON Schema and documentation**

Document the exact fields and fail-closed behavior. Keep `activation` and `context_scenarios` optional for backward compatibility.

- [ ] **Step 5: Run focused tests**

Run:

```bash
python -m unittest tests.test_skill_spec_v2 -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/skill_spec_v2.py specs/skill-spec-v2.schema.json docs/SKILL_SPEC_V2.md tests/test_skill_spec_v2.py
git commit -m "feat: add declarative module activation"
```

---

### Task 2: Build the pure module selector and context bundle

**Files:**
- Create: `scripts/skill_context.py`
- Create: `tests/test_skill_context.py`

**Interfaces:**
- Produces:

```python
select_modules(
    spec: dict,
    mode: str,
    inputs: dict | None = None,
    explicit_module_ids: list[str] | None = None,
) -> dict

build_skill_context(
    root: Path,
    spec: dict,
    mode: str,
    inputs: dict | None = None,
    explicit_module_ids: list[str] | None = None,
) -> dict
```

- [ ] **Step 1: Write failing selector tests**

Cover:

- mode-only activation;
- `present`, `equals`, and `contains-any` operators;
- multi-right input loading multiple modules;
- no auto-loading for modules with prose-only `load_when`;
- required modules;
- unresolved modules when an activation input is absent;
- unknown mode, disabled mode, and unknown explicit IDs;
- explicit module selection with a transparent reason;
- deterministic module order.

- [ ] **Step 2: Run tests and observe import failure**

```bash
python -m unittest tests.test_skill_context -v
```

Expected: FAIL because `scripts/skill_context.py` does not exist.

- [ ] **Step 3: Implement selector**

Use normalized scalar/list comparison. Return:

```python
{
    "mode": mode,
    "selected": [{"module": module, "reason": reason}],
    "unresolved": [{"module": module, "reason": reason}],
}
```

Do not mutate the spec.

- [ ] **Step 4: Implement bundle builder**

Read `spec["skill_path"]` and selected module paths. Return:

```python
{
    "skill_id": spec["skill_id"],
    "schema_version": spec["schema_version"],
    "mode": mode,
    "normalized_inputs": inputs,
    "missing_required_inputs": [...],
    "core": {"path": ..., "content": ..., "estimated_tokens": ...},
    "modules": [{"id": ..., "path": ..., "content": ..., "reason": ..., "estimated_tokens": ...}],
    "unresolved_modules": [...],
    "estimated_tokens": {"core": ..., "modules": ..., "total": ...},
    "complete": not missing_required_inputs and not unresolved_required_modules,
}
```

Estimate tokens as `(len(text) + 3) // 4`, matching existing metrics.

- [ ] **Step 5: Run focused tests**

```bash
python -m unittest tests.test_skill_context -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/skill_context.py tests/test_skill_context.py
git commit -m "feat: build selective skill context bundles"
```

---

### Task 3: Expose selective context through MCP

**Files:**
- Modify: `agentcounsel_mcp.py`
- Modify: `mcp_server.py`
- Modify: `docs/MCP_SERVER.md`
- Test: `tests/test_mcp_service.py`

**Interfaces:**
- Consumes: `build_skill_context` from Task 2.
- Produces: `CatalogService.get_skill_context(...)` and MCP tool `get_skill_context`.

- [ ] **Step 1: Add failing MCP tests**

Extend the fixture registry with activated modules and module files. Assert:

```python
bundle = service.get_skill_context(
    "ip/infringement-triage",
    mode="standard",
    inputs={"ip-rights-at-issue": ["trademark"]},
)
```

returns only the common and trademark modules, includes reasons, and reports token totals. Assert missing rights creates unresolved modules rather than loading all right-specific modules.

- [ ] **Step 2: Run focused tests and observe failure**

```bash
python -m unittest tests.test_mcp_service -v
```

- [ ] **Step 3: Implement catalog and transport methods**

Add:

```python
def get_skill_context(
    self,
    skill_id: str,
    mode: str = "standard",
    inputs: dict[str, Any] | None = None,
    module_ids: list[str] | None = None,
) -> dict[str, Any]:
    stable_id = self._resolve_id(skill_id)
    return build_skill_context(
        self.root,
        self._skill_specs[stable_id],
        mode,
        inputs,
        module_ids,
    )
```

Expose the same signature in `mcp_server.py`.

- [ ] **Step 4: Document the recommended client flow**

Explain `get_skill` versus `get_skill_spec` versus `get_skill_context`, including unresolved conditions and explicit module selection.

- [ ] **Step 5: Run tests**

```bash
python -m unittest tests.test_mcp_service -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add agentcounsel_mcp.py mcp_server.py docs/MCP_SERVER.md tests/test_mcp_service.py
git commit -m "feat: expose selective skill context over MCP"
```

---

### Task 4: Modularize Motion Opposition Drafter

**Files:**
- Modify: `skills/litigation/motion-opposition-drafter/SKILL.md`
- Create: `skills/litigation/motion-opposition-drafter/SPEC.json`
- Create: `skills/litigation/motion-opposition-drafter/modules/motion-deconstruction.md`
- Create: `skills/litigation/motion-opposition-drafter/modules/opposition-drafting.md`
- Create: `skills/litigation/motion-opposition-drafter/modules/expanded-verification.md`
- Test: `tests/test_modularized_skills.py`

**Interfaces:**
- Produces: mode-activated modules and three context scenarios.

- [ ] **Step 1: Write content-preservation and selection tests**

Assert the deep bundle includes these obligations:

- never invent counter-authority;
- verify every movant authority and current treatment;
- cite every factual assertion to provided record material;
- never calculate the response deadline;
- do not file without attorney review;
- candidly flag weak response points.

Assert quick loads zero modules, standard loads `motion-deconstruction` and `opposition-drafting`, and deep adds `expanded-verification`.

- [ ] **Step 2: Extract modules without changing substance**

Keep concise universal language in the core. Move the detailed argument-deconstruction procedure, drafting/output instructions, and expanded filing checklist into the three module files. Begin each module with:

```markdown
> Draft legal work product for attorney review. This module inherits every safety rule and gate in the parent skill.
```

- [ ] **Step 3: Add the sidecar**

Declare the modules with mode-only activation and scenarios:

- `quick-triage`, baseline 6346, max ratio 0.40;
- `standard`, baseline 6346, max ratio 0.75;
- `deep-review`, baseline 6346, max ratio 1.10.

- [ ] **Step 4: Run focused tests**

```bash
python -m unittest tests.test_modularized_skills -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/litigation/motion-opposition-drafter tests/test_modularized_skills.py
git commit -m "refactor: modularize motion opposition drafting"
```

---

### Task 5: Modularize Infringement Triage

**Files:**
- Modify: `skills/ip/infringement-triage/SKILL.md`
- Create: `skills/ip/infringement-triage/SPEC.json`
- Create: `skills/ip/infringement-triage/modules/factor-method.md`
- Create: `skills/ip/infringement-triage/modules/trademark.md`
- Create: `skills/ip/infringement-triage/modules/copyright.md`
- Create: `skills/ip/infringement-triage/modules/patent.md`
- Create: `skills/ip/infringement-triage/modules/trade-secret.md`
- Create: `skills/ip/infringement-triage/modules/defenses-routing-output.md`
- Create: `skills/ip/infringement-triage/modules/expanded-verification.md`
- Test: `tests/test_modularized_skills.py`

**Interfaces:**
- Produces: input-activated IP-right modules and seven context scenarios.

- [ ] **Step 1: Add failing multi-right selection and preservation tests**

Assert standard trademark loads only common, trademark, and output modules. Assert patent plus trade secret loads both right modules. Assert a missing rights input leaves four right-specific modules unresolved.

Deep bundle preservation must include:

- no infringement conclusion;
- registry and filing status remain unverified;
- jurisdiction-specific factor frameworks require attorney confirmation;
- patent claim comparison is preliminary, not claim construction;
- affirmative defenses are identified but not decided;
- no deadline calculation;
- routing signals are not merits findings.

- [ ] **Step 2: Extract common and right-specific modules**

Move only detailed factor lists and expanded output/checklist material. Keep the routing boundary, required inputs, universal safety rules, high-level factor method, and concise output structure in the core.

- [ ] **Step 3: Add the sidecar**

Refine `ip-rights-at-issue` to `string-list` with allowed items:

```json
["trademark", "copyright", "patent", "trade-secret"]
```

Declare common mode modules, four `contains-any` right modules, and scenario budgets:

- quick: 0.40;
- each single-right standard scenario: 0.70;
- deep all-rights: 1.15;

All baselines are 6,115 tokens.

- [ ] **Step 4: Run focused tests**

```bash
python -m unittest tests.test_modularized_skills -v
```

Expected: PASS.

- [ ] **Step 5: Commit**

```bash
git add skills/ip/infringement-triage tests/test_modularized_skills.py
git commit -m "refactor: modularize infringement triage"
```

---

### Task 6: Generate selective-context metrics and enforce budgets

**Files:**
- Create: `scripts/generate_selective_context_metrics.py`
- Create: `metadata/selective_context_metrics.json`
- Create: `reports/selective-context.md`
- Create: `tests/test_selective_context_metrics.py`
- Modify: `.github/workflows/validate.yml`
- Modify: `scripts/check_all.py`

**Interfaces:**
- Consumes: compiled `context_scenarios` and `build_skill_context`.
- Produces: deterministic JSON/Markdown metrics and CI budget failures.

- [ ] **Step 1: Write failing generator tests**

Test deterministic rendering, drift detection, ratio calculation, and a fixture exceeding its max ratio.

- [ ] **Step 2: Implement generator**

For every compiled spec with scenarios, build each bundle and record:

```python
{
    "skill_id": skill_id,
    "scenario_id": scenario["id"],
    "mode": scenario["mode"],
    "selected_module_ids": [...],
    "core_estimated_tokens": ...,
    "module_estimated_tokens": ...,
    "total_estimated_tokens": ...,
    "baseline_estimated_tokens": ...,
    "ratio": round(total / baseline, 4),
    "max_ratio": ...,
    "within_budget": ratio <= max_ratio,
}
```

Exit non-zero if any scenario is over budget or incomplete.

- [ ] **Step 3: Generate artifacts**

```bash
python scripts/build_skill_specs.py
python scripts/generate_selective_context_metrics.py
```

- [ ] **Step 4: Add CI and local drift checks**

Add after the skill-spec registry check:

```yaml
- name: Check selective context metrics and budgets
  run: python scripts/generate_selective_context_metrics.py --check
```

Mirror it in `scripts/check_all.py`.

- [ ] **Step 5: Run focused tests and checks**

```bash
python -m unittest tests.test_selective_context_metrics -v
python scripts/build_skill_specs.py --check
python scripts/generate_selective_context_metrics.py --check
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add scripts/generate_selective_context_metrics.py metadata/selective_context_metrics.json reports/selective-context.md tests/test_selective_context_metrics.py .github/workflows/validate.yml scripts/check_all.py metadata/skill_specs.json
git commit -m "feat: enforce selective context budgets"
```

---

### Task 7: Refresh generated artifacts and adapters

**Files:**
- Modify generated files as required by existing scripts.
- Modify: `CHANGELOG.md`
- Modify: `docs/SKILL_SPEC_V2.md`

**Interfaces:**
- Produces: synchronized plugin copies, context metrics, health reports, and documentation.

- [ ] **Step 1: Regenerate all affected artifacts**

```bash
python scripts/sync_plugin_skills.py
python scripts/build_skill_index.py
python scripts/build_skill_specs.py
python scripts/build_platform_packs.py
python scripts/generate_context_metrics.py
python scripts/generate_skill_health_report.py
python scripts/generate_selective_context_metrics.py
```

- [ ] **Step 2: Update changelog and migration guidance**

Document the two modularized skills, the new MCP bundle tool, activation semantics, and measured context savings without claiming provider billing savings.

- [ ] **Step 3: Run focused repository checks**

```bash
python scripts/sync_plugin_skills.py --check
python scripts/build_skill_index.py --check
python scripts/build_skill_specs.py --check
python scripts/build_platform_packs.py --check
python scripts/generate_context_metrics.py --check
python scripts/generate_skill_health_report.py --check
python scripts/generate_selective_context_metrics.py --check
```

Expected: PASS.

- [ ] **Step 4: Commit**

```bash
git add -A
git commit -m "docs: document selective skill modules"
```

---

### Task 8: Full verification and review-ready PR

**Files:**
- Review all changed files.

**Interfaces:**
- Produces: review-ready Phase 2B pull request.

- [ ] **Step 1: Run the full CI-equivalent suite**

```bash
python scripts/check_all.py
```

Expected: all checks pass.

- [ ] **Step 2: Review the diff for scope and safety**

Confirm:

- only the two target skills were physically modularized;
- every extracted module is referenced from its sidecar;
- no safety requirement disappeared from the deep bundle;
- quick and standard bundles meet budgets;
- generated files are current;
- no runtime dependency was added.

- [ ] **Step 3: Open a draft PR with measured results**

Summarize baseline and scenario token estimates, tests, and explicit non-goals.

- [ ] **Step 4: Mark ready only after the exact PR head passes GitHub Actions**
