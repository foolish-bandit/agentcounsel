---
name: Motion Opposition Drafter
description: "Use when organizing and drafting a DRAFT opposition or response brief to a pending motion — deconstructing the movant's arguments into a point-by-point response outline, mapping the movant's cited authorities to verification placeholders, and assembling a source-cited opposition draft for attorney review before filing."
practice_area: litigation
task_type: drafting
jurisdictions: []
risk_level: high
requires_attorney_review: true
inputs:
  - "The movant's motion, memorandum, and any supporting declarations or exhibits"
  - "The case theory and the client's position in opposition"
  - "The relevant record materials that support the opposition"
  - "The response deadline as stated on the docket or scheduling order"
outputs:
  - "Point-by-point response outline mapped to the movant's arguments"
  - "Draft opposition brief cited to the record and flagged for attorney verification"
  - "Authority-verification and research-referral list for every movant citation"
related_skills:
  - skills/litigation/brief-section-drafter/SKILL.md
  - skills/legal-research/legal-research-memo/SKILL.md
  - skills/legal-research/negative-treatment-check/SKILL.md
  - skills/litigation/litigation-chronology/SKILL.md
tags:
  - litigation
  - opposition-brief
  - motion-practice
  - drafting
  - record-citation
  - response-brief
---

# Motion Opposition Drafter

## Purpose

Produce a disciplined first draft of an opposition or response brief for attorney review. The workflow deconstructs the movant's actual papers, maps each argument to a point-by-point response, cites only provided record materials, and treats every movant authority as unverified. It never invents counter-authority. A missing authority becomes a visible research referral rather than a fabricated citation.

This skill does not decide litigation strategy, predict an outcome, or produce a final filing. The draft is legal work product for a licensed attorney to revise and approve. Do not file unreviewed.

## Use When

- An opposing party has filed a dispositive or non-dispositive motion and counsel needs a first-draft opposition, response outline, or structured oral-argument outline.
- The complete motion papers and enough record material to answer them are available.
- The user needs drafting around authority already supplied or directed by counsel, not independent legal research.
- The matter is active litigation and the output will remain within attorney review.

## Required Inputs

- **Matter identification.** Matter name, number, and enough context to identify the proceeding.
- **Complete movant papers.** The motion, supporting memorandum, declarations, affidavits, and exhibits. A summary is not a substitute. Stop if the papers are missing.
- **Case theory and opposition position.** A concise statement of why the requested relief should be denied or limited. Stop if this is missing.
- **Record materials.** Documents, testimony, pleadings, declarations, or other provided items supporting each response point. Every factual statement must cite a provided record item or carry `[VERIFY: record cite needed]`.
- **Response deadline.** Record only the date exactly as supplied from the docket, scheduling order, or attorney. The skill never calculates a response date and always marks it `[deadline verification required]`.
- **Forum requirements.** Pasted local rules, standing orders, page or word limits, and citation requirements. Anything not supplied remains `[CONFIRM: forum rule not provided]`.
- **Directed authorities.** Authorities counsel has already identified and authorized for use. Missing response authority remains `[citation needed]` and may require `skills/legal-research/legal-research-memo/SKILL.md`.
- **Standard of review.** Use counsel's supplied formulation or `[CONFIRM: standard of review - verify jurisdiction]`.
- Optional: a populated `practice-profiles/litigation.md`, treated as guidance rather than authority.

Do not fabricate an input or draft against a motion the skill has not been shown.

## Do Not Use When

- Drafting the client's affirmative motion or reply. Use `skills/litigation/brief-section-drafter/SKILL.md`.
- Locating new authority. Use `skills/legal-research/legal-research-memo/SKILL.md`, then return with attorney-directed sources.
- Determining whether a cited case remains good law. Use `skills/legal-research/negative-treatment-check/SKILL.md`.
- Building a litigation-grade chronology before drafting. Use `skills/litigation/litigation-chronology/SKILL.md`.
- No complete motion papers are available.
- The user seeks a prediction, merits conclusion, or filing-ready document.

## Legal Safety Rules

