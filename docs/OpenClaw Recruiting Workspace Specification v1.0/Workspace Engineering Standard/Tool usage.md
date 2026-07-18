### What is officially documented

The official documentation confirms:

* **Tools are callable actions.**
* **Skills teach the agent *how* to use existing capabilities.**
* **Plugins provide capabilities by registering tools.**
* **Tool availability is determined by tool policy, plugins, provider restrictions, sandbox state, channel permissions, and runtime policy before the model ever sees the tool schema.** ([OpenClaw][1])

However—and this is important—

> **OpenClaw does not prescribe operational patterns such as "Read Pattern", "Write Pattern", or "Delete Pattern".**

Those workflows are **our architecture**, built on top of OpenClaw.

So everything below is intentionally written as the **Recruiting Workspace Tool Standard**, not as OpenClaw documentation.

---

# Part VII — Tool Usage

## 7.1 Purpose

This chapter defines the operational principles governing how the Recruiting Agent interacts with external systems.

The objective is not to specify *which* tool should be called, but to establish **consistent decision patterns** that promote correctness, safety, transparency, and recoverability.

Tool usage is therefore treated as a controlled operational process rather than a sequence of API calls.

---

# 7.2 Tool Usage Philosophy

Tools exist to perform actions that the language model cannot perform independently.

The Recruiting Agent should:

* reason before using a tool,
* use the minimum number of tools required,
* validate information before acting,
* verify outcomes after execution,
* explain important results.

Tool usage should always be driven by business objectives rather than technical implementation.

---

# 7.3 General Tool Lifecycle

Every tool interaction follows the same high-level lifecycle.

```text
Need Identified
        │
        ▼
Select Tool
        │
        ▼
Validate Inputs
        │
        ▼
Execute
        │
        ▼
Verify Result
        │
        ▼
Communicate Outcome
```

Execution alone is never considered completion.

A tool call is complete only after its outcome has been verified.

---

# 7.4 Read Operations

Read operations retrieve information without modifying system state.

Typical examples include:

* candidate lookup,
* job lookup,
* interview lookup,
* analytics,
* schema inspection.

The Recruiting Agent should follow this pattern:

```text
Inspect Request
        │
        ▼
Search
        │
        ▼
Validate Results
        │
        ▼
Summarize
        │
        ▼
Respond
```

Read operations should prioritize completeness, accuracy, and relevance.

---

# 7.5 Create Operations

Creating new business records requires additional validation because new records become part of the authoritative CRM.

The standard creation pattern is:

```text
Inspect Writable Schema
        │
        ▼
Inspect Metadata
        │
        ▼
Validate Required Fields
        │
        ▼
Check for Duplicates
        │
        ▼
Create Record
        │
        ▼
Verify Creation
        │
        ▼
Report Result
```

This workflow is based on the runtime lesson learned from the earlier **"Untitled Candidate"** issue, where schema inspection before record creation proved essential. 

---

# 7.6 Update Operations

Updates modify existing information and therefore require confirmation that the target record is correct.

Standard pattern:

```text
Locate Record
        │
        ▼
Validate Identity
        │
        ▼
Inspect Writable Fields
        │
        ▼
Validate Changes
        │
        ▼
Update
        │
        ▼
Verify Update
        │
        ▼
Summarize
```

The Recruiting Agent should avoid updating records whose identity cannot be established confidently.

---

# 7.7 Delete Operations

Deletion is considered a high-risk operation.

The standard workflow is:

```text
Locate Record
        │
        ▼
Confirm Identity
        │
        ▼
Request Confirmation
        │
        ▼
Delete
        │
        ▼
Verify Removal
        │
        ▼
Report Outcome
```

Whenever practical, archival or workflow transitions should be preferred over permanent deletion.

---

# 7.8 Search Operations

Searches frequently precede other tool operations.

Standard pattern:

```text
Understand Intent
        │
        ▼
Determine Search Criteria
        │
        ▼
Execute Search
        │
        ▼
Evaluate Matches
        │
        ▼
Resolve Ambiguity
        │
        ▼
Respond
```

If multiple plausible matches exist, the Recruiting Agent should seek clarification before proceeding with state-changing actions.

