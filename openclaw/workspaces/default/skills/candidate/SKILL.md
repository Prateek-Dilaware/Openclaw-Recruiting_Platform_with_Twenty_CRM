---
name: candidate
description: "Use for candidate search, create, update, merge review, profile summary, and timeline review in Twenty CRM. Uses the Twenty plugin through the CRM operation boundary and never assumes CRM schema details."
---

# Candidate Management

## Purpose

Perform candidate-profile activities while preserving Twenty CRM as the system of record.

## Responsibilities

- Search candidates using verified metadata and record filters.
- Create a candidate after duplicate review.
- Update non-lifecycle candidate data.
- Prepare a merge recommendation; never automatically merge records.
- Produce profile summaries and activity timelines from CRM evidence.

## Scope

This skill owns person-level candidate information. It does not assess resumes, make comparative hiring recommendations, send messages, or move recruiting lifecycle state.

## When to use

Use for a person-level recruiting record. Use the `resume` skill for resume analysis, `evaluation` for comparative decisions, and `crm` for lifecycle state changes.

## Approval requirements

Candidate creation and non-state updates require confirmation of the target and intended fields. Candidate merge requires explicit human approval after a side-by-side comparison. A stage change is not a candidate update; use `crm.trigger_workflow()` against the related application.

## Process

1. Read `references/candidate-procedure.md`.
2. Discover candidate metadata when fields are not verified.
3. Search by stable identifiers first (email, then verified name/context). Return ambiguity instead of selecting silently.
4. For create/update, state the data source, target record, and fields. Use the CRM safe-write procedure.
5. For a merge request, compare identities, applications, interviews, evaluations, notes, and conflict fields; provide a proposed survivor and conflict list only.
6. For a summary/timeline, distinguish CRM facts from generated interpretation and cite record ids/dates.
7. Re-read after a successful mutation and report the result.

## Failure handling

- Missing consent or identifying data: request the minimum needed information.
- Multiple possible matches: return them; do not create a duplicate or merge.
- Unverified custom field: inspect metadata before writing.
- Plugin failure: do not retry a create blindly; search/re-read first.

## Related skills

`crm` supplies the Twenty boundary. `resume` writes resume-derived facts. `research` prepares public evidence without automatically storing it.

## Examples and validation

See `examples/README.md`, `references/candidate-procedure.md`, and `tests/README.md`.