This is exactly the chapter where we **must distinguish between what OpenClaw defines and what our architecture defines**.

After checking the latest official documentation and comparing it with your runtime investigation, here's the important conclusion:

> **OpenClaw officially documents what each bootstrap file is generally for, but it does *not* define strict architectural contracts such as "allowed content", "forbidden content", ownership, or dependency rules.** Those are intentionally left to the workspace designer. ([OpenClaw][1])

That means **Part V is where our architecture begins.**

Everything before this chapter is largely derived from OpenClaw.

Everything from this chapter onward becomes **our Recruiting Workspace Standard**.

I would even call this out at the beginning of the chapter.

---

# Part V — Workspace Architecture

## 5.1 Purpose

The Workspace Architecture defines the structural contracts for every bootstrap file within the Recruiting Workspace.

OpenClaw specifies the existence and general purpose of these files, but it deliberately leaves their internal organization to the workspace designer. This specification formalizes those responsibilities to ensure consistency, maintainability, and clear separation of concerns across the Recruiting Workspace. ([OpenClaw][1])

Each workspace file has a single primary responsibility. Responsibilities must not overlap unless explicitly defined by this specification.

---

# 5.2 Workspace Layer Model

The Recruiting Workspace is organized as six behavioral layers.

```text
Layer 1
Identity
        │
Layer 2
Principles & Personality
        │
Layer 3
Operational Behavior
        │
Layer 4
Tool Guidance
        │
Layer 5
User Context
        │
Layer 6
Memory & Background Operations
```

Each bootstrap file belongs to exactly one layer.

This separation minimizes instruction conflicts and improves long-term maintainability.

---

# 5.3 Workspace Responsibilities

| File                       | Primary Responsibility                                                  |
| -------------------------- | ----------------------------------------------------------------------- |
| `IDENTITY.md`              | Defines who the agent is.                                               |
| `SOUL.md`                  | Defines how the agent thinks and behaves.                               |
| `AGENTS.md`                | Defines how the agent performs work.                                    |
| `TOOLS.md`                 | Defines how tools should be used.                                       |
| `USER.md`                  | Defines stable information about the primary user.                      |
| `MEMORY.md`                | Stores durable executive knowledge.                                     |
| `HEARTBEAT.md`             | Defines lightweight background maintenance behavior.                    |
| `BOOTSTRAP.md` / `BOOT.md` | One-time workspace initialization (runtime-managed, version-dependent). |

---

# 5.4 Workspace Contracts

Every workspace file follows the same architectural contract.

Each file defines:

* Purpose
* Responsibilities
* Allowed Content
* Forbidden Content
* Lifecycle
* Dependencies
* Ownership

These contracts prevent behavioral duplication across the workspace.

---

# 5.5 IDENTITY.md

## Purpose

Defines the immutable professional identity of the Recruiting Agent.

It answers one question:

> **Who am I?**

It does **not** explain how the agent performs recruiting.

---

### Responsibilities

* Professional role
* Agent name
* Mission summary
* Scope
* Professional identity
* High-level objectives

---

### Allowed Content

* Name
* Title
* Role
* Mission
* Scope
* Identity traits
* Stable role description

---

### Forbidden Content

* Recruiting workflows
* Tool instructions
* Memory
* User preferences
* Planning logic
* Implementation details
* CRM procedures

---

### Lifecycle

Created during the bootstrap process.

Updated only when the agent's identity changes.

Expected to remain highly stable.

---

### Dependencies

None.

This file forms the foundation for all other workspace files.

---

### Ownership

Recruiting Workspace Architecture

---

# 5.6 SOUL.md

## Purpose

Defines the behavioral philosophy of the Recruiting Agent.

It answers:

> **How should I think?**

---

### Responsibilities

* Values
* Communication style
* Professional ethics
* Reasoning philosophy
* Behavioral principles
* Personality
* Decision mindset

---

### Allowed Content

* Tone
* Boundaries
* Values
* Principles
* Communication preferences
* Professional behavior

---

### Forbidden Content

* CRM workflow
* Recruiting lifecycle
* Tool procedures
* User profile
* Memory
* Candidate-specific logic

---

### Lifecycle

Rarely changes.

Should evolve only when organizational philosophy changes.

---

### Dependencies

Identity

---

### Ownership

Recruiting Workspace Architecture

---

# 5.7 AGENTS.md

## Purpose

Defines the operational manual of the Recruiting Agent.

It answers:

> **How do I perform recruiting work?**

---

### Responsibilities

* Recruiting workflow
* Planning
* Validation
* Decision process
* Workflow sequencing
* Business procedures
* Recovery guidance

---

### Allowed Content

* Hiring lifecycle
* Workflow stages
* Decision framework
* Operational rules
* Planning guidance
* Verification procedures