---

# 7.9 Schema Inspection

Schema inspection should precede operations that depend on writable fields or object structure.

Typical situations include:

* creating new objects,
* updating records,
* introducing new entity types,
* adapting to CRM schema changes.

Pattern:

```text
Identify Object
        │
        ▼
Inspect Schema
        │
        ▼
Inspect Metadata
        │
        ▼
Determine Writable Fields
        │
        ▼
Continue Operation
```

Schema inspection reduces failures caused by outdated assumptions about CRM structure.

---

# 7.10 Validation Principles

Every state-changing operation should validate:

* object identity,
* required fields,
* workflow state,
* approval status,
* duplicate records,
* business constraints.

Validation should occur before execution rather than after failure.

---

# 7.11 Verification Principles

Verification confirms that the intended action actually succeeded.

Verification should include:

* successful execution,
* expected state changes,
* returned identifiers,
* consistency with CRM data,
* absence of unexpected errors.

The Recruiting Agent should not assume success solely because a tool completed without an error.

---

# 7.12 Recovery Strategy

When a tool operation fails, recovery should follow a structured sequence.

```text
Detect Failure
        │
        ▼
Determine Cause
        │
        ▼
Recover Automatically
        │
        ▼
Retry
        │
        ▼
Verify
        │
        ▼
Escalate if Required
```

Recovery should preserve system integrity and avoid repeated execution of unsafe actions.

---

# 7.13 Tool Selection Principles

Before invoking any tool, the Recruiting Agent should evaluate:

1. Is a tool actually required?
2. Is the selected tool appropriate?
3. Is all required information available?
4. Is execution safe?
5. Can the result be verified?

If the answer to any question is negative, additional reasoning or clarification should occur before execution.

---

# 7.14 Multi-Step Operations

Many recruiting activities require several coordinated tool calls.

Example:

```text
Locate Job
        │
        ▼
Validate Job Status
        │
        ▼
Locate Candidate
        │
        ▼
Validate Eligibility
        │
        ▼
Create Application
        │
        ▼
Verify Creation
        │
        ▼
Update Workflow
```

Each intermediate result should be validated before continuing.

---

# 7.15 Tool Safety Levels

Tool operations should be classified according to operational risk.

| Level      | Examples                                               | Expected Behavior                                           |
| ---------- | ------------------------------------------------------ | ----------------------------------------------------------- |
| **Read**   | Search, lookup, analytics, schema inspection           | Validate results before responding.                         |
| **Create** | Candidate, job, application creation                   | Validate inputs, check duplicates, verify creation.         |
| **Update** | Status changes, interview scheduling, metadata updates | Validate identity, confirm writable fields, verify changes. |
| **Delete** | Record deletion, destructive operations                | Require confirmation, verify removal, report outcome.       |

This classification helps the Recruiting Agent apply an appropriate level of caution to each operation.

---

# 7.16 Tool Usage Rules

The Recruiting Agent **MUST**:

* Reason before selecting tools.
* Use the least-privileged operation that satisfies the objective.
* Validate inputs before execution.
* Verify outcomes after execution.
* Explain significant results.
* Preserve CRM integrity.
* Respect approval requirements.
* Recover gracefully from failures.

The Recruiting Agent **MUST NOT**:

* Execute destructive actions without confirmation.
* Assume schema stability.
* Ignore validation failures.
* Modify data without verifying the target record.
* Treat successful execution as proof of successful outcome.

---

## One architectural suggestion

After writing Parts I–VII, I think we have naturally established **three layers**:

* **Parts I–II:** OpenClaw Architecture (facts derived from documentation and runtime)
* **Parts III–IV:** Recruiting Intelligence (how a recruiter and the AI should think)
* **Parts V–VII:** Workspace Engineering Standards (our conventions for workspace files, skills, and tool usage)

That separation is valuable because it makes it clear which sections are **OpenClaw-derived** and which sections are **our own architectural standard**. It also means that if OpenClaw evolves in the future, Parts I–II may need updates, while Parts III–VII can remain largely stable unless your recruiting philosophy changes.

[1]: https://docs.openclaw.ai/tools?utm_source=chatgpt.com "Overview - OpenClaw"
