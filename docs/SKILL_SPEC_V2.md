# AgentCounsel Skill Specification v2

Skill Specification v2 adds a typed execution contract to AgentCounsel without replacing the existing Markdown skill format.

Every canonical skill continues to use:

```text
skills/<practice-area>/<skill-slug>/SKILL.md
```

A skill may also include:

```text
skills/<practice-area>/<skill-slug>/SPEC.json
```

`SKILL.md` remains the canonical human-readable workflow. `SPEC.json` is an optional, canonical overlay for fields that benefit from explicit types, stable IDs, execution modes, safety gates, evidence requirements, and selective module loading.

The generated registry is:

```text
metadata/skill_specs.json
```

Do not edit that file by hand.

## Phase 2A coverage

The current registry contains typed execution contracts for all **212 canonical skills**. Of those, **209** use safe contracts compiled entirely from their existing Markdown metadata and **three** use reviewed custom sidecars:

- `contracts/nda-review`
- `legal-research/legal-research-memo`
- `privacy/breach-response-workflow`

No existing `SKILL.md` body was changed to establish this foundation. Future sidecars should be added incrementally in risk- and usage-priority order.

## Why a JSON sidecar

AgentCounsel's YAML frontmatter deliberately supports only top-level scalars and lists. That keeps the library portable and parseable with the Python standard library. Typed inputs, nested gates, evidence records, and mode-specific behavior require a deeper structure, so v2 uses JSON rather than expanding the frontmatter parser or adding a YAML dependency.

## Backward compatibility

A custom sidecar is not required. `scripts/build_skill_specs.py` compiles every existing skill into a safe v2 contract using:

- the eleven existing frontmatter fields;
- derived jurisdiction and deadline gates;
- the generated quality-check mapping;
- conservative input and output type inference;
- baseline inheritance, evidence, and attorney-review controls.

A sidecar enriches those defaults. It does not replace the skill wholesale.

## Baseline controls that cannot be weakened

Every compiled contract inherits:

- `core/legal-work-product.md`
- `core/source-and-citation-discipline.md`
- `core/output-format-rules.md`
- `core/attorney-review-checklist.md`

`core/jurisdiction-and-deadline-gates.md` is added whenever jurisdiction or deadline handling is required.

A custom sidecar cannot:

- make attorney review optional;
- continue substantive work when required inputs are missing;
- permit the agent to calculate a legal deadline;
- allow a required legal input to be inferred;
- remove baseline evidence fields;
- remove baseline inherited safety rules;
- make an output artifact exempt from attorney review.

The compiler rejects any sidecar that attempts these changes.

## Compiled contract fields

### `schema_version`

Always `2.0`.

### `skill_id`

The stable `<practice-area>/<skill-slug>` ID. When included in a sidecar, it must match the directory.

### `inherits`

Additional repository files whose rules apply to the skill. A sidecar adds to the baseline inheritance set; it cannot subtract from it.

### `gates`

Normalized execution boundaries:

- `missing_inputs.behavior` is always `stop-and-ask`.
- `attorney_review.required` is always `true` for current skills.
- `jurisdiction.required` indicates whether jurisdiction must be confirmed.
- `deadline.required` indicates whether dates or clocks require attention.
- `deadline.calculation_allowed` is always `false`.
- `escalation.minimum` reflects the skill's risk.
- `custom` contains skill-specific gates.

Custom gate actions are:

- `flag`
- `stop-and-ask`
- `stop-and-escalate`
- `require-attorney-confirmation`

Each custom gate needs a stable ID, an observable condition, an action, and a reason.

### `execution_modes`

Every compiled contract contains:

| Mode | Purpose |
|---|---|
| `quick-triage` | Confirm applicability, missing inputs, top issues, and escalation without generating the full work product. |
| `standard` | Produce the normal attorney-ready draft. |
| `deep-review` | Load applicable modules and run expanded completeness and verification checks. |

A sidecar may disable a mode when the limited mode would be unsafe. It must still retain all three mode records so consumers can distinguish “unsupported” from “unknown.”

### `input_schema`

Each input has:

- `id`
- `label`
- `type`
- `required`
- `description`
- `source_requirement`
- `may_infer`
- `sensitive`
- optional `enum` values

Allowed types:

```text
text, document, document-set, enum, date, datetime, boolean,
integer, number, jurisdiction, object, string-list
```

Required inputs must set `may_infer` to `false`.

`string-list` represents one or more strings. A sidecar may add an `items`
allow-list when the values are controlled, such as the IP rights
`trademark`, `copyright`, `patent`, and `trade-secret`. The compiler rejects
empty values and values that collide after whitespace trimming and
case-insensitive normalization. Runtime inputs use the allow-list's canonical
spelling. Numeric runtime inputs must also be finite, and `object` inputs must
contain only JSON-compatible values with string keys so bundle hashes remain
portable and reproducible.

