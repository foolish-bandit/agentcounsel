---
name: Infringement Triage
description: "Use when a client needs a first-pass, structured triage of a potential intellectual property infringement issue — identifying the key factors, flagging their direction, and routing to IP counsel — without concluding whether infringement occurred."
practice_area: ip
task_type: triage
jurisdictions: []
risk_level: medium
requires_attorney_review: true
inputs:
  - "IP rights at issue"
  - "The parties' posture and relationship"
  - "The available evidence of potential infringement"
outputs:
  - "Infringement triage memo identifying key factors and routing to IP counsel"
related_skills:
  - skills/ip/cease-and-desist-response/SKILL.md
  - skills/ip/fto-triage/SKILL.md
  - skills/ip/trademark-clearance-triage/SKILL.md
  - skills/ip/dmca-takedown/SKILL.md
  - skills/litigation/demand-letter/SKILL.md
tags:
  - ip
  - infringement
  - triage
  - ip-enforcement
  - routing
---

# Infringement Triage

## Purpose

Produce a structured first-pass triage memo for a potential intellectual-property dispute. The workflow identifies the rights implicated, organizes the disclosed facts under the applicable factor categories, records which direction each factor appears to point, assigns a routing signal, and frames next steps for either a potential senior party or an accused party.

This is draft legal work product for attorney review. It is not a legal opinion on whether infringement occurred, a merits determination, a freedom-to-operate opinion, formal claim construction, or legal advice. Only counsel may determine validity, infringement, defenses, and strategy.

## Use When

- A client believes its trademark, copyright, patent, or trade secret may be infringed and needs structured intake before enforcement counsel acts.
- A client may be accused of infringement and needs a privileged first-pass organization of facts and issues.
- The user needs a briefing memo for IP counsel rather than a definitive conclusion.
- More than one IP right may apply and each needs a separate, inspectable analysis.

## Required Inputs

- **IP rights at issue.** One or more of `trademark`, `copyright`, `patent`, or `trade-secret`. Do not infer a right from ambiguous facts; request confirmation.
- **Party posture.** Confirm whether the client is the potential senior party or accused party. Stop if unclear because routing recommendations differ.
- **Jurisdiction or governing law.** If missing, use `[CONFIRM: governing law and jurisdiction]`; factor frameworks applied in this memo must be confirmed `[verify jurisdiction]`.
- **Relevant facts and evidence.** The asserted right, accused material or conduct, available comparison evidence, ownership facts, and source attribution.
- **Known identifiers and status information.** Registration, filing, claim, or application details only as supplied. This workflow does not perform a registry or docket search; every status remains `[VERIFY: current status]`.
- **Timing information.** Record supplied conduct, priority, creation, complaint, or demand dates. No clock is computed, and every timing issue is marked `[deadline verification required]`.
- Optional: the client's enforcement posture, risk tolerance, and preservation or insurance context.

If a required input is absent, stop and ask or state exactly which part of the analysis remains incomplete. Never fabricate ownership, registration, priority, claim language, facts, or dates.

## Do Not Use When

- Responding to a formal cease-and-desist letter. Use `cease-and-desist-response`.
- Conducting patent freedom-to-operate work. Use `fto-triage`.
- Clearing a proposed mark before use. Use `trademark-clearance-triage`.
- Preparing or evaluating a DMCA notice. Use `dmca-takedown`.
- Drafting an outbound demand. Use `demand-letter`.
- The user requests a definitive infringement, validity, enforceability, or outcome conclusion.
- The issue is exclusively non-domestic and no supported legal framework has been supplied. `[ATTORNEY TO CONFIRM]`

## Legal Safety Rules

- The output is draft legal work product for attorney review. Do not enforce, stop conduct, answer a demand, or make a commercial commitment based solely on it.
- This workflow produces a **routing signal, not an infringement finding**. GREEN, YELLOW, and RED communicate review urgency and fact posture only; they are not merits findings or outcome predictions.
- Counsel determines the controlling right, validity, legal test, element weighting, infringement, available relief, and strategy. Every jurisdiction-specific framework remains `[verify jurisdiction]`.
- For an accused-party patent matter, preserve privilege and confidentiality because awareness and analysis may affect a later willfulness inquiry. `[ATTORNEY TO CONFIRM]`
- Do not run or claim to run a registry, register, docket, or database search. Treat all ownership, registration, filing, maintenance, cancellation, reexamination, and status information as unverified.
- Follow `core/source-and-citation-discipline.md`. Never invent authority, named tests, statutes, cases, quotations, deadlines, registration facts, or claim language.
- Apply the two-way-door rule: surface every plausible right, factor, defense, timing issue, and preservation concern; counsel may narrow later.
- Do not decide any affirmative defense. Identify it as an issue for counsel and use `[ATTORNEY TO CONFIRM]`.
- Separate disclosed facts, analytical observations, assumptions, and verification items.
- Flag uncertainty visibly instead of silently resolving it.
- Preserve client confidentiality, privilege, and work-product restrictions.

## Workflow

1. Confirm rights, posture, jurisdiction, facts, evidence, supplied status information, and dates. Stop for ambiguous posture or rights.
2. Analyze each selected right separately. Do not blend legal frameworks or allow strength under one right to substitute for another.
3. Select the execution mode:
   - **quick-triage:** use this core only to confirm scope, posture, missing inputs, immediate privilege or preservation concerns, and the right-specific modules required;
   - **standard:** load `modules/factor-method.md`, each selected right module, and `modules/defenses-routing-output.md`;
   - **deep-review:** load all standard modules plus `modules/expanded-verification.md`.
4. For each selected right, record each factor, disclosed facts, apparent direction, missing facts, and jurisdiction-verification need. Do not resolve close calls.
5. Identify defenses without deciding them; assign a routing signal; frame posture-specific next steps; list assumptions and missing information.

## Output Format

Label the result:

> **DRAFT - INFRINGEMENT TRIAGE MEMO**
> Attorney review is required before any enforcement action, demand, response, or change in conduct. This memo does not conclude whether infringement occurred.

Return only the detail supported by the selected mode. Standard and deep-review outputs use `templates/infringement-triage-memo.md` and contain:

1. **Scope and Posture**
2. **Factor Analysis by Right**
3. **Defenses and Threshold Questions**
4. **Triage Signal**, with the no-conclusion caveat
5. **What Cuts Which Way Summary**
6. **Recommended Next Steps**
7. **Assumptions and Missing Information**
8. **Attorney Verification Items**

Use `[CONFIRM: ...]`, `[VERIFY: ...]`, `[ATTORNEY TO CONFIRM: ...]`, `[citation needed]`, `[verify jurisdiction]`, and `[deadline verification required]` wherever the source or conclusion is not confirmed.

## Attorney Verification Checklist

- [ ] The rights and party posture are complete and accurate; no plausible additional right was missed.
- [ ] Governing law and the controlling factor framework for each right are confirmed.
- [ ] Ownership, registration or filing status, chain of title, maintenance, and enforceability were independently verified.
- [ ] Every fact, comparison, identifier, date, and quoted or paraphrased source was checked against supplied material.
- [ ] Every defense and timing-sensitive doctrine was evaluated by counsel; no deadline was derived from this memo.
- [ ] The triage signal is treated only as routing information, not a legal opinion or prediction.
- [ ] Preservation, legal-hold, privilege, confidentiality, insurance, and response issues were considered.
- [ ] Recommended next steps were tailored and approved by IP counsel before action.
- [ ] All assumptions, gaps, and placeholders were resolved before the memo was relied upon or shared with the client.
