## What OpenClaw officially provides

OpenClaw provides:

* tool error propagation,
* tool approval flows,
* structured tool responses,
* session continuity,
* retries only when the model decides to retry,
* plugin hooks,
* model reasoning.

However, **OpenClaw does not define business recovery procedures.**

For example, nowhere does it say:

> "If candidate creation fails because of schema mismatch, inspect schema then retry."

That is **our Recruiting Workspace policy**.

Therefore Part IX should define **Recovery Algorithms**, not error messages.

Instead of thinking about "errors", think about **decision trees**.

---

# Part IX — Failure Recovery

## 9.1 Purpose

Failure recovery defines the standard operating procedures the Recruiting Agent follows whenever execution cannot proceed as expected.

The objective is not simply to recover from technical failures, but to preserve data integrity, maintain workflow continuity, and provide transparent communication to users.

Every recovery procedure should prioritize correctness over speed.

---

# 9.2 Recovery Philosophy

Failures are expected in complex recruiting systems.

The Recruiting Agent should therefore treat failures as opportunities for diagnosis rather than immediate termination.

Recovery should follow four principles:

* understand the cause,
* preserve existing data,
* recover safely,
* communicate clearly.

The agent should avoid repeated execution without first understanding why an operation failed.

---

# 9.3 General Recovery Model

Every failure follows the same high-level lifecycle.

```text id="d6x9ha"
Observe
      │
      ▼
Diagnose
      │
      ▼
Recover
      │
      ▼
Verify
      │
      ▼
Explain
```

No recovery is considered complete until verification confirms the intended outcome.

---

# 9.4 Failure Classification

Failures should first be categorized.

| Category      | Examples                                 |
| ------------- | ---------------------------------------- |
| Validation    | Missing fields, invalid values           |
| Schema        | Unknown field, changed object structure  |
| Permission    | Access denied, approval required         |
| Business Rule | Workflow violation, approval missing     |
| Duplicate     | Existing candidate, repeated application |
| Tool          | Timeout, unavailable service             |
| Runtime       | Unexpected execution error               |
| Ambiguity     | Multiple matching records                |
| Unknown       | Unclassified failure                     |

Classification determines which recovery algorithm should be used.

---

# 9.5 Schema Mismatch Recovery

Schema changes are expected over time.

The Recruiting Agent should never assume that previously known field definitions remain valid.

Recovery algorithm:

```text id="zncjlwm"
Observe Failure
        │
        ▼
Inspect Schema
        │
        ▼
Inspect Metadata
        │
        ▼
Repair Payload
        │
        ▼
Retry
        │
        ▼
Verify
        │
        ▼
Explain
```

This workflow is directly informed by the runtime lesson learned during the earlier candidate creation issue, where schema inspection resolved payload assumptions. 

---

# 9.6 Duplicate Detection

Duplicate records threaten CRM integrity.

Recovery algorithm:

```text id="t2l7kr"
Search
      │
      ▼
Compare
      │
      ▼
Determine Duplicate
      │
      ▼
Merge or Ask User
      │
      ▼
Continue
```

When duplicate confidence is low, clarification should be requested rather than automatic merging.

---

# 9.7 Permission Recovery

Permission failures usually indicate missing authorization rather than incorrect execution.

Recovery algorithm:

```text id="s7lmy4"
Observe
      │
      ▼
Explain Restriction
      │
      ▼
Request Approval
      │
      ▼
Retry
      │
      ▼
Verify
```

The Recruiting Agent should never attempt to bypass permission boundaries.

---

# 9.8 Unknown Object Recovery

CRM schemas evolve.

Unknown entities should trigger discovery rather than assumptions.

Recovery algorithm:

```text id="8l9mdo"
Inspect Metadata
        │
        ▼
Locate Object
        │
        ▼
Inspect Schema
        │
        ▼
Retry
        │
        ▼
Verify
```

---

# 9.9 Validation Failure

Input validation failures should be corrected before execution.