To refine a legacy input, use the generated stable input ID. To add a new input, provide every required field.

### `output_schema`

Each output artifact has:

- `id`
- `label`
- `type`
- `required`
- `description`
- `attorney_review_required`

Allowed types:

```text
section, table, checklist, memo, letter, tracker, timeline,
matrix, structured-data
```

Every current output artifact requires attorney review.

### `evidence_schema`

All skills use a claim-support record. Baseline required fields are:

- `claim_id`
- `source_document_id`
- `locator`
- `support_type`
- `verification_status`

A sidecar may require additional fields such as `support_text`, `authority_status`, or `fact_as_of`. It cannot remove baseline fields.

### `modules`

Modules identify context that should be loaded only when relevant. They do not execute code.

Allowed kinds:

- `reference`
- `template`
- `profile`
- `connector`
- `quality-check`
- `workflow-module`

Every module path must resolve to an existing repository file. `load_when` must state the condition or mode that justifies loading it.

A module may also declare a machine-readable `activation` object. This is the
deterministic counterpart to the human-readable `load_when` field:

```json
{
  "modes": ["standard", "deep-review"],
  "input_id": "ip-rights-at-issue",
  "operator": "contains-any",
  "values": ["trademark"]
}
```

The supported operators are deliberately limited:

| Operator | Required fields | Meaning |
|---|---|---|
| `always` | `modes` | Load whenever the requested mode is allowed. |
| `present` | `modes`, `input_id` | Load when the supplied input is present and non-empty. |
| `equals` | `modes`, `input_id`, `value` | Load when the normalized scalar input equals the declared value. |
| `contains-any` | `modes`, `input_id`, `values` | Load when a normalized scalar or list input contains at least one declared value. |

Mode and input conditions are ANDed. Modules without `activation` retain the
Phase 2A behavior: they are not automatically selected unless they are marked
`required` or a client explicitly asks for their ID. Missing activation inputs
fail closed. The selector reports the unresolved condition instead of loading
every candidate module.

### `context_scenarios`

A custom sidecar may declare deterministic scenarios used to measure and
enforce selective-context budgets:

```json
{
  "id": "standard-trademark",
  "mode": "standard",
  "inputs": {"ip-rights-at-issue": ["trademark"]},
  "baseline_estimated_tokens": 6115,
  "max_ratio": 0.7
}
```

Scenario IDs must be unique, modes must be known, inputs must refer to declared
input IDs, baselines must be positive integers, and ratios must be positive
and finite. Repository tooling builds the exact context bundle for each
scenario and fails
validation when a bundle is incomplete or exceeds its declared ratio. These
estimates measure repository text size; they do not claim a provider-specific
token bill or latency reduction.

### `quality_checks`

Additional quality-check IDs appended to the generated baseline checks. Mode-specific checks belong on the corresponding execution mode.

## Authoring workflow

1. Start from `docs/templates/SPEC_TEMPLATE.json`.
2. Set `skill_id` to the exact directory-derived ID.
3. Add only fields that genuinely need refinement; inherited legacy records remain available automatically.
4. Use stable IDs. When overriding an inferred input or output, copy its ID from `metadata/skill_specs.json`.
5. Declare only repository paths that already exist.
6. Keep required legal inputs non-inferable.
7. Use gates for observable stop, escalation, or confirmation boundaries—not for legal conclusions.
8. Use declarative module activation only for inputs and modes that can be
   evaluated without legal judgment or fuzzy prose interpretation.
9. Add context scenarios for every materially different activation path and
   keep their budgets conservative enough to catch accidental context growth.
10. Regenerate and validate:

```bash
python scripts/build_skill_specs.py
python scripts/build_skill_specs.py --check
python scripts/generate_selective_context_metrics.py --check
python -m unittest tests.test_skill_spec_v2 tests.test_build_skill_specs tests.test_real_skill_specs -v
python scripts/check_all.py
```

## Migration strategy

Phase 2A compiles all legacy skills and provides three reviewed pilots:

- `contracts/nda-review`
- `legal-research/legal-research-memo`
- `privacy/breach-response-workflow`

Additional skills should be migrated in risk- and usage-priority order. A sidecar should be added when it materially improves at least one of:

- input validation;
- output consistency;
- safety gating;
- evidence traceability;
- execution-mode behavior;
- selective context loading.

Do not create sidecars merely to duplicate frontmatter in a second format.

## Generated JSON Schema

`specs/skill-spec-v2.schema.json` documents the compiled contract's structural shape. Repository validation in `scripts/skill_spec_v2.py` is authoritative for cross-field and non-weakening safety rules that JSON Schema alone cannot express.
