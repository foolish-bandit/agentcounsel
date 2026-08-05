# Quick Start

From zero to your first AgentCounsel skill run in about five minutes. Pick the
path for the tool you use — ChatGPT, Claude, Cursor/Codex, Gemini, or plain
Markdown.

> Everything AgentCounsel produces is **draft legal work product for attorney
> review** — not legal advice, and not a substitute for a licensed attorney. A
> qualified lawyer must review every output before it is relied upon.

## The idea in one minute

- A **skill** (`skills/<area>/<slug>/SKILL.md`) is one Markdown file describing a
  legal workflow: what it is for, the inputs it needs, the steps, the output
  structure, and what an attorney must verify. You give it to an AI assistant as
  context, provide inputs, and review the structured draft it produces.
- A **pack** bundles every skill in a practice area plus the safety rules and
  commands into one uploadable file — the fastest way to start.
- A **playbook** explains how a recurring task should be run; a **matter pack**
  recommends a sequence for a broader matter type; a **matter plan** is the
  validated graph that makes dependencies, artifact handoffs, parallel lanes,
  and attorney gates machine-readable; and a **matter workspace** stores one
  matter's actual documents, facts, artifacts, and decisions. Review panels and
  quality checks inspect drafts before attorney reliance. See
  [`docs/CHOOSE_YOUR_WORKFLOW.md`](docs/CHOOSE_YOUR_WORKFLOW.md) to decide which.

Not sure which surface fits your task? Read
[`docs/CHOOSE_YOUR_WORKFLOW.md`](docs/CHOOSE_YOUR_WORKFLOW.md) first. The common
steps in every path are the same: **pick a pack or skill → provide Required
Inputs → review against the Attorney Verification Checklist.**

---

## Pick your platform

### ChatGPT Projects

