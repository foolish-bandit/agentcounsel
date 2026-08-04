# Changelog

All notable changes to AgentCounsel are recorded in this file. The format follows the Keep a Changelog convention. AgentCounsel is pre-1.0; the library's content and structure may still change between releases.

> Current totals (practice areas, skill counts) are tracked in [`metadata/index.json`](metadata/index.json) and summarized in [`README.md`](README.md). Figures quoted below reflect the state at the time each entry was written.

## [Unreleased]

## [0.3.0] - 2026-08-04

### Added

- **Phase 2B deterministic selective context:** Skill Specification v2 now
  supports controlled `string-list` inputs, declarative module activation, and
  context-budget scenarios. The standard-library context engine fails closed on
  missing activation inputs, explains every selected, skipped, or unresolved
  module, hashes the compiled contract, inherited rules, and every loaded file, and emits a reproducible bundle fingerprint.
  The MCP catalog exposes this through `get_skill_context`.
- **Two fully modularized flagship workflows:**
  `litigation/motion-opposition-drafter` and `ip/infringement-triage` now keep a
  compact canonical core and load detailed Markdown modules by execution mode
  and, for IP matters, by the rights actually implicated. All nine declared
  scenarios are complete and within CI-enforced budgets. Quick-triage bundles
  use 34.8% to 38.0% of the pre-migration context estimate; standard bundles use
  58.0% to 58.5%. These are deterministic planning estimates, not provider token
  counts or billing claims.
- **Selective-context observability and distribution:** generated JSON and
  Markdown scorecards record complete module-selection traces and bundle
  fingerprints. ChatGPT, Claude, Gemini, and repo-agent packs now preserve
  custom specs and selectable resources, with an explicit distinction between
  logical selection in consolidated packs and true prompt-size reduction through
  MCP or another selective client.
- **Catalog execution packages:** custom-spec skill pages now distinguish the
  compact core from the complete portable package, display the typed contract
  and module activation table, expose every selectable resource, and include
  the full package in one-off prompts. Ordinary skills keep the simple one-file
  copy experience.

- **Skill Specification v2 foundation:** every canonical skill now compiles
  to a typed execution contract in `metadata/skill_specs.json`, with
  non-weakening inheritance, missing-input and attorney-review gates,
  three execution modes, typed inputs and outputs, claim-support evidence
  records, selective modules, and compiled quality checks. Optional
  `SPEC.json` sidecars pilot the format for NDA review, legal research
  memos, and critical breach response. MCP routing now returns typed
  required inputs, modes, custom gates, and compiled escalation behavior.
- **Phase 1 MCP and repository metrics:** `agentcounsel_mcp.py` now uses
  canonical generated metadata for stable-ID discovery and structured routing;
  `mcp_server.py` is a thin FastMCP adapter with compact skill-card retrieval.
  Standard-library tests cover routing, aliases, missing-input gates, context
  metrics, and readiness signals. New generated reports track per-skill and
  per-pack context pressure plus repository-readiness evidence without claiming
  legal correctness. CI and `scripts/check_all.py` enforce report drift checks.
- **Three privacy skills** filling gaps identified against the largest
  open-source privacy-skills collection:
  `privacy/data-retention-schedule-review`, `privacy/childrens-privacy-review`
  (no age threshold ever stated as settled; actual-knowledge escalation),
  and `privacy/cookie-consent-review` — each with a template, starter evals,
  and full index/router/commands wiring. Library total: 212 skills.
- **Citation-trust upgrade:**
  `skills/legal-methodology/references/citation-confidence-tiers.md` (a
  verification-status ladder — connector-verified / secondary-source /
  model-knowledge→`[VERIFY]` / unresolvable→placeholder — complementing the
  citation-type taxonomy), a "Citation provenance tags" convention in
  `core/source-and-citation-discipline.md` (every citation carries its
  provenance; no silent no-op when no verification source is available), and
  a mechanical grounding pass (string-match quotations/pinpoints against
  the provided sources before any judgment pass) opening
  `review-panels/citation-source-red-team-panel.md`.
- **Two connectors:** `connectors/congress-gov.md` (federal bill status,
  enacted-vs-pending, public-law numbers — status only, never legal effect)
  and `connectors/municipal-ordinances.md` (local-ordinance existence
  checks; hosted codes are not operative — always re-verify against the
  official municipal code).
- **`docs/AI_GOVERNANCE_DISCLOSURE.md`** — the answer sheet for a firm's
  risk/compliance team: every AgentCounsel safety mechanism mapped to NIST
  AI RMF functions, EU AI Act framing, and vendor-diligence questions, with
  what remains the firm's responsibility stated per row.
- **`docs/SCANNED_DOCUMENTS.md`** — OCR-as-transcription discipline for
  scanned exhibits: verify against the page image, record provenance,
  red-flag checklist mapped to `[CONFIRM against original: ...]`.
- **Matter-workspace conventions:** a per-source **Document Map**
  (hierarchical structure, conversion method, processing status,
  provenance) and an append-only **Session Notes** log (drafting context,
  not work product) in the canonical template and documented in
  `docs/MATTER_WORKSPACES.md`.
- **`docs/templates/SKILL_TEMPLATE.md`** — fill-in-the-blanks scaffold for
  new skills (all 11 frontmatter fields, eight canonical sections with
  safety framing), linked from `CONTRIBUTING.md`.

### Changed

- `COMMANDS.md` practice-area sections now carry a one-line *Typical
  chain* showing the natural command sequence, derived from the area's
  matter pack or playbook.
- `docs/OSS_BORROWING_MAP.md` gained 25 evaluated rows from the round-3
  repo audit (including explicit rejections: AGPL/noncommercial licenses,
  a deadline calculator contrary to the never-compute-deadlines rule, and
  an output-compression skill flagged as a counter-pattern that would strip
  verification language); `THIRD_PARTY_NOTICES.md` records the five
  adapted structures.

- **Five shared reference catalogs**, completing the catalog program across
  every large practice area: `skills/bankruptcy-restructuring/references/issue-catalog.md`,
  `skills/tax/references/issue-catalog.md`,
  `skills/trusts-estates/references/issue-catalog.md` (governed by the
  capacity/vulnerable-party escalation rule),
  `skills/insurance/references/red-flags.md`, and
  `skills/m-and-a/references/red-flags.md` — wired with one-line pointers
  into 50 skills across the five areas.
- **Scored eval coverage expanded 8 → 20 skills** (35 new candidate outputs
  across 12 skills in previously unscored areas — securities, bankruptcy,
  trusts-estates, insurance, tax, employment, antitrust, ip, corporate,
  m-and-a, legal-research, legal-methodology); `REQUIRED_EVAL_SLUGS` widened
  so CI gates on all 20 permanently.
- **Two matter packs:** `matter-packs/corporate.md` (Governance Cycle, Deal
  Support) and `matter-packs/privacy.md` (Vendor & Data-Flow, Rights &
  Incidents — notification clocks always flagged, never computed).
- **Markdown→Word bridge:** `docs/MARKDOWN_TO_WORD.md` — pandoc
  `--reference-doc` workflow for turning any skill's draft into a
  firm-styled Word file for redlining, with a placeholder-survival check
  before attorney review.
- **Guided practice matter:** `docs/tutorials/practice-matter.md` — a
  tabletop-style fictional first matter (structure adapted from CISA CTEP,
  public domain) that walks a new user through routing, Required Inputs,
  placeholder discipline, and the attorney-review gate.
- **Plain-language pass:** `skills/legal-methodology/references/plain-language-checklist.md`
  (distilled from the Federal Plain Language Guidelines, CC0) for
  client-facing and stakeholder communications — explicitly not for legal
  drafting, where precision outranks plainness.
- **Site search:** the static catalog site now ships Pagefind search
  (MIT; indexed at deploy time via a one-shot CI step — no repo
  dependency), scoped to page content via `data-pagefind-body`.
- **Learning deck:** `scripts/build_flashcards.py` (stdlib-only) emits an
  Anki-importable TSV of routing flashcards from `metadata/index.json` —
  one card per skill, for learning which skill fits which task.
- **Repo trust & setup:** `CITATION.cff` (GitHub cite-this-repository
  support) and `.devcontainer/devcontainer.json` (one-click validated
  environment; runs the quick check suite on create).

- **Two new skills** closing gaps named in the July 2026 audit backlog:
  `skills/litigation/motion-opposition-drafter` (the opposition counterpart to
  `brief-section-drafter` — deconstructs movant arguments, flags every movant
  authority `[VERIFY]`, routes counter-authority research to the
  legal-research skills) and
  `skills/m-and-a/transition-services-agreement-review` (13 per-topic steps
  with named red flags — evergreen extensions, unpriced omitted services,
  TSA-to-purchase-agreement consistency). Both ship templates, starter evals,
  and index/router/commands entries. Library total: 209 skills.
- **OSS-derived reference catalogs** (taxonomies adapted with attribution in
  `THIRD_PARTY_NOTICES.md`; all descriptions rewritten):
  `skills/contracts/references/clause-category-checklist.md` (40 clause
  categories adapted from the CUAD dataset, CC-BY-4.0),
  `skills/contracts/references/market-standard-baselines.md` (oneNDA /
  Bonterms / Common Paper as labeled-inference comparison baselines),
  `skills/legal-research/references/citation-type-taxonomy.md` (citation
  forms adapted from eyecite's classification, with per-type verification
  needs and hallucination risks), and `connectors/reporters-and-courts.md`
  (Free Law Project reporters-db / courts-db as existence-verification
  sources). Wired with minimal touches into `nda-review`,
  `contract-risk-review`, `citation-integrity-check`, and
  `source-validation`.
