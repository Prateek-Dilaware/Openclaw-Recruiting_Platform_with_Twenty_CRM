---
name: retrospective
description: "Use for reviewing recruiter overrides, failed recommendations, recurring mistakes, and improvement recommendations. Read-only analysis; never automatically changes prompts, skills, workflows, or CRM records."
---

# Recruiting Retrospective

## Purpose

Analyze outcomes and recruiter feedback to recommend measurable improvements to recruiting skills and operations.

## Responsibilities

- Review recruiter overrides and their stated reasons.
- Review failed recommendations and workflow/plugin failures.
- Identify recurring evidence gaps, calibration issues, and process friction.
- Produce recommendations with expected benefit, risk, and validation plan.

## Scope

This skill owns read-only operational learning. It does not edit prompts, skills, workflows, configuration, scores, or CRM records.

## Scope and approvals

This skill is read-only. It must never modify prompts, skills, workflow definitions, CRM records, scores, or configuration. Recommendations require human review and a separate implementation/change process.

## Process

1. Read `references/retrospective-method.md`.
2. Define a bounded review period and data set; minimize personal data in the analysis.
3. Compare original recommendation, available evidence, human override/outcome, and stated reason.
4. Separate root-cause hypotheses from observed facts.
5. Group recurring patterns only when the sample and evidence justify it.
6. Recommend reversible, testable changes with metrics and a human owner.
7. Report explicitly that no changes were applied.

## Failure handling

- Missing override reason/outcome: label the case incomplete; do not infer cause.
- Small or biased sample: report directional findings only.
- Sensitive data: aggregate/redact as appropriate and avoid reproducing unnecessary candidate content.
- Request to auto-fix: refuse automatic modification and provide a proposed reviewed change plan instead.

## Related skills

`evaluation`, `resume`, and `interview` provide recommendation artifacts. `crm` provides read-only evidence access. Changes are implemented only through a separate approved engineering workflow.

## Examples and validation

See `examples/README.md` and `tests/README.md`.