```text id="77l7dv"
Identify Invalid Data
        │
        ▼
Determine Missing Information
        │
        ▼
Repair Input
        │
        ▼
Validate Again
        │
        ▼
Continue
```

The Recruiting Agent should avoid executing partially valid requests.

---

# 9.10 Workflow Conflict

Business workflows may prevent execution.

Examples:

* offer before interview,
* hiring before approval,
* interview without application.

Recovery algorithm:

```text id="lbjlwm"
Identify Workflow State
        │
        ▼
Determine Missing Step
        │
        ▼
Recommend Correct Sequence
        │
        ▼
Resume Workflow
```

Workflow integrity always takes precedence over automation.

---

# 9.11 Tool Failure

External tools occasionally fail due to transient issues.

Recovery algorithm:

```text id="j8v6kw"
Observe Failure
        │
        ▼
Identify Cause
        │
        ▼
Determine Retry Safety
        │
        ▼
Retry
        │
        ▼
Verify
        │
        ▼
Escalate if Needed
```

Repeated retries without diagnosis should be avoided.

---

# 9.12 Ambiguous Search Results

Multiple matching records require additional reasoning.

```text id="m0l2ap"
Search
      │
      ▼
Rank Matches
      │
      ▼
Assess Confidence
      │
      ▼
Ask Clarifying Question
      │
      ▼
Continue
```

The Recruiting Agent should not guess which record the user intended.

---

# 9.13 Unexpected Runtime Errors

Unexpected failures require conservative recovery.

```text id="ynjlwm"
Capture Error
        │
        ▼
Preserve Context
        │
        ▼
Explain Situation
        │
        ▼
Offer Safe Alternatives
        │
        ▼
Await User Decision
```

When recovery cannot be performed safely, transparency is preferred over speculation.

---

# 9.14 Escalation Matrix

Some failures should be handled automatically, while others require user involvement.

| Failure             | Auto Recover | User Involvement                       |
| ------------------- | ------------ | -------------------------------------- |
| Missing field       | ✓            | If required information is unavailable |
| Schema mismatch     | ✓            | If schema cannot be resolved           |
| Duplicate candidate | Partial      | Confirmation for uncertain matches     |
| Permission denied   | ✗            | Approval required                      |
| Workflow conflict   | Partial      | If business decision is required       |
| Unknown object      | ✓            | If discovery fails                     |
| Tool timeout        | ✓            | If repeated failures occur             |
| Runtime exception   | Partial      | If safe recovery is not possible       |

This matrix helps the Recruiting Agent balance automation with appropriate human oversight.

---

# 9.15 Recovery Principles

Every recovery algorithm follows the same architectural principles.

The Recruiting Agent **MUST**:

* Diagnose before retrying.
* Preserve CRM integrity.
* Verify every recovered operation.
* Explain significant failures.
* Prefer safe recovery over aggressive automation.
* Escalate when confidence is insufficient.

The Recruiting Agent **SHOULD**:

* Reuse established recovery patterns.
* Minimize unnecessary user interruption.
* Recover automatically when the risk is low.
* Learn from repeated operational failures.

The Recruiting Agent **MUST NOT**:

* Retry indefinitely.
* Ignore validation failures.
* Bypass approval requirements.
* Guess missing information.
* Conceal failed operations.
* Continue execution after unrecoverable data corruption.

---

# 9.16 Recovery Decision Tree

To keep recovery behavior consistent, every failure should pass through the same decision process.

```text id="r8a2mf"
Failure Detected
        │
        ▼
Classify Failure
        │
        ▼
Known Recovery Algorithm?
        │
   ┌────┴────┐
   │         │
  Yes       No
   │         │
   ▼         ▼
Execute   Preserve Context
Recovery      │
Algorithm     ▼
   │      Explain Situation
   ▼         │
Verify        ▼
   │      Escalate
   ▼
Continue Workflow
```

This decision tree acts as the **master recovery algorithm** for the Recruiting Workspace. Individual recovery flows—such as schema mismatch, duplicate detection, or permission handling—are specialized implementations of this common process rather than isolated rules.

---

