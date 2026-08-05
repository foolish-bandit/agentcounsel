# Matter Plans

Matter plans are typed, machine-validated directed acyclic graphs for recurring
multi-skill legal workflows. Playbooks and matter packs remain the canonical
human guidance. A plan sidecar references that source and encodes only workflow
structure: skill nodes, dependencies, controlled conditions, artifact handoffs,
and explicit attorney-review gates.

Matter plans do not execute a model, state law, decide strategy, compute a
deadline, or produce final legal advice. Every skill output remains draft legal
work product for review and adoption by a qualified, licensed attorney.

## Node types

- `skill`: references one canonical `<practice-area>/<slug>` skill contract and
  a declared execution mode.
- `attorney-gate`: a human interruption point. Downstream nodes remain blocked
  until the caller records `approved`; `rejected` remains visible in the plan
  state and does not silently route around the gate.

## Conditions

The v1 condition language is deliberately small: `always`, `present`, `equals`,
`contains-any`, `artifact-present`, and `gate-approved`. Missing condition data
is unresolved and fails closed. Arbitrary expressions and interpretation of
prose are prohibited.

## Artifacts and bindings

Artifacts are stable identities with one producer. Bindings connect matter
inputs, artifacts, controlled constants, or gate decisions to canonical skill
inputs. The plan stores lineage, not confidential artifact content. Actual
files remain in the user's matter workspace.

## Privacy and receipts

Exported receipts contain plan and contract hashes, node states, gates, artifact
lineage, context fingerprints, and matter-input presence/type metadata. They do
not contain raw sensitive matter input values or legal document contents. A receipt is a deterministic integrity and self-consistency record, not a digital signature, proof of identity, or proof that a particular attorney approved a gate. Callers must authenticate users and approvals in their own system. Artifact content and paths remain outside the planner; only stable IDs and optional SHA-256 digests enter the graph state.

## Authoring

Create `matter-plans/<plan-id>.json`, keep all IDs in lowercase slug form, link a
real playbook or matter-pack `source_path`, and run:

```bash
python scripts/build_matter_plans.py
python scripts/build_matter_plans.py --check
```
