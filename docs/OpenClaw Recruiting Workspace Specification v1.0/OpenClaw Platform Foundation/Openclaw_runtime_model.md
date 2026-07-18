# Part I — Foundations

## 1.1 Purpose

This specification defines the architecture, behavioral contracts, and implementation standards for the **OpenClaw Recruiting Workspace**.

It is the governing document for the Recruiting AI layer and serves as the authoritative source from which all workspace files, skills, memory structures, and future agents are derived.

---

## 1.2 Goals

The Recruiting Workspace shall:

* Define a consistent recruiting operating model.
* Teach the AI how to reason about recruiting workflows.
* Establish clear responsibilities for every workspace component.
* Provide reusable behavioral standards for skills and future agents.
* Produce predictable, auditable, and maintainable AI behavior.

---

## 1.3 Non-Goals

This specification does **not** define:

* FastAPI implementation details
* Docker deployment
* Twenty CRM schema implementation
* React frontend architecture
* Plugin source code
* Model-specific prompts
* Business APIs

Those systems consume or support the workspace but are outside its scope.

---

## 1.4 System Architecture

```text
React Frontend
        │
        ▼
FastAPI Backend
        │
        ▼
OpenClaw Runtime
        │
        ▼
Recruiting Workspace
        │
        ▼
Skills
        │
        ▼
Official Twenty Plugin
        │
        ▼
Twenty CRM
```

Responsibilities are intentionally separated:

* **OpenClaw** provides the agent runtime.
* **Workspace** provides recruiting intelligence.
* **Skills** provide reusable recruiter procedures.
* **Plugins** provide system capabilities.
* **Twenty CRM** remains the authoritative source of business data.

---

## 1.5 Terminology

| Term            | Definition                                                                                                        |
| --------------- | ----------------------------------------------------------------------------------------------------------------- |
| Runtime         | OpenClaw execution environment responsible for reasoning, planning, tools, memory, sessions, and prompt assembly. |
| Workspace       | The collection of bootstrap files, memory, and skills that define an agent's behavior and domain knowledge.       |
| Skill           | A reusable instruction module describing how to perform a specific recruiter activity.                            |
| Plugin          | A capability provider exposing executable tools to the runtime.                                                   |
| Session         | A conversation with its own context and execution state.                                                          |
| Bootstrap Files | Workspace files injected into the Project Context during session initialization.                                  |
| Project Context | The structured context assembled from workspace files and supplied to the model.                                  |

---

## 1.6 Design Principles

The Recruiting Workspace follows these principles:

1. **Twenty CRM is the source of truth.**
2. **Verify before acting.**
3. **Never fabricate information.**
4. **Explain significant decisions.**
5. **Prefer validation over assumption.**
6. **Recover gracefully from failures.**
7. **Keep responsibilities separated.**
8. **Optimize for maintainability rather than prompt complexity.**

---

## 1.7 Workspace Philosophy

The workspace is not application configuration.

It is the behavioral architecture of the Recruiting Agent.

Rather than describing software implementation, it defines:

* how the AI reasons,
* how it plans,
* how it communicates,
* how it validates information,
* how it uses tools,
* and how it performs recruiting work.

Every workspace artifact exists to improve the quality and consistency of the agent's decision making.

---

# Part II — OpenClaw Runtime Model

This chapter explains the execution environment that hosts the Recruiting Workspace. The workspace is only one component of a larger runtime responsible for planning, reasoning, memory management, tool execution, and conversation orchestration. Understanding this separation is essential because the workspace should define recruiting behavior rather than reimplement runtime capabilities.

---

## 2.1 Runtime Overview

OpenClaw provides an integrated agent runtime that combines model execution, prompt assembly, tool orchestration, session management, memory, plugins, and skills into a single execution environment. Each configured agent has its own workspace, session store, and runtime state. ([OpenClaw][1])

Conceptually:

```text
User Request
      │
      ▼
OpenClaw Runtime
      │
      ├── Session Manager
      ├── Prompt Builder
      ├── Memory Manager
      ├── Skill Manager
      ├── Plugin Manager
      ├── Tool Execution
      └── Model Provider
      │
      ▼
Model Response
```

The runtime is responsible for *how* an agent executes. The workspace is responsible for *how the agent behaves*.

---

## 2.2 Workspace

