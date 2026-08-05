# Repository Validation

AgentCounsel ships a lightweight validation script, `scripts/validate_repo.py`, that checks the repository for structural and consistency problems. It uses only the Python standard library — no dependencies, no package manager, no build tooling.

## Running it

```
python scripts/check_all.py

# Or run the core generators individually:
python scripts/validate_repo.py
python scripts/build_skill_index.py --check
python scripts/build_skill_specs.py --check
python scripts/generate_selective_context_metrics.py --check
python scripts/build_platform_packs.py --check
```

Run it from anywhere; the script locates the repository root relative to its own location. It prints a report and exits with status `0` if all checks pass, or `1` if any error is found. Warnings are advisory and do not affect the exit code.

## What it checks

**Structure**

- The directories the library is organized around exist: `core/`, `skills/`, `adapters/`, `practice-profiles/`, `matter-workspaces/`, `overlays/`, `skills/setup/`, `skills/legal-methodology/`, and `skills/contracts/references/`.
- Every canonical skill folder under `skills/` contains a `SKILL.md`. A `references/` folder under a practice area is treated as shared reference material, not a skill.
- Every overlay folder under `overlays/` contains an `OVERLAY.md`. Folders whose name starts with `_` (such as `_template`) are scaffolding and are skipped.
- Every plugin skill folder under `adapters/claude-code-plugin/skills/` contains a `SKILL.md`.
- Every `SKILL.md` has valid YAML frontmatter (an opening and a closing `---`).
- Every `SKILL.md` frontmatter has a non-empty `name` and `description`.
- Every `SKILL.md` has an H1 title.
- Every canonical skill under `skills/` contains all eight required sections, in order: Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, Attorney Verification Checklist.

**Skill metadata**

- Every canonical skill under `skills/` declares valid standardized frontmatter — all eleven fields (`name`, `description`, `practice_area`, `task_type`, `jurisdictions`, `risk_level`, `requires_attorney_review`, `inputs`, `outputs`, `related_skills`, `tags`), each with the correct type.
- `description` is trigger-rich and begins with `Use when`; `practice_area` matches the directory area; `task_type` and `risk_level` use the allowed values; `related_skills` entries resolve to real skills. The full standard is in `docs/SKILL_METADATA_STANDARD.md`.
- `metadata/index.json` and `metadata/router.json` exist and match the canonical skills. If either is stale, run `python scripts/build_skill_index.py` to regenerate them.
- Normalized generated metadata has unique skill IDs, existing skill paths, valid risk levels, valid compatible-platform IDs, valid recommended quality-check IDs, and valid eval coverage statuses.
- Eval framework validation covers skill eval schemas, benchmark schemas, router eval schemas, static metadata/pack/router integrity evals, valid skill IDs, valid quality-check IDs, and current eval coverage reports.

**Safety and content**

- No file describes AgentCounsel as providing legal advice. Outputs must be described as draft legal work product for attorney review.
- Every `SKILL.md` references the source/citation discipline core rule (`core/source-and-citation-discipline.md`) or carries equivalent language against inventing legal authority or citations.
- Quality-layer docs and citation/source-validation skills must not imply that AgentCounsel independently verifies current law, guarantees citation correctness, or provides automated legal citation verification.
- No file contains the forbidden framing that this project is a ChatGPT Project instructions or package repository.
- No substantive file contains a leftover placeholder marker (such as a TODO or FIXME note, or lorem ipsum filler text).

**Links and paths**

