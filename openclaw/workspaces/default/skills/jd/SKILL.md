---
name: jd
description: "Use for job-description generation, improvement, requirement extraction, and requirement summaries tied to a recruiting requisition. Produces drafts and safe informational CRM updates, not requisition lifecycle changes."
---

# Job Description

## Purpose

Prepare clear, inclusive, role-specific job-description drafts and structured requirement summaries.

## Responsibilities

- Generate a JD from supplied hiring context.
- Improve an existing JD without changing its approved meaning silently.
- Extract requirements into explicit, reviewable categories.
- Summarize requirements for recruiters and downstream assessment skills.

## Scope

This skill owns content drafting and requirement clarification for a requisition. It does not approve, post, close, or otherwise transition a requisition lifecycle.

## Approval requirements

Treat generated JDs as drafts. A recruiter must approve content before external publication. Saving `jobDescription`, `requiredSkills`, or other non-lifecycle requisition content uses `crm.write_field()`. Approval, posting, closing, or any requisition-status change uses `crm.trigger_workflow()`.

## Process

1. Read `references/jd-standard.md`.
2. Read the requisition and confirm role, department, location, employment type, seniority, and constraints.
3. Separate required, preferred, and negotiable criteria. Flag contradictory or missing requirements.
4. Draft or revise only from supplied facts; label assumptions/questions.
5. Run the validation checklist before presenting the draft.
6. Persist only an approved informational draft via the CRM safe-write procedure; verify it.

## Failure handling

- Missing role context: request a minimum hiring brief.
- Conflicting requirements: preserve both positions and request a decision.
- Request to post/approve: route through the approved requisition workflow, not a field update.

## Related skills

`resume` consumes requirement summaries; `communication` formats approved external copy; `crm` owns persistence and workflows.

## Examples and validation

See `examples/README.md` and `tests/README.md`.