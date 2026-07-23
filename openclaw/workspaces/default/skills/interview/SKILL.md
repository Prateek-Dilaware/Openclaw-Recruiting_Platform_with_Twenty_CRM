---
name: interview
description: "Use for interview preparation, interview briefs, transcript interpretation, and interview-evaluation drafts. Does not perform ElevenLabs integration or lifecycle transitions directly."
---

# Interview Preparation and Interpretation

## Purpose

Prepare structured interviews and interpret authorized transcript material into explainable evaluation drafts.

## Responsibilities

- Build an interview brief from the requisition, application, and prior evidence.
- Produce role-relevant question plans and scoring criteria.
- Interpret supplied transcripts with evidence and uncertainty.
- Draft interview evaluations for human review.

## Scope

This skill owns interview preparation and interpretation of authorized artifacts. It does not schedule, send invitations, operate voice services, or transition interview/application state.

## Scope and approvals

Do not implement ElevenLabs calls or send invitations. Store authorized transcript/evaluation artifacts only through `crm.write_field()`. Scheduling, confirmation, completion, cancellation, and stage movement are workflow operations owned by `scheduling`/`crm`.

## Process

1. Read `references/interview-framework.md`.
2. Confirm the application, requisition, interview round, interview type, and interviewer role.
3. Build a structured brief: objectives, evidence to probe, questions, rubric, and interviewer notes.
4. For a transcript, separate direct evidence, candidate statements, evaluator interpretation, and missing evidence.
5. Produce a draft evaluation with score rationale, strengths, concerns, and follow-up questions.
6. Persist only after the intended record and fields are confirmed; re-read to verify.

## Failure handling

- Missing requisition/round: request the role context before producing a generic plan.
- Incomplete transcript: report coverage limits; do not infer answers.
- Conflicting interviewer evidence: preserve the conflict and recommend human review.
- Any instruction to complete/cancel an interview: use the Interview Lifecycle workflow through `crm.trigger_workflow()`.

## Related skills

`scheduling` owns lifecycle scheduling; `evaluation` compares results; `communication` drafts follow-up text; `crm` is the sole CRM boundary.

## Examples and validation

See `examples/README.md` and `tests/README.md`.