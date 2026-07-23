

* Skills are instruction modules discovered from configured directories via `SKILL.md`.
* Skills use YAML frontmatter with fields such as `name` and `description`.
* Skills are selected by the model when appropriate, rather than being permanently embedded into every prompt.
* Skills are intended to encapsulate reusable procedures, not general knowledge or agent identity.
* OpenClaw defines the loading mechanism, but it does **not** prescribe naming conventions, granularity, lifecycle, or engineering standards. Those are left to the workspace designer.

Therefore, everything below becomes the **Recruiting Workspace Skill Standard**, built on top of OpenClaw rather than copied from it.

---

# Part VI — Skills Architecture

## 6.1 Purpose

Skills are reusable instruction modules that teach the Recruiting Agent how to perform specific recruiting activities.

Unlike bootstrap files, which define persistent identity and behavior, skills provide **task-specific operational knowledge** that the runtime can invoke when relevant.

Skills extend the capabilities of the Recruiting Agent without changing its identity or operating principles.

---

# 6.2 What is a Skill?

A skill is a self-contained procedural guide describing **how to accomplish one well-defined objective**.

A skill is **not**:

* a personality definition,
* a workflow manual,
* a memory store,
* a plugin,
* business logic,
* or source code.

Instead, a skill captures expert knowledge for performing a repeatable recruiting activity.

Examples include:

* Resume Screening
* Candidate Comparison
* Interview Planning
* Offer Preparation
* Hiring Analytics

---

# 6.3 Architectural Role

The Recruiting Workspace consists of multiple architectural layers.

```text
Identity
      │
      ▼
Behavior
      │
      ▼
Operational Rules
      │
      ▼
Skills
      │
      ▼
Plugins
      │
      ▼
CRM
```

Each layer answers a different question.

| Layer    | Question                    |
| -------- | --------------------------- |
| Identity | Who am I?                   |
| Soul     | How should I think?         |
| Agent    | How should I work?          |
| Skill    | How do I perform this task? |
| Plugin   | What can I execute?         |

---

# 6.4 Skill Lifecycle

Every skill follows a defined lifecycle.

```text
Identify Need
      │
      ▼
Design
      │
      ▼
Implement
      │
      ▼
Review
      │
      ▼
Deploy
      │
      ▼
Observe
      │
      ▼
Refine
```

Skills should evolve independently from the Recruiting Agent.

Adding or improving a skill should not require modifying the agent's identity or philosophy.

---

# 6.5 Skill Anatomy

Every skill contains four conceptual sections.

```text
Metadata
      │
Purpose
      │
Execution Guidance
      │
Validation
```

Typical contents include:

* YAML frontmatter
* Description
* When to use
* When not to use
* Preconditions
* Execution process
* Validation rules
* Expected outcome
* Recovery guidance

---

# 6.6 Skill Granularity

A skill should perform **one recruiter activity**.

Good examples:

* Resume Screening
* Candidate Comparison
* Schedule Interview
* Prepare Offer

Poor examples:

* Recruiting
* CRM Operations
* Interview + Offer + Hiring
* Everything about Candidates

A skill should answer a single operational question.

If a skill becomes difficult to explain in one document, it should probably be divided.

---

# 6.7 Skill Naming

Skill names should describe recruiter activities rather than software features.

Recommended pattern:

```text
Verb + Business Activity
```

Examples:

* Screen Resume
* Compare Candidates
* Plan Interview
* Prepare Offer
* Generate Hiring Report

Avoid:

* Candidate Skill
* Workflow Skill
* CRM Skill
* Utilities
* Miscellaneous

Names should be immediately understandable to both humans and language models.

---

# 6.8 Skill Dependencies

Skills should remain as independent as possible.

A skill may depend upon:

* Recruiting principles
* Agent operating rules
* Workspace philosophy

A skill should **not** depend directly upon another skill.

Instead, shared behavior belongs inside the workspace architecture.

