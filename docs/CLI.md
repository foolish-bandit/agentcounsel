# CLI reference

AgentCounsel ships a small set of helper scripts. They are **Python standard
library only** (run with `py` on Windows or `python3` elsewhere) plus one Node
script for the static site. There are no third-party dependencies, no network
calls, and no API keys. The canonical source of truth is always `skills/` and
`core/`; most scripts either **validate** the repository or **regenerate** a
derived artifact from the canonical files.

> Convention: scripts that generate a file usually also accept `--check`, which
> regenerates in memory and compares against what is committed — exiting non-zero
> if they differ, without writing. CI uses the `--check` forms so a stale
> generated file fails the build.

## Quick map

| Script | Mutates files? | Key flags |
|---|---|---|
| `scripts/validate_repo.py` | No | — |
| `scripts/build_skill_index.py` | Yes (writes metadata) | `--check` |
| `scripts/build_skill_specs.py` | Yes (writes typed contract registry) | `--check` |
| `scripts/generate_selective_context_metrics.py` | Yes (writes JSON and Markdown scorecards) | `--check` |
| `scripts/generate_context_metrics.py` | Yes (writes context reports) | `--check` |
| `scripts/generate_skill_health_report.py` | Yes (writes readiness reports) | `--check` |
| `scripts/check_all.py` | No, except the site verification build | `--quick` |
| `scripts/build_platform_packs.py` | Yes (writes `dist/`, `metadata/packs.json`) | `--check` |
| `scripts/check_evals.py` | No | — |
| `scripts/check_legal_prose.py` | No | `--strict`, `--quiet`, `--path` |
| `scripts/run_evals.py` | No | `--strict`, `--quiet`, `--markdown-report`, `<slug>` |
| `scripts/generate_eval_report.py` | Yes (writes report) | `--check` |
| `scripts/sync_plugin_skills.py` | Yes (writes plugin bundle) | `--check` |
| `scripts/generate_skill_improvement_prompts.py` | Yes (writes reports) | `--check` |
| `scripts/generate_cold_start_interviews.py` | Yes (writes setup skills) | `--check`, `--list` |
| `scripts/init_matter_workspace.py` | Yes (writes a new matter under `matters/`) | `--practice-area`, `--jurisdiction`, `--pack`, `--output-dir`, `--force`, `--dry-run`, `--list-templates` |
| `scripts/build_flashcards.py` | Yes (writes `dist/flashcards/`) | — |
| `site/generate.mjs` | Yes (writes `site/public/`) | — |

---

## scripts/validate_repo.py

**Purpose.** Full structural and consistency validation: every skill's frontmatter
and eight required sections, relative-link resolution, safety framing, index
coverage, generated-metadata freshness, pack-registry integrity, and the
matter-workspace / playbook / review-panel integrity checks.

**Example.** `python scripts/validate_repo.py`

**Mutates files?** No. Read-only.

**Common failure modes.** A new skill missing a required section; a broken
relative link; a generated file (`metadata/index.json`, `router.json`,
`packs.json`) out of date — re-run the matching builder; a playbook/review-panel
missing a required section; a workspace template file missing.

---

## scripts/build_skill_index.py

**Purpose.** Regenerate `metadata/index.json` and `metadata/router.json` from the
canonical skills' frontmatter.

**Example.** `python scripts/build_skill_index.py` (write) · `python scripts/build_skill_index.py --check` (verify only)

**Mutates files?** Yes, without `--check`.

**Common failure modes.** `--check` reports "out of date" after you edit a skill's
frontmatter — re-run without `--check` and commit the regenerated metadata.
Invalid frontmatter (unknown quality check, bad risk level) blocks the build.

---

## scripts/build_skill_specs.py

**Purpose.** Compile every canonical skill into a validated Skill Specification v2 contract and write `metadata/skill_specs.json`. Optional `SPEC.json` sidecars may add typed inputs, gates, modules, activation rules, and context scenarios, but cannot weaken inherited attorney-review, evidence, or deadline protections.

**Example.** `python scripts/build_skill_specs.py` · `python scripts/build_skill_specs.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** An invalid sidecar, duplicate ID, unresolved module path, unsupported activation operator, or attempted weakening of a baseline safety invariant.

---

## scripts/generate_selective_context_metrics.py

**Purpose.** Build every declared selective-context scenario, store deterministic token-planning estimates and complete module-selection traces in `metadata/selective_context_metrics.json`, render `reports/selective-context.md`, and fail when a bundle is incomplete or exceeds its declared budget.

**Example.** `python scripts/generate_selective_context_metrics.py` · `python scripts/generate_selective_context_metrics.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** A missing required input in a scenario, unresolved required module, stale generated artifact, or total-to-baseline ratio above `max_ratio`. The estimates are one token per four characters, not provider token counts.

