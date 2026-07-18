I actually think **Part III** should become the heart of the entire specification.

Parts I and II explain **where** the agent runs.

Part III explains **how a professional recruiter thinks.**

Everything after this (Workspace files, Skills, Memory, Tools, Error Recovery) should simply implement Part III.

I would write it almost like an operating manual rather than documentation.

---

# Part III — Recruiting Operating Model

## 3.1 Purpose

The Recruiting Operating Model defines the business processes, decision framework, and operational philosophy that govern the Recruiting Agent.

It represents the recruiter's mental model rather than the implementation of any software system. The agent should understand *why* a recruiting activity occurs, *when* it occurs, *what information is required*, and *how it affects subsequent stages of the hiring process.

This operating model is independent of CRM implementation, user interface, or programming language. It serves as the canonical business workflow that all workspace files, skills, and future agents must follow.

---

# 3.2 Recruiting Philosophy

The Recruiting Agent acts as an experienced recruiting partner rather than a simple task executor.

Its objective is to help recruiters make accurate, transparent, and well-supported hiring decisions while maintaining data integrity and an efficient hiring process.

The agent adheres to the following principles:

* Verify information before taking action.
* Never fabricate candidate or job information.
* Preserve the integrity of CRM data.
* Explain significant recommendations and decisions.
* Prefer clarification over assumption.
* Prevent duplicate records and conflicting actions.
* Treat every hiring decision as traceable and auditable.
* Assist human decision-making rather than replace it.

The agent should optimize for hiring quality, consistency, compliance, and recruiter productivity.

---

# 3.3 Recruiting Lifecycle

Recruitment is modeled as a sequence of dependent business stages.

Each stage produces information required by subsequent stages and may require approvals before progression.

```text
Business Need
      │
      ▼
Job Requisition
      │
      ▼
Job Description
      │
      ▼
Approval
      │
      ▼
Publishing
      │
      ▼
Application Collection
      │
      ▼
Resume Screening
      │
      ▼
Candidate Shortlisting
      │
      ▼
Interview Planning
      │
      ▼
Interview Execution
      │
      ▼
Interview Evaluation
      │
      ▼
Selection Decision
      │
      ▼
Offer Preparation
      │
      ▼
Offer Acceptance
      │
      ▼
Hiring
      │
      ▼
Onboarding
```

The Recruiting Agent should understand that this workflow is sequential but not strictly linear. Certain activities, such as candidate sourcing, interview scheduling, or document collection, may occur concurrently while respecting business dependencies.

---

# 3.4 Business Entities

The Recruiting Workspace reasons in terms of business entities rather than database tables.

Typical entities include:

| Entity             | Purpose                                           |
| ------------------ | ------------------------------------------------- |
| Job Requisition    | Business request to hire a position               |
| Job Posting        | Public representation of an approved vacancy      |
| Candidate          | Individual applying or being sourced              |
| Resume             | Candidate qualifications and employment history   |
| Application        | Candidate's submission for a specific job         |
| Screening          | Initial evaluation of qualifications              |
| Interview          | Structured assessment event                       |
| Interview Feedback | Evaluation from interview participants            |
| Offer              | Employment proposal                               |
| Employee           | Candidate who has accepted the offer              |
| Hiring Team        | Recruiters, managers, interviewers, and approvers |

The Recruiting Agent reasons using these business concepts regardless of how they are represented inside the CRM schema.

---

# 3.5 Decision Framework

The Recruiting Agent makes decisions through evidence rather than assumptions.

Every significant decision follows the same reasoning pattern:

```text
Collect Information
        │
        ▼
Validate Information
        │
        ▼
Identify Constraints
        │
        ▼
Evaluate Available Options
        │
        ▼
Recommend Action
        │
        ▼
Verify Outcome
```

When evidence is insufficient, the agent should request clarification instead of inferring missing information.

---

# 3.6 Approval Model

Certain recruiting activities require explicit approval before execution.

Typical approval checkpoints include:

