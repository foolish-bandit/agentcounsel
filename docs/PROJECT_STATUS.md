# Project Status

This is an honest status snapshot of what AgentCounsel is today, labeled by
maturity. AgentCounsel is **pre-1.0**: the core skills library is solid, but
newer surfaces are still settling and the whole library produces draft legal
work product that a qualified, licensed attorney must review. Nothing here is an
AI lawyer, and it does not give legal advice.

This page describes maturity, not law. For how the safety model works, see
[`SAFETY_MODEL.md`](SAFETY_MODEL.md).

## Stable

These parts of the library are established and exercised by the validation and
CI tooling on every change:

- The **skills library** itself, grouped by practice area under
  [`../skills/`](../skills/), with the fixed **8-section skill structure**
  (Purpose, Use When, Required Inputs, Do Not Use When, Legal Safety Rules,
  Workflow, Output Format, Attorney Verification Checklist).
- The **core operating rules** every skill inherits, in [`../core/`](../core/).
- The generated metadata: [`../metadata/index.json`](../metadata/index.json), [`../metadata/router.json`](../metadata/router.json), [`../metadata/skill_specs.json`](../metadata/skill_specs.json), [`../metadata/selective_context_metrics.json`](../metadata/selective_context_metrics.json), and [`../metadata/packs.json`](../metadata/packs.json).
- **Platform packs** that bundle skills, core rules, and quality checks for a
  given platform.
- The **validation and CI scripts** in [`../scripts/`](../scripts/), run by
  [`../.github/workflows/`](../.github/workflows/) on every pull request. See
  [`../VALIDATION.md`](../VALIDATION.md).
- The **static site** generated into [`../site/`](../site/).
- The **quick start** guide, [`../QUICKSTART.md`](../QUICKSTART.md).
- Both **single-file and multi-file matter workspaces** under
  [`../matter-workspaces/`](../matter-workspaces/).

## Manual review required

Some things are not, and are not designed to be, handled automatically. These
always require a human attorney:

- **All legal output, always.** Every deliverable is a draft for attorney
  review. There is no path that produces a final, relied-upon legal answer.
- **Evals do not verify legal correctness.** The eval system in
  [`../evals/`](../evals/) checks *structure, routing, metadata, and safety
  signals* — whether a skill has the right sections, points to the right places,
  carries valid metadata, and uses safe framing. It does **not** check whether
  the legal substance of any output is correct. A passing eval says the skill is
  well-formed, not that its analysis is right.
- **Deadlines are never computed.** Every date, limitations period, filing
  window, or notice period is flagged for attorney verification, never
  calculated. See [`../core/jurisdiction-and-deadline-gates.md`](../core/jurisdiction-and-deadline-gates.md).
- **Citations must be attorney-verified.** The citation and source quality
  checks are structured review workflows that surface invented or unsupported
  authority; they do not confirm that a citation is real, current, or on point.

## Experimental / newer

These surfaces exist and are usable, but are newer and still settling. Expect
their structure and conventions to keep evolving:

- **Typed execution and selective context** are new but fully validated. Every skill has a compiled contract, while the first two physically modularized workflows exercise deterministic mode- and input-based loading. The MCP bundle API, context budgets, decision traces, and pack compatibility are expected to evolve before 1.0.
- **Playbooks** in [`../playbooks/`](../playbooks/). See
  [`PLAYBOOKS.md`](PLAYBOOKS.md).
- **Review panels** in [`../review-panels/`](../review-panels/). See
  [`REVIEW_PANELS.md`](REVIEW_PANELS.md).
- The **multi-file matter workspace template** at
  [`../matter-workspaces/_template/`](../matter-workspaces/_template/) and its
  initializer
  [`../scripts/init_matter_workspace.py`](../scripts/init_matter_workspace.py).
  See [`MATTER_WORKSPACES.md`](MATTER_WORKSPACES.md).
- **Connectors** in [`../connectors/`](../connectors/) — Markdown-only
  descriptions of external sources a skill can consult to help verify citation
  placeholders. No runtime.

## Future platform concepts (not built)

[`LOCAL_PLATFORM_PATH.md`](LOCAL_PLATFORM_PATH.md) sketches, at the architecture
level only, an optional future application layer on top of the unchanged
Markdown library. **None of it is built.** In summary, it describes:

- a **local desktop app** that opens and renders matter directories and runs the
  existing scripts locally;
- a **self-hosted web app** serving the same view from the user's own
  infrastructure;
- a **matter-scoped chat** grounded only in a single workspace's own facts,
  source log, and documents; and
- **local model compatibility** through a pluggable, OpenAI-compatible local
  inference endpoint (for example LocalAI or Ollama), so a matter can be worked
  on-device with no third-party model call.

These are design notes to keep the library a clean foundation — not committed
features.

## What AgentCounsel intentionally does not do

These are deliberate limits, not gaps waiting to be filled:

- No authentication, database, payments, hosted backend, hosted SaaS, or chat
  UI. The library is plain Markdown.
- It is **not an AI lawyer** and does not present itself as one.
- It does **not give legal advice** or tell you what you must do.
- It does **not state jurisdiction-specific law** — the law of a jurisdiction is
  supplied by the supervising attorney, per matter.
- It does **not compute deadlines**.
- It does **not verify legal correctness automatically** — the validator and
  evals check structure and consistency, not legal accuracy.
