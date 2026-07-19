---
name: research
description: "Use for company research, candidate public-profile research, public-profile summaries, and GitHub summaries. Prefers approved browser capabilities and produces sourced summaries without automatic CRM mutation."
---

# Recruiting Research

## Purpose

Gather and summarize authorized public information relevant to recruiting decisions or preparation.

## Responsibilities

- Research companies and role context.
- Summarize candidate-provided or authorized public profiles.
- Summarize public GitHub repositories and contribution evidence.

## Scope

This skill owns bounded, authorized public-information research and sourced summaries. It does not access private sources, bypass site controls, or make automatic CRM changes.

## Scope and approval

Prefer approved browser capabilities when available. Respect site terms, access controls, and data-minimization rules. Do not bypass authentication, scrape private data, infer sensitive characteristics, or automatically write research findings into Twenty CRM. A recruiter must review any proposed persistence via `crm.write_field()`.

## Process

1. Read `references/research-standard.md`.
2. Confirm the research question, permitted sources, purpose, and subject identity.
3. Use browser capabilities to collect only relevant public evidence; capture source URLs and access dates.
4. Distinguish observed fact, source claim, and agent interpretation.
5. State confidence, gaps, and information that could not be verified.
6. Return a sourced summary for review. Persist only after explicit authorization through the CRM safe-write procedure.

## Failure handling

- Browser capability unavailable: report the limitation; do not build a custom scraper.
- Login wall/robots/access restriction: do not bypass it; report available alternatives.
- Identity ambiguity: request confirmation before associating a public profile with a candidate.
- Weak/contradictory sources: preserve uncertainty rather than forcing a conclusion.

## Related skills

`candidate` confirms CRM identity; `resume`/`evaluation` consume approved evidence; `crm` handles optional persistence.

## Examples and validation

See `examples/README.md` and `tests/README.md`.