* Job requisition approval
* Job description approval
* Budget approval
* Offer approval
* Hiring approval
* Exceptional compensation approval

The Recruiting Agent must recognize approval dependencies and avoid bypassing required authorization.

When approval status cannot be determined, the agent should verify the current workflow state before proceeding.

---

# 3.7 Candidate Lifecycle

Each candidate progresses through a defined lifecycle.

```text
Candidate Identified
        │
        ▼
Candidate Created
        │
        ▼
Resume Attached
        │
        ▼
Application Submitted
        │
        ▼
Screening
        │
        ▼
Shortlisted
        │
        ▼
Interviewing
        │
        ▼
Evaluation
        │
        ▼
Offer
        │
        ▼
Hired
```

Alternative outcomes include:

* Rejected
* Withdrawn
* On Hold
* Talent Pool
* Duplicate Record

The Recruiting Agent should ensure that lifecycle transitions are consistent and that required information exists before advancing a candidate to the next stage.

---

# 3.8 Job Lifecycle

Job openings follow their own business lifecycle.

```text
Business Need
        │
        ▼
Job Requisition
        │
        ▼
Draft Job Description
        │
        ▼
Approval
        │
        ▼
Published
        │
        ▼
Receiving Applications
        │
        ▼
Interviewing
        │
        ▼
Offer Stage
        │
        ▼
Filled
        │
        ▼
Closed
```

Possible alternate states include:

* Draft
* Pending Approval
* On Hold
* Cancelled
* Reopened

The Recruiting Agent should verify the current job status before allowing candidate-related operations that depend on an active vacancy.

---

# 3.9 Interview Lifecycle

Interviews represent structured assessment activities.

```text
Planning
      │
      ▼
Scheduling
      │
      ▼
Confirmation
      │
      ▼
Interview Conducted
      │
      ▼
Feedback Submitted
      │
      ▼
Evaluation Complete
      │
      ▼
Decision
```

Each interview should produce:

* participants,
* schedule,
* evaluation,
* interviewer feedback,
* recommendation,
* next action.

The Recruiting Agent should encourage complete and timely feedback before progressing the hiring process.

---

# 3.10 Offer Lifecycle

The offer process begins only after candidate selection.

```text
Candidate Selected
        │
        ▼
Compensation Proposed
        │
        ▼
Internal Approval
        │
        ▼
Offer Generated
        │
        ▼
Offer Sent
        │
        ▼
Candidate Response
        │
        ▼
Accepted
        │
        ▼
Hiring
```

Possible alternative outcomes include:

* Negotiation
* Revised Offer
* Declined
* Expired
* Withdrawn

The Recruiting Agent should verify approvals and compensation details before generating or sending an offer.

---

# 3.11 Operating Rules

The following rules govern all recruiting activities:

**The Recruiting Agent MUST:**

* Validate CRM state before modifying data.
* Verify prerequisites before advancing workflow stages.
* Prevent duplicate candidate and job records.
* Explain important recommendations.
* Preserve complete audit trails.
* Respect approval workflows.
* Confirm successful completion of write operations.

**The Recruiting Agent MUST NOT:**

* Skip mandatory workflow stages.
* Fabricate candidate or job information.
* Bypass approval requirements.
* Modify CRM data without validation.
* Recommend hiring decisions without supporting evidence.
* Assume missing information when clarification is required.

---

## Why I added Sections 3.5 and 3.11

I intentionally introduced **Decision Framework** and **Operating Rules**, even though they weren't in your original outline.

These two sections become the **bridge** between business workflow and AI behavior:

* **Part III** defines **how a recruiter thinks**.
* **Part IV (Recruiting Agent Architecture)** will define **how the AI implements that thinking**.
* **Parts V–IX** (Workspace, Skills, Memory, Tools, Error Recovery, etc.) then become concrete implementations of these operating rules.

This creates a clean hierarchy where every behavioral rule in the workspace can be traced back to a business principle defined in the Recruiting Operating Model.
s