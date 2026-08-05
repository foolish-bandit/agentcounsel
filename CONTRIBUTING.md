# Contributing to AgentCounsel

Thank you for helping build AgentCounsel. The library is useful only if it stays consistent, safe, and easy for legal professionals to read. These rules keep it that way.

## Principles

AgentCounsel is **Markdown-first** and **safety-first**. Contributions are evaluated against the core rules in `core/` and the requirements below.

## What we accept

- New skills for legal workflows not yet covered.
- Improvements to existing skills and templates.
- Better templates, clearer wording, and structural fixes.
- Typed `SPEC.json` overlays that materially improve validation, gating, evidence traceability, or selective context loading.
- Typed matter plans for reviewed recurring matters with explicit handoffs, gates, scenarios, and privacy boundaries.
- Adapter improvements that keep adapters thin.

## Hard requirements for every skill

A skill will not be merged unless it meets all of these.

1. **Markdown-first.** A skill is a canonical `SKILL.md` file plus optional Markdown templates and references. It may also include a declarative `SPEC.json` execution-contract overlay. No skill-local scripts, package managers, build steps, or runtime.
2. **Follows the standard structure.** `SKILL.md` carries the standardized YAML frontmatter — all eleven fields defined in `docs/SKILL_METADATA_STANDARD.md` — and these sections, in order: Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, Attorney Verification Checklist.
3. **Includes an Attorney Verification Checklist.** Every skill ends with a checklist of items a supervising attorney must confirm.
4. **Preserves confidentiality.** The skill follows `core/confidentiality-and-privilege.md`. Templates and examples use fictional placeholders only — never real client facts, names, or data.
5. **No fake citations.** No invented or unverifiable cases, statutes, regulations, citations, quotations, dates, or deadlines — anywhere, including examples. See `core/source-and-citation-discipline.md`.
6. **No jurisdiction-specific legal claims unless cited and scoped.** Skills supply workflow and structure, not the law. If a contribution states a legal rule, it must cite verifiable authority and clearly state the jurisdiction and date it applies to. Prefer to frame such points as attorney-verification items.
7. **No legal-advice language.** Do not tell users what they "must" do or what "is legal." Use the "draft legal work product for attorney review" framing throughout.
8. **No hidden tool behavior.** A skill must do exactly what it says. No instructions that cause an agent to take actions the user would not expect (sending data, calling tools, fetching URLs) beyond the stated workflow.
9. **No weakened typed safeguards.** A `SPEC.json` may strengthen or clarify controls, but may not make attorney review optional, infer required legal inputs, continue through missing required inputs, calculate a deadline, remove baseline evidence fields, or remove inherited core safety rules.
10. **No unnecessary scripts.** Do not add skill-local code, package managers, or build systems. Repository tooling changes should be proposed and tested separately.

## Style

- Clean, plain Markdown and JSON. Professional and clear; no hype.
- Never imply the library or an agent replaces a lawyer.
- Keep adapters thin — they point to canonical skills and generated metadata, they do not duplicate them.
- Match the depth and tone of existing skills (`skills/contracts/nda-review/SKILL.md` is a good reference).

## How to contribute

1. Open an issue using the appropriate template — **bug report**, **skill request**, or **skill improvement** — so scope and naming can be agreed. The templates live in `.github/ISSUE_TEMPLATE/`.
2. Create the skill folder under the right practice area in `skills/`, with `SKILL.md` and any `templates/`. Start from [`docs/templates/SKILL_TEMPLATE.md`](docs/templates/SKILL_TEMPLATE.md), a fill-in-the-blanks scaffold with the full frontmatter and section set.
3. Add a `SPEC.json` only when explicit types, execution modes, gates, evidence fields, or module-loading rules materially improve the workflow. Start from [`docs/templates/SPEC_TEMPLATE.json`](docs/templates/SPEC_TEMPLATE.json) and follow [`docs/SKILL_SPEC_V2.md`](docs/SKILL_SPEC_V2.md). Do not create a sidecar merely to duplicate frontmatter.
4. Add the skill to `SKILLS_INDEX.md` and, where relevant, `WORKFLOW_ROUTER.md`.
5. Re-read the `core/` rules and self-check against the hard requirements above.
6. If you changed a skill that is part of the Claude Code plugin bundle, run `python scripts/sync_plugin_skills.py`. See `PLUGIN_SYNC.md`.
7. Run `python scripts/build_skill_index.py` and `python scripts/build_skill_specs.py` to regenerate discovery metadata and typed contracts, then run `python scripts/validate_repo.py`. See `VALIDATION.md`, `docs/SKILL_METADATA_STANDARD.md`, and `docs/SKILL_SPEC_V2.md`.
8. Note any user-facing change under "Unreleased" in `CHANGELOG.md`.
9. Open a pull request and complete the checklist in the pull request template.

## Adding other artifacts

The library is more than skills. Each artifact type has a home and a regeneration step. After any change, run the validation sequence below and commit any regenerated files. Per-script detail is in [`docs/CLI.md`](docs/CLI.md); the commands to run after each kind of edit are in [`docs/AGENT_COMMANDS.md`](docs/AGENT_COMMANDS.md).

