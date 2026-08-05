# Choose Your Workflow

AgentCounsel is a Markdown-native library of legal **skills**. Every surface in
the library produces **draft legal work product for attorney review** — never
legal advice, never a final answer. This guide helps you pick the right surface
for the task in front of you.

Most tasks are a single skill run. You have one document and you want one draft
output: open the narrowest `SKILL.md` that fits and follow it. Larger or
recurring work uses the other surfaces — quality checks, packs, matter
workspaces, playbooks, and review panels — that wrap, bundle, or organize those
skills. Start narrow; reach for a heavier surface only when the task actually
needs it.

**New to AgentCounsel?** You only need the first row of the table below — a
one-off skill (or the practice-area pack you installed from
[QUICKSTART.md](../QUICKSTART.md), which routes to skills for you). Ignore
matter packs, matter plans, workspaces, playbooks, and review panels until you have run a few
skills; they will make much more sense then.

For mapping a specific "I need to do X" request to a skill, use
[`../WORKFLOW_ROUTER.md`](../WORKFLOW_ROUTER.md). This page is about choosing the
*shape* of the work.

## The eight surfaces

| Surface | Use it when | Example | Where it lives |
|---|---|---|---|
| One-off skill | You have one self-contained task and want one draft output. | "Review this NDA." | `skills/<area>/<skill>/SKILL.md` |
| Quality check | A draft already exists and you want to audit its prose, citations, sources, assumptions, or format. | "Polish this paragraph"; "check these citations." | `skills/legal-methodology/<check>/SKILL.md` |
| Practice-area pack | You run several tasks in one practice area on a given platform (Claude, ChatGPT, Gemini, Cursor, Codex). | "Set up our contracts team in Claude." | [`../metadata/packs.json`](../metadata/packs.json) |
| Matter pack | You need human-readable guidance for an ordered sequence of skills. | "Show our standard M&A diligence sequence." | [`../matter-packs/`](../matter-packs/) |
| Matter plan | A supported recurring matter needs a validated dependency graph, typed handoffs, parallel lanes, and explicit attorney gates. | "Build the current legal-research memo plan state." | [`../matter-plans/`](../matter-plans/) |
| Matter workspace | Work spans multiple documents, deadlines, or skill runs and context must persist. | "Open a deal that will run for months." | [`../matter-workspaces/_template/`](../matter-workspaces/_template/) (init via [`../scripts/init_matter_workspace.py`](../scripts/init_matter_workspace.py)) |
| Playbook | You run the *same* task type the same way every time and want a repeatable recipe. | "We review NDAs the same way weekly." | [`../playbooks/`](../playbooks/) |
| Review panel | A high-risk draft needs several review lenses before the attorney. | "Run a full multi-pass review before signing." | [`../review-panels/`](../review-panels/) |

## How to decide

Walk these questions in order and stop at the first that fits.

1. **Is there already a draft you only want to check?** Use a **quality check**
   in `skills/legal-methodology/`. See [`QUALITY_LAYER.md`](QUALITY_LAYER.md).
2. **Is this one document and one output, done once?** Use a **one-off skill**.
   Route it with [`../WORKFLOW_ROUTER.md`](../WORKFLOW_ROUTER.md).
3. **Will you run this same task type repeatedly, the same way?** Use a
   **playbook** in [`../playbooks/`](../playbooks/). See
   [`PLAYBOOKS.md`](PLAYBOOKS.md).
4. **Does a high-risk draft need several review lenses before the attorney?**
   Use a **review panel** in [`../review-panels/`](../review-panels/). See
   [`REVIEW_PANELS.md`](REVIEW_PANELS.md).
5. **Does the work span many documents, deadlines, or skill runs that must share
   context?** Use a **matter workspace**. See
   [`MATTER_WORKSPACES.md`](MATTER_WORKSPACES.md).
6. **Is this a recurring multi-step matter *type* where you only need the human sequence?** Use a **matter pack** in [`../matter-packs/`](../matter-packs/).
7. **Does a supported matter need machine-readable dependencies, handoffs, gates, and current ready nodes?** Use a **matter plan** in [`../matter-plans/`](../matter-plans/). A plan organizes work but does not execute legal analysis.
8. **Are you standing up a whole practice area on a platform?** Use a
   **practice-area pack** plus a **practice profile**. See
   [`../metadata/packs.json`](../metadata/packs.json) and
   [`../practice-profiles/`](../practice-profiles/).

