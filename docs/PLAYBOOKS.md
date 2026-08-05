# Playbooks

A **playbook** (`playbooks/<task>.md`) is a repeatable recipe for a recurring
legal task type. It wraps an underlying skill with the context a team applies the
same way every time: default client-position questions, risk-tolerance settings,
required source materials, required quality checks, escalation triggers, and
common failure modes. Every playbook produces **draft legal work product for
attorney review** — never legal advice.

## How a playbook differs from other surfaces

| Surface | What it is |
|---|---|
| Skill | One workflow that produces one type of draft output. |
| **Playbook** | A recipe for running a recurring task type — adds default questions, risk-tolerance settings, required sources, and required quality checks on top of a skill. |
| Matter pack | Human-readable recommended skill sequences for a broader matter type. |
| Matter plan | A validated graph companion for a supported recurring matter, with typed handoffs, parallel lanes, and attorney gates. |
| Matter workspace | The organizing file/folder for one live matter. |
| Review panel | A multi-pass supervised review of a draft. |

Use a playbook when the same task recurs (for example, "we review NDAs the same
way every week") and you want a consistent, repeatable approach. Use a single
skill for a one-off; use a matter plan when a supported recurring matter needs
machine-readable dependencies and gates; use a matter workspace when the work is
multi-step and ongoing and actual documents or outputs must persist.

## Available playbooks

| Playbook | When to use |
|---|---|
| `playbooks/nda-review.md` | Reviewing an NDA from a defined client posture. |
| `playbooks/commercial-contract-review.md` | Reviewing a commercial contract (MSA, services, license). |
| `playbooks/employment-termination-analysis.md` | Analyzing a proposed employment termination. |
| `playbooks/litigation-demand-letter.md` | Preparing a demand letter on a counsel-supplied claim theory. |
| `playbooks/regulatory-rule-change-summary.md` | Summarizing a new or amended rule from an official source. |
| `playbooks/privacy-dpa-review.md` | Reviewing a data processing agreement. |
| `playbooks/corporate-governance-review.md` | Board consent / corporate governance review. |
| `playbooks/securities-disclosure-review.md` | Securities / capital-markets disclosure review. |
| `playbooks/legal-research-memo.md` | Scoping and drafting an IRAC-structured legal research memo. |
| `playbooks/legal-intake-response.md` | Triaging and responding to an inbound legal-team request. |

## Required sections

Every playbook follows the same structure, in order:

1. When to Use
2. Required Inputs
3. Default Client-Position Questions
4. Risk Tolerance Settings
5. Required Source Materials
6. Recommended Primary Skills
7. Required Quality Checks
8. Attorney Escalation Triggers
9. Expected Outputs
10. Source and Citation Expectations
11. Common Failure Modes
12. Final Attorney-Review Gate

## Safety posture

Playbooks are process guidance, not legal advice. They never invent authority,
never compute deadlines, and always end with the final attorney-review gate. The
required quality checks reference the `skills/legal-methodology/` quality layer;
the source/citation expectations use the classification vocabulary in
`docs/SOURCE_VALIDATION.md`. Playbooks are plain Markdown with no backend.

See `WORKFLOW_ROUTER.md` for how a vague request routes to a playbook,
`matter-plans/README.md` for how selected playbooks acquire a typed graph
companion, and `docs/MATTER_WORKSPACES.md` for how actual outputs are organized
in a matter workspace.
