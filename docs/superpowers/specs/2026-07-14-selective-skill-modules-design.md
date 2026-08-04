# Phase 2B Selective Skill Modules Design

## Status

Approved for implementation by the user's instruction to merge Phase 2A and continue with the previously identified Phase 2B modularization work.

## Problem

AgentCounsel now has typed execution contracts for all 212 skills, but the two largest canonical skills still require loading more than 6,000 estimated tokens before any task-specific filtering:

- `litigation/motion-opposition-drafter`: 6,346 estimated tokens
- `ip/infringement-triage`: 6,115 estimated tokens

The Phase 2A `modules` records identify potentially useful files, but `load_when` is prose only. The runtime cannot deterministically choose modules from execution mode and typed inputs, and the two largest skills have not yet been physically decomposed.

## Goals

1. Reduce routine context for the two largest skills without weakening their legal-safety rules.
2. Prove two selection models:
   - mode-based loading for motion-opposition drafting;
   - input-based loading for infringement triage by IP right.
3. Keep Markdown canonical and readable.
4. Make every module-selection decision inspectable.
5. Preserve existing `get_skill` behavior while adding a selective bundle API.
6. Measure and enforce context reduction against the pre-migration baseline.

## Non-goals

- Migrating every high-context skill in this PR.
- Automatically interpreting arbitrary natural-language `load_when` prose.
- Executing connectors, models, searches, or document parsing.
- Choosing legal tests, calculating deadlines, or making legal conclusions.
- Removing the complete attorney-review and verification obligations from the canonical skill package.

## Considered approaches

### A. Keep full skills and add more references

This is low risk but does not reduce the core context because the complete detailed workflow remains in `SKILL.md`.

### B. Parse `load_when` prose heuristically

This avoids a schema change but makes module selection unpredictable and difficult to test. Legal workflows should not depend on fuzzy parsing of authoring prose.

### C. Declarative activation plus compact core skills — selected

Detailed, conditionally useful procedures move into adjacent Markdown modules. Each module keeps human-readable `load_when` prose and gains an optional machine-readable `activation` object. A pure selector chooses modules from mode and supplied typed inputs. The returned bundle includes selection reasons and unresolved conditions.

This approach provides measurable context reduction, deterministic behavior, backward compatibility, and inspectable safety boundaries.

## Architecture

### Canonical files

Each migrated skill remains rooted at:

```text
skills/<area>/<skill>/SKILL.md
```

Detailed procedures live under:

```text
skills/<area>/<skill>/modules/*.md
```

`SKILL.md` retains the eight required sections and all universal rules:

- purpose and routing boundaries;
- required inputs and stop behavior;
- non-negotiable legal-safety rules;
- a concise workflow map;
- a concise output skeleton;
- an attorney-verification checklist that identifies the applicable modules.

A user can understand the workflow and safety model from the core file. The module files supply the detailed steps needed for a selected mode or fact pattern.

### Module activation schema

Existing module fields remain valid. A module may add:

```json
{
  "activation": {
    "modes": ["standard", "deep-review"],
    "input_id": "ip-rights-at-issue",
    "operator": "contains-any",
    "values": ["trademark"]
  }
}
```

Supported operators are deliberately small:

- `always`
- `present`
- `equals`
- `contains-any`

`modes` is always an allow-list. The input fields are optional for mode-only activation. Conditions are ANDed: the mode must match and, when present, the input condition must match.

Modules without `activation` preserve Phase 2A behavior: they are not auto-selected unless `required: true` or explicitly requested by ID.

### Input type extension

Add `string-list` as an allowed input type. It represents a list of controlled strings and may include an `items` allow-list. This supports matters involving more than one IP right without forcing an untyped object.

### Selector and bundle builder

A new standard-library module, `scripts/skill_context.py`, provides:

```python
select_modules(spec, mode, inputs, explicit_module_ids=None) -> dict
build_skill_context(root, spec, mode, inputs, explicit_module_ids=None) -> dict
```

The selector returns:

- selected module records;
- a reason for every selection;
- unresolved conditional modules when a required activation input is absent;
- rejected or unknown explicit module IDs as errors.