The workspace is the agent's operational home. It is the default working directory for file-based operations and the location where OpenClaw expects behavioral files such as `AGENTS.md`, `SOUL.md`, `IDENTITY.md`, `TOOLS.md`, `USER.md`, and `HEARTBEAT.md`. OpenClaw treats this directory as part of the agent's contextual memory rather than application configuration. Configuration, credentials, sessions, and managed skills reside under `~/.openclaw/` instead of the workspace. ([OpenClaw][3])

Within the Recruiting Platform, the workspace represents the Recruiter's operating model rather than project documentation.

---

## 2.3 Skills

Skills are modular instruction packages that extend the agent with domain-specific procedures. OpenClaw discovers skills from multiple locations (workspace, project, personal, managed, bundled, and additional configured directories) and exposes a compact list of available skills in the system prompt. The detailed `SKILL.md` instructions are loaded on demand when the model chooses to use a skill, reducing unnecessary prompt overhead. ([OpenClaw][1])

For this project, skills correspond to recruiter activities such as resume screening, interview planning, candidate comparison, and offer preparation—not CRM entities.

---

## 2.4 Plugins

Plugins provide executable capabilities rather than reasoning. They register tools with the runtime, contribute tool schemas, and may add lifecycle hooks. The Recruiting Workspace does not own these capabilities; it decides when and why to use them. In this platform, the official Twenty plugin supplies CRM operations while the workspace supplies recruiting intelligence. This separation keeps business reasoning independent of infrastructure. ([OpenClaw][1])

---

## 2.5 Memory

Memory exists at multiple levels.

The workspace may contain durable behavioral memory (for example `MEMORY.md` when present), while OpenClaw also maintains session state and searchable memory through its runtime. These mechanisms serve different purposes: behavioral guidance, operational knowledge, and conversational continuity. The runtime controls retrieval and persistence; the workspace defines what knowledge should be retained. ([OpenClaw][1])

---

## 2.6 Sessions

Every conversation executes within a session. A session maintains conversation history, execution state, tool interactions, and memory references. New sessions receive a fresh bootstrap of the current workspace, whereas existing sessions retain the bootstrap context established when they were created. This separation enables workspace evolution without retroactively altering active conversations. ([OpenClaw][1])

---

## 2.7 Context Assembly

Before a model receives a user request, OpenClaw assembles context from multiple sources.

```text
Workspace Bootstrap Files
          │
          ▼
Project Context
          │
Skills Index
          │
Memory
          │
Conversation History
          │
Available Tools
          │
Current User Request
          │
          ▼
Prompt Builder
          │
          ▼
LLM
```

The runtime composes these components into the final model request. Workspace files provide long-lived behavioral guidance, while conversation history, memory, and tool definitions supply the dynamic execution context. ([OpenClaw][1])

---

## 2.8 Bootstrap Process

When a new workspace is initialized, OpenClaw creates the standard bootstrap files and runs a one-time onboarding process to establish the agent's identity. During normal operation, the runtime injects the bootstrap files into the Project Context at the beginning of each new session. Blank files are skipped, optional files such as `MEMORY.md` are included only when present, and large files may be truncated to stay within configured context limits. ([OpenClaw][2])

This behavior reinforces an important architectural principle:

> The workspace is the persistent behavioral layer of the agent, while sessions are temporary execution contexts.

---

## 2.9 Prompt Composition

OpenClaw constructs prompts by combining several independent context sources rather than relying on a single system prompt.

At a high level, prompt composition follows this flow:

```text
Runtime Instructions
        +
Workspace Bootstrap
        +
Skills Catalog
        +
Relevant Memory
        +
Conversation History
        +
Available Tool Schemas
        +
Current User Request
        ↓
Model Request
```

Two observations from the official documentation and your runtime analysis are particularly important:

* Bootstrap files are injected into the Project Context for new sessions.
* The system prompt contains a compact catalogue of available skills, while full skill instructions are accessed only when needed, improving context efficiency. ([OpenClaw][1])

This layered composition model explains why the Recruiting Workspace should focus on durable behavior and operating principles rather than attempting to encode every workflow into a single prompt.

[1]: https://docs.openclaw.ai/agent?utm_source=chatgpt.com "Agent runtime - OpenClaw"
[2]: https://docs.openclaw.ai/start/bootstrapping?utm_source=chatgpt.com "Agent bootstrapping - OpenClaw"
[3]: https://docs.openclaw.ai/agent-workspace?utm_source=chatgpt.com "Agent workspace - OpenClaw"