When in doubt, pick the narrowest surface that fits the immediate task. A skill
will point to its siblings if the work grows.

## Worked examples

### "I just need to polish a draft"

Use a **quality check**. Run
[`../skills/legal-methodology/legal-prose-polish/SKILL.md`](../skills/legal-methodology/legal-prose-polish/SKILL.md)
to tighten prose without changing legal meaning, then
[`../skills/legal-methodology/output-format-compliance-check/SKILL.md`](../skills/legal-methodology/output-format-compliance-check/SKILL.md)
if the draft must match a required deliverable format. No new analysis is needed —
the draft already exists, so a primary skill would be overkill.

### "I need to review an NDA"

For a single agreement, use the one-off skill
[`../skills/contracts/nda-review/SKILL.md`](../skills/contracts/nda-review/SKILL.md).
If you review NDAs the same way on a recurring basis, use the playbook
[`../playbooks/nda-review.md`](../playbooks/nda-review.md) instead — it adds
default client-position questions, risk-tolerance settings, required source
materials, and the required quality checks on top of the same skill.

### "I have multiple documents and deadlines"

Use a **matter workspace**, because context must persist across skill runs and
multiple documents and dates are involved. Initialize the multi-file template
with [`../scripts/init_matter_workspace.py`](../scripts/init_matter_workspace.py)
(template at
[`../matter-workspaces/_template/`](../matter-workspaces/_template/)). The
workspace carries the matter's parties, facts, jurisdiction, deadlines, sources,
and the drafts each skill produces. Deadlines are recorded for attorney
verification, never computed.

### "I need a litigation demand letter"

For a one-off, use the skill
[`../skills/litigation/demand-letter/SKILL.md`](../skills/litigation/demand-letter/SKILL.md),
followed by the citation and source quality checks for any legal assertion. If
this is a recurring task you run the same way, use the playbook
[`../playbooks/litigation-demand-letter.md`](../playbooks/litigation-demand-letter.md).
A demand letter is adversarial and often deadline-sensitive, so escalate to
attorney review before anything is sent.

### "I need to validate citations"

Use **quality checks**. Run
[`../skills/legal-methodology/citation-integrity-check/SKILL.md`](../skills/legal-methodology/citation-integrity-check/SKILL.md)
for invented or unsupported authorities, quotations, and pin cites, paired with
[`../skills/legal-methodology/source-validation/SKILL.md`](../skills/legal-methodology/source-validation/SKILL.md)
to classify each claim against the source materials available in the session.
These are structured review workflows; they do not automatically verify current
law, and every authority remains flagged for attorney verification.

### "I am setting up a repeatable firm workflow"

Combine three surfaces: a **practice-area pack** (see
[`../metadata/packs.json`](../metadata/packs.json)) to bundle the relevant
skills, core rules, and quality checks for a platform; a **practice profile**
(see [`../practice-profiles/`](../practice-profiles/)) to capture the team's
configuration; and a **playbook** in [`../playbooks/`](../playbooks/) for each
recurring task type the team runs the same way.


### "I need to coordinate a multi-step research memo"

Use the `legal-research-memo` **matter plan** when you need the current ready
wave, typed artifact handoffs, and an explicit attorney scope-approval gate.
Inspect it with `python scripts/matter_plan_cli.py show legal-research-memo
--markdown`, then build its state from declared inputs. Keep the actual research
roadmap, authorities, memo, and review reports in a matter workspace. The plan
loads context only for ready nodes and never approves its own attorney gates.

### "I want to use AgentCounsel in Cursor or Codex"

Use the repo-agent setup. Point your agent at
[`../AGENTS.md`](../AGENTS.md), the universal operating manual, and start from
[`../QUICKSTART.md`](../QUICKSTART.md). For how AgentCounsel maps onto specific
tools and plugin hosts, see
[`PLUGIN_COMPATIBILITY.md`](PLUGIN_COMPATIBILITY.md).

## Every path ends in attorney review

Whichever surface you choose, the output is the same kind of thing: draft legal
work product that a qualified, licensed attorney reviews and adopts. Quality
checks, packs, matter plans, matter workspaces, playbooks, and review panels make that review
easier and more auditable — they never make it optional.