The bundle builder returns:

- compact core `SKILL.md` content;
- selected module contents;
- unresolved module conditions;
- missing required typed inputs;
- estimated core, module, and total tokens;
- the exact execution mode and normalized inputs used.

The selector never loads every conditional module merely because an input is missing. It fails closed and surfaces the unresolved condition.

### MCP surface

Add:

```text
get_skill_context(skill_id, mode="standard", inputs={}, module_ids=[])
```

`get_skill` remains unchanged and returns only the canonical core `SKILL.md`. `get_skill_spec` remains the contract inspection surface. The new tool is the recommended execution surface for modularized skills.

### Context scenarios and budgets

A custom spec may include `context_scenarios`:

```json
{
  "id": "standard-trademark",
  "mode": "standard",
  "inputs": {"ip-rights-at-issue": ["trademark"]},
  "baseline_estimated_tokens": 6115,
  "max_ratio": 0.70
}
```

The compiler validates unique IDs, known modes, object inputs, positive baselines, and ratios greater than zero. A new generated report measures each scenario and fails CI when a bundle exceeds its declared ratio.

## First migration targets

### Motion Opposition Drafter

Mode-based modules:

1. `modules/motion-deconstruction.md`
   - standard and deep-review;
   - argument mapping, authority inventory, and record mapping.
2. `modules/opposition-drafting.md`
   - standard and deep-review;
   - point-by-point draft discipline and the three-part output.
3. `modules/expanded-verification.md`
   - deep-review only;
   - the full filing-oriented verification checklist and weak-point review.

Quick triage loads the compact core only. Standard loads the first two modules. Deep review loads all three.

Context targets against the 6,346-token baseline:

- quick triage: at most 40%;
- standard: at most 75%;
- deep review: at most 110%.

### Infringement Triage

Mode- and input-based modules:

1. `modules/factor-method.md` — standard and deep-review.
2. `modules/trademark.md` — when the right list contains `trademark`.
3. `modules/copyright.md` — when it contains `copyright`.
4. `modules/patent.md` — when it contains `patent`.
5. `modules/trade-secret.md` — when it contains `trade-secret`.
6. `modules/defenses-routing-output.md` — standard and deep-review.
7. `modules/expanded-verification.md` — deep-review only.

Quick triage loads only the core. A standard single-right matter loads the common method, one right-specific module, and the routing/output module. A multi-right matter loads each applicable right module. Deep review adds the expanded verification module.

Context targets against the 6,115-token baseline:

- quick triage: at most 40%;
- each standard single-right scenario: at most 70%;
- deep review with all four rights: at most 115%.

## Safety and error handling

- Unknown mode: reject.
- Disabled mode: reject.
- Unknown explicit module ID: reject.
- Missing required typed input: report it and do not infer it.
- Missing activation input: report the conditional module as unresolved; do not load all candidates.
- Module path missing at compile or bundle time: reject.
- `required: true` module: load whenever its activation mode matches; if its input condition cannot be evaluated, mark unresolved and stop the bundle from claiming completeness.
- Legal deadline calculation remains prohibited.
- Every output remains attorney-review required.
- Extracted modules inherit the core skill's legal-safety rules and must begin with a draft-work-product scope note.

## Testing

1. Compiler tests for `string-list`, activation objects, and context scenarios.
2. Selector tests for mode-only, input-based, multi-value, explicit, unresolved, and invalid selections.
3. Repository tests confirming every module path resolves and only the two target skills use auto-activation initially.
4. MCP tests for selective bundles and transparent selection reasons.
5. Content-preservation tests for key safety phrases and workflow obligations across the core-plus-deep bundle.
6. Generated context-budget tests and CI drift checks.
7. Full existing validation, eval, plugin-sync, and site-build suites.

## Success criteria

- Both target core skills fall below the `large` context-pressure band.
- Quick and standard scenarios remain within declared ratios.
- Deep bundles preserve all material safety and workflow obligations.
- Module selection is deterministic and fully explained in the response.
- Existing non-modular skills and Phase 2A custom specs continue to compile unchanged.
- No runtime dependencies beyond the Python standard library are added.
