# Context

A vocabulary and mental-model reference for AI agents and LLMs working in the AgentCounsel repository. Read it alongside `README.md` and the `core/` rules. The terms below have specific meanings here — use them precisely.

## Language

- **Skill** — a single, standalone legal workflow. Each skill is one folder at `skills/<practice-area>/<skill-name>/` containing a `SKILL.md` and an optional `templates/` directory. _Avoid_ calling a skill a "prompt," a "command," an "agent," or a "tool."
- **`SKILL.md`** — the file that defines a skill: YAML frontmatter (`name`, `description`) followed by eight H2 sections in a fixed order — Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, Attorney Verification Checklist. Every skill is exactly one `SKILL.md`.
- **Practice area** — the top-level grouping of skills under `skills/` (for example `litigation`, `contracts`, `corporate`). _Avoid_ "category," "module," or "package."
- **Core rules** — the seven files in `core/`. They are the operating rules every skill inherits; they are not configuration. Read them before reasoning about any skill.
- **Template** — a copyable, attorney-review-ready Markdown file under a skill's `templates/`. A template is a deliverable scaffold, not a skill.
- **Adapter** — a thin integration file under `adapters/`. An adapter tells one environment how to use the library; it does not contain the library.
- **Canonical** — `skills/` and `core/` are the single source of truth. _Avoid_ treating any copy as authoritative.
- **Plugin bundle** — `adapters/claude-code-plugin/skills/`: a *generated* copy of a curated subset of skills. It is produced by `scripts/sync_plugin_skills.py` and is never edited by hand.
- **Draft legal work product** — what every skill produces: an intermediate deliverable for a supervising attorney to review and adopt. _Avoid_ "legal advice," "the answer," or "the opinion" — AgentCounsel produces none of those.
- **Jurisdiction-agnostic** — skills carry workflow discipline, not the law. A skill never states a statute, case, rule, or named doctrine as authority; jurisdiction-specific points are flagged for verification.
- **Matter pack** — human-readable process guidance that recommends a skill sequence for a recurring matter type. It is not a machine-executable graph.
- **Matter plan** — a validated JSON DAG under `matter-plans/` that references canonical skills, typed artifact handoffs, conditional branches, execution waves, and explicit attorney gates. It plans work but does not run a model or make a legal decision.
- **Matter workspace** — the Markdown files that hold one live matter's actual facts, documents, artifacts, dates, outputs, quality checks, and attorney decisions. A matter plan points to artifact identities; the workspace holds their content.
- **Plan receipt** — a privacy-conscious integrity record for one matter-plan state. It contains source hashes, node states, gates, lineage, context fingerprints, and budget arithmetic, not raw sensitive matter text.
- **Placeholder** — a bracketed marker for a gap, such as `[CONFIRM: ...]`, `[VERIFY: ...]`, `[verify jurisdiction]`, or `[deadline verification required]`. Skills flag gaps with placeholders rather than guessing.

## Relationships

- The repository is one canonical library of standalone skills (`skills/`), grouped into practice areas. Standard-library tooling compiles metadata, selective contexts, and matter plans; no hosted runtime is required.
- Every skill inherits the `core/` rules. A skill's own Legal Safety Rules section is skill-specific emphasis on top of `core/`, not a replacement for it.
- `SKILLS_INDEX.md` is the full catalog of skills. `WORKFLOW_ROUTER.md` maps a task ("review this NDA") to the skill that handles it.
- The plugin bundle is generated from canonical `skills/` by `scripts/sync_plugin_skills.py`. `scripts/validate_repo.py` enforces repository structure and is run by CI on every pull request.
- A matter pack or playbook supplies human process guidance. A matter plan may reference that source and compile supported work into typed dependencies and gates. A matter workspace stores the actual matter content and outputs.
- A skill produces a draft; a supervising attorney reviews it. The Attorney Verification Checklist in each `SKILL.md` is the handoff to that attorney.

## Flagged ambiguities

- **Matter pack vs. matter plan.** A matter pack describes a recommended sequence in Markdown. A matter plan is a validated graph for a specifically supported recurring matter. Do not call either one an autonomous agent or assume a plan executes its own nodes.
- **Matter plan vs. matter workspace.** The plan stores graph structure and artifact identities; the workspace stores confidential facts, source documents, draft contents, and attorney decisions.
- **"Prompt" vs. "skill."** The upstream project `agnostic-skills-for-legal` calls these workflows "prompts." In AgentCounsel they are **skills**. Use "skill."
- **A skill vs. its `SKILL.md`.** A skill is the *folder*; `SKILL.md` is the workflow *file* inside it. Templates are separate files in the same folder.
- **Attorney Verification Checklist vs. "Open items for attorney verification."** The first is a section of every `SKILL.md`; the second is a section of every template. They are distinct lists with different scopes — do not conflate them.
- **Canonical skill vs. plugin copy.** Edits always go to the canonical skill under `skills/`. The matching file under `adapters/claude-code-plugin/skills/` is regenerated, never hand-edited.
- **"Legal advice" vs. "draft legal work product for attorney review."** AgentCounsel never produces legal advice. Always describe output as draft legal work product for attorney review.
