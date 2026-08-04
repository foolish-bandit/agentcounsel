# AgentCounsel

**An open, Markdown-native library of legal skills for AI agents — and the legal professionals who supervise them.**

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Practice areas](https://img.shields.io/badge/practice%20areas-20-purple.svg)](SKILLS_INDEX.md)
[![Skills](https://img.shields.io/badge/skills-212-success.svg)](SKILLS_INDEX.md)
[![Works with](https://img.shields.io/badge/works%20with-ChatGPT%20%C2%B7%20Claude%20%C2%B7%20Gemini%20%C2%B7%20Codex%20%C2%B7%20Cursor-lightgrey.svg)](#ways-to-use-agentcounsel)
[![CI](https://github.com/zgbrenner/agentcounsel/actions/workflows/validate.yml/badge.svg)](https://github.com/zgbrenner/agentcounsel/actions/workflows/validate.yml)
[![Site](https://github.com/zgbrenner/agentcounsel/actions/workflows/deploy-pages.yml/badge.svg)](https://zgbrenner.github.io/agentcounsel/)

AgentCounsel is a collection of standalone **legal skills**. Each skill is a structured workflow that helps an AI agent — or a lawyer — produce **draft legal work product for attorney review**. The skills supply discipline and structure: how to scope a task, what inputs to gather, how to organize the output, and what a supervising attorney must verify before anything is relied upon.

> **AgentCounsel does not provide legal advice.** It produces draft work product intended for review and adoption by a qualified, licensed legal professional. Using it does not create an attorney–client relationship.

New here? Start with **[QUICKSTART.md](QUICKSTART.md)** — it walks through your first skill run in about five minutes.

## Who AgentCounsel is for

- **Practicing lawyers and in-house legal teams** who want AI assistance that is consistent, reviewable, and built around attorney oversight instead of around a vendor's product.
- **Legal operations and knowledge-management teams** standardizing how their organization uses AI for routine legal work — intake, triage, first-pass review, and drafting.
- **Law students and new lawyers** who want to see how experienced practitioners structure a contract review, a chronology, a research memo, or a risk assessment.
- **AI builders and engineers** assembling legal agents or assistants who need well-scoped, safety-first workflow definitions they can drop into any model or framework.

Whoever you are, the assumption is the same: a licensed attorney reviews the output before it is used.

## What it is — and is not

**It is:**

- A library of legal **workflows** and **output structures**.
- A way to make AI-assisted legal drafting more consistent, reviewable, and safe.
- Useful piecemeal (one Markdown file) or as a whole.
- Plain Markdown at its core, with no required runtime, account, or vendor lock-in. An optional MCP catalog provides typed routing and selective context retrieval.

**It is not:**

- Legal advice, or a substitute for a licensed attorney.
- A source of jurisdiction-specific legal rules. Skills give you process and structure, not the law of any jurisdiction.
- A finished-document generator. Every output is a **draft** that an attorney must review.
- Built around any single AI product. It is a portable library with thin adapters for many environments.

## Quick start

**[QUICKSTART.md](QUICKSTART.md) is the one place to start** — pick your platform, install a practice-area pack, and run your first skill in about five minutes. Sample outputs are in **[`examples/`](examples/)**.

You do not need to read `core/` to get started: every pack and adapter loads those operating rules for the AI automatically. Read [`core/`](core/) yourself only if you are using a raw `SKILL.md` file on its own, or you want to understand the rules your AI is following (a worthwhile ten minutes, but not a prerequisite).

## Deterministic selective context

Every one of the 212 skills compiles to a validated [Skill Specification v2](docs/SKILL_SPEC_V2.md) contract. For ordinary Markdown use, the canonical `SKILL.md` remains enough. For agent runtimes, the optional MCP catalog can route a task, require typed inputs, choose an execution mode, and return only the applicable core and modules through `get_skill_context`.

Selection is fail-closed and inspectable. Missing activation inputs do not load every candidate module. Each bundle includes a decision record for every declared module, per-file SHA-256 hashes, inherited-rule dependency hashes, a compiled-contract fingerprint, token-planning estimates, and a deterministic bundle fingerprint for audit or replay. CI enforces declared context budgets in [`reports/selective-context.md`](reports/selective-context.md).

The first two modularized workflows show the model:

- `litigation/motion-opposition-drafter`: mode-based loading for quick triage, standard drafting, and deep verification.
- `ip/infringement-triage`: mode-based common modules plus right-specific loading for trademark, copyright, patent, and trade secret matters.

The compact cores are now below the repository's large-context band. Standard scenarios use about 58% of their pre-migration context estimate while preserving the complete deep-review package. These figures are deterministic planning estimates, not provider token counts or billing claims.

## Practice areas

AgentCounsel has **212 skills**: 177 across **20 practice areas**, plus 35 cross-cutting skills in three supporting groups (Setup, Legal Operations, Legal Methodology).

| Practice area | Skills | Covers |
|---|--:|---|
| Legal Research | 6 | Research planning (roadmap before authority gathering), structured IRAC memos, case briefs, multi-authority rule synthesis, negative-treatment (good-law) checks, and CFR amendment-history tracing. |
| Litigation | 11 | Matter intake, chronologies, demand letters, subpoena triage, discovery-response organization, depositions, legal holds, privilege logs, claim charts, brief drafting, and motion-opposition drafting. |
| Contracts | 5 | NDAs, commercial contracts, redlines, statements of work, vendor agreement status. |
| Corporate | 7 | Board minutes, shareholder-meeting minutes, written consents, closing checklists, diligence review, material-contract schedules, entity compliance. |
| Employment | 10 | Terminations, reductions in force, worker classification, hiring, restrictive-covenant review, internal investigations, protected leave, severance, workplace policies. |
| Privacy | 10 | Data processing agreements, impact assessments, data subject requests, policy gaps, breach and incident response, cross-border transfer review, vendor privacy diligence, data retention schedule review, children's privacy review, and cookie consent review. |
| Product Legal | 4 | Launch review, marketing claims, terms of service, AI features. |
| Regulatory | 5 | Enforcement risk, rule-change summaries, compliance gaps, compliance-program tracking, examination/inquiry response. |
| AI Governance | 4 | AI use-case intake, vendor terms, model risk, AI policies. |
| Intellectual Property | 7 | Trademark triage, infringement triage, cease-and-desist response, patent FTO triage, invention intake, DMCA, open-source licensing. |
| Financial Crime / AML | 5 | KYC onboarding review, sanctions / PEP / adverse-media screening review, transaction-monitoring alert triage, AML program gap review, and EDD file review. |
| Real Estate | 10 | Commercial lease abstraction and review, amendment reconciliation, purchase and sale agreement review, loan-document review, title and survey objection tracking, diligence and closing checklists, estoppel and SNDA review, zoning issue-spotting. |
| Mergers & Acquisitions | 12 | LOI and term-sheet review, acquisition diligence and data-room review, purchase-agreement and disclosure-schedule review, indemnity and escrow analysis, R&W-insurance review, transition-services-agreement review, third-party consents, and closing, post-closing, and integration tracking. |
| Antitrust / Competition | 10 | Antitrust risk intake, competitor-collaboration and information-sharing review, pricing-algorithm and distribution-restraint review, merger issue-spotting, gun-jumping checklists, and compliance-policy review. |
| Securities / Capital Markets | 13 | Private and public offerings, exemption issue-spotting, offering-document and risk-factor review, SEC filing consistency, Form D and blue-sky tracking, investor-rights, equity-incentive-plan, and insider-trading review, beneficial-ownership triage, and capital-markets closings. |
| Tax | 10 | Tax issue intake, entity tax-classification facts, transaction tax diligence, sales/use tax nexus triage, employment-tax worker-classification intake, contract tax-provision and covenant/indemnity review, tax document organization, international tax issue-spotting, and crypto/digital-asset tax intake. |
| Bankruptcy / Restructuring | 12 | Bankruptcy and creditor-claim intake, proof-of-claim checklists, automatic-stay and preference issue-spotting, executory-contract assumption/rejection review, distressed-M&A diligence and asset-sale checklists, restructuring term-sheet review, plan and disclosure-statement issue-spotting, DIP financing issue-spotting, and deadline-tracker intake. |
| Insurance | 12 | Insurance policy summaries, coverage issue-spotting, claim chronologies, reservation of rights and tender review, coverage-position outlines, bad-faith risk triage, certificate of insurance and contract insurance-requirements review, subrogation/recovery tracking, and renewal/placement diligence checklists. |
| Trusts & Estates | 12 | Estate-planning intake, estate-document summaries, probate document checklists, trust administration and post-death task tracking, fiduciary-duty issue-spotting, beneficiary-designation review, asset and liability inventories, capacity and undue-influence facts organization, estate-litigation chronologies, trust-funding checklists, and estate-tax issue intake. |
| Family Law | 12 | Family-law matter and divorce intake, custody and parenting facts chronologies and schedule organization, custody-order review, child-support and spousal-support facts intake, asset/debt schedules, settlement-agreement issue-spotting, discovery tracking, hearing preparation, and domestic-violence safety referral. |

Three **cross-cutting skill groups** support work in every practice area:

- **Setup** (20 skills) — cold-start interviews that configure AgentCounsel for a practice group, plus a matter-workspace builder.
- **Legal Methodology** (11 skills) — source validation, citation integrity, assumption audit, hallucination red-team, attorney-review gate, privilege/confidentiality review, legal prose polish, output-format compliance, statutory interpretation, risk assessment, and red-team verification.
- **Legal Operations** (4 skills) — legal intake triage, templated legal responses, meeting briefings, and signature-routing checks.

The four-tier taxonomy that classifies these areas and groups — and the model for expanding it — is recorded in [`docs/PRACTICE_AREAS.md`](docs/PRACTICE_AREAS.md).

See [`SKILLS_INDEX.md`](SKILLS_INDEX.md) for the full catalog and [`WORKFLOW_ROUTER.md`](WORKFLOW_ROUTER.md) to route from a task to a skill.

## Choose your workflow

Most tasks are one skill. When the work is larger, AgentCounsel gives you several surfaces:

| Surface | Use it when |
|---|---|
| **One-off skill** | A single, self-contained task and one draft output. |
| **Quality check** | Reviewing an existing draft — source validation, citation integrity, prose polish, red-team. |
| **Practice-area pack** | Repeated work in one practice area, installed into your AI tool. |
| **Matter pack** | A recurring matter *type* that runs an ordered sequence of skills. |
| **Matter workspace** | A multi-step, document-heavy, deadline- or source-sensitive, ongoing matter. |
| **Playbook** | A recurring task type you run the same way every time (e.g., NDA review). |
| **Review panel** | A high-risk draft that needs several supervised review passes before reliance. |

Full decision guide with worked examples: **[docs/CHOOSE_YOUR_WORKFLOW.md](docs/CHOOSE_YOUR_WORKFLOW.md)**. Every surface ends in attorney review.

## How it is organized

```
core/               Operating rules every skill inherits (read these first).
skills/             The canonical skill library, grouped by practice area.
examples/           Illustrative sample outputs, with fictional facts.
practice-profiles/  Per-practice-area configuration profiles for a legal team.
matter-workspaces/  Scaffolds for organizing one matter — single-file templates
                    plus the canonical multi-file _template/.
matter-packs/       Workflow bundles — recommended skill sequences per matter type.
playbooks/          Repeatable recipes for recurring task types (NDA review, etc.).
review-panels/      Supervised multi-pass review workflows for a draft.
overlays/           Industry and sector overlays that tune skills for a context.
adapters/           Thin integration files for specific environments.
connectors/         External-source verification integrations (e.g., CourtListener).
metadata/           Generated machine-readable skill index (index.json).
docs/               The metadata standard, the safety model, the FAQ, and the practice-area registry.
scripts/            Standard-library Python helpers (validation, index, packs).
dist/               Generated platform install packs (gitignored; built by
                    scripts/build_platform_packs.py).
SKILLS_INDEX.md     Full catalog of every skill.
WORKFLOW_ROUTER.md  "I need to do X" -> which skill to use.
COMMANDS.md         Slash-style command shorthands mapped to skills.
```

The `skills/` directory is the **canonical source of truth.** Everything else points back to it.

### Anatomy of a skill

Each skill lives in its own folder with a `SKILL.md` file and optional `templates/`:

```
skills/contracts/nda-review/
  SKILL.md                     The workflow.
  templates/nda-risk-table.md  A copyable, attorney-review-ready template.
```

Every `SKILL.md` follows the same structure — Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, and an Attorney Verification Checklist — and carries standardized, agent-readable YAML frontmatter so tools and agents can discover and route skills. See [`docs/SKILL_METADATA_STANDARD.md`](docs/SKILL_METADATA_STANDARD.md).

## Ways to use AgentCounsel

### Recommended: install a pre-built practice-area pack

A platform pack is one file that bundles the global safety rules, the practice profile, the slash commands, and every skill in a practice area. Upload it to your AI tool's project or workspace and you can start work immediately — no copying files one at a time.

Pre-built packs are hosted on the deployed Pages site and rebuilt on every push to `main`:

- **[Browse the packs page](https://zgbrenner.github.io/agentcounsel/packs/)** — direct downloads per practice area for ChatGPT (.md), Claude (.zip), and Gemini (.zip), plus AGENTS.md / CLAUDE.md for repo agents.
- The packs page lists every practice area with its skill count and a "How to use" block per platform.

### For finer-grained control, you can also...

AgentCounsel is plain Markdown, so it works anywhere an agent or person can read a file. The library-as-files paths below give you more control than a consolidated pack.

| Surface | How to use AgentCounsel | Where to look |
|---|---|---|
| **Generic Markdown** | Open any ordinary `SKILL.md` directly. When a skill has `SPEC.json`, use the catalog's **Copy Full Package** action or copy the complete skill folder so its selectable resources remain available. | [`adapters/generic-md/`](adapters/generic-md/) |
| **ChatGPT** | Create a ChatGPT Project and add individual skill files. (For the consolidated practice-area pack, use the packs page above.) | [`adapters/generic-md/`](adapters/generic-md/) |
| **Claude (claude.ai)** | Create a Claude Project and upload a practice-area pack from the packs page — no command line needed. | [QUICKSTART.md](QUICKSTART.md) |
| **Claude Code** | Use the Claude Code plugin-style bundle, or keep the repo in a folder Claude can read as a local playbook. | [`adapters/claude-code-plugin/`](adapters/claude-code-plugin/) |
| **Claude Cowork** | Point Cowork at the repo folder; `START_HERE.md` gives it the operating model. | [`adapters/claude-cowork/`](adapters/claude-cowork/) |
| **Gemini** | Install the repository as a Gemini CLI extension — `gemini-extension.json` and `GEMINI.md` load the operating model automatically. | [`adapters/gemini/`](adapters/gemini/) |
| **Codex / repo agents** | Point a repo-based coding or legal agent at the library through `AGENTS.md` so it selects the narrowest relevant skill. | [`adapters/codex/`](adapters/codex/), [`AGENTS.md`](AGENTS.md) |
| **Cursor** | Add the library to a project and reference it from a `.cursorrules` file or `AGENTS.md`. (The packs page above also serves a ready-made `.cursorrules`.) | [`adapters/codex/`](adapters/codex/) |
| **MCP client** | Use the optional local MCP catalog for stable-ID routing, typed contracts, and deterministic `get_skill_context` bundles. | [`docs/MCP_SERVER.md`](docs/MCP_SERVER.md), [`agentcounsel_mcp.py`](agentcounsel_mcp.py) |
| **Your own agent** | Vendor the `skills/` and `core/` directories into your project and reference them from your agent's instructions. | [`skills/`](skills/), [`core/`](core/) |

Adapters are intentionally **thin**: they tell an environment how to find and use the canonical library; they do not duplicate it. The one exception is the Claude Code plugin bundle, which carries generated copies of a curated set of skills — regenerate it with `python scripts/sync_plugin_skills.py` (see [`PLUGIN_SYNC.md`](PLUGIN_SYNC.md)).

### Installing or copying skills

- **A practice area (recommended):** download a pre-built pack from the [packs page](https://zgbrenner.github.io/agentcounsel/packs/) — one file per practice area for ChatGPT, Claude, and Gemini. Or run `python scripts/build_platform_packs.py` locally to produce the same packs in `dist/`.
- **One skill:** for an ordinary skill, copy `SKILL.md` and any templates. When the folder contains `SPEC.json`, copy the complete folder or use the catalog's **Copy Full Package** action; the compact `SKILL.md` alone is the routing and quick-triage core, not the full standard/deep package.
- **The whole library:** clone the repository, or vendor `skills/` and `core/` into your own project.

There is no required installer or runtime dependency. Ordinary skills remain portable files; modularized skills remain portable Markdown-plus-JSON folders. The MCP server is optional and exists for clients that need typed routing, true selective loading, and reproducible context bundles.

## Safety model

Every skill inherits the operating rules in [`core/`](core/):

- **Draft legal work product only.** Attorney review is always required before output is relied upon.
- **Never invent legal authority, citations, quotations, facts, or deadlines.**
- **Separate** facts, assumptions, law, analysis, strategy, and verification items.
- **Identify** jurisdiction, governing law, posture, and the relevant date — or flag them as unknown.
- **Preserve** confidentiality and privilege.
- **Flag uncertainty** with visible placeholders instead of guessing.

The full safety model — the threat model, what AgentCounsel deliberately does *not* do, and how to use it safely with confidential material — is in **[docs/SAFETY_MODEL.md](docs/SAFETY_MODEL.md)**. Security reporting and guidance are in [`SECURITY.md`](SECURITY.md).

A firm's risk or compliance team assessing AgentCounsel for adoption should start with [docs/AI_GOVERNANCE_DISCLOSURE.md](docs/AI_GOVERNANCE_DISCLOSURE.md), which maps these controls to common AI-governance framework questions.

## Configuring AgentCounsel for a team

AgentCounsel runs out-of-the-box without configuration. To improve output quality for a practice group adopting the library across multiple matters, you can populate a practice-group profile at `practice-profiles/<area>.md`. The profile gives ~20 skills access to the group's standing positions, escalation thresholds, and output preferences.

Eval coverage is tracked through lightweight, no-API checks in `evals/` and
`reports/eval-coverage.md`. These evals test structure, routing, metadata,
packs, quality checks, and candidate-output safety signals; they do not verify
legal correctness or replace attorney review.

See [`CONFIGURING.md`](CONFIGURING.md) for the full configuration guide. The short version:

1. Run the cold-start interview for the practice area (`skills/setup/<area>-cold-start-interview/SKILL.md`) with a supervising attorney, or edit the profile template directly.
2. Load the populated profile into your AI workspace alongside any skill that consumes it (see `practice-profiles/README.md` for the list).
3. Skills that consume the profile will benchmark against its Standard Positions and Escalation Thresholds; skills that do not consume it are unaffected.

Configuration is opt-in. Skipping it costs you benchmarking-against-standing-positions but does not degrade any other skill's output.

Two optional layers let a legal team adapt the library without changing any skill:

- **[`practice-profiles/`](practice-profiles/)** — one profile per practice area capturing the team's jurisdictions, escalation thresholds, standard positions, review requirements, and prohibited assumptions. The **Setup** cold-start interview skills fill a profile in.
- **[`matter-workspaces/`](matter-workspaces/)** — scaffolds for organizing one specific matter: parties, documents, deadlines (always flagged for attorney verification), open items, sources, and an index of the draft work product produced by skills. Single-file templates plus a canonical multi-file template at `matter-workspaces/_template/`, which `python scripts/init_matter_workspace.py` instantiates. See [`docs/MATTER_WORKSPACES.md`](docs/MATTER_WORKSPACES.md).

Both are plain Markdown and add no backend, runtime, or vendor dependency.

## Examples

The [`examples/`](examples/) directory contains illustrative sample outputs — including primary skill outputs and quality-layer passes such as source validation, prose polish, hallucination red-team, and attorney-review gating. **Every fact in them is fictional.** They show the shape and quality of a skill's deliverable; they are not legal advice and not templates for a real matter. If you have not run a skill end-to-end yet, [`docs/tutorials/practice-matter.md`](docs/tutorials/practice-matter.md) is a guided, fictional first-run walkthrough.

## Validation and continuous integration

The repository ships a lightweight validation script — Python standard library only, no dependencies — that checks every skill's structure, frontmatter, links, and safety framing:

```
python scripts/validate_repo.py
```

GitHub Actions runs the same checks on every pull request and on pushes to `main` (see [`.github/workflows/validate.yml`](.github/workflows/validate.yml)):

```
python scripts/sync_plugin_skills.py --check   # plugin bundle is in sync
python scripts/validate_repo.py                # full repository validation
```

Other standard-library helpers in `scripts/` build the machine-readable skill index (`build_skill_index.py`), the per-platform install packs (`build_platform_packs.py`), the matter-workspace initializer (`init_matter_workspace.py`), and the browsable static catalog under [`site/`](site/). Every script is documented in [`docs/CLI.md`](docs/CLI.md); the recommended commands to run after each kind of edit are in [`docs/AGENT_COMMANDS.md`](docs/AGENT_COMMANDS.md). See [`VALIDATION.md`](VALIDATION.md) for the full list of checks.

Platform pack manifests and plugin-compatibility guidance are documented in
[`docs/PLUGIN_COMPATIBILITY.md`](docs/PLUGIN_COMPATIBILITY.md). The generated metadata files `metadata/index.json`, `metadata/router.json`, `metadata/skill_specs.json`, `metadata/selective_context_metrics.json`, and `metadata/packs.json` are the machine-readable surfaces for skills, routing, typed execution, context budgets, and platform packs.

## Contributing

New skills and improvements are welcome. AgentCounsel is Markdown-first and safety-first — see [`CONTRIBUTING.md`](CONTRIBUTING.md) for the rules (including how to add skills, quality checks, evals, playbooks, review panels, and packs), [`docs/SKILL_METADATA_STANDARD.md`](docs/SKILL_METADATA_STANDARD.md) for the frontmatter standard, and [`SECURITY.md`](SECURITY.md) for security guidance. Questions are answered in [`docs/FAQ.md`](docs/FAQ.md).

For the bigger picture, see [`docs/PROJECT_STATUS.md`](docs/PROJECT_STATUS.md) (an honest maturity snapshot — what is stable, what needs manual review, what is experimental) and [`docs/WORKFLOW_MAP.md`](docs/WORKFLOW_MAP.md) (how core rules, skills, quality checks, packs, workspaces, playbooks, review panels, and evals fit together).

## License

MIT License — see [`LICENSE`](LICENSE). Attribution for content adapted from other open-source projects (which remain under their original Apache-2.0 terms) is recorded in [`THIRD_PARTY_NOTICES.md`](THIRD_PARTY_NOTICES.md). AgentCounsel is an independent open-source project and is not affiliated with, endorsed by, or sponsored by Anthropic, OpenAI, or Google.

## Disclaimer

AgentCounsel is a workflow library — not a law firm and not a lawyer. Using it does not create an attorney–client relationship, and it does not provide legal advice. All output is draft work product that must be reviewed and adopted by a qualified, licensed legal professional before it is relied upon. You are responsible for the use of these materials and for compliance with the rules of professional conduct that apply to you.
