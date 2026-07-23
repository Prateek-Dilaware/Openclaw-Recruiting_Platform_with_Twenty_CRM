This is another chapter where I checked the official documentation before proposing an architecture.

There is an important distinction here.

## What OpenClaw officially provides

From the official documentation and your runtime investigation:

* OpenClaw has **conversation/session memory**.
* OpenClaw has a **memory system** (through the `memory-core` capability) that supports storing and retrieving memories.
* `MEMORY.md` is **optional** and acts as long-term bootstrap guidance when present.
* Daily notes under `memory/` are part of the workspace and can be searched/retrieved.
* The runtime decides **when** to retrieve memories; it does **not** prescribe an organizational methodology for project memory. Your runtime analysis also observed the `session-memory` hook writing summaries into the workspace `memory/` directory. 

What OpenClaw **does not** define is:

* a memory hierarchy,
* promotion rules,
* retention policy,
* compression strategy,
* memory hygiene,
* project knowledge management.

Therefore this chapter becomes **our Memory Architecture Standard**.

I would also make one architectural decision that differs slightly from your original outline.

Instead of talking only about **types of memory**, I would describe **memory flow**.

That makes implementation much easier.

---

# Part VIII — Memory Architecture

## 8.1 Purpose

Memory enables the Recruiting Agent to accumulate knowledge while maintaining efficient reasoning and predictable behavior.

The objective of the memory architecture is not to remember everything, but to preserve information at the appropriate level of permanence.

The Recruiting Workspace therefore separates transient execution context from durable organizational knowledge.

---

# 8.2 Memory Philosophy

The Recruiting Agent treats memory as a managed knowledge system rather than a conversation archive.

Good memory should be:

* relevant,
* concise,
* verifiable,
* reusable,
* maintainable.

The agent should remember knowledge that improves future reasoning while allowing temporary execution details to expire naturally.

---

# 8.3 Memory Hierarchy

The Recruiting Workspace organizes memory into four conceptual layers.

```text id="ubc7mr"
Persistent Memory
        │
Operational Memory
        │
Session Memory
        │
Historical Memory
```

Each layer has a different purpose and lifecycle.

---

# 8.4 Persistent Memory

Persistent Memory contains durable knowledge that remains valuable across long periods.

Examples include:

* recruiting philosophy,
* stable organizational policies,
* long-term project knowledge,
* permanent workspace decisions,
* architectural standards.

Persistent memory changes infrequently.

It represents institutional knowledge rather than recent activity.

Typical implementation:

* `MEMORY.md`
* stable workspace reference documents

---

# 8.5 Operational Memory

Operational Memory contains active project knowledge.

Examples include:

* current recruiting campaigns,
* active hiring initiatives,
* recurring workflow observations,
* ongoing process improvements,
* operational summaries.

Operational Memory evolves regularly but remains useful across multiple sessions.

It provides continuity for active work.

---

# 8.6 Session Memory

Session Memory contains information relevant only to the current conversation.

Examples:

* intermediate reasoning,
* current tool outputs,
* temporary plans,
* user requests,
* execution context.

Session Memory is maintained by the runtime and normally expires when the session ends.

It should not be promoted automatically.

---

# 8.7 Historical Memory

Historical Memory records completed work.

Examples:

* daily summaries,
* completed recruiting activities,
* project milestones,
* archived observations,
* previous decisions.

Historical Memory provides traceability rather than operational guidance.

Daily memory files naturally belong in this layer.

---

# 8.8 Memory Flow

Information moves through the memory hierarchy according to its long-term value.

```text id="1qokfy"
Conversation
        │
        ▼
Session Memory
        │
        ▼
Operational Summary
        │
        ▼
Historical Archive
        │
        ▼
Persistent Knowledge
```

Most information should never reach Persistent Memory.

Only knowledge with lasting value should be promoted.

---

# 8.9 Memory Retrieval