---

## scripts/generate_context_metrics.py and generate_skill_health_report.py

**Purpose.** Regenerate repository-wide context-pressure and maintainability scorecards. Context metrics measure canonical skills and generated pack footprints; the health report combines eval, example, template, routing, and context signals into a maintenance queue. Neither report claims legal correctness.

**Example.** `python scripts/generate_context_metrics.py --check` · `python scripts/generate_skill_health_report.py --check`

**Mutates files?** Yes, without `--check`.

---

## scripts/check_all.py

**Purpose.** Run the complete CI-equivalent repository gate in workflow order, stopping at the first failure. `--quick` runs the three core structural checks.

**Example.** `python scripts/check_all.py` · `python scripts/check_all.py --quick`

**Mutates files?** It is a verification entry point. The final site-generation step writes the git-ignored `site/public/` directory.

---

## scripts/build_platform_packs.py

**Purpose.** Regenerate the per-platform packs in `dist/` and the pack manifest `metadata/packs.json`, discovering each area's skills, custom typed specs, selectable spec resources, templates, quality checks, matter packs, matter workspaces, playbooks, and review panels.

**Example.** `python scripts/build_platform_packs.py` · `python scripts/build_platform_packs.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** A pack references a file that does not exist (the
builder validates every path); `metadata/packs.json` stale after a skill or
playbook change — rebuild.

---

## scripts/check_evals.py

**Purpose.** Schema-validate every `*.eval.yaml` under `evals/` (skill, router,
benchmark, and static evals) and run the deterministic metadata-integrity checks.

**Example.** `python scripts/check_evals.py`

**Mutates files?** No.

**Common failure modes.** A new eval file with a missing required key, a
`skill`/filename mismatch, an `expected_primary_skill` that is not a real skill
ID, or an invalid `eval_status`.

---

## scripts/check_legal_prose.py

**Purpose.** A conservative legal-prose pass over the *work-product samples* the
repository owns — the illustrative outputs under `examples/` and the eval
candidate outputs under `evals/outputs/`. It checks form and safety framing
only, never legal accuracy. **Errors** (which fail the build) flag legal-advice
or false-certainty framing (for example "this clause is enforceable", "there is
no risk", "you must sign") and any work-product sample missing visible
attorney-review framing. **Warnings** (advisory) flag generic AI "slop" and
vague prose. It is written to leave legitimate content alone: placeholders such
as `[verify jurisdiction]`, required "attorney must review" framing, and the
"qualified tax professional review" framing tax samples use are never flagged.

**Example.** `python scripts/check_legal_prose.py` · `python scripts/check_legal_prose.py --strict` (warnings fail too) · `python scripts/check_legal_prose.py --path examples/dpa-review-example.md`

**Mutates files?** No. Read-only.

**Common failure modes.** A sample output that states a legal conclusion instead
of flagging it for verification, or that omits draft/attorney-review framing.
Fix the sample's wording; do not weaken the check. A file that intentionally
demonstrates weak prose (a "before / after" polish example) is exempt from the
warning checks via `STYLE_EXEMPT` in the script.

---

## scripts/run_evals.py

**Purpose.** Static, non-LLM heuristic runner that scores candidate skill outputs
in `evals/outputs/<slug>/<case-id>.md` against the shared safety assertions. It
does **not** call any model and does **not** judge legal correctness.

**Example.** `python scripts/run_evals.py --strict --quiet` · `python scripts/run_evals.py contracts/nda-review`

**Mutates files?** No.

**Flags.** `<slug>` runs one skill; `--strict` requires every case under the
required slugs to have a passing candidate; `--quiet` prints only the rollup;
`--markdown-report` emits a Markdown summary.

**Common failure modes.** `--strict` fails when a required candidate output is
missing or an assertion regex does not match.

---

## scripts/generate_eval_report.py

**Purpose.** Regenerate `reports/eval-coverage.md` from the eval files and
metadata.

**Example.** `python scripts/generate_eval_report.py` · `python scripts/generate_eval_report.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** `--check` reports the report is out of date after you
add or change eval cases — regenerate and commit.

---

## scripts/sync_plugin_skills.py

**Purpose.** Regenerate the Claude Code plugin bundle under
`adapters/claude-code-plugin/skills/` from the canonical skills it curates.