- **Source discipline.** Follow `core/source-and-citation-discipline.md`. Never invent authority, quotations, procedural rules, facts, or dates. Distinguish supplied facts, supplied sources, assumptions, analysis, and verification items.
- **Never invent counter-authority.** Mark response propositions `[citation needed]`; route genuine research gaps to the legal-research workflow.
- **Verify every movant authority and current treatment.** Record the citation as presented and mark it `[VERIFY: confirm citation, characterization, holding, and current treatment]`. Never accept the movant's description as correct.
- **Attorney review is mandatory.** The output is draft legal work product, not legal advice. It may not be filed, transmitted, or relied upon until a licensed attorney reviews and approves it.
- **The standard and burden are unverified unless supplied by counsel.** Do not fill either from model memory.
- **Record fidelity is mandatory.** Every factual statement must trace to provided record material. Never characterize an unseen document. Quote supplied text exactly; flag paraphrases `[VERIFY: paraphrase and pinpoint]`.
- **Characterize the motion fairly.** Do not weaken, simplify, or guess at the movant's theory. Flag ambiguity.
- **Flag weak counter-arguments honestly.** Identify unsupported, risky, or strategically weak points and give counsel options to omit, reframe, or research them.
- **Never calculates or implies a deadline.** Record only user-supplied dates and mark every timing item `[deadline verification required]`.
- **Forum rules remain unverified unless provided.** Do not assert format or length requirements from background knowledge.
- **Protect confidentiality and privilege.** Keep sensitive facts and work product inside the matter team.
- **Use the filing banner.** Every opposition draft must state `DRAFT FOR ATTORNEY REVIEW - DO NOT FILE UNREVIEWED`.
- A loaded practice profile may guide style and positions, but never overrides attorney judgment.

## Workflow

1. Confirm the complete motion papers, case theory, matter identity, posture, record materials, supplied deadline, and forum materials. Stop and ask for any required missing input.
2. Route affirmative drafting, new research, negative-treatment checking, and chronology work to the appropriate sibling skill before substantive drafting.
3. Select the execution mode:
   - **quick-triage:** use this core only to identify scope, missing inputs, motion posture, deadline-verification needs, and the modules required for a later draft;
   - **standard:** load `modules/motion-deconstruction.md` and `modules/opposition-drafting.md`;
   - **deep-review:** load both standard modules plus `modules/expanded-verification.md`.
4. Follow the selected modules in order. Universal sequence: deconstruct the motion, verify and map authorities, map record support, flag weak points, draft point by point, and assemble the attorney-review package.
5. Keep all unsupported propositions and missing record support visible. Never silently fill a gap.

## Output Format

Return only the detail supported by the selected mode.

1. **Drafting Notes (internal work product):** motion and posture summary, argument map, movant-authority verification list, response outline, record and authority gaps, weak points, forum-rule questions, and research referrals.
2. **Opposition Draft:** begin with `DRAFT FOR ATTORNEY REVIEW - DO NOT FILE UNREVIEWED`; fairly state each movant argument before answering it; use only supplied record material and directed authority; preserve every verification placeholder.
3. **Attorney Verification Checklist:** include the applicable core and module checks, pre-populated with every unresolved item.

Use `templates/opposition-response-outline.md` when the standard or deep-review mode is selected.

## Attorney Verification Checklist

- [ ] Complete motion papers and supporting materials were reviewed, not summarized or assumed.
- [ ] The case theory, procedural posture, and requested relief are accurately stated.
- [ ] Every movant argument is characterized fairly and every movant authority has been independently checked, including current treatment.
- [ ] Every response authority and pinpoint is supplied from a verified source.
- [ ] Every quotation, paraphrase, and factual statement is confirmed against provided record material.
- [ ] Standard of review, burden, forum rules, and response deadline are independently confirmed. `[verify jurisdiction]` `[deadline verification required]`
- [ ] Every weak point and research referral has been resolved by the responsible attorney.
- [ ] Confidentiality, privilege, and duty-of-candor concerns have been reviewed.
- [ ] The responsible attorney has revised and approved the final filing and accepts professional responsibility for it.
- [ ] Any loaded practice-profile position was treated as guidance, with deviations and profile-silent issues surfaced.
