# Implementation Sequence

This sequence consolidates related work into small PRs that extend the current
AgentCounsel systems instead of replacing them.

> **Note:** the original platform sequence is largely complete. PRs 2, 3, 5, and 6 shipped; the broader registry and connector registry remain partially open. A second execution-contract sequence also shipped: Phase 2A compiled typed contracts for all skills, and Phase 2B added deterministic selective modules, context bundles, decision traces, and budget gates.

## PR 1: Generated Platform Registry

Create a generated platform registry that exposes the systems AgentCounsel
already has.

Affected files:

- `scripts/build_skill_index.py` or a new `scripts/build_platform_registry.py`
- `metadata/index.json`
- new `metadata/platform.json`
- `docs/SKILL_METADATA_STANDARD.md`
- `VALIDATION.md`

Scope:

- Keep `skills/` frontmatter as the source of truth for skills.
- Generate records for skills, matter packs, matter workspaces, practice
  profiles, connectors, adapters, and eval coverage.
- Include stable IDs, paths, titles, category, platform surfaces, and validation
  status where available.
- Add validation that generated metadata is current.

Borrowing inputs:

- Use `anthropics/knowledge-work-plugins` and `mukul975/Anthropic-Cybersecurity-Skills`
  as license-compatible references for registry and pack thinking.
- Use no copied text or schemas unless separately attributed.

## PR 2: Router And Pack Manifest Improvements

Status: shipped — `metadata/router.json` and `metadata/packs.json` are
generated and checked in.

Make routing and pack outputs easier for agents and platforms to consume.

Affected files:

- `scripts/build_platform_packs.py`
- `scripts/build_skill_index.py` or `scripts/build_platform_registry.py`
- `metadata/router.json`
- `metadata/packs.json`
- `site/generate.mjs`
- `adapters/`

Scope:

- Generate `metadata/router.json` from existing frontmatter and `COMMANDS.md`.
- Generate a pack manifest with platform, practice area, included skills,
  output file names, checksums, and source paths.
- Add a thin Cursor-specific generated artifact only if the required format can
  be implemented from public facts or license-compatible sources.
- Keep ChatGPT, Claude, Gemini, Codex, and generic Markdown packs generated
  from canonical source files.

Borrowing inputs:

- Use `humanlayer/12-factor-agents` for high-level agent design principles.
- Treat `cursor/plugins` as inspiration only unless its license changes or
  Cursor publishes reusable specs under clear terms.

## PR 3: Legal Prose And Citation Quality Checks

Status: shipped — `scripts/check_legal_prose.py` exists and covers the scope
below.

Add automated quality checks for repository-owned outputs without introducing a
model dependency.

Affected files:

- new `scripts/check_legal_prose.py`
- `scripts/run_evals.py`
- `evals/shared/assertions.md`
- `evals/outputs/`
- `VALIDATION.md`
- `.github/workflows/validate.yml`

Scope:

- Check generated examples and eval candidate outputs for attorney-review
  framing, overclaiming, fake citation patterns, unresolved citation claims,
  vague AI-style phrasing, and missing uncertainty flags.
- Integrate with existing eval output checks.
- Keep the first version heuristic and stdlib-only.

Borrowing inputs:

- Use `hardikpandya/stop-slop` as MIT-licensed inspiration for prose-quality
  categories, but write AgentCounsel-specific legal checks independently.
- Use `harveyai/harvey-labs` as MIT-licensed inspiration for legal benchmark
  discipline, not as a source of copied eval content.

## PR 4: Connector And Source-Validation Registry

Turn connector documentation into a machine-readable source map while keeping
connectors documentation-only.

Affected files:

- `connectors/README.md`
- `connectors/*.md`
- new `metadata/connectors.json`
- `scripts/validate_repo.py`
- `skills/legal-methodology/source-validation/SKILL.md`
- `site/generate.mjs`

Scope:

- Add a consistent metadata header or parseable table for each connector.
- Generate connector records for source, coverage, license/access model, query
  surfaces, and fallback behavior.
- Validate connector docs against the connector contract.
- Surface connectors in the site and in source-validation guidance.

Borrowing inputs:

- Use `public-api-lists/public-api-lists` for permissively licensed API-list
  organization patterns.
- Use `LearningCircuit/local-deep-research` and `mvanhorn/last30days-skill`
  as inspiration for research-source workflows, without copying search logic or
  prompt text.