1. **Get the pack.** Open the [packs page](https://zgbrenner.github.io/agentcounsel/packs/) and download your practice area's ChatGPT pack (`.md`).
2. **Install.** Create a ChatGPT Project, upload the `.md` to its files, and in the Project instructions paste: *"Follow the AgentCounsel pack in the project files. Apply the global safety rules to every task. Use the practice profile and the skill that matches the request. Produce draft legal work product for attorney review — not legal advice."*
3. **Start a matter (optional).** For a multi-document, multi-deadline engagement, ask the project to set up a matter workspace (see [`docs/MATTER_WORKSPACES.md`](docs/MATTER_WORKSPACES.md)), or initialize one locally with `python scripts/init_matter_workspace.py`.
4. **Run a skill.** Describe the task in plain language; ChatGPT routes to the matching skill. Provide the Required Inputs it asks for.
5. **Quality checks.** For anything that cites authority or leaves the building, ask it to run the quality checks (source validation, citation integrity, hallucination red-team). See [`docs/QUALITY_LAYER.md`](docs/QUALITY_LAYER.md).
6. **Attorney review gate.** Always finish with the Attorney Verification Checklist before relying on, sending, or filing anything.
7. **What not to do.** Do not treat the output as final or as legal advice; do not paste real privileged client data into a consumer account you have not cleared for confidential material.

### Claude (claude.ai — no command line needed)

If you use Claude in the browser or the desktop/mobile app, this is your path. It
requires no technical setup.

1. **Get the pack.** Download your practice area's Claude pack (`.zip`) from the [packs page](https://zgbrenner.github.io/agentcounsel/packs/) and unzip it on your computer.
2. **Create a Project.** In Claude, create a new Project (e.g., "Contracts — AgentCounsel").
3. **Upload the files.** Add all of the unzipped files to the Project's knowledge. Folder structure is not preserved there — that's fine; every filename in the pack is unique.
4. **Paste the instructions.** Copy this into the Project's custom instructions:

   ```
   Follow the AgentCounsel pack in the project files. Apply the global safety
   rules to every task. Use the practice profile and the skill that matches my
   request. Produce draft legal work product for attorney review — not legal
   advice. Flag every gap with a visible placeholder instead of guessing, and
   never invent a citation, date, or deadline.
   ```

5. **Run a skill.** Start a conversation and describe the task in plain language ("review this NDA — we're the receiving party"). Claude routes to the matching skill and asks for its Required Inputs.
6. **Quality checks.** For anything that cites authority or leaves the building, ask Claude to run the quality checks (source validation, citation integrity, hallucination red-team).
7. **Attorney review gate.** Complete the Attorney Verification Checklist before relying on, sending, or filing anything.
8. **What not to do.** Do not treat output as final or as legal advice; do not paste privileged client material into an account you have not cleared for confidential work.

### Claude Code (developers and technical users)

1. **Get the library.** Clone the repository; the plugin bundle in [`adapters/claude-code-plugin/`](adapters/claude-code-plugin/) carries a curated skill set, and `CLAUDE.md` loads the operating model for the whole library.
2. **Run a skill.** Ask for the task; Claude Code routes to the narrowest `SKILL.md` and follows it.
3. **Start a matter (optional).** `python scripts/init_matter_workspace.py "<matter name>"` scaffolds a workspace under `matters/` (git-ignored).
4. **Quality checks / review gate.** Same as above — quality-layer skills on authority-heavy drafts, Attorney Verification Checklist before reliance.
5. **What not to do.** Do not hand-edit the generated plugin bundle; regenerate it with `python scripts/sync_plugin_skills.py`. Do not let the agent edit `skills/` or `core/` unless the task is explicitly to change the library.

### Cursor / Codex (repo agents)

1. **Get the instructions.** Use [`AGENTS.md`](AGENTS.md) (Codex and most repo agents) or [`CLAUDE.md`](CLAUDE.md) (Claude Code); the packs page also serves a ready-made `.cursorrules`. See [`docs/PLUGIN_COMPATIBILITY.md`](docs/PLUGIN_COMPATIBILITY.md).
2. **Install.** Vendor `skills/` and `core/` into your project (or work in a checkout) and copy the instruction file to the project root. The agent loads the operating model and routes to the narrowest skill.
3. **Start a matter (optional).** Run `python scripts/init_matter_workspace.py "<matter name>" --practice-area <area>` to scaffold a workspace under `matters/` (git-ignored).
4. **Run a skill.** Ask for the task; the agent opens the single narrowest `SKILL.md` and follows it. See [`docs/AGENT_COMMANDS.md`](docs/AGENT_COMMANDS.md) for the commands to run after edits.
5. **Quality checks.** Run the quality-layer skills, and `python scripts/validate_repo.py` if you edited library files.
6. **Attorney review gate.** The agent hands off the Attorney Verification Checklist unchecked — a person completes it.
7. **What not to do.** Do not let the agent edit `skills/`/`core/` unless the task is explicitly to change the library; do not commit anything under `matters/`.

### Gemini

1. **Get the pack.** Download your practice area's Gemini pack (`.zip`), or install the repo as a Gemini CLI extension via [`adapters/gemini/`](adapters/gemini/) (`gemini-extension.json` + `GEMINI.md`).
2. **Install.** Add the unzipped contents as sources in a Gemini notebook/workspace, or let the CLI extension load the operating model automatically.
3. **Start a matter (optional).** Set up a matter workspace for multi-step engagements.
4. **Run a skill.** Tell Gemini to follow the AgentCounsel pack and apply the safety rules; provide the Required Inputs for the matching skill.
5. **Quality checks.** Run source validation and citation integrity on anything that cites law.
6. **Attorney review gate.** Finish with the Attorney Verification Checklist before reliance.
7. **What not to do.** Do not rely on routing if the practice area is ambiguous — name the skill, or check [`WORKFLOW_ROUTER.md`](WORKFLOW_ROUTER.md).

### Local / Markdown-only (no AI tool required)

1. **Get the files.** Clone the repository. For an ordinary skill, you may instead copy its `SKILL.md` and templates. When the skill folder contains `SPEC.json`, copy the complete folder or use **Copy Full Package** on the catalog page so every selectable resource remains available.
2. **Read the rules.** Read [`core/`](core/) once — the operating rules every skill inherits.
3. **Start a matter (optional).** `python scripts/init_matter_workspace.py "<matter name>"` scaffolds a workspace from [`matter-workspaces/_template/`](matter-workspaces/_template/). Everything is plain Markdown you can fill in by hand.
4. **Run a skill.** Follow the chosen skill's Workflow and produce its Output Format — with any model, or as a structured worksheet for a person.
5. **Quality checks.** The quality-layer skills under [`skills/legal-methodology/`](skills/legal-methodology/) are themselves Markdown workflows you can apply by hand.
6. **Attorney review gate.** Complete the Attorney Verification Checklist before reliance.
7. **What not to do.** Do not delete the visible placeholders (`[CONFIRM: ...]`, `[verify jurisdiction]`) without resolving them — each is a task for a person.

---

## A worked example: planning a legal research memo

Matter plans organize multi-step work but do not execute legal analysis. This example builds the first ready wave for the typed legal-research graph.

1. Create an input file such as `research-inputs.json`:

   ```json
   {
     "legal-question": "[Matter question supplied by the supervising attorney]",
     "known-facts": {"fact-1": "[User-supplied fact]"},
     "jurisdiction": "[Confirmed jurisdiction]",
     "existing-authorities": ["[Provided authority or source file]"],
     "relevant-date": "[User-supplied date]",
     "time-and-scope": "[Attorney-approved research scope]"
   }
   ```

2. Inspect the graph:

   ```bash
   python scripts/matter_plan_cli.py show legal-research-memo --markdown
   ```

3. Build the current plan state:

   ```bash
   python scripts/matter_plan_cli.py build legal-research-memo \
     --inputs research-inputs.json \
     --output research-plan-state.json
   ```

4. The result identifies the ready node, blocked nodes, artifact handoffs, and the attorney scope-approval gate. It loads context only for the ready skill. It does not call a model, invent research, approve the scope, or calculate a deadline.
5. After a person runs the ready skill and records the resulting artifact identity, rebuild the plan with an artifacts file. After the attorney approves the scope gate, rebuild with a gates file containing the explicit `approved` decision. Downstream nodes then become eligible in deterministic waves.
6. Keep actual documents and draft outputs in a matter workspace. The exported plan receipt contains hashes, lineage, states, and presence metadata, not the raw legal question or confidential facts.

The same operations are available to MCP clients through `build_matter_plan` and `verify_matter_plan_receipt`.

## A worked example: reviewing an NDA

1. **Route.** `WORKFLOW_ROUTER.md` → "Review this NDA" → `skills/contracts/nda-review/SKILL.md`. (In a Contracts pack, just say "review this NDA" in chat. If you review NDAs the same way every week, use [`playbooks/nda-review.md`](playbooks/nda-review.md).)
2. **Read.** Required Inputs: the NDA text, your client's role (disclosing, receiving, or mutual), and the business context.
3. **Run.** With a pack: state the task and provide the NDA + role. With files: paste `core/` plus the skill package and the NDA text into your assistant. If the catalog shows **Copy Full Package**, use it for standard or deep work.
4. **Get back.** A triage rating, a key-terms table, a risk table, prioritized redline points, and an Attorney Verification Checklist.
5. **Quality + review.** Run citation/source checks if any authority is cited; resolve every `[CONFIRM: ...]` placeholder; have an attorney confirm the triage rating and redline priorities before negotiating or signing.

## Where to go next

- [`README.md`](README.md) — what AgentCounsel is, who it is for, how it is organized.
- [`docs/tutorials/practice-matter.md`](docs/tutorials/practice-matter.md) — a guided, fictional first run of a skill end-to-end, if you have not run one yet.
- [`docs/CHOOSE_YOUR_WORKFLOW.md`](docs/CHOOSE_YOUR_WORKFLOW.md) — choosing among skills, packs, workspaces, playbooks, panels, and quality checks.
- [`docs/SAFETY_MODEL.md`](docs/SAFETY_MODEL.md) — the safety model and using AgentCounsel with confidential material.
- [`docs/QUALITY_LAYER.md`](docs/QUALITY_LAYER.md) — the quality checks and when to run them.
- [`docs/MARKDOWN_TO_WORD.md`](docs/MARKDOWN_TO_WORD.md) — converting a Markdown draft to a Word redline or PDF.
- [`docs/FAQ.md`](docs/FAQ.md) — common questions.