- **Composition layer completed:** `matter-packs/litigation.md` (three
  bundles with handoff notes), `playbooks/legal-research-memo.md`, and
  `playbooks/legal-intake-response.md`; every playbook and matter pack now
  names its matching review panel in its quality-checks section (the panels
  were previously unreachable from the production layers);
  `WORKFLOW_ROUTER.md` gained a new-user cue and one whole-matter routing row
  per area with a pack or playbook.
- **Thirteen output templates** for the skills that had none: contracts
  redline-summary, employment severance-review, legal-research case-brief,
  privacy dsar-workflow, all five financial-crime skills, and all four
  legal-ops skills.
- **Decision records:** `docs/decisions/` (MADR-style) documenting three
  standing architecture decisions — the generated plugin bundle, the
  eight-section skill structure, and the Markdown-only/no-runtime rule.
- **Tooling:** three new validators in `scripts/validate_repo.py`
  (`check_matter_packs`, `check_connectors`, and
  `check_practice_area_doc_sync`, closing the doc-drift risk the July audit
  flagged); `scripts/check_all.py` runs the full 12-step CI sequence locally
  (`--quick` for the core trio); a weekly external-link workflow
  (`.github/workflows/links.yml`) so cited source URLs cannot rot silently;
  unit tests for the new validators.

### Changed

- **Novice onboarding path fixed:** `QUICKSTART.md` now gives claude.ai users
  their own no-command-line path (separate from Claude Code) with a literal
  copy-paste Project instruction block; `README.md` points to QUICKSTART as
  the single starting point and no longer asks new users to read `core/`
  first (packs load it for the AI automatically); `docs/CHOOSE_YOUR_WORKFLOW.md`
  tells first-time users to start with a single skill.
- **Claude platform packs restructured for claude.ai:** every file in each
  Claude pack zip now has a unique basename (claude.ai Project knowledge
  flattens uploads, so the previous per-skill `SKILL.md` files collided);
  install instructions updated to match.
- **Skill-quality backlog:** the canonical source-and-citation-discipline
  bullet added to the ten analytical skills that restated it informally;
  `tax/tax-document-organizer` and
  `bankruptcy-restructuring/creditor-claim-intake` deepened from the generic
  intake skeleton to per-topic steps with named red flags; reciprocal
  `related_skills` links fixed for four skill pairs.
- Stale hardcoded counts in `docs/FAQ.md` and `docs/DEMO_SCRIPT.md` replaced
  with count-free wording; Windows-only `py scripts/...` invocations replaced
  with `python scripts/...` across all docs; `AGENTS.md` now points to
  `scripts/check_all.py` as the full local equivalent of CI.

- **Three connectors** extending the citation-verification surface (Markdown
  integration contracts, no runtime): `connectors/pacer-recap.md` (federal
  dockets via PACER / the free RECAP archive — for litigation and bankruptcy),
  `connectors/uspto.md` (patent and trademark existence/status — for the ip
  cluster), and `connectors/state-courts.md` (state-court and state-register
  aggregators). Each verifies existence and metadata only — never legal
  sufficiency, never a deadline — and is lightly wired into its consuming
  skills (subpoena-triage, bankruptcy-deadline-tracker-intake, fto-triage,
  trademark-clearance-triage, case-brief).
- **Two shared reference catalogs** in the `contracts/references/` model:
  `skills/family-law/references/issue-catalog.md` (449 lines, 8 issue areas,
  framed as facts-and-questions per the area's no-conclusions posture, with a
  safety-escalation section keyed to `core/capacity-and-vulnerable-parties.md`)
  and `skills/real-estate/references/red-flags.md` (588 lines, 21 topic
  sections across lease / purchase-and-sale / loan / cross-cutting families).
- **Four playbooks** closing the orchestration gap for the areas that had
  neither a playbook nor a matter-pack: `ip-brand-clearance-and-enforcement`,
  `ai-governance-use-case-review`, `product-launch-legal-review`, and
  `aml-customer-lifecycle-review`.
- **Two review panels** for the individual-client and deadline-critical work
  the existing six panels did not cover:
  `review-panels/individual-client-capacity-panel.md` (operationalizes
  `core/capacity-and-vulnerable-parties.md`) and
  `review-panels/deadline-critical-bankruptcy-panel.md`.
- **Five worked examples** for flagship older skills that had no sample output:
  `termination-risk`, `board-minutes`, `claim-chart`, `rule-change-summary`,
  and `legal-research-memo` — all on fictional facts with every citation,
  case name, and authority a visible placeholder (no real-looking citations).

### Changed

- **Two family-law review skills de-boilerplated and differentiated** —
  `settlement-agreement-issue-spotter` (now a cross-issue review across all
  eight catalog areas) and `custody-order-review-checklist` (now scoped to a
  custody/parenting order), each wired to the new issue catalog with a
  scan step, output section, and checklist line, so they no longer read as
  near-interchangeable.
- **Four real-estate review skills wired** to the new red-flag catalog
  (`commercial-lease-review`, `psa-review`, `loan-document-review`,
  `estoppel-snda-review`) — each with a red-flags quick-scan step, output
  section, and checklist line.
- Updated `connectors/README.md`, `playbooks/README.md`,
  `review-panels/README.md` (six → eight panels), and `examples/README.md`;
  marked audit backlog items 6–10 (orchestration) progressed in
  `reports/repository-audit-2026-07.md`; regenerated `metadata/`.

- **Nine new skills** closing the audit backlog's "carved-out sibling" gaps
  (workflows existing skills already pointed at) and rounding out the newer
  areas:
  - `corporate/shareholder-meeting-minutes` — the member/shareholder-meeting
    sibling `board-minutes` explicitly carved out.
  - `employment/reduction-in-force-review` — group-termination selection,
    adverse-impact, notice, and group-release organization.
  - `employment/restrictive-covenant-review` — non-compete/non-solicit/
    confidentiality review from any party posture (enforceability framed as
    questions, never asserted).
  - `regulatory/regulatory-exam-response` — organizing a regulator's exam
    letter or information request into a request-item tracker.
  - `legal-research/negative-treatment-check` — a citator-style good-law check
    that never asserts treatment from model memory.
  - `litigation/discovery-response-workflow` — document-request, interrogatory,
    and RFA responses into a tracker (no final objection, no admit/deny).
  - `real-estate/loan-document-review` — CRE financing documents from a
    borrower/guarantor/lender posture (no computed figures, no lien-priority or
    title conclusions).
  - `securities-capital-markets/equity-incentive-plan-review` — plan and award
    review with securities and tax hooks (no share-pool, vesting, exemption, or
    tax conclusions).
  - `m-and-a/rw-insurance-review` — RWI policy/quote against the deal (coverage
    map and exclusions register, never a coverage determination).
  Each ships with starter evals, index/router/commands entries, and
  cross-links from the sibling skills that route to it.