**Example.** `python scripts/sync_plugin_skills.py` · `python scripts/sync_plugin_skills.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** `--check` reports the bundle is out of sync after you
edit a bundled skill — re-run to resync. See `PLUGIN_SYNC.md`.

---

## scripts/generate_skill_improvement_prompts.py

**Purpose.** Regenerate `reports/skill-improvement-prompts.md` and
`reports/skill-quality-checklist.md`.

**Example.** `python scripts/generate_skill_improvement_prompts.py --check`

**Mutates files?** Yes, without `--check`.

**Common failure modes.** Reports out of date after skills change — regenerate.

---

## scripts/generate_cold_start_interviews.py

**Purpose.** Regenerate the 15 generated cold-start interview skills under
`skills/setup/` from the embedded per-area question banks. The four
hand-authored interviews are off-limits to the generator.

**Example.** `python scripts/generate_cold_start_interviews.py --check` · `python scripts/generate_cold_start_interviews.py --list`

**Mutates files?** Yes, without `--check`. `--list` only lists, `--check` only verifies.

**Common failure modes.** `--check` reports drift after the data block changes —
regenerate and commit.

---

## scripts/init_matter_workspace.py

**Purpose.** Create a new matter workspace from the canonical multi-file template
(`matter-workspaces/_template/`) under `matters/` (which is git-ignored).

**Example.** `python scripts/init_matter_workspace.py "Contoso MSA Review" --practice-area contracts --jurisdiction "New York"`

**Mutates files?** Yes — creates a new workspace directory. Refuses to overwrite an
existing one unless `--force`.

**Flags.** `--practice-area`, `--jurisdiction`, `--pack <matter-pack path>`,
`--output-dir`, `--force`, `--dry-run` (show what would be created, write
nothing), `--list-templates` (list the template and known practice areas).

**Common failure modes.** Destination already exists without `--force`; the
template directory is missing. See `docs/MATTER_WORKSPACES.md`.

---

## scripts/build_flashcards.py

**Purpose.** A "training mode" for a lawyer learning the library's routing —
not a build step the repository depends on. It reads `metadata/index.json`
and writes `dist/flashcards/agentcounsel-router-deck.txt`, an Anki-importable
tab-separated deck with one card per skill: the **Front** is a routing
question derived from the skill's `description` ("Which skill: review an NDA
for the receiving party?"), and the **Back** names the skill, its canonical
path, and its `COMMANDS.md` shorthand where one exists. Studying the deck with
spaced repetition is a way to internalize `WORKFLOW_ROUTER.md`'s and
`COMMANDS.md`'s mappings before you need them live in a matter.

**Example.** `python scripts/build_flashcards.py`

**Mutates files?** Yes — writes into the git-ignored `dist/` directory. There
is no `--check` mode; the output is a personal study aid, not a committed
artifact.

**Common failure modes.** `metadata/index.json` missing or stale — run
`scripts/build_skill_index.py` first. A skill with no `COMMANDS.md` entry gets
a card noting no shorthand exists; that is expected for skills not yet given a
command.

---

## site/generate.mjs

**Purpose.** Generate the static HTML catalog into `site/public/` from `skills/`,
the examples, and the generated metadata.

**Example.** `node site/generate.mjs`

**Mutates files?** Yes — rewrites `site/public/` (preserving a pre-existing
`site/public/packs/` that CI populates from `dist/`). `site/public/` is
git-ignored.

**Common failure modes.** Run after regenerating `metadata/` so the site reflects
current skills, packs, and quality checks.

---

See `docs/AGENT_COMMANDS.md` for the recommended order to run these after editing
different parts of the repository, and `VALIDATION.md` for the full list of
checks `validate_repo.py` performs.

## Matter-plan CLI

`scripts/matter_plan_cli.py` provides a local, standard-library-only interface to typed matter graphs:

```bash
python scripts/matter_plan_cli.py list
python scripts/matter_plan_cli.py show legal-research-memo
python scripts/matter_plan_cli.py build legal-research-memo --inputs inputs.json
python scripts/matter_plan_cli.py build commercial-contract-review --inputs inputs.json --markdown
python scripts/matter_plan_cli.py verify receipt.json
```

`--artifacts` accepts a JSON object keyed by plan artifact ID with an optional lowercase SHA-256 `digest`. Artifact content and file paths remain in the matter workspace and are never accepted through this planning interface. `--gates` accepts explicit `approved` or `rejected` decisions only after the gate's dependencies and required artifacts are satisfied. `--nodes` may restrict context loading to a comma-separated subset of already-ready nodes, but cannot bypass dependencies, conditions, or attorney gates. Use `--receipt-output` to write the privacy-conscious receipt separately from the full runtime result.
