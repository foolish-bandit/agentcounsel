# AgentCounsel v0.3.0: Deterministic Selective Context

**Release date:** 2026-08-04
**License:** MIT

> AgentCounsel produces **draft legal work product for attorney review**. It does not provide legal advice, replace a licensed attorney, or create an attorney-client relationship.

AgentCounsel v0.3.0 turns the Markdown library into a more precise execution substrate without making a runtime mandatory. All 212 canonical skills now have validated typed contracts. Clients that use the optional MCP catalog can retrieve the narrowest applicable context bundle, understand exactly why each module was or was not selected, and reproduce the bundle from its content fingerprint.

## Highlights

### Deterministic selective context

Skill Specification v2 now supports:

- controlled `string-list` inputs;
- machine-readable module activation by mode and typed input;
- `always`, `present`, `equals`, and `contains-any` operators;
- fail-closed behavior when activation inputs are missing;
- scenario-specific context budgets; and
- non-weakening validation that preserves attorney review, source discipline, evidence requirements, and the prohibition on deadline calculation.

The new `get_skill_context` MCP tool returns the canonical core plus only the selected modules. It includes normalized inputs, missing required inputs, unresolved conditions, token-planning estimates, per-file hashes, inherited-rule dependency hashes, a compiled-contract `contract_sha256`, a complete module-selection trace, and a deterministic `bundle_sha256`.

### Two flagship skills modularized

The two skills that previously exceeded the repository's large-context threshold were decomposed without weakening their deep-review obligations:

- **Motion Opposition Drafter:** quick triage loads the compact core; standard adds motion deconstruction and opposition drafting; deep review adds the expanded verification module.
- **Infringement Triage:** standard and deep modes load common factor and output modules, then only the right-specific modules implicated by trademark, copyright, patent, or trade secret inputs. Multi-right matters load multiple modules in stable order.

Measured against the pre-migration baselines:

| Workflow | Scenario | Estimated context ratio |
|---|---|---:|
| Infringement Triage | quick triage | 34.8% |
| Infringement Triage | standard, single right | 58.0% to 58.3% |
| Infringement Triage | deep, all rights | 89.1% |
| Motion Opposition Drafter | quick triage | 38.0% |
| Motion Opposition Drafter | standard | 58.5% |
| Motion Opposition Drafter | deep review | 70.0% |

These are deterministic one-token-per-four-characters planning estimates. They are not provider token counts, latency measurements, or billing claims.

### Context budgets are now release gates

Nine generated scenarios are checked on every CI run. A scenario fails when it is incomplete, leaves a required module unresolved, or exceeds its declared ratio. The machine-readable results live in `metadata/selective_context_metrics.json`; the human scorecard lives in `reports/selective-context.md`.

### Platform packs preserve modular resources

ChatGPT, Claude, Gemini, and repo-agent distributions now include custom typed contracts and every resource those contracts may select. Claude ZIP packs use unique flattened filenames for safe Project uploads. Consolidated ChatGPT and Gemini packs explain that logical selection does not physically remove already-uploaded content; true prompt-size reduction requires MCP or another client that sends only the selected bundle.

### Complete decision traces

Every declared module receives one deterministic status: `selected`, `not-selected`, or `unresolved`, with a human-readable reason. This makes omissions visible. The bundle fingerprint incorporates the complete compiled-contract fingerprint and inherited-rule hashes, so contract, global-rule, or routing changes remain distinguishable even when the selected Markdown content does not change.

### Complete catalog execution packages

Custom-spec skill pages now show the typed contract, every module's activation rule, and the underlying Markdown resources. **Copy Core Skill** preserves the compact quick-triage path; **Copy Full Package** produces a portable all-resource package for standard or deep work; **Copy One-Off Prompt** includes the complete package automatically. Ordinary skills retain the simpler one-file experience. The catalog states plainly that the portable full package is complete but not context-minimal; exact prompt-size reduction still requires `get_skill_context` or an equivalent selective client.

## Repository state

- 212 canonical skills across 20 substantive practice areas and three cross-cutting groups.
- 5 reviewed custom Skill Specification v2 sidecars.
- 2 physically modularized flagship skills.
- 9 selective-context scenarios, all complete and within budget.
- 587 skill eval cases, 18 benchmark cases, 31 router cases, and 14 static cases.
- 287 generated HTML pages plus `llms.txt` and `llms-full.txt`.
- No new runtime dependency in the context engine or generators. The optional MCP adapter remains the only third-party Python dependency.

## Safety properties preserved

- Every output remains draft legal work product requiring attorney review.
- Required legal inputs are not inferred.
- Missing module activation inputs fail closed.
- Legal authority, quotations, facts, and deadlines must not be invented.
- Deadline calculation remains prohibited.
- Deep bundles preserve the material workflow and verification obligations extracted from the former monolithic skills.
- Context fingerprints support audit and replay; they do not certify legal correctness or attorney approval.

## Validation

The release gate is:

```bash
python scripts/check_all.py
```

It validates plugin synchronization, repository structure, the complete unit suite, generated skill and contract registries, selective-context budgets, platform packs, context and health reports, all eval schemas and required candidates, legal-prose safety checks, generated reports, and the static site.

## Open-source research

The architecture was independently implemented after reviewing progressive disclosure and context-selection patterns from Anthropic Skills, LangChain context engineering and Bigtool, the MCP resource/tool separation, OpenAI Agents SDK tracing, Promptfoo's declarative eval discipline, and Microsoft agent-framework interoperability. No source code, prompt text, schema, or examples from those projects were copied. The research classification is recorded in `docs/OSS_BORROWING_MAP.md`.

## Upgrade notes

Existing plain-Markdown workflows continue to work. Existing Phase 2A specs compile unchanged. MCP clients may adopt `get_skill_context` incrementally. Pack builders should regenerate artifacts because the pack manifest schema is now 1.1 and includes custom specs and selectable resources.