- **Four area red-flag catalogs**, extending the `contracts/references/`
  shared-library model to the contract-review skills outside `contracts` (the
  July 2026 audit's top backlog item). Each follows the contracts catalog's
  entry format (Pattern / Why it matters / What to check / Most exposed) with
  per-section preferred/fallback direction lines, and its review skill gains a
  red-flags quick-scan workflow step, output section, and attorney-checklist
  line:
  - `skills/privacy/references/dpa-red-flags.md` → `dpa-review` (which now
    also rates issues with the contracts negotiability vocabulary)
  - `skills/product-legal/references/terms-of-service-red-flags.md` →
    `terms-of-service-review`
  - `skills/ai-governance/references/ai-vendor-terms-red-flags.md` →
    `ai-vendor-terms-review`
  - `skills/employment/references/severance-release-red-flags.md` →
    `severance-review`
- **Five output templates** extracted from inline table definitions and wired
  into their skills' Workflow and Output Format:
  `regulatory/compliance-gap-matrix`, `ai-governance/model-risk-triage`
  (risk register), `product-legal/launch-review` (issues register),
  `ip/infringement-triage` (triage memo), `litigation/matter-intake`
  (intake summary) — the first templates in the regulatory, ai-governance,
  product-legal, and ip areas.
- **Seven new skills** filling the three most under-covered areas the July 2026
  repository audit identified (`reports/repository-audit-2026-07.md`):
  - `privacy/breach-response-workflow` — organizes a privacy/security incident
    for counsel; notification clocks are flagged, never computed.
  - `privacy/cross-border-transfer-review` — data-flow inventory, claimed
    transfer-mechanism map, and TIA fact pattern for attorney completion.
  - `privacy/vendor-privacy-diligence` — pre-contract/renewal vendor privacy
    diligence feeding contract-term asks into `dpa-review`.
  - `financial-crime/transaction-monitoring-alert-triage` — fills the gap
    `kyc-onboarding-review` previously routed away.
  - `financial-crime/aml-program-gap-review` and
    `financial-crime/edd-file-review`.
  - `legal-ops/legal-intake-triage` — the legal front-door: classify, gate,
    and route an inbound business request.
  Each ships with starter evals and index/router/commands entries.
- **New core operating rule `core/capacity-and-vulnerable-parties.md`** —
  capacity, undue influence, safety escalation, minors, unrepresented parties,
  and no outcome predictions about people, binding every skill in the
  individual-client areas; wired into `docs/SAFETY_MODEL.md`.
- **Two new overlays** — `overlays/education-law/` and
  `overlays/environmental-esg/` (OVERLAY.md + profile.md each).
- **`connectors/sec-edgar.md`** — SEC EDGAR connector for the securities,
  m-and-a, and corporate verification surface.
- **Three new matter workspaces** — `bankruptcy-matter.md` (bar-date register,
  stay touchpoints), `family-law-matter.md` (safety screening first), and
  `trusts-estates-matter.md` (capacity observations as facts only), aligned
  with the new core rule.
- **17 new router eval cases** — routing coverage extended from 8 practice
  areas to all of them, plus cross-practice disambiguation cases.
- **`reports/repository-audit-2026-07.md`** — the full audit record: findings,
  what this change addressed, and a prioritized backlog.

### Changed

- **Two collapsed workflows exploded to per-topic depth** at the granularity
  of `m-and-a/purchase-agreement-issue-list`:
  `bankruptcy-restructuring/cash-collateral-dip-financing-issue-spotter`
  (one bullet → 12 per-topic steps: priming liens, roll-ups, budget/variance,
  adequate protection, carve-outs, waiver patterns, challenge periods,
  defaults, releases) and `tax/tax-covenants-indemnities-review` (one bullet
  → 14 per-topic steps: straddle allocation, transfer taxes, contests, filing
  control, indemnity interplay, survival, caps/baskets, definitional hooks) —
  with output formats and attorney checklists mirroring the new structure and
  all never-compute / never-conclude safety framing preserved.
- Updated the backlog in `reports/repository-audit-2026-07.md` to record this
  second pass; regenerated `metadata/`, the plugin bundle (`dpa-review`
  mirror), and platform packs.

- **All 10 antitrust-competition skills de-boilerplated** — the byte-identical
  Purpose / Use When / description headers were rewritten per skill
  (trigger-rich, document-specific), and skill-specific safety bullets added
  (gun-jumping, pricing-algorithm, trade-association cartel escalation).
- **Six thin practice profiles rewritten to the full template standard** —
  `securities-capital-markets` (was a 9-line stub), `antitrust-competition`,
  `tax`, `bankruptcy-restructuring`, `trusts-estates`, and `insurance` now
  carry the full fill-in tables (jurisdictions, escalation thresholds,
  standard positions, prohibited assumptions) at ~190 lines each.
- **Verification-skill boundaries sharpened** — `red-team-verifier`,
  `hallucination-red-team`, `citation-integrity-check`, and
  `source-validation` each now state when to use it versus a sibling.
- **Safety boilerplate standardized** — the bolded
  `core/source-and-citation-discipline.md` rule added to the six skills that
  lacked it (all four product-legal skills, `ai-governance/ai-use-case-intake`,
  `legal-methodology/hallucination-red-team`).
- **Stale planning/standards docs corrected** — the expansion plan is
  re-labeled substantially implemented with an implementation-status table and
  superseded-passage annotations; `docs/SKILL_METADATA_STANDARD.md` gains the
  seven missing practice areas; count and release-name fixes in `COMMANDS.md`,
  `CONFIGURING.md`, `docs/PRACTICE_AREAS.md`, `docs/PLATFORM_GAP_ANALYSIS.md`,
  `docs/IMPLEMENTATION_SEQUENCE.md`, and `practice-profiles/README.md`.
- Regenerated `metadata/index.json`, `metadata/router.json`,
  `metadata/packs.json`, the plugin bundle, and the eval-coverage and
  skill-improvement reports for the 198-skill library.

- Added cross-practice `related_skills` links so a skill points to adjacent
  workflows in other practice areas, not just its own: antitrust merger
  issue-spotting ↔ M&A deal skills, privacy PIA ↔ AI-governance and product AI
  reviews, deal-tax diligence/covenants ↔ M&A diligence and purchase-agreement
  review, employment ↔ tax worker classification, IP open-source review ↔ M&A
  diligence, and insurance/M&A consent reviews → contract risk review.
  Regenerated `metadata/index.json` and `metadata/router.json` accordingly.
- Surfaced the headline cross-practice pairings in `WORKFLOW_ROUTER.md`'s
  "When several skills could apply" section.
- **Relicensed from Apache-2.0 to MIT.** `LICENSE` now carries the MIT
  License text. The repository's `NOTICE` file has been removed and the
  upstream Apache-2.0 attributions it carried (for `agnostic-skills-for-legal`
  and its lineage, plus `anthropics/financial-services` and
  `anthropics/knowledge-work-plugins`) have been preserved in a new
  `THIRD_PARTY_NOTICES.md`. The borrowed content from those projects continues
  to be governed by Apache-2.0, including the §4 attribution requirement;
  AgentCounsel's own additions are now MIT. License references and the
  attribution path were updated across `README.md`, `CONTRIBUTING.md`,
  `RELEASE_NOTES.md`, `adapters/claude-code-plugin/plugin.json`,
  `site/package.json`, `docs/FAQ.md`, `docs/RELEASE_CHECKLIST.md`,
  `docs/DEMO_SCRIPT.md`, `docs/LAUNCH_POST.md`,
  `docs/THIRD_PARTY_ATTRIBUTION_POLICY.md`, and `docs/OSS_BORROWING_MAP.md`.

## [0.2.0] - 2026-05-27 — First public release

AgentCounsel's first public release: a polished, open, Markdown-native legal
skills library with a workflow router, platform packs, a quality layer, an eval
system, matter workspaces, playbooks, review panels, a static site, and full
onboarding and contributor documentation. Every output remains draft legal work
product for attorney review. The granular entries below (carried over from the
development cycle that produced this release) detail the changes; the summary
gives the shape of the release.

### Release summary

- **Metadata, router, and packs:** normalized `metadata/index.json`,
  `metadata/router.json`, and `metadata/packs.json`; an upgraded
  `WORKFLOW_ROUTER.md`; and generated per-platform packs (ChatGPT, Claude,
  Gemini, Cursor, Codex, repo agents) with pack-registry validation.
- **Quality layer:** nine cross-cutting checks (source validation, citation
  integrity, assumption audit, hallucination red-team, privilege/confidentiality,
  legal prose polish, output-format compliance, jurisdiction/deadline gates, and
  the attorney-review gate), with source/citation classification workflows.
- **Evals and benchmarks:** 186 eval files (509 cases) plus router,
  static-integrity, and benchmark suites; a static, no-API eval runner; and the
  generated `reports/eval-coverage.md`. The evals check structure and safety
  signals, not legal correctness.
- **Matter workspaces:** six single-file templates, a canonical multi-file
  template (`matter-workspaces/_template/`), and `scripts/init_matter_workspace.py`.
- **Playbooks and review panels:** eight playbooks (recurring task recipes) and
  six review panels (supervised multi-pass reviews); both Markdown-native and
  attorney-supervised.
- **Site and onboarding docs:** a static catalog site; a rewritten `README.md`;
  a per-platform `QUICKSTART.md`; and `docs/CHOOSE_YOUR_WORKFLOW.md`,
  `docs/CLI.md`, `docs/AGENT_COMMANDS.md`, `docs/WORKFLOW_MAP.md`, and
  `docs/PROJECT_STATUS.md`.
- **Validation improvements:** deterministic checks for workspace/playbook/panel
  integrity, source/citation classification alignment, required docs, doc/script
  references, router references, and pack-manifest references — all standard
  library, no network calls.

### Added

- A **platformization / polish phase** that makes AgentCounsel approachable as a usable open-source tool, not just a repository. (1) New onboarding and decision docs: `docs/CHOOSE_YOUR_WORKFLOW.md` (a decision guide with worked examples for choosing among one-off skill, quality check, practice-area pack, matter pack, matter workspace, playbook, and review panel), `docs/CLI.md` (every script and `site/generate.mjs` — purpose, example, failure modes, whether it mutates files, and supported flags), `docs/AGENT_COMMANDS.md` (repo-agent guidance: the pre-commit validation sequence, what to run after editing skills/packs/evals/site/workspaces, the generated files that must be refreshed, and the files agents should not touch), `docs/WORKFLOW_MAP.md` (a Mermaid map plus a text legend and component-to-directory table relating core rules, skills, quality checks, packs, workspaces, playbooks, review panels, and evals), and `docs/PROJECT_STATUS.md` (an honest maturity snapshot: stable, manual-review-required, experimental, future concepts, and what AgentCounsel intentionally does not do). (2) `QUICKSTART.md` rewritten with concrete per-platform paths for ChatGPT Projects, Claude Projects / Claude Code, Cursor / Codex repo agents, Gemini, and local Markdown-only use — each covering what to install, which pack, how to start a matter, when to run quality checks, the attorney-review gate, and what not to do. (3) `README.md` gains a "Choose your workflow" surface table, an updated repository map (playbooks, review panels, multi-file workspace template), and links to the new docs. (4) `CONTRIBUTING.md` gains how-to sections for metadata, quality checks, evals, playbooks, review panels, and packs, the full validation command list, the legal-safety requirements, and the third-party attribution / no-GPL-AGPL rules. (5) Three new GitHub issue templates — pack/platform compatibility, eval/benchmark, and documentation — and an expanded PR template (new artifact types, the full validation sequence, and an attribution checkbox). (6) Static site improvements: a new "How it works" page surfacing skills, packs, the quality layer, evals, matter workspaces, playbooks, review panels, platform compatibility, the workflow router, and contributing; an "At a glance" facts panel on every skill page (practice area, category, risk level, recommended quality checks, eval coverage, compatible platforms, related skills) sourced from `metadata/index.json`; and expandable per-pack detail on the packs page (included skills, quality checks, playbooks, review panels, attorney-review requirements, and setup) with playbook/panel columns. (7) New deterministic checks in `scripts/validate_repo.py`: required top-level docs exist, and command docs reference only scripts that exist (`site/generate.mjs` included). No auth, database, payments, backend, hosted SaaS, or chat UI was added; the project stays Markdown-native, static, and offline-friendly.

- A **matter-platform phase** that extends (without rebuilding) the workspace, playbook, and review-panel surfaces. (1) A canonical **multi-file matter workspace template** at `matter-workspaces/_template/` — `matter_profile.md`, `facts.md`, `open_questions.md`, `documents/`, `source_log.md`, `citation_map.md`, `unsupported_claims.md`, `assumptions.md`, `tasks.md`, `skills_used.md`, `outputs/`, `quality_checks/`, `attorney_review.md`, `matter_status.md` — Markdown-native, usable without a database, alongside the existing single-file workspaces. The four source/citation tracking files carry the exact quality-layer classification vocabulary used by source-validation and citation-integrity (source-supported, source-mentioned but insufficient, unsupported, contradicted by source, legal authority required, attorney judgment required, user-provided authority, model-suggested authority requiring verification, unsupported or unverifiable authority). (2) A new **`playbooks/`** directory with eight recurring-task recipes (NDA review, commercial contract review, employment termination analysis, litigation demand letter, regulatory rule-change summary, privacy DPA review, corporate governance review, securities disclosure review), each with twelve required sections ending in a final attorney-review gate. (3) A new **`review-panels/`** directory with six supervised multi-pass review workflows (contract, litigation risk, regulatory risk, citation/source red-team, external communication, deal diligence); each defines review passes (issue spotter, source/citation reviewer, client-position reviewer, privilege/confidentiality reviewer, business-risk reviewer, attorney gatekeeper) and states explicitly that the passes are review passes, not autonomous agents and not lawyers — output stays attorney-supervised draft work product. (4) A stdlib-only initializer `scripts/init_matter_workspace.py` (`--practice-area`, `--jurisdiction`, `--pack`, `--output-dir`, `--force`, `--dry-run`, `--list-templates`) that copies the template into a git-ignored `matters/` directory and seeds `matter_profile.md`. (5) Router integration: `scripts/build_skill_index.py` adds `workspace_triggers`, an expanded `routing_order`, and routing examples for the matter-workspace, review-panel, playbook, practice-area-pack, and quality-check route types; `WORKFLOW_ROUTER.md` gains workspace/playbook/panel guidance and example rows. (6) Pack integration: `scripts/build_platform_packs.py` includes playbooks, review panels, source/citation templates, and attorney-review templates in packs whose workflow type justifies them, with file-existence validation. (7) Eval and validation coverage: `evals/static/workspace-platform-integrity.eval.yaml`, four new router cases, and new deterministic checks in `scripts/validate_repo.py` for workspace-template completeness, playbook/panel required sections and ordering, classification-vocabulary alignment, and router example references. (8) New docs `docs/MATTER_WORKSPACES.md`, `docs/PLAYBOOKS.md`, `docs/REVIEW_PANELS.md`, and `docs/LOCAL_PLATFORM_PATH.md` (architecture-level only), plus a "Beyond a single skill" section on the generated site home page. No auth, database, payments, hosted backend, or chat UI was added; everything remains Markdown-native and offline.
- Two new regulatory connectors extending the `connectors/` framework introduced earlier in this Unreleased cycle. **`connectors/federal-register.md`** documents the [Federal Register](https://www.federalregister.gov) v1 REST API surface (free, no API key) — `documents.json` search with `conditions[term]`, `conditions[type]`, `conditions[agencies]`, and `conditions[publication_date]` filters; single-document fetch by document number; Public Inspection endpoint; document-type codes (`RULE`, `PRORULE`, `NOTICE`, `PRESDOCU`); and the public document-page URL pattern. **`connectors/ecfr.md`** documents the [eCFR](https://www.ecfr.gov) v1 REST API surface (also free, no key) — the Versioner endpoint for point-in-time text retrieval (`/api/versioner/v1/full/<YYYY-MM-DD>/title-<N>.xml` with optional `chapter` / `subchapter` / `part` / `subpart` / `section` subset filters), structure and search endpoints, and the public section-URL pattern. Both docs specify what each source verifies and — explicitly — what it does not: Federal Register confirms publication of record but not operative status (rules can be vacated, stayed, enjoined, withdrawn, or superseded); eCFR confirms the codified text on a specific date but not applicability, interpretation, or litigation status. Endpoint shapes, methods, and date semantics are sourced from the live agency docs; items prone to drift carry `[CONFIRM: ...]` placeholders. Wires both connectors into three regulatory skills via Legal Safety Rules bullets, preserving the eight-section structure: `skills/regulatory/rule-change-summary/SKILL.md` (Federal Register, since it already explicitly handled FR documents), `skills/regulatory/compliance-gap-matrix/SKILL.md` (eCFR — the skill matches controls to provisions extracted from a regulation source, and the snapshot-date discipline matters when the matter turns on a specific date), and `skills/regulatory/enforcement-risk-memo/SKILL.md` (both — memos may cite codified CFR sections and published FR documents). Updates `connectors/README.md` to list the two new connectors alongside CourtListener. As with the first connector, the library remains Markdown-only with no runtime; the user's environment supplies the actual HTTP / MCP integration, and the placeholder discipline is unchanged when no connector is available.
- A new top-level **`connectors/`** directory introducing the *connector* concept to the library: documented external sources a skill can consult to verify a `[VERIFY-CITE: ...]` or `[CONFIRM: ...]` citation placeholder, instead of leaving every placeholder for the attorney. Adds `connectors/README.md` defining the contract (in scope, out of scope, surface, calling pattern, fallback behavior, limits) and `connectors/courtlistener.md` as the first concrete connector — documenting the Free Law Project's [CourtListener](https://www.courtlistener.com) v4 REST API surface (Citation Lookup, Search, Opinion fetch), the free public-web URL patterns, rate limits, and what the connector can and cannot verify. The Citation Lookup endpoint is framed by the Free Law Project as a guardrail against hallucinated citations; the connector doc wires that capability into AgentCounsel's existing "Never invent authority" discipline. Wires the connector into three skills: `skills/legal-research/legal-research-memo/SKILL.md` (Workflow step 8, Legal Safety Rules bullet, Output Format Authorities Cited column, Attorney Verification Checklist) plus its `templates/legal-research-memo.md` (Authority source key); `skills/litigation/brief-section-drafter/SKILL.md` (Legal Safety Rules bullet); and `skills/litigation/claim-chart/SKILL.md` (Legal Safety Rules bullet). Each skill update preserves the eight-section structure — content is added inside existing sections, no new H2 sections. Registers `connectors/` in `scripts/validate_repo.py` (`EXPECTED_DIRS`), the repo map in `AGENTS.md` and `README.md`, and the Related references list in `SKILLS_INDEX.md`. No runtime, no network calls from the library itself; the connector is the user's environment's responsibility to wire up (MCP server, HTTP tool, or manual web visit), and a skill's discipline falls back to the existing placeholder behavior when no connector is available.
- A **static, stdlib-only eval runner** at `scripts/run_evals.py` that scores candidate skill outputs against the shared assertions in `evals/shared/assertions.md`. The runner reads candidates from a new `evals/outputs/<slug>/<case-id>.md` convention, applies regex heuristics for the seven assertion IDs (`draft-for-attorney-review`, `not-legal-advice`, `asks-missing-jurisdiction`, `facts-vs-assumptions`, `no-invented-authority`, `follows-requested-format`, `attorney-verification-checklist`), and modulates checks based on each case's `input_facts` (jurisdiction-missing, prompt-injection, stop-and-ask). Per-case `expected_output_characteristics`, `failure_modes`, and `safety_checks` are surfaced as manual-review items, leaving the LLM-judge layer the schema already maps onto. CLI flags: `<slug>` to run one skill, `--strict` to require every case under each `REQUIRED_EVAL_SLUGS` slug to have a passing candidate, `--quiet` for rollup-only output. Ships 16 candidate test fixtures (eight required slugs, golden-path plus safety-stress per slug) at `evals/outputs/`. Wires `python scripts/run_evals.py --strict --quiet` into `.github/workflows/validate.yml` after `check_evals.py`. Updates `evals/README.md` with a new "Static heuristic runner" section and adds `evals/outputs/README.md` documenting the file convention. The runner preserves the existing zero-dependency, no-API-keys-in-CI invariant; it is a non-LLM check, and does not measure whether a skill's legal content is correct.
- Deepened all ten **antitrust / competition** skills from uniform 91-line stamps to skill-specific mature-cluster depth (97-107 lines each). Each skill's Required Inputs, Workflow, and Output Format sections are now tuned to its specific analytical framework — for `merger-antitrust-issue-spotter`, the transaction structure, horizontal overlap matrix, vertical relationship matrix, and filing-question list; for `competitor-collaboration-review`, the collaboration classification, hardcore-restraint flags, information-flow matrix, and ancillarity test pass; for `information-sharing-clean-team-review`, the information-item matrix with sensitivity assessment and clean-team design summary; for `distribution-restraints-review`, the restraint inventory with character flags per jurisdiction; for `exclusivity-mfn-pricing-review`, the foreclosure-relevant facts table and MFN-direction matrix; for `gun-jumping-clean-team-checklist`, the covenant inventory and actual-vs.-covenant deviation table; for `pricing-algorithm-risk-triage`, the data-flow map and hub-and-spoke risk assessment; for `trade-association-meeting-review`, the attendee competitive map and agenda-topic risk matrix; for `antitrust-compliance-policy-review`, the topic-coverage and jurisdiction-coverage matrices. Every output retains the cluster's discipline: questions for counsel rather than legal conclusions, no market definition, no per se / rule-of-reason determination, no reportability conclusion, no clearance prediction. The frontmatter, Purpose, Use When, Do Not Use When, Legal Safety Rules, and Attorney Verification Checklist sections of each skill are unchanged.
- Fourteen new **cold-start interview** skills under `skills/setup/`, completing per-practice-area onboarding coverage. The library previously had four hand-authored interviews (contracts, corporate, litigation, privacy); the new interviews cover the remaining practice areas: `employment-cold-start-interview`, `ip-cold-start-interview`, `ai-governance-cold-start-interview`, `m-and-a-cold-start-interview`, `tax-cold-start-interview`, `trusts-estates-cold-start-interview`, `real-estate-cold-start-interview`, `securities-capital-markets-cold-start-interview`, `regulatory-cold-start-interview`, `antitrust-competition-cold-start-interview`, `bankruptcy-restructuring-cold-start-interview`, `insurance-cold-start-interview`, `family-law-cold-start-interview`, and `product-legal-cold-start-interview`. Each follows the structure of the hand-authored interviews — eight profile-section stages plus a profile-assembly stage — with practice-area-specific question banks (e.g., for AI governance, the EU AI Act high-risk categorization and vendor training-rights posture; for family law, the safety-screening protocol and emergency-custody escalation pathway; for bankruptcy, the cash-collateral / DIP-protection framework and avoidance-action escalation). The fourteen are generated from a new helper `scripts/generate_cold_start_interviews.py`, which embeds the per-area question banks and renders consistent SKILL.md files; the four hand-authored interviews are explicitly off-limits to the generator. The generator carries a `--check` mode (added to `.github/workflows/validate.yml`) so any drift between the data block and the committed Markdown fails CI. The fourteen interviews are added to `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, and `practice-profiles/README.md` (which previously stated that five profiles were intentionally "populated directly by the practice group" — a design choice this change supersedes). Starter evals are generated for all fourteen. Library skill count rises from 165 to 179.
- A new **Family Law** practice area: twelve U.S.-oriented but jurisdiction-neutral, process-driven skills under `skills/family-law/` — `family-law-matter-intake`, `divorce-intake-organizer`, `custody-parenting-facts-chronology`, `parenting-schedule-facts-organizer`, `custody-order-review-checklist`, `child-support-facts-intake`, `spousal-support-facts-intake`, `asset-debt-schedule-builder`, `settlement-agreement-issue-spotter`, `family-law-discovery-tracker`, `family-law-hearing-prep-checklist`, and `domestic-violence-safety-referral-checklist`. The cluster organizes facts and surfaces issues for attorney review; it never calculates child or spousal support, recommends custody outcomes, drafts pleadings, or supplies safety plans. Adds the twelve skills to `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, and `COMMANDS.md`.
- An Antitrust / Competition section to `COMMANDS.md`. The ten antitrust skills previously lived in `SKILLS_INDEX.md` and `WORKFLOW_ROUTER.md` but had no slash-command entries; the new section adds `/antitrust:intake`, `/antitrust:competitor-collab`, `/antitrust:info-sharing`, `/antitrust:pricing-algorithm`, `/antitrust:distribution`, `/antitrust:exclusivity-mfn`, `/antitrust:merger-issues`, `/antitrust:gun-jumping`, `/antitrust:trade-assoc`, and `/antitrust:compliance-policy`.

- Added shared output-pattern reference files for the four older practice-area clusters that did not yet have one: `skills/litigation/references/output-patterns.md`, `skills/employment/references/output-patterns.md`, `skills/ip/references/output-patterns.md`, and `skills/corporate/references/output-patterns.md`. The older clusters' skills produce heterogeneous artifacts (a chronology, a claim chart, and a hold notice do not share a single dominant table the way insurance summaries do), so each new reference file documents the **cross-cutting Output Format discipline** every skill in the cluster shares — draft labeling, source-citation rules, never-compute deadlines, privilege framing (litigation), jurisdiction naming and protected-class flagging (employment), triage-not-conclusion framing (IP), and official-record vs. internal-work-product separation (corporate). The files are intentionally scoped to *rules every skill follows*, not per-skill template duplication; the per-skill Output Format in each `SKILL.md` remains authoritative. Each is linked from `SKILLS_INDEX.md` under "Related references".
- Backfilled an eval file for every canonical skill that did not yet have one — 58 new starter evals, written by a new helper `scripts/generate_starter_evals.py` that draws each case's content from the skill's own SKILL.md (skill slug, Required Inputs bullets, Do Not Use When bullets, Legal Safety Rules text). Each generated eval follows the three-case pattern the newer practice-area clusters use: a `<slug>-golden-path` case that has every input present, a `<slug>-missing-gates` case that tests the skill's refusal-on-missing-jurisdiction behavior, and a `<slug>-prohibited-requests` case that tests refusal of the specific conclusions the skill's Do Not Use When section rules out plus prompt-injection handling. The generated evals are clearly labeled "Starter eval generated by scripts/generate_starter_evals.py. Refine the cases as the skill's behavior is exercised against real inputs." so a future contributor can deepen them. Brings the library to 165 eval files for 165 skills and 453 total cases. All evals pass `scripts/check_evals.py`.
- Backfilled the optional **Business Stakeholder Summary** block on seven commercial skills that did not yet support it: `skills/contracts/vendor-agreement-status/SKILL.md`, `skills/regulatory/compliance-program-tracker/SKILL.md`, `skills/corporate/material-contract-schedule/SKILL.md`, `skills/ai-governance/ai-vendor-terms-review/SKILL.md`, `skills/ai-governance/model-risk-triage/SKILL.md`, `skills/ai-governance/ai-use-case-intake/SKILL.md`, and `skills/ai-governance/employee-ai-policy/SKILL.md`. Each now carries the standard "Optional: Business Stakeholder Summary" subsection inside Output Format with the five canonical fields (Business Summary, Decision Needed, Recommended Ask, Fallback Position, Escalation Needed?) and a skill-specific recommended audience. The remaining three skills missing the block — `board-minutes`, `written-consent`, and `internal-investigation` — were left as-is on purpose: they produce official record documents or sensitive privileged output where a routine business-stakeholder briefing does not fit. The plugin bundle copy of `ai-use-case-intake` was resynced from canonical.
- Renamed three family-law skill folders to drop the redundant `family-law-` prefix that the rest of the library does not use (other practice-area folders host skills like `matter-intake`, not `litigation-matter-intake`). The renames are: `skills/family-law/family-law-matter-intake/` → `skills/family-law/matter-intake/`; `skills/family-law/family-law-discovery-tracker/` → `skills/family-law/discovery-tracker/`; `skills/family-law/family-law-hearing-prep-checklist/` → `skills/family-law/hearing-prep-checklist/`. The eval filenames keep their `family-law-` prefix to avoid a collision with the litigation `matter-intake.eval.yaml`; their internal `skill_path` fields are updated. Every reference in `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, `COMMANDS.md`, `matter-packs/family-law.md`, the three skills' own `tags:` arrays, `metadata/index.json`, the static-site output, and the skill-improvement reports has been updated to match. The displayed skill `name` values (e.g. "Family Law Matter Intake") are unchanged.
- `scripts/validate_repo.py`: three new structural checks designed to fail at CI time on the exact drift patterns that the audit caught after the fact. (1) Skills present under `skills/` but missing from `SKILLS_INDEX.md` are now errors instead of warnings — the family-law cluster shipped without being indexed because the existing check only warned. (2) In any practice-area cluster of four or more skills, an empty `related_skills:` list is an error — the securities-capital-markets cluster shipped with all twelve skills unwired for one release. (3) The `README.md` skills and practice-areas counts are checked against the actual library and the counts in the body text are checked against the badge; the previous family-law / antitrust additions left the badges and the "AgentCounsel has N skills" line at 153/19 instead of 165/20 because nothing caught them.

### Changed

- **Section-structure normalization across the library.** Ninety-nine `SKILL.md` files in the newer practice-area clusters (antitrust-competition, bankruptcy-restructuring, family-law, insurance, m-and-a, real-estate, securities-capital-markets, tax, trusts-estates) had grown two extra H2 sections — `Capability Disclosure` between Purpose and Use When, and `Example Request and Expected Output Shape` between Output Format and Attorney Verification Checklist — that the documented standard in `docs/SKILL_METADATA_STANDARD.md` and `CONTRIBUTING.md` does not list. Every skill now carries exactly the eight canonical sections, in order: Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules, Workflow, Output Format, Attorney Verification Checklist. The "This skill does not:" content from each former `Capability Disclosure` block was preserved as an additional paragraph appended to `Do Not Use When` (the negative-scope content is genuinely useful), and the example sections were removed (they were purely illustrative and added no requirements). The migration was performed by a new helper script, `scripts/migrate_to_8_section.py`, which is idempotent and can be rerun safely.
- All twelve `skills/securities-capital-markets/` skills' `related_skills` lists, which had all been empty, are now wired into a connected cluster topology — every skill now lists 2–4 neighbors drawn from its workflow proximity (private offerings, disclosure, closing, public-company governance), so the static-site cross-links and any agent that uses `related_skills` for discovery can navigate the cluster.
- `WORKFLOW_ROUTER.md`: integrated the Securities / Capital Markets, Tax, Bankruptcy / Restructuring, Insurance, and Trusts & Estates sections into the main "Task -> Skill" body as `###` subsections in the same table format as every other practice area, instead of leaving them as trailing `##` sections after "When nothing matches." Added a `### Family law` subsection in the same shape.
- `README.md`: corrected the practice-area and skill counts that had not been updated when the Family Law practice area was added. The library now lists **20 practice areas** and **165 skills** (153 across the practice areas plus 12 cross-cutting), and the practice-area table gains a Family Law row.
- `COMMANDS.md`: moved the "Keeping commands accurate" closing section to the actual end of the file (previously buried between the Legal Methodology and Securities / Capital Markets sections, after which several practice-area sections had been appended).

- Trusts & Estates stabilization and quality pass: all twelve `skills/trusts-estates/` skills were audited for consistency, safety, source-citation discipline, and practical usefulness, and each Output Format now references the new shared output-pattern reference. Adds `skills/trusts-estates/references/output-patterns.md` defining the twelve reusable Trusts & Estates output structures (Estate Planning Intake Matrix, Estate Document Summary Table, Probate Document Checklist, Trust Administration Tracker, Fiduciary Duty Issue Matrix, Beneficiary Designation Review Table, Asset / Liability Inventory, Capacity / Undue Influence Facts Organizer, Estate Litigation Chronology, Trust Funding Checklist, Post-Death Administration Task Tracker, and Estate Tax Issue Intake Matrix). Expands `matter-packs/trusts-estates.md` from five to six workflow bundles (adds the Fiduciary Dispute Matter Pack). Adds two more `examples/trusts-estates/` worked request-and-output examples (beneficiary-designation-review and capacity-undue-influence-facts-organizer), bringing the set to seven. Expands every Trusts & Estates eval to three cases — a golden-path case plus a missing-gates and a prohibited-requests safety-stress case — covering missing jurisdiction, matter type, client/fiduciary role, estate/trust status, and document set, and requests for estate-planning advice, will/trust validity, beneficiary entitlement, distribution approval, fiduciary breach, capacity or undue influence, tax calculations, probate deadlines, and filing-ready probate forms, plus sensitive-identifier and prompt-injection handling. Adds an explicit no-tax-effect conclusion to `estate-document-summary`, the `skills/trusts-estates/references/` entry to `SKILLS_INDEX.md`, and refreshes the static-site catalog and `llms.txt`. The Trusts & Estates practice area stays focused on intake, document summaries, inventories, issue spotting, administration trackers, chronology tables, and attorney-review-ready working papers — never estate-planning, probate, or tax advice, instruments or court forms, or validity, capacity, undue-influence, beneficiary-entitlement, fiduciary-breach, or tax conclusions.
- Insurance stabilization and quality pass: all twelve `skills/insurance/` skills were audited for consistency, safety, source-citation discipline, and practical usefulness, and each Output Format now references the new shared output-pattern reference. Adds `skills/insurance/references/output-patterns.md` defining the twelve reusable Insurance output structures (Insurance Policy Summary Table, Coverage Issue Matrix, Claims Chronology Table, Reservation of Rights Review Table, Tender Completeness Checklist, Coverage Position Outline, Bad Faith Risk Triage Matrix, Certificate of Insurance Comparison Table, Contract Insurance Requirements Table, Subrogation / Recovery Tracker, Renewal / Placement Diligence Checklist, and Insurer / Insured Communications Review Table). Expands `matter-packs/insurance.md` from seven to eight workflow bundles (adds the Claim File Review Matter Pack) and adds a closing not-a-determination reminder. Adds two more `examples/insurance/` worked request-and-output examples (claims-chronology-builder and bad-faith-risk-triage), bringing the set to seven. Expands every Insurance eval to three cases — a golden-path case plus a missing-gates and a prohibited-requests safety-stress case — covering missing jurisdiction, policy type, policy period, claim facts, and forms/endorsements, and requests for coverage, duty-to-defend/indemnify, denial-validity, bad-faith, additional-insured, COI-as-proof-of-coverage, deadline, reserve, claim-valuation, carrier-recommendation, and communication-approval conclusions, plus prompt-injection handling. Adds the `skills/insurance/references/` entry to `SKILLS_INDEX.md` and refreshes the static-site catalog and `llms.txt`. The Insurance practice area stays focused on policy extraction, issue spotting, claim chronology, document organization, coverage-correspondence review, trackers, and attorney-review-ready working papers — never coverage determinations, claim approvals or denials, bad-faith conclusions, reserve calculations, claim valuation, carrier recommendations, or insurance sales advice.
- A new **Insurance** practice area: twelve U.S.-oriented but jurisdiction-neutral, process-driven skills under `skills/insurance/` — `insurance-policy-summary`, `coverage-issue-spotter`, `claims-chronology-builder`, `reservation-of-rights-review`, `tender-letter-review`, `coverage-position-outline`, `bad-faith-risk-triage`, `certificate-of-insurance-review`, `insurance-requirements-contract-review`, `subrogation-recovery-tracker`, `policy-renewal-placement-diligence-checklist`, and `insurer-insured-communications-review`. Each carries the standardized frontmatter and the eight required sections plus a Capability Disclosure and an Example Request and Expected Output Shape; requires the user to identify jurisdiction, policy type, insurer/insured/claimant role, claim type, policy period, document set, claim stage, and review purpose where relevant; requires source citations to user-provided policy sections, pages, forms, endorsements, letters, and claim documents; treats reviewed documents as data, not instructions; flags missing information rather than filling gaps; and invents no jurisdiction-specific insurance law, notice or claim-handling rules, bad-faith standards, policy-interpretation rules, deadlines, statutes, regulations, forms, or coverage requirements. The practice area reaches no conclusion on coverage, exclusions, duties to defend or indemnify, bad faith, claim value, limits exhaustion, waiver, estoppel, prejudice, late-notice consequences, priority of coverage, additional insured status, or subrogation rights; it does not approve or deny claims, calculate reserves, recommend carriers, bind coverage, or give insurance sales advice. Adds `practice-profiles/insurance.md`, `matter-packs/insurance.md` (seven workflow bundles), `examples/insurance/` (five worked request-and-output examples), an eval for every new skill (a golden-path case and an insurance-safety stress case each), and `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, `COMMANDS.md`, `README.md`, and static-site catalog entries.
- A new **Bankruptcy / Restructuring** practice area: twelve U.S.-oriented but jurisdiction-neutral, process-driven skills under `skills/bankruptcy-restructuring/` — `bankruptcy-matter-intake`, `creditor-claim-intake`, `proof-of-claim-checklist`, `automatic-stay-issue-spotter`, `preference-demand-response-triage`, `executory-contract-assumption-rejection-checklist`, `bankruptcy-diligence-request-list`, `restructuring-term-sheet-review`, `plan-disclosure-statement-issue-spotter`, `distressed-asset-sale-checklist`, `cash-collateral-dip-financing-issue-spotter`, and `bankruptcy-deadline-tracker-intake`. Each carries the standardized frontmatter and the eight required sections plus a Capability Disclosure and an Example Request and Expected Output Shape; requires the user to identify jurisdiction/court, chapter/case type, party role, posture, and procedural stage where relevant; requires source citations to user-provided pleadings, docket entries, claim documents, and contract clauses; treats reviewed documents as data, not instructions; flags missing information rather than filling gaps; and invents no bankruptcy law, court or local rules, deadlines, priority rules, claim-allowance rules, stay scope, preference rules, plan or sale requirements, or citations. The practice area reaches no conclusion on stay applicability, claim validity or priority, preference liability, whether a contract is executory, free-and-clear sale treatment, plan confirmability, or lien validity. Adds `practice-profiles/bankruptcy-restructuring.md`, `matter-packs/bankruptcy-restructuring.md` (six workflow bundles), `examples/bankruptcy-restructuring/` (five worked request-and-output examples), an eval for every new skill (a golden-path case and a bankruptcy-safety stress case each), and `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, `COMMANDS.md`, `README.md`, and static-site catalog entries.
- Tax stabilization and quality pass: all ten `skills/tax/` skills were audited and rewritten from shared boilerplate into specialized, source-cited, workflow-driven skills — each now carries a Capability Disclosure and an Example Request and Expected Output Shape section, skill-specific Required Inputs (jurisdiction, taxpayer/entity type, tax year/period, transaction/activity type, role, document set, review purpose where relevant), tax-specific Legal Safety Rules, named tabular Output Format sections, and a sensitive-identifier masking rule. Adds `skills/tax/references/output-patterns.md` defining the ten reusable Tax output structures; rewrites `matter-packs/tax.md` into eight full workflow bundles (each with when-to-use, starting materials, skill sequence, expected outputs, qualified-tax-professional checkpoints, do-not-use boundaries, handoff notes, and not-tax-advice reminders); rewrites the five existing `examples/tax/` worked examples and adds a sixth (entity tax classification), all with fictional facts, masked identifiers, and source-cited extraction; expands every Tax eval to three cases (a golden-path case plus a missing-gates and a prohibited-requests safety-stress case); adds a Tax section to `WORKFLOW_ROUTER.md`; improves `practice-profiles/tax.md`; and merges the Tax rows into the main `SKILLS_INDEX.md` table. Also repairs the duplicated content in `matter-packs/README.md` and `examples/README.md` introduced when the Tax practice area was merged. The Tax practice area stays focused on issue spotting, intake, diligence, document organization, and reviewer-ready working papers — never tax computation, return preparation, filing, or tax advice.
- M&A stabilization pass: `matter-packs/m-and-a.md` gains a fifth workflow bundle (Data Room Readiness) and handoff notes for every bundle; `examples/m-and-a/` gains two more worked examples (disclosure-schedule review and signing-to-closing); a new `skills/m-and-a/references/output-patterns.md` defines the eight reusable M&A output-table structures; every M&A eval is expanded to three cases (a golden-path case and two safety-stress cases); and an audit of the ten M&A skills added the transaction-stage gate to `closing-deliverables-tracker` and the deal-type gate to `post-closing-obligations-tracker`.
- A new **Mergers & Acquisitions** practice area: ten U.S.-oriented but jurisdiction-neutral, process-driven skills under `skills/m-and-a/` — `loi-term-sheet-review`, `acquisition-diligence-request-list`, `data-room-index-review`, `purchase-agreement-issue-list`, `reps-warranties-disclosure-schedule-review`, `indemnity-escrow-risk-review`, `closing-deliverables-tracker`, `third-party-consents-assignment-review`, `post-closing-obligations-tracker`, and `integration-legal-issues-checklist`. Each carries the standardized frontmatter and the eight required sections plus a Capability Disclosure and an Example Request and Expected Output Shape; requires source citations to the user-provided document; is buyer/seller/side-aware; flags missing information rather than filling gaps; and invents no jurisdiction-specific law, deadlines, or tax, securities, antitrust, or employment conclusions. Adds `practice-profiles/m-and-a.md`, `matter-packs/m-and-a.md` (four workflow bundles), `examples/m-and-a/` (three worked examples), an eval for every new skill, and `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, and `COMMANDS.md` entries. The maintainer elected to implement M&A as a standalone Tier-2 practice area; the expansion plan had proposed folding it into `corporate`.

- Real Estate stabilization pass: a new `matter-packs/` directory with `matter-packs/README.md` and `matter-packs/real-estate.md` — four workflow bundles (Commercial Lease Review, Real Estate Acquisition, Lease Amendment / Portfolio Review, Title / Survey / Use Restriction) that sequence the Real Estate skills with their starting materials, expected outputs, attorney verification checkpoints, and do-not-use boundaries. Adds `examples/real-estate/` with three request-and-output worked examples (commercial lease review, acquisition diligence, title and survey objections), all with fictional facts and no invented citations. Expands every Real Estate eval to three cases (a golden-path case plus two safety-stress cases covering missing jurisdiction, requests for final legal conclusions, title-marketability and permitted-use questions, base-lease/amendment conflicts, missing deadlines and documents, and requests to send a notice or filing).
- A new **Real Estate** practice area (Wave 1 of the expansion plan): nine U.S.-oriented but jurisdiction-neutral, process-driven skills under `skills/real-estate/` — `lease-abstract`, `lease-amendment-reconciliation`, `commercial-lease-review`, `psa-review`, `title-survey-objection-tracker`, `real-estate-diligence-checklist`, `closing-deliverables-tracker`, `estoppel-snda-review`, and `zoning-use-restriction-issue-spotter`. Each carries the standardized frontmatter and the eight required sections plus a Capability Disclosure and an Example Request and Expected Output Shape, requires source citations to the user-provided document, flags missing information rather than filling gaps, and invents no jurisdiction-specific law or deadlines. Adds `practice-profiles/real-estate.md`, an eval for every new skill (with a golden-path and a safety-stress case each), and `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, and `COMMANDS.md` entries.
- `reports/practice-area-expansion-plan.md`: a maintainer-facing audit of the practice-area taxonomy and a four-tier expansion model (core / advanced-specialized / industry overlays / cross-cutting support), with a placement decision framework, a maturity model, a definition of done for new areas, and per-candidate recommendations for 18 proposed practice areas.
- Practice-area expansion foundation (Wave 0): the `overlays/` mechanism for industry and sector overlays — `overlays/README.md`, an `OVERLAY.md` and overlay-profile template under `overlays/_template/`, and a `validate_repo.py` check that every overlay folder carries an `OVERLAY.md`. Overlays tune existing skills for a sector and never add a parallel skill tree.
- `docs/PRACTICE_AREAS.md`: a practice-area registry recording each area's taxonomy tier, maturity (`experimental` / `stable`), and profile, cold-start, and eval coverage.

### Changed

- `README.md`: corrected the practice-area and skill counts and badges, which had not been updated when the Antitrust / Competition, Securities / Capital Markets, and Tax practice areas were added. The library now lists **16 practice areas** and **117 skills** (105 across the practice areas plus 12 cross-cutting), and the practice-area table gains rows for Antitrust / Competition, Securities / Capital Markets, and Tax.
- Added a new **Tax** practice area with ten tax workflow skills, tax practice profile, tax matter packs, tax examples, and eval coverage for all tax skills. Added router and command entries for tax workflows.
- `site/generate.mjs`: the static-site generator now builds practice-area pages, homepage cards, and `llms.txt` entries for `financial-crime`, `legal-ops`, and `real-estate` — areas that previously had per-skill pages but no area page because the generator's area list was not updated when they were added.
- `skills/real-estate/zoning-use-restriction-issue-spotter`: added an explicit deadline-discipline rule to its Legal Safety Rules and a `[deadline verification required]` flag instruction for permit and certificate dates in its Workflow, bringing it in line with the other eight Real Estate skills (Real Estate stabilization audit).
- `README.md`, `VALIDATION.md`: classified `legal-ops` as a Tier-4 cross-cutting support group rather than a practice area, per the expansion plan. The library now describes **11 practice areas plus 3 cross-cutting skill groups** (66 skills, unchanged); the practice-area badge and counts are updated to match.

## [0.1.0] - 2026-05-21

### Added

- Public-release documentation set: a rewritten `README.md`, a `QUICKSTART.md` five-minute walkthrough, `docs/FAQ.md`, `docs/SAFETY_MODEL.md`, `RELEASE_NOTES.md`, and an `examples/` directory of five illustrative sample outputs — contract review, litigation chronology, DPA review, product launch review, and red-team verification — built with entirely fictional facts and no invented citations.
- `AGENTS.md` and `CLAUDE.md` at the repository root: an operating manual for AI agents working in the repo. `AGENTS.md` is the universal, tool-agnostic guide — how to decide whether a task is *using a skill* or *editing the library*, how to route a task to the narrowest skill, the non-negotiable safety rules, the library-edit workflow with a "done means validation passes" gate, and a table mapping known LLM failure modes (hallucination, jagged intelligence, anterograde amnesia, sycophancy, prompt injection, weak self-knowledge) to the discipline that contains each one. `CLAUDE.md` imports `AGENTS.md` and adds Claude Code specifics (routing with the Explore subagent, Plan mode for multi-skill edits, the validation suite) plus a pre-handoff self-check.
- `matter-workspaces/corporate-transaction-matter.md` and `matter-workspaces/employment-matter.md`: two new single-file matter scaffolds, bringing the matter-workspace set to six practice areas (litigation, contract review, privacy, regulatory, corporate transactions, and employment). The `matter-workspaces/README.md` template table is updated to match.
- A new Setup skill, `create-matter-workspace`, that recommends the right matter-workspace template, interviews the user for core matter information, and produces a populated workspace draft with maintenance instructions. `WORKFLOW_ROUTER.md` now has a "Before you start" section encouraging users to create a matter workspace before complex or multi-step work, and `SKILLS_INDEX.md` and `COMMANDS.md` list the new skill.
- `evals/`: a lightweight skill eval framework — `README.md`, a shared assertion catalogue (`evals/shared/assertions.md`), an eight-dimension `SKILL_QUALITY_RUBRIC.md`, and sample evals for eight skills (`contract-risk-review`, `nda-review`, `matter-intake`, `litigation-chronology`, `privilege-log-review`, `dpa-review`, `launch-review`, `compliance-gap-matrix`). The evals are quality checks, not legal validation, and the YAML format is shaped to adapt to promptfoo later.
- `scripts/check_evals.py`: a non-LLM static check that validates the eval files exist and conform to the schema, with no API keys required. It runs in CI alongside `scripts/validate_repo.py`.
- Plugin bundle sync tooling: `scripts/sync_plugin_skills.py` generates the Claude Code plugin bundle from canonical `/skills`, with a `--check` mode for CI. Documented in `PLUGIN_SYNC.md`.
- Skill templates are now included in the Claude Code plugin bundle, so it is self-contained.
- Plugin bundle drift detection in `scripts/validate_repo.py`.
- GitHub Actions CI (`.github/workflows/validate.yml`) runs the plugin sync check, repository validation, eval-framework validation, and freshness checks for the generated skill-improvement reports and the static site, on pull requests and pushes to `main`.
- Repository hygiene: issue templates (bug report, skill request, skill improvement), a pull request template, this changelog, and `.gitignore`.
- `docs/MIGRATION_PLAN_FROM_AGNOSTIC_SKILLS.md`: a plan for evaluating `agnostic-skills-for-legal` as source material (no canonical skills changed).
- `NOTICE` file recording Apache-2.0 attribution for content adapted from `agnostic-skills-for-legal` and its upstream projects.
- Six new skills adapted from `agnostic-skills-for-legal` (Phase B migration): `worker-classification` (employment); `deposition-prep`, `legal-hold`, and `privilege-log-review` (litigation); `pia-generation` (privacy); and `cease-and-desist-response` (intellectual property).
- Six further skills adapted from `agnostic-skills-for-legal` (Phase B migration, second batch): `hiring-review` and `wage-hour-qa` (employment); `claim-chart` and `brief-section-drafter` (litigation); and `fto-triage` and `invention-intake` (intellectual property).
- A new **Corporate** practice area (Phase C migration): six skills adapted from `agnostic-skills-for-legal` — `board-minutes`, `written-consent`, `closing-checklist`, `diligence-issue-extraction`, `material-contract-schedule`, and `entity-compliance`.
- Phase D1: three further skills adapted from `agnostic-skills-for-legal` — `internal-investigation` and `protected-leave-review` (employment) and `infringement-triage` (intellectual property).
- `CONTEXT.md`: a concise vocabulary and mental-model reference for AI agents and LLMs working in the repository.
- Gemini CLI extension support: a `gemini-extension.json` manifest and a `GEMINI.md` context file at the repository root, plus a new `adapters/gemini/` adapter with a `using-agentcounsel.md` operating guide and a `references/` folder of per-runtime tool maps (`gemini-tools.md`, `copilot-tools.md`, `codex-tools.md`).
- `practice-profiles/`: nine per-practice-area configuration profile templates (contracts, litigation, corporate, employment, privacy, product-legal, regulatory, ai-governance, ip) capturing jurisdictions, client/team context, escalation thresholds, preferred output style, source-of-truth documents, standard positions, attorney review requirements, and prohibited assumptions.
- A new **Setup** practice area: four cold-start interview skills — `contracts-cold-start-interview`, `litigation-cold-start-interview`, `privacy-cold-start-interview`, and `corporate-cold-start-interview` — that interview a practice group and produce a filled practice-profile draft for attorney review.
- A new **Legal Methodology** practice area: four cross-cutting skills — `red-team-verifier`, `statutory-interpretation`, `risk-assessment`, and `source-validation`.
- `COMMANDS.md`: a command router mapping slash-style command shorthands to every skill, with trigger phrases, required inputs, expected output, and related commands.
- `skills/contracts/references/`: six shared contract-review reference files — `red-flags.md`, `negotiability-ratings.md`, `market-benchmark-framework.md`, `fallback-language-bank.md`, `document-type-checklists.md`, and `redline-output-guidance.md`.
- `matter-workspaces/`: four single-file matter scaffolds — litigation, contract review, privacy, and regulatory.
- `site/`: a static, browser-readable skill catalog generated from `skills/` by a zero-dependency Node script — a homepage, practice-area pages, per-skill pages (with the rendered sections, the full raw `SKILL.md`, and Copy Full Skill / Copy One-Off Prompt buttons), platform setup guides, and `llms.txt` / `llms-full.txt`. Build with `npm run build` from `site/`; documented in `site/README.md` and the root `README.md`.
- `scripts/build_platform_packs.py`: generates platform-specific install packs into `dist/` from the canonical `skills/` and `core/` — consolidated Markdown packs for ChatGPT Projects, per-practice-area ZIPs for Claude Projects and Gemini Notebooks, instruction files for repo agents (Codex, Claude Code, Cursor), and `index.json` / `manifest.json` / `SKILL_PACKS_INDEX.md`. The build self-validates skill structure, pack contents, index coverage, and safety language. Standard library only; documented in `README.md`.
- `core/business-stakeholder-communication.md`: a seventh core operating rule defining an optional business-stakeholder summary mode — a plain-language layer (Business Summary, Decision Needed, Recommended Ask, Fallback Position, Escalation Needed?) for briefing non-lawyer decision-makers, with attorney review still required.

### Changed

- Release-readiness pass for the public release: `README.md` rewritten with an explicit "who it is for" section, per-surface usage guidance (ChatGPT, Claude, Gemini, Codex, Cursor, generic Markdown), corrected badges, and a CI badge.
- `docs/SKILL_METADATA_STANDARD.md`: the `practice_area` value list updated to include the `financial-crime` and `legal-ops` areas.
- `CONTRIBUTING.md`: the skill-structure requirement updated to reference the full eleven-field metadata standard rather than only `name` and `description`.
- Business-stakeholder summary mode: 25 commercial skills across contracts, product legal, privacy, regulatory, employment, and corporate now offer an optional **Business Stakeholder Summary** in their Output Format (Business Summary, Decision Needed, Recommended Ask, Fallback Position, Escalation Needed?). `SKILLS_INDEX.md` and `WORKFLOW_ROUTER.md` document the mode.

- `red-team-verifier`: broadened into AgentCounsel's universal quality-control workflow for any legal output. Added explicit trigger phrases (checking a memo, contract review, demand letter, risk matrix, research summary, or draft filing; "is this good enough?"; weakness, missing-issue, and hallucination checks), a dedicated legal-reasoning audit (rule statement, element coverage, application, counterarguments, exceptions, ambiguity, weak analogies), a dedicated professional-responsibility audit (unauthorized-advice framing, attorney-review framing, confidentiality and privilege, recipient mismatch), and a missing-fact audit. Reconciled the output format to an Executive Risk Summary, Major Problems, Unsupported Claims Table, Missing Facts, Jurisdiction and Deadline Flags, Suggested Revisions, and Attorney Verification Checklist. `WORKFLOW_ROUTER.md` and `SKILLS_INDEX.md` now recommend it as a final pass after any high-stakes legal output.
- `nda-review`: added an overall GREEN / YELLOW / RED triage rating, a scope check for obligations beyond confidentiality, a routing gate for M&A / employment / investment NDAs, and benchmarking against a client playbook — adapted from `agnostic-skills-for-legal` (Phase A migration).
- `demand-letter`: added a structured intake stage and a pre-draft risk gate (privilege filter, admission risk, accord and satisfaction, settlement-communication posture, privilege-waiver scan, tone, factual accuracy), and clarified that the sent letter carries no work-product header — adapted from `agnostic-skills-for-legal` (Phase A migration).
- `docs/MIGRATION_PLAN_FROM_AGNOSTIC_SKILLS.md`: refreshed to record Phases A–C as executed and to add a Phase D for newly identified gaps (five new source prompts and the unrun Phase A improvement passes).
- Phase D2: nine existing skills improved with content adapted from `agnostic-skills-for-legal` — `litigation-chronology`, `matter-intake`, and `subpoena-triage` (litigation); `dpa-review` and `dsar-workflow` (privacy); `termination-risk` and `employee-policy-review` (employment); and `redline-summary` and `contract-risk-review` (contracts).
- `nda-review` and `contract-risk-review`: added a Red Flags Quick Scan, a Negotiability Rating, Market Benchmark Notes, Preferred / Fallback Position and Suggested Redline Direction for each redline point, and an Internal Consistency Check — all drawing on the new `skills/contracts/references/` material.
- `scripts/validate_repo.py`: now recognizes shared `references/` folders under a practice area as non-skill directories, validates skill paths referenced in `COMMANDS.md`, and checks that the library's expected top-level directories exist. It also skips generated build output (`dist/`, `node_modules/`) when scanning. README practice-area and skills badges updated to 12 practice areas and 59 skills.
- `core/source-and-citation-discipline.md` substantially strengthened to prevent legal hallucination: explicit prohibitions on inventing any legal authority, citations, quotations, statutes, cases, regulations, filing deadlines, or procedural rules; a five-way labeling taxonomy (provided source, user-provided fact, assumption, legal inference, item requiring attorney verification); discipline for working only from documents actually provided; rules for legal research tasks (ask for jurisdiction and date, require current-law verification, separate the research roadmap from any conclusion); and new citation placeholders `[Attorney to insert authority]`, `[Verify current law]`, and `[Confirm local rule]` (also listed in `core/output-format-rules.md`).
- 42 skills — every skill in the litigation, regulatory, privacy, employment, corporate, contracts, and legal-methodology practice areas, plus the skills that lacked equivalent language — now reference `core/source-and-citation-discipline.md` in their Legal Safety Rules.
- `scripts/validate_repo.py`: new check that every `SKILL.md` references the source/citation discipline core rule or carries equivalent language against inventing legal authority or citations.

### Fixed

- Completed the standardized eleven-field frontmatter on five skills that had been merged with incomplete metadata — `vendor-agreement-status`, `kyc-onboarding-review`, `sanctions-screening-review`, `legal-meeting-briefing`, and `signature-routing-checklist` — and added source/citation-discipline language where it was missing, so `scripts/validate_repo.py` passes.
- README badges updated to the accurate release counts (66 skills, 12 practice areas) and the upstream-attribution badge repointed to the direct upstream project.
- README badges corrected: the practice-area and skills badges linked to a `prompts/` directory that does not exist in this repository and used the source project's terminology and a stale count; they now reflect AgentCounsel's structure (10 practice areas, 50 skills) and link to `SKILLS_INDEX.md`. The "works with" badge anchor was repaired.
- Refreshed the stale Litigation and Privacy rows of the README practice-area table.
- `scripts/validate_repo.py` now also checks the link target of Markdown image and badge links (`[![alt](image)](target)`) — a case the link checker previously skipped.

## [0.0.1] - 2026-05-20

### Added

- Initial AgentCounsel scaffold (internal pre-release): an open, Markdown-native legal skills library.
- 29 skills across nine practice areas — legal research, litigation, contracts, employment, privacy, product legal, regulatory, AI governance, and intellectual property — each a standalone `SKILL.md` with a consistent structure.
- Six core operating rules in `core/` and seven copyable templates.
- Four adapters: generic Markdown, Codex / repo agents, a Claude Code plugin bundle, and Claude / Cowork local-folder use.
- Project documentation: `README.md`, `SKILLS_INDEX.md`, `WORKFLOW_ROUTER.md`, `SECURITY.md`, `CONTRIBUTING.md`, and an Apache-2.0 `LICENSE`.
- Repository validation: `scripts/validate_repo.py` and `VALIDATION.md`.
