---
name: evaluation
description: "Use for candidate comparison, evidence-based ranking, hiring-recommendation drafts, and shortlist generation. Requires explainable criteria and never makes unexplained or automatic hiring decisions."
---

# Candidate Evaluation

## Purpose

Help recruiters compare candidates consistently using role-relevant, traceable evidence.

## Responsibilities

- Compare candidates/applications against one requisition.
- Create transparent rankings and shortlist drafts.
- Prepare hiring recommendation drafts with evidence, uncertainty, and disconfirming evidence.

## Scope

This skill owns comparative decision support. It does not make final hiring decisions or mutate recruiting lifecycle state.

## Scope and approvals

This skill produces recommendations, not final employment decisions. It may save an authorized evaluation score, summary, recommendation, or evidence through `crm.write_field()`. It must never reject, hire, offer, or advance an application through a raw update; those are approved workflow changes.

## Process

1. Read `references/decision-standard.md`.
2. Confirm all compared candidates relate to the same requisition or explicitly explain the mismatch.
3. Establish criteria from the approved requisition before reviewing candidates.
4. Apply the same criteria and weights to every candidate.
5. Show evidence, uncertainty, gaps, and counterevidence for each conclusion.
6. Produce a ranked shortlist only when evidence is comparable. Otherwise return grouped findings or “insufficient evidence.”
7. Label the output as a recruiter decision aid and persist only non-state evaluation artifacts after confirmation.

## Failure handling

- Missing requisition criteria: stop ranking; request criteria or provide a non-ranked evidence summary.
- Unequal evidence: identify the missing evidence and avoid false precision.
- Sensitive/irrelevant data: exclude it from assessment and flag it for human handling.
- Request to change an outcome: invoke the relevant approved workflow via `crm.trigger_workflow()` only after authorization.

## Related skills

`resume` and `interview` create evidence; `crm` stores it; `retrospective` reviews overrides and failures.

## Examples and validation

See `examples/README.md` and `tests/README.md`.