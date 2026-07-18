
### What OpenClaw currently supports

From the current OpenClaw documentation and runtime capabilities:

* OpenClaw supports **sub-agents/sessions**, allowing an agent to delegate work to another execution context.
* Agents can share workspace resources and use common tools, but **OpenClaw does not prescribe a canonical organizational model** (e.g., manager/worker, planner/executor, or specialist teams). Those are left to workspace designers.
* There is no official "Recruiting Team" architecture; communication protocols, ownership boundaries, and shared-memory strategies are application-specific.

So this chapter should **not** describe what OpenClaw is today—it should define the **target architecture** for the Recruiting Workspace while remaining compatible with current capabilities.

---

# Part X — Multi-Agent Architecture

## 10.1 Purpose

This chapter defines the long-term evolution of the Recruiting Workspace from a single intelligent recruiting assistant into a coordinated team of specialized agents.

The objective is to improve scalability, specialization, maintainability, and operational efficiency while preserving a unified user experience.

Multi-agent architecture is considered an **evolutionary capability**, not an initial implementation requirement.

---

# 10.2 Current Architecture

The current Recruiting Workspace is intentionally simple.

```text
User
   │
   ▼
Recruiting Agent
   │
   ▼
Skills
   │
   ▼
Tools
   │
   ▼
Twenty CRM
```

The Recruiting Agent performs:

* planning,
* reasoning,
* tool selection,
* workflow execution,
* user communication.

This centralized architecture minimizes complexity during the initial implementation.

---

# 10.3 Future Architecture

As recruiting operations grow, responsibilities may be delegated to specialized agents.

```text
                     Recruiting Agent
                            │
      ┌──────────────┬──────────────┬──────────────┬──────────────┐
      ▼              ▼              ▼              ▼              ▼
Interview Agent  Sourcer Agent  Scheduler Agent  Analytics Agent  Offer Agent
```

The Recruiting Agent remains the primary interface while specialist agents execute domain-specific responsibilities.

---

# 10.4 Architectural Philosophy

The Recruiting Agent remains the **orchestrator**.

Specialized agents act as **domain experts**.

Users interact with a single recruiting assistant regardless of how many internal agents participate.

This preserves simplicity while enabling specialization behind the scenes.

---

# 10.5 When to Introduce Additional Agents

Additional agents should be introduced only when clear architectural benefits outweigh the added complexity.

Indicators include:

* rapidly growing skill libraries,
* distinct recruiting domains,
* independent workflows,
* specialized reasoning requirements,
* parallel execution opportunities,
* separate ownership by different teams.

A new agent should represent a **business capability**, not merely a technical function.

---

# 10.6 When Not to Introduce Additional Agents

Specialization should not be driven by technology alone.

Do not introduce a new agent simply because:

* a new CRM object exists,
* a new tool is available,
* a workflow is only slightly different,
* a new model is being evaluated,
* an existing skill could perform the task adequately.

When responsibilities remain tightly coupled, a single Recruiting Agent is usually the better architectural choice.

---

# 10.7 Agent Responsibilities

Each specialized agent should own one coherent business domain.

| Agent            | Primary Responsibility                                              |
| ---------------- | ------------------------------------------------------------------- |
| Recruiting Agent | Planning, orchestration, user interaction                           |
| Interview Agent  | Interview preparation, scheduling support, feedback synthesis       |
| Sourcer Agent    | Talent discovery, candidate sourcing, market research               |
| Scheduler Agent  | Calendar coordination, interview logistics, availability management |
| Analytics Agent  | Pipeline reporting, hiring metrics, forecasting                     |
| Offer Agent      | Offer preparation, compensation review, approval coordination       |

Ownership should be exclusive wherever possible to avoid overlapping responsibilities.

---

# 10.8 Delegation Model

The Recruiting Agent determines whether delegation is beneficial.

Delegation follows a structured decision process.

```text
Receive Request
        │
        ▼
Understand Goal
        │
        ▼
Can Primary Agent Complete Efficiently?
        │
   ┌────┴────┐
   │         │
  Yes       No
   │         │
   ▼         ▼
Execute   Delegate
             │
             ▼
Receive Result
             │
             ▼
Verify
             │
             ▼
Respond
```

Delegation should improve overall effectiveness rather than distribute work unnecessarily.

---

# 10.9 Communication Principles

Agent-to-agent communication should be:

* structured,
* concise,
* deterministic,
* evidence-based,
* auditable.

Communication should exchange **objectives, context, and verified results**, not raw conversational history.

---

# 10.10 Handoff Protocol

Every handoff should include sufficient context for the receiving agent to work independently.

Minimum handoff package:

* objective,
* relevant business context,
* current workflow state,
* constraints,
* completed work,
* expected deliverable.

A handoff should not require the receiving agent to rediscover information that is already known.

---

# 10.11 Shared Memory

Agents should share organizational knowledge while maintaining independent execution context.

Conceptually:

```text
               Shared Workspace Memory
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
Recruiting Agent  Interview Agent  Analytics Agent
        │              │              │
   Session A      Session B      Session C
```

Shared memory should contain durable organizational knowledge, while session memory remains private to each agent's execution.

---

# 10.12 Ownership Model

Each business capability should have a single owning agent.

Ownership includes:

* planning,
* execution,
* validation,
* quality,
* recommendations.

Other agents may contribute information but should avoid modifying another agent's area of responsibility without explicit coordination.

---

# 10.13 Coordination Patterns

Different recruiting activities benefit from different coordination styles.

| Pattern      | Suitable For                                                  |
| ------------ | ------------------------------------------------------------- |
| Sequential   | Job approval → posting → sourcing → interviews → offer        |
| Parallel     | Resume screening across multiple candidate pools              |
| Consultation | Recruiting Agent requests analytics or sourcing advice        |
| Delegation   | Specialist agent completes an independent task                |
| Aggregation  | Multiple agents contribute results for a final recommendation |

The Recruiting Agent selects the coordination pattern based on the nature of the work.

---

# 10.14 Trade-offs

Multi-agent systems introduce both advantages and costs.

| Benefits                   | Trade-offs                         |
| -------------------------- | ---------------------------------- |
| Domain specialization      | Increased architectural complexity |
| Parallel execution         | Coordination overhead              |
| Independent evolution      | More communication paths           |
| Clear ownership            | Additional operational governance  |
| Better scalability         | Higher debugging complexity        |
| Modular skill organization | Potential latency between agents   |

The workspace should adopt specialization only when these benefits clearly outweigh the operational costs.

---

# 10.15 Evolution Strategy

The Recruiting Workspace should evolve incrementally.

```text
Phase 1
Recruiting Agent
        │
        ▼
Phase 2
Recruiting Agent
+ Specialist Skills
        │
        ▼
Phase 3
Recruiting Agent
+ Domain Agents
        │
        ▼
Phase 4
Coordinated Recruiting Team
```

This progression preserves stability while allowing specialization to emerge as the recruiting platform grows.

---

# 10.16 Governance Principles

The Recruiting Agent **MUST**:

* Remain the primary user-facing interface.
* Delegate only when there is a clear benefit.
* Verify results received from specialist agents.
* Preserve workflow continuity across handoffs.
* Ensure accountability for final responses.

Specialist Agents **MUST**:

* Focus on their defined domain.
* Return structured, verifiable outcomes.
* Avoid assuming responsibilities owned by other agents.
* Respect shared workspace standards.

All Agents **MUST NOT**:

* Duplicate responsibilities without justification.
* Modify shared organizational knowledge without appropriate ownership.
* Bypass established coordination or approval processes.

---