## PR 5: Review Panels And Workspace Validation

Status: shipped — landed as the top-level `review-panels/` directory and
`docs/REVIEW_PANELS.md` rather than the `core/legal-review-panel.md` file
proposed below.

Make attorney review state more structured across skills, matter workspaces,
and evals.

Affected files:

- new `core/legal-review-panel.md`
- high-risk `skills/**/SKILL.md` where a review panel materially improves the
  output
- `matter-workspaces/*.md`
- `scripts/validate_repo.py`
- `evals/shared/assertions.md`

Scope:

- Define a reusable review-panel pattern: status, reviewer, unresolved
  authority, unresolved facts, deadlines, privilege/confidentiality, source
  checks, and sign-off state.
- Add the pattern first to high-risk and critical skills, then expand only
  where it improves reviewability.
- Validate that high-risk skills either use the panel or explain why their
  existing Attorney Verification Checklist is sufficient.

Borrowing inputs:

- Use `AnttiHero/lavern`, `prowler-cloud/prowler`, and `OpenBMB/ChatDev` as
  inspiration for human gates, evidence-backed checks, and review loops.
- Do not import multi-agent debate machinery into the core Markdown library.

## PR 6: Optional Local App Path Design

Status: shipped — landed as `docs/LOCAL_PLATFORM_PATH.md` rather than the
`docs/LOCAL_APP_PATH.md` file proposed below.

Design, but do not immediately build, an optional local/self-hosted app that
consumes the generated registry and Markdown library.

Affected files:

- new `docs/LOCAL_APP_PATH.md`
- `docs/PLATFORM_GAP_ANALYSIS.md`
- optional prototype under a future app directory only after design approval

Scope:

- Keep the core repository usable as plain Markdown.
- Define app boundaries: local file ingestion, registry consumption, offline
  storage, matter workspace editing, review panels, and connector launch links.
- Decide whether the app belongs in this repository or a separate companion
  repo before implementation.

Borrowing inputs:

- Use `localForage/localForage`, `mudler/LocalAI`, `iOfficeAI/AionUi`,
  `zakirullin/files.md`, and `awesome-selfhosted/awesome-selfhosted` as
  references for optional local/offline/self-hosted paths.
- Treat GPL/AGPL and share-alike sources as inspiration only.

## Churn Controls

- Do not duplicate canonical skill content in new registries or adapters.
- Prefer generated JSON manifests over hand-maintained parallel indexes.
- Keep scripts standard-library-only unless a PR explicitly introduces an
  optional app package with its own dependency boundary.
- Add validation in the same PR that introduces a new generated artifact.
- Update `NOTICE` only when external code, prose, schemas, prompts, templates,
  examples, or eval content is copied or closely adapted.

## Phase 2 Execution Contracts

### Phase 2A: Typed contract foundation

Status: shipped. Every canonical skill compiles to Skill Specification v2, and custom sidecars may add exact types, modes, gates, modules, and quality checks without weakening inherited safety invariants.

### Phase 2B: Deterministic selective context

Status: shipped in v0.3.0. The two former large-context skills were decomposed into compact cores and Markdown modules. Selection is declarative, fail-closed, and fully traced. The MCP catalog returns reproducible bundles, generated scorecards enforce nine context scenarios in CI, and platform packs preserve every custom contract and selectable resource.

Next candidates should be chosen from generated context and health metrics, not from file size alone. A future migration should require a concrete scenario matrix, content-preservation tests, and measurable routine-context reduction before splitting another skill.

## Phase 3: Typed Matter Graphs

Status: shipped in v0.4.0. Four recurring legal matters now compile from declarative JSON sidecars into validated directed acyclic graphs. Skill nodes reference canonical Skill Specification v2 contracts; attorney-review gates are explicit graph nodes; artifacts have typed producers and consumers; conditions fail closed; and only the current ready wave loads selective skill context.

The first pilots cover legal research memos, commercial contract review, litigation motion opposition, and privacy incident response. Together they contain 34 nodes, 23 skill nodes, 11 attorney gates, and 23 typed artifacts. Sixteen lifecycle scenarios and eight destructive mutations enforce state transitions, gate integrity, artifact lineage, receipt privacy, and budget arithmetic in CI.

The next platform phase should attach claim-to-evidence ledgers to matter-plan artifacts. That work should map draft claims to supplied sources and verification status without turning graph validity into a claim of substantive legal correctness.