---

### Forbidden Content

* Personality
* Identity
* User profile
* Tool syntax
* CRM implementation
* Memory

---

### Lifecycle

Frequently refined as recruiting processes evolve.

---

### Dependencies

IDENTITY.md

SOUL.md

---

### Ownership

Recruiting Operations

---

# 5.8 TOOLS.md

## Purpose

Defines how tools should be used during recruiting activities.

It answers:

> **When should I use a tool?**

OpenClaw documentation is explicit that `TOOLS.md` provides guidance only and **does not grant or restrict tool permissions**; actual availability is determined by the runtime, plugins, and policy configuration. ([OpenClaw][1])

---

### Responsibilities

* Tool selection guidance
* Tool sequencing
* Validation
* Retry strategy
* Verification
* Recovery strategy

---

### Allowed Content

* Best practices
* Tool ordering
* Validation rules
* Error handling
* Safety guidance

---

### Forbidden Content

* Business workflow
* Identity
* Personality
* Permissions
* API documentation

---

### Lifecycle

Updated whenever tooling evolves.

---

### Dependencies

AGENTS.md

---

### Ownership

Platform Architecture

---

# 5.9 USER.md

## Purpose

Defines stable knowledge about the primary user.

It answers:

> **Who am I working for?**

---

### Responsibilities

* Preferred name
* Communication preferences
* Stable working preferences
* Long-term objectives
* Organizational role

---

### Allowed Content

* Persistent preferences
* Stable user context
* Communication style
* Long-term goals

---

### Forbidden Content

* Conversation history
* Temporary tasks
* Session state
* CRM records
* Runtime state

---

### Lifecycle

Updated only when long-term user information changes.

---

### Dependencies

None

---

### Ownership

User

---

# 5.10 MEMORY.md

## Purpose

Defines durable executive knowledge that should persist across sessions.

Unlike daily memory files, this document captures stable operational knowledge that improves future reasoning.

The file is optional in OpenClaw and is only injected into normal sessions when it exists at the workspace root. ([OpenClaw][2])

---

### Responsibilities

* Long-term operational knowledge
* Stable project knowledge
* Persistent reminders
* Organizational context

---

### Allowed Content

* Durable knowledge
* Executive summaries
* Long-term lessons
* Stable reference material

---

### Forbidden Content

* Daily logs
* Temporary notes
* Conversation transcripts
* Session history
* Detailed audit records

---

### Lifecycle

Continuously refined through long-term experience.

---

### Dependencies

None

---

### Ownership

Agent Memory

---

# 5.11 HEARTBEAT.md

## Purpose

Defines lightweight instructions executed during background heartbeat runs.

OpenClaw recommends keeping this file intentionally small to minimize token usage during scheduled heartbeat execution. ([OpenClaw][1])

It answers:

> **What routine maintenance should I perform when no user is interacting with me?**

---

### Responsibilities

* Maintenance checklist
* Health monitoring
* Periodic reviews
* Workspace hygiene

---

### Allowed Content

* Short checklists
* Maintenance tasks
* Background reminders

---

### Forbidden Content

* Personality
* Recruiting workflow
* Business logic
* Large documentation
* Conversation memory

---

### Lifecycle

Updated only when maintenance behavior changes.

---

### Dependencies

None

---

### Ownership

Platform Operations

---

# 5.12 BOOTSTRAP.md / BOOT.md

## Purpose

Defines the one-time initialization ritual for a brand-new workspace.

This file is created during onboarding, guides the agent through establishing its identity, personality, and user context, and is removed once the workspace is considered configured. Newer documentation refers to `BOOT.md`, while the current runtime behavior documented for your installation uses `BOOTSTRAP.md`; the specification should therefore treat this as a version-specific implementation detail rather than a behavioral difference. ([OpenClaw][3])

---

## 5.13 Dependency Graph

```text
IDENTITY.md
      │
      ▼
SOUL.md
      │
      ▼
AGENTS.md
      │
      ├─────────────┐
      ▼             ▼
TOOLS.md       MEMORY.md
      │             │
      └──────┬──────┘
             ▼
      HEARTBEAT.md
```

The dependency graph expresses **conceptual dependence**, not loading order. OpenClaw has its own runtime bootstrap order, but this specification defines how the content should build upon itself so that each file has a single responsibility and minimal overlap.

[1]: https://docs.openclaw.ai/agent-workspace?utm_source=chatgpt.com "Agent workspace - OpenClaw"
[2]: https://docs.openclaw.ai/agent?utm_source=chatgpt.com "Agent runtime - OpenClaw"
[3]: https://docs.openclaw.ai/start/bootstrapping?utm_source=chatgpt.com "Agent bootstrapping - OpenClaw"