This minimizes coupling and improves reuse.

---

# 6.9 When to Create a New Skill

Create a new skill when:

* a recruiting activity is reused frequently,
* the procedure is sufficiently complex,
* specialized reasoning improves quality,
* instructions would otherwise clutter AGENTS.md,
* multiple workflows share the same process.

Examples:

* Resume Screening
* Candidate Ranking
* Interview Evaluation
* Offer Generation

---

# 6.10 When Not to Create a Skill

Do **not** create a new skill merely because:

* a new CRM object exists,
* a new API exists,
* a new database table exists,
* a workflow differs only slightly,
* instructions are only one or two sentences.

The Recruiting Workspace should prefer fewer, higher-quality skills over many narrowly focused skills.

---

# 6.11 Standard SKILL.md Structure

Every recruiting skill should follow a consistent structure.

```text
YAML Metadata

Purpose

When to Use

When NOT to Use

Inputs

Preconditions

Execution Process

Validation

Recovery

Expected Output
```

Recommended execution pattern:

```text
Understand
      │
Validate
      │
Plan
      │
Execute
      │
Verify
      │
Report
```

This structure improves readability and promotes consistency across the workspace.

---

# 6.12 Planning Expectations

A skill should assist execution rather than replace reasoning.

Before using a skill, the Recruiting Agent should:

1. Confirm the skill is appropriate.
2. Verify prerequisites.
3. Gather required information.
4. Determine whether additional skills are necessary.
5. Validate the final outcome.

Skills provide procedures, while the agent remains responsible for planning.

---

# 6.13 Error Handling

Every skill should anticipate operational failures.

Minimum recovery expectations include:

* missing information,
* validation failures,
* duplicate records,
* permission issues,
* unavailable tools,
* workflow conflicts,
* unexpected CRM responses.

Recovery should follow the general workspace strategy:

```text
Detect
      │
Diagnose
      │
Recover
      │
Verify
      │
Explain
```

Skills should recover gracefully whenever possible and escalate when recovery is unsafe or impossible.

---

# 6.14 Examples

### Good Skills

* Resume Screening
* Candidate Comparison
* Interview Planning
* Interview Evaluation
* Prepare Offer
* Hiring Analytics
* Workflow Recovery

These skills represent **recruiter activities**.

---

### Poor Skills

* Candidate Object
* CRM API
* Database Operations
* Utilities
* Helper Functions
* Everything Recruiting

These represent technical implementation details rather than business procedures.

---

# 6.15 Skill Quality Checklist

Every skill should satisfy the following criteria before deployment.

## Purpose

* Clearly defines one recruiting activity.
* Solves a reusable problem.
* Avoids overlapping responsibilities.

## Structure

* Follows the standard SKILL.md layout.
* Uses clear metadata.
* Maintains consistent terminology.

## Behavior

* Defines appropriate usage conditions.
* States explicit preconditions.
* Describes expected outputs.
* Includes validation guidance.
* Includes recovery guidance.

## Quality

* Focused on one responsibility.
* Independent of implementation details.
* Reusable across recruiting workflows.
* Easy to understand.
* Easy to maintain.

A skill should be considered complete only when it can be reused confidently without requiring additional explanation.

---

# 6.16 Skill Taxonomy

To maintain long-term organization, recruiting skills should be grouped by business capability rather than by technical implementation.

| Category             | Example Skills                                                    |
| -------------------- | ----------------------------------------------------------------- |
| Candidate Management | Resume Screening, Candidate Comparison, Talent Pool Review        |
| Job Management       | Job Creation Support, Job Description Review, Publishing Guidance |
| Interview Management | Interview Planning, Interview Evaluation, Feedback Consolidation  |
| Offer Management     | Offer Preparation, Compensation Review, Offer Validation          |
| Analytics            | Hiring Analytics, Pipeline Analysis, Recruitment Metrics          |
| Operations           | Workflow Recovery, Duplicate Resolution, Data Quality Review      |

