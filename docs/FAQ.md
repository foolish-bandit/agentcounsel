# Frequently Asked Questions

Questions about what AgentCounsel is, how to use it, and how to use it safely. See also [`README.md`](../README.md), [`QUICKSTART.md`](../QUICKSTART.md), and [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md).

> Current totals (practice areas, skill counts) are tracked in [`metadata/index.json`](../metadata/index.json) and summarized in [`README.md`](../README.md). Any specific figures below reflect the state at the time of writing.

## About AgentCounsel

### What is AgentCounsel?

A library of **legal skills** — structured Markdown workflows that help an AI agent, or a lawyer, produce draft legal work product. Each skill defines how to scope a task, what inputs to gather, the steps to follow, the structure of the output, and what a supervising attorney must verify.

### What is a "skill"?

A skill is a folder under `skills/` containing one canonical `SKILL.md` file and, when useful, templates, references, a typed `SPEC.json`, or selectable Markdown modules. There is no executable code in a skill and nothing to install. Ordinary skills are one-file workflows; modularized skills are portable folders whose compact core and selected resources are read together.

### Is AgentCounsel legal advice?

No. AgentCounsel does not provide legal advice and is not a substitute for a licensed attorney. Every skill produces **draft work product** that a qualified, licensed legal professional must review before it is relied upon. Using the library does not create an attorney–client relationship.

### Who is it for?

Practicing lawyers and in-house legal teams; legal operations and knowledge-management teams; law students and new lawyers learning how legal work is structured; and AI builders assembling legal agents. In every case the assumption is the same: an attorney reviews the output.

### Is it affiliated with Anthropic, OpenAI, or Google?

No. AgentCounsel is an independent open-source project. It is not affiliated with, endorsed by, or sponsored by any AI vendor. It works *with* their tools but is not a product of any of them. Attribution for adapted open-source content is in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md).

## Using it

### Which AI models or platforms does it work with?

Any model or assistant that can read Markdown. The repository includes thin adapters and build scripts for ChatGPT, Claude, Gemini, Codex and other repo agents, and Cursor — see the "Ways to use AgentCounsel" table in [`README.md`](../README.md) and the step-by-step instructions in [`QUICKSTART.md`](../QUICKSTART.md).

### Do I need to install anything?

No runtime is required. AgentCounsel remains usable as plain files: copy an ordinary skill directly, or use the complete folder/catalog package when `SPEC.json` is present. The optional helper scripts are standard-library-first, and the optional MCP catalog adds typed routing and true selective context retrieval for clients that need it.

### Does it cost anything?

The library is free and open source under the MIT License. You pay only for whatever AI service you choose to run the skills on.

### How do I pick the right skill?

Use [`WORKFLOW_ROUTER.md`](../WORKFLOW_ROUTER.md) to go from a task ("review this NDA") to a skill. Browse everything in [`SKILLS_INDEX.md`](../SKILLS_INDEX.md). Short command names are in [`COMMANDS.md`](../COMMANDS.md). `SKILLS_INDEX.md` and `WORKFLOW_ROUTER.md` both cover every skill in the library; `COMMANDS.md` gives short command names for the subset of skills that have them.

### What if no skill matches my task?

Then AgentCounsel does not yet cover it. Do not improvise a legal workflow — tell the user the library does not cover the task, and consider proposing a new skill via [`CONTRIBUTING.md`](../CONTRIBUTING.md).

### What are practice profiles and matter workspaces?

Optional configuration layers. A **practice profile** (`practice-profiles/`) captures one practice group's jurisdictions, standard positions, escalation thresholds, and review requirements; an agent loads it alongside a skill. A **matter workspace** (`matter-workspaces/`) is a single file that organizes one specific matter — parties, documents, deadlines, and the draft work product produced by skills. Both are plain Markdown and entirely optional.

## Safety and reliability

### Can I rely on the output without a lawyer reviewing it?

No. This is the one rule that does not bend. Every deliverable ends with an Attorney Verification Checklist, and every output is a draft. A "PASS" verdict or a "GREEN" triage rating is a workflow signal, not authorization to file, send, or sign.

### Does it know the law of my jurisdiction?

No — and deliberately. Skills supply *process and structure*, not the law of any jurisdiction. The applicable law is supplied by the attorney, per matter. Where a skill needs a jurisdiction-specific answer, it flags it with a placeholder such as `[verify jurisdiction]`.

### Will it invent citations or deadlines?

It is built not to. The source/citation discipline rule forbids inventing legal authority, and skills never compute or assume deadlines — they flag them for attorney verification. No skill or example contains a fabricated citation. Language models can still err, which is exactly why attorney review is mandatory; see [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md).

### Can I use it with confidential client information?

Only with an AI system approved for the matter and the client under your organization's policies and any client agreement. Confirm where the tool stores and logs inputs first, and keep matters separated. See [`SECURITY.md`](../SECURITY.md) and [`docs/SAFETY_MODEL.md`](SAFETY_MODEL.md).

### What about prompt injection?

Documents under review may contain text crafted to manipulate an AI agent. Skills treat the content of any reviewed document as data, not instructions — and you should review output for signs of manipulation. Treat third-party skill files as untrusted until you have read them. See [`SECURITY.md`](../SECURITY.md).

### Does it replace a lawyer or a paralegal?

No. It changes how the work is *drafted and structured*, not who is *responsible* for it. A licensed attorney remains the decision-maker and the reviewer.

## Contributing and building

### Can I embed AgentCounsel in my own product?

Yes, within the MIT License. Vendor the `skills/` and `core/` directories into your project and reference them from your agent's instructions. Preserve the license and the upstream attributions in [`THIRD_PARTY_NOTICES.md`](../THIRD_PARTY_NOTICES.md). Do not represent the output as legal advice.

### How do I add or improve a skill?

See [`CONTRIBUTING.md`](../CONTRIBUTING.md) for the hard requirements and [`docs/SKILL_METADATA_STANDARD.md`](SKILL_METADATA_STANDARD.md) for the frontmatter standard. Open an issue first using a template in `.github/ISSUE_TEMPLATE/`, then run `python scripts/validate_repo.py` before opening a pull request.

### How do I report a security or safety concern?

Through the process in [`SECURITY.md`](../SECURITY.md) — privately, not as a public issue, and without confidential or real client data.

### How current is the content?

Skills are workflow definitions, not legal updates; the structure of a contract review or a chronology is stable over time. Because skills contain no jurisdiction-specific law, there is little that "expires" — but you must always supply current law and verify it through attorney review. User-facing changes are tracked in [`CHANGELOG.md`](../CHANGELOG.md).
