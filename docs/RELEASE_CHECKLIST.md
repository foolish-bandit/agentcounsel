# Release checklist

A deterministic, offline checklist for cutting an AgentCounsel release. Everything
here uses the Python standard library and one Node script — no network calls, no
API keys. Replace `vX.Y.Z` with the version you are cutting. The current
release is `v0.4.0`.

## 1. Regenerate derived artifacts

The canonical source is `skills/` and `core/`; several files are generated from
them and must be refreshed and committed. See [`CLI.md`](CLI.md).

```
python scripts/build_skill_index.py            # metadata/index.json, metadata/router.json
python scripts/build_skill_specs.py            # metadata/skill_specs.json
python scripts/generate_selective_context_metrics.py
python scripts/build_matter_plans.py            # metadata/matter_plans.json, reports/matter-plans.md
python scripts/evaluate_matter_plans.py         # metadata/matter_plan_evals.json, reports/matter-plan-evals.md
python scripts/build_platform_packs.py         # metadata/packs.json, dist/
python scripts/generate_eval_report.py         # reports/eval-coverage.md
python scripts/generate_skill_improvement_prompts.py
python scripts/generate_cold_start_interviews.py
python scripts/sync_plugin_skills.py           # adapters/claude-code-plugin/skills/
node site/generate.mjs                     # site/public/
```

## 2. Run the full validation suite

All must pass (CI runs the same set on every push):

```
python scripts/validate_repo.py
python scripts/build_skill_index.py --check
python scripts/build_skill_specs.py --check
python scripts/generate_selective_context_metrics.py --check
python scripts/build_matter_plans.py --check
python scripts/evaluate_matter_plans.py --check
python scripts/build_platform_packs.py --check
python scripts/check_evals.py
python scripts/run_evals.py --strict --quiet
python scripts/generate_eval_report.py --check
python scripts/sync_plugin_skills.py --check
python scripts/generate_skill_improvement_prompts.py --check
python scripts/generate_cold_start_interviews.py --check
node site/generate.mjs
```

If a `--check` reports "out of date", run the matching generator from step 1,
commit the result, and re-run.

## 3. Manual review

- [ ] `README.md` reads correctly: counts/badges match the actual library, links
      resolve, the "Choose your workflow" table is current.
- [ ] `QUICKSTART.md` paths still work for each platform.
- [ ] `RELEASE_NOTES.md` describes this release accurately and avoids overclaims.
- [ ] `CHANGELOG.md` has a dated section for this version and a fresh
      `## [Unreleased]` above it.
- [ ] `docs/PROJECT_STATUS.md` is honest about what is stable vs. experimental.
- [ ] `metadata/matter_plans.json`, `metadata/matter_plan_evals.json`, and both matter-plan reports are current.
- [ ] Every pilot graph ends behind an explicit attorney gate; blocked nodes contain no skill context; generated receipts contain no raw sensitive matter inputs.
- [ ] Overclaim scan: no affirmative "legal advice", "AI lawyer", "verified law",
      "guaranteed citation verification", "autonomous legal agent", "replaces
      attorney review", or "production-ready legal advice" phrasing anywhere in
      public docs. (`validate_repo.py` flags affirmative legal-advice phrasing.)

## 4. License and attribution

- [ ] `LICENSE` is present and MIT.
- [ ] `THIRD_PARTY_NOTICES.md` lists attribution for any adapted third-party source material (including upstream Apache-2.0 projects whose terms continue to apply to the borrowed content).
- [ ] No GPL/AGPL material was introduced (per `CONTRIBUTING.md` and
      `docs/THIRD_PARTY_ATTRIBUTION_POLICY.md`).
- [ ] Any directly adapted third-party content is attributed in `THIRD_PARTY_NOTICES.md`.

## 5. GitHub topics

Set the repository topics so the project is discoverable and accurately described.
See [`GITHUB_TOPICS.md`](GITHUB_TOPICS.md) for the recommended list. Topics must
stay accurate — do not add topics that overclaim (for example, never `legal-advice`
or `ai-lawyer`).

## 6. Tag and push the release

```
git tag -a v0.4.0 -m "AgentCounsel v0.4.0: typed matter graphs"
git push origin v0.4.0
```

(Do not force-push tags. If a tag is wrong, delete and recreate it deliberately.)

## 7. Draft the GitHub release

1. Go to the repository's **Releases** → **Draft a new release**.
2. Choose the `v0.4.0` tag.
3. Title: `AgentCounsel v0.4.0: Typed Matter Graphs`.
4. Paste the body of [`../RELEASE_NOTES.md`](../RELEASE_NOTES.md) (or summarize it
   and link to the file).
5. Keep the safety framing in the description: draft legal work product for
   attorney review, not legal advice, not an AI lawyer.
6. Attach no secrets or client data. The generated packs are rebuilt by CI and
   served from the Pages site; you do not need to attach `dist/`.
7. Publish when validation is green and the manual review above is complete.

## 8. Post-release

- [ ] Confirm the Pages site rebuilt and the packs page serves current downloads.
- [ ] Confirm CI is green on `main`.
- [ ] Start a fresh `## [Unreleased]` section in `CHANGELOG.md` for the next cycle
      (done as part of cutting the release).