When solving a problem, memory should be consulted in the following order.

```text id="igz5ob"
Current Session
        │
        ▼
Operational Memory
        │
        ▼
Persistent Memory
        │
        ▼
Historical Memory
```

This ordering prioritizes relevance while minimizing unnecessary context.

Historical Memory should generally be used only when additional background or traceability is required.

---

# 8.10 Memory Writing Rules

The Recruiting Agent should write memory only when information satisfies one or more of the following criteria:

* reusable,
* long-term valuable,
* operationally significant,
* repeatedly referenced,
* beneficial for future reasoning.

The agent should avoid storing:

* routine conversations,
* temporary execution details,
* duplicate information,
* speculative observations,
* transient errors.

---

# 8.11 Memory Promotion

Promotion determines whether information should move to a more durable layer.

Promotion should occur only when knowledge demonstrates continuing value.

Typical promotion path:

```text id="1yyknm"
Session Observation
        │
Repeated Importance
        │
Operational Knowledge
        │
Long-Term Value
        │
Persistent Memory
```

Promotion should be conservative.

Most information should remain temporary.

---

# 8.12 Memory Compression

As information accumulates, the Recruiting Agent should compress memory while preserving meaning.

Compression should:

* remove repetition,
* merge similar observations,
* preserve important decisions,
* retain supporting context,
* improve retrieval efficiency.

Compression must never alter the meaning of stored knowledge.

---

# 8.13 Summarization

Summaries transform detailed information into reusable knowledge.

A good summary should preserve:

* decisions,
* outcomes,
* lessons learned,
* unresolved issues,
* important context.

Summaries should be factual rather than interpretive.

---

# 8.14 Retention

Each memory layer has its own expected retention period.

| Layer       | Typical Retention                      |
| ----------- | -------------------------------------- |
| Session     | Current conversation                   |
| Operational | Active project duration                |
| Historical  | Long-term archive                      |
| Persistent  | Indefinite until intentionally revised |

Retention should reflect business value rather than age alone.

---

# 8.15 Memory Hygiene

Memory quality is more important than memory quantity.

The Recruiting Agent should periodically:

* remove obsolete information,
* merge duplicate memories,
* archive completed work,
* eliminate contradictory knowledge,
* update outdated references,
* maintain concise executive summaries.

A well-maintained memory system improves reasoning efficiency and reduces conflicting context.

---

# 8.16 Memory Ownership

Each memory layer has a defined ownership model.

| Layer       | Owner                  |
| ----------- | ---------------------- |
| Persistent  | Workspace Architecture |
| Operational | Recruiting Operations  |
| Session     | OpenClaw Runtime       |
| Historical  | Workspace Archive      |

Ownership determines who is responsible for maintaining the quality and accuracy of each layer.

---

# 8.17 Memory Governance

The Recruiting Agent **MUST**:

* Store only information with appropriate long-term value.
* Preserve factual accuracy.
* Avoid unnecessary duplication.
* Promote knowledge conservatively.
* Summarize before archiving.
* Maintain consistency across memory layers.

The Recruiting Agent **MUST NOT**:

* Treat memory as a conversation log.
* Store speculative conclusions as facts.
* Duplicate information across multiple layers without justification.
* Promote temporary execution details into persistent knowledge.
* Retain obsolete operational information after it has lost value.

---

# 8.18 Memory Architecture Overview

```text id="i6ejv5"
                  Memory System

                        │

        ┌───────────────┼───────────────┐

        ▼               ▼               ▼

   Session         Operational      Historical

        │               │               │

        └───────────────┼───────────────┘

                        ▼

               Persistent Knowledge

                  (MEMORY.md)
```

Information naturally flows **downward** from active execution into historical records, while only carefully curated knowledge is **promoted upward** into persistent memory.

---


* **OpenClaw** manages **memory retrieval and storage**.
* **Our workspace** manages **knowledge organization and governance**.

T