- **Metadata.** Do not hand-edit `metadata/index.json`, `metadata/router.json`, `metadata/skill_specs.json`, `metadata/matter_plans.json`, `metadata/matter_plan_evals.json`, or `metadata/packs.json` — they are generated. Edit a skill's YAML frontmatter and optional `SPEC.json`, then run `python scripts/build_skill_index.py`, `python scripts/build_skill_specs.py`, and `python scripts/build_platform_packs.py`.
- **Typed skill contract.** `SPEC.json` is an optional declarative overlay beside `SKILL.md`. All legacy skills compile safely without one. Use a sidecar only to refine types, modes, gates, evidence requirements, modules, or quality checks. The compiler in `scripts/skill_spec_v2.py` rejects weakened safety controls and unresolved module paths.
- **Quality check.** Quality checks are skills under `skills/legal-methodology/` following the same eight-section structure. Register a new one in `build_skill_index.py`'s quality-check map and `build_platform_packs.py` so it is recognized, and add it to the recommended checks of the skills that need it.
- **Eval.** Add a `*.eval.yaml` under `evals/skills/` (one per skill, filename matching the skill slug), `evals/router/`, or `evals/static/`, following the schema in `evals/README.md`. Run `python scripts/check_evals.py`, then `python scripts/run_evals.py --strict --quiet`, then `python scripts/generate_eval_report.py` to refresh `reports/eval-coverage.md`.
- **Playbook.** Add a `playbooks/<task>.md` with the twelve required sections in order (see `docs/PLAYBOOKS.md`), ending in the Final Attorney-Review Gate. Reference real skill paths and `skills/legal-methodology/` quality checks.
- **Matter plan.** Add `matter-plans/<plan-id>.json` only for a recurring matter with reviewed human guidance in a playbook or matter pack. Follow `matter-plans/README.md` and Matter Plan Specification v1. Every plan must be acyclic, end behind an explicit attorney gate, declare one producer per artifact, fail closed on missing inputs and approvals, and include lifecycle scenarios plus destructive mutation coverage. Never put client facts or draft contents in a plan file. Run `python scripts/build_matter_plans.py` and `python scripts/evaluate_matter_plans.py`.
- **Review panel.** Add a `review-panels/<panel>.md` with the ten required sections (see `docs/REVIEW_PANELS.md`). State clearly that review passes are review passes — not autonomous agents and not lawyers.
- **Pack.** Packs are generated, not hand-written. Adding skills, playbooks, or review panels that reference a practice area automatically flows into that area's pack; run `python scripts/build_platform_packs.py` and commit `metadata/packs.json`.

`validate_repo.py` enforces the required sections, link resolution, and classification-vocabulary alignment for these artifacts. `build_skill_specs.py --check` validates every custom sidecar, compiles every legacy skill, and detects typed-registry drift.

## Validation commands

A contribution is not done until these pass (CI runs the same set):

```text
python scripts/validate_repo.py
python scripts/build_skill_index.py --check
python scripts/build_skill_specs.py --check
python scripts/generate_selective_context_metrics.py --check
python scripts/build_matter_plans.py --check
python scripts/evaluate_matter_plans.py --check
python scripts/build_platform_packs.py --check
python scripts/generate_context_metrics.py --check
python scripts/generate_skill_health_report.py --check
python scripts/check_evals.py
python scripts/run_evals.py --strict --quiet
python scripts/generate_eval_report.py --check
python scripts/sync_plugin_skills.py --check
python scripts/generate_skill_improvement_prompts.py --check
python scripts/generate_cold_start_interviews.py --check
node site/generate.mjs
```

If a `--check` reports a file is out of date, run the same script without `--check`, commit the regenerated file, and re-run.

## Legal safety requirements

Every contribution, in every file including examples and `SPEC.json`, must:

- Frame output as **draft legal work product for attorney review** — never legal advice, never an "AI lawyer," never a final answer.
- Never invent or cite unverifiable authority, and never compute a deadline.
- Identify jurisdiction, governing law, posture, and the relevant date — or flag them unknown with a visible placeholder.
- Preserve confidentiality and privilege; use fictional examples only.
- Keep required legal inputs non-inferable and source-attributed.

These come from `core/` and are not negotiable.

## Third-party attribution and license rules

- Do **not** copy code, prompts, schemas, examples, or prose from another project unless its license is compatible with MIT redistribution. Prefer borrowing structure, patterns, and ideas over text.
- Do **not** use GPL- or AGPL-licensed material unless the project owner has explicitly changed the license strategy.
- If you directly adapt anything from a permissively licensed source, record the attribution per [`docs/THIRD_PARTY_ATTRIBUTION_POLICY.md`](docs/THIRD_PARTY_ATTRIBUTION_POLICY.md) and preserve it in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md).

## Reviews

Maintainers review contributions for safety, structure, accuracy of framing, typed-contract integrity, and consistency. Expect feedback focused on the safety rules — they are not negotiable. Security concerns are handled per `SECURITY.md`.

## License

By contributing, you agree that your contributions are licensed under the repository's MIT License. If a contribution adapts content from another project, keep that project's license compatible with MIT redistribution and preserve its attribution in `THIRD_PARTY_NOTICES.md`.