- Every relative Markdown link resolves to a file that exists.
- Every skill path referenced in `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, and `COMMANDS.md` points to a real `SKILL.md`.
- Adapter index files point back to the canonical root files.
- `adapters/claude-code-plugin/plugin.json` is valid JSON and has `name`, `version`, and `description`.
- The distribution manifests (`adapters/claude-code-plugin/plugin.json`, `gemini-extension.json`, `site/package.json`) all declare a `version` matching the latest released version in `CHANGELOG.md`, so a release bump cannot silently drift.

**Plugin bundle**

- Every expected plugin skill is present — the eight curated skills plus the hand-maintained `legal-core`.
- Each curated plugin skill under `adapters/claude-code-plugin/skills/` matches its canonical source in `/skills`, including templates. If they differ, the validator reports drift; run `python scripts/sync_plugin_skills.py` to regenerate the bundle. See `PLUGIN_SYNC.md`.

**Typed contracts and selective context**

- `metadata/skill_specs.json` matches all canonical skills and preserves non-weakening Skill Specification v2 invariants.
- Every declared module path resolves inside the repository.
- Module activation uses only supported, validated operators and modes.
- `metadata/selective_context_metrics.json` and `reports/selective-context.md` are current.
- Every declared scenario supplies its required inputs, resolves required modules, and stays within its explicit context ratio.
- Bundle fingerprints and complete module-selection traces are deterministic.

**Platform pack registry**

- `metadata/packs.json` exists and matches `scripts/build_platform_packs.py`.
- Every pack manifest has a pack ID, platform, practice area or use case, included skills, included core rules, custom skill specs, selectable spec resources, quality checks, setup instructions, safety disclaimer, attorney-review requirements, version, and date.
- Every referenced skill, core rule, skill spec, spec resource, template, matter pack, matter-workspace template, and quality-check target exists.
- High-risk generated metadata must recommend the attorney-review gate and assumption audit; high-risk authority-heavy skills must also recommend citation integrity.
- Generated pack manifests preserve the draft-work-product and attorney-review posture.

**Warnings (advisory)**

- A canonical skill that is not listed in `SKILLS_INDEX.md`.
- An index file with no skill paths to validate.
- A plugin skill folder that is not part of the curated bundle or the maintained set.

**Typed matter plans**

- Every `matter-plans/*.json` file conforms to Matter Plan Specification v1 and references a real playbook or matter pack.
- Every skill node references a canonical skill, enabled execution mode, and valid target inputs.
- Dependencies are acyclic; artifact producers and handoffs are unambiguous; exactly one terminal attorney gate closes the graph; every final output is upstream of that gate.
- Missing inputs and attorney approvals fail closed, blocked nodes load no skill context, and declared graph-depth, width, ready-node, and context budgets are enforced.
- `metadata/matter_plans.json` and `reports/matter-plans.md` match the source plans.
- Sixteen lifecycle scenarios produce valid privacy-conscious receipts, and eight destructive mutations are detected by `scripts/evaluate_matter_plans.py`.
- Receipts exclude raw sensitive matter inputs and artifact paths, require complete nested inventories, and detect plan, source, contract, gate, state, lineage, resource-fingerprint, and arithmetic drift. They are integrity records, not digital signatures or identity attestations.

## What it does not check

The script validates structure and consistency — not legal accuracy. It cannot tell whether a skill's workflow is sound, whether its content is correct, or whether its legal framing is appropriate for a given matter. Substantive review by a qualified, licensed legal professional, together with each skill's Attorney Verification Checklist, remains essential. See `CONTRIBUTING.md` and the `core/` operating rules.

## When to run it

- Before opening or updating a pull request.
- After adding, renaming, or moving a skill, template, or adapter file.
- After editing a skill's frontmatter — then run `python scripts/build_skill_index.py` to regenerate `metadata/index.json` and `metadata/router.json` (see `docs/SKILL_METADATA_STANDARD.md`).
- After changing a `SPEC.json`, module, or modularized core, run `python scripts/build_skill_specs.py`, `python scripts/generate_selective_context_metrics.py`, and `python scripts/build_platform_packs.py`.
- After changing platform pack inputs, run `python scripts/build_platform_packs.py` to regenerate `metadata/packs.json` and `dist/` locally.
- After editing `SKILLS_INDEX.md` or `WORKFLOW_ROUTER.md`.
- After running `python scripts/sync_plugin_skills.py` to regenerate the plugin bundle (see `PLUGIN_SYNC.md`).

## Companion: legal-prose pass

`scripts/check_legal_prose.py` is a separate, conservative quality pass over the
repository-owned work-product samples (`examples/` outputs and `evals/outputs/`).
It checks form and safety framing only — not legal accuracy. It **fails the
build** on legal-advice or false-certainty framing (for example "this clause is
enforceable", "there is no risk", "you must sign") and on any work-product
sample missing visible attorney-review framing; it **warns** (advisory) on
generic AI "slop" and vague prose, which fail only under `--strict`. CI runs it
in its default (non-strict) mode. See [`docs/CLI.md`](docs/CLI.md) for details.

## Note

`scripts/validate_repo.py` and this file (`VALIDATION.md`) are excluded from the forbidden-phrase scans, because they necessarily describe the phrases being checked for.

Generated build output is not validated as repository source: the scan skips `dist/` (platform install packs from `scripts/build_platform_packs.py`) and `node_modules/`. `scripts/build_platform_packs.py` performs its own build-time validation of the packs it generates.
