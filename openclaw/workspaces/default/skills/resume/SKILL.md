---
name: resume
description: "Use for resume parsing, screening, matching, comparison, and evidence-based ranking. Integrates with candidate/application records through the Twenty plugin but does not change lifecycle state."
---

# Resume Assessment

## Purpose

Convert supplied resume and job-requirement evidence into structured, explainable recruiter support.

## Responsibilities

- Extract factual resume content with uncertainty markers.
- Screen a resume against a requisition.
- Match and compare resumes using role-relevant criteria.
- Produce evidence-based ranking, not an automatic employment decision.

## Scope

This skill owns analysis of authorized resume materials against explicit role criteria. It does not resolve candidate identity, create external communications, or change application lifecycle state.

## Scope and approval

Use only candidate-provided or authorized resume artifacts. Store a parsed summary or draft evaluation only through `crm.write_field()` after confirming the target application. Do not advance/reject an application; use the application workflow only after an authorized human decision.

## Process

1. Read `references/assessment-rubric.md`.
2. Read the requisition and its requirements; inspect metadata if fields are uncertain.
3. Extract evidence, preserving unknowns and avoiding inference from protected or irrelevant personal attributes.
4. Compare evidence against explicit role criteria; record strengths, gaps, and questions.
5. For multi-candidate comparison, use the same criteria and weights for every candidate.
6. Produce an explanation with evidence citations and uncertainty.
7. If asked to persist a summary/evaluation, use a safe CRM write; verify it afterward.

## Failure handling

- Unreadable/incomplete resume: report missing sections rather than filling them in.
- Missing requisition criteria: request or summarize available requirements; do not fabricate a rubric.
- Incomparable materials: explain why a rank cannot be defensible.
- Sensitive information: exclude it from scoring and flag it for appropriate human handling.

## Related skills

`candidate` resolves identity; `jd` improves requisition criteria; `evaluation` produces shortlist/recommendation artifacts; `crm` handles persistence.

## Examples and validation

See `examples/README.md` and `tests/README.md`.