# CRM Schema V2 Provisioning

Schema V2 is the canonical, repeatable Twenty CRM foundation for recruiting. It provisions exactly these **custom objects**:

1. `candidate`
2. `requisition`
3. `application`
4. `interview`
5. `evaluation`
6. `offer`

Twenty standard objects are reused and are never created or deleted by these scripts: `workspaceMember`, `note`, `attachment`, `timelineActivity`, and `company`.

## Prerequisites

1. Start the Twenty stack and create a workspace.
2. Generate a Twenty API key with Data Model permissions. Workflow creation additionally needs workflow permission.
3. Configure `TWENTY_API_URL` and `TWENTY_API_KEY` in `backend/.env`, or pass them as environment variables.
4. Run scripts with the Python environment containing `httpx` from `backend/requirements.txt`.

The scripts replace `host.docker.internal` with `localhost` when run from the host. Use a host-reachable URL, normally `http://localhost:3000`.

## Script order

Run each script from `CRM/scripts/schema_v2` in this exact order:

1. `01_delete_schema.py` — removes only prior project schema objects (`candidate`, legacy `requistion`, `requisition`, `application`, `interview`, `evaluation`, `offer`).
2. `02_create_objects.py` — creates the six canonical custom objects.
3. `03_create_fields.py` — creates scalar and status/select fields.
4. `04_create_relationships.py` — creates Candidate–Application–Requisition and Application–Interview–Evaluation/Offer relationships.
5. `05_create_workflows.py` — creates the named workflow draft catalogue.
6. `06_seed_demo_data.py` — creates deterministic demo records.
7. `07_verify_schema.py` — validates metadata, statuses, relations, and demo records.

Example on Windows PowerShell:

```powershell
cd E:\Code\CRM\scripts\schema_v2
python .\01_delete_schema.py
python .\02_create_objects.py
python .\03_create_fields.py
python .\04_create_relationships.py
python .\05_create_workflows.py
python .\06_seed_demo_data.py
python .\07_verify_schema.py
```

## Deleting the schema safely

`01_delete_schema.py` uses an explicit project allowlist. It does **not** discover arbitrary custom objects by scanning the workspace; that would risk deleting unrelated CRM data. It discovers only existing objects with these project-owned API names:

```text
candidate, requistion, requisition, application, interview, evaluation, offer
```

The script performs the required Twenty dependency order:

```text
relation fields → other custom fields → deactivate object → delete object
```

Deleting one endpoint of a Twenty relation removes its companion endpoint. The script records each relation once, tolerates a `404` as an already-removed idempotent result, and emits Created/Deleted/Skipped/Warnings/Errors report sections.

> **Warning:** Object deletion drops the corresponding Twenty workspace table and records. Export any real data before running the deletion script. The Schema V1 scripts are retained unchanged in `scripts/archive/` as historical reference only; they must not be run against Schema V2.

## Idempotency and failure handling

- Object, field, relation, workflow, and demo record creation first checks for existing metadata/records.
- Requests retry transient network failures and common retryable HTTP errors up to three times.
- IDs are always read from Twenty metadata or record responses; no IDs are hard-coded.
- An incompatible pre-existing field or relation produces an error instead of silently changing CRM metadata.
- Every operation prints a detailed report.

## Workflow provisioning scope

The deployed Twenty version exposes workflow **configuration** through versioned GraphQL mutations. The exact trigger/action payloads are version-sensitive and cannot be safely hard-coded without querying that deployed GraphQL schema. `05_create_workflows.py` therefore creates the stable named workflow records and their initial drafts only; it deliberately does not publish empty workflows.

After the deployed workflow GraphQL schema is validated, configure and activate these four workflows in Twenty:

- `Recruiting V2 - Requisition Approval`
- `Recruiting V2 - Application Stage Transition`
- `Recruiting V2 - Interview Lifecycle`
- `Recruiting V2 - Offer Lifecycle`

Do not use a direct field patch as a production fallback for a missing workflow.

## Seed data coverage

The seed creates:

- Three Candidates
- Two Requisitions
- Three Applications, including one rejected path with no downstream records
- Two Interviews
- Two Evaluations (agent and human) for one interview
- One approved Offer

The primary relationship chain is:

```text
Candidate → Application → Requisition
Application → Interview → Evaluation
Application → Offer
```

## Verification

`07_verify_schema.py` checks:

- all six custom objects,
- every required field and type,
- all required status enum values,
- all relationship and inverse relation fields,
- expected demo records, and
- the linked Ada Lovelace demo relationship chain.

A non-zero process exit indicates that the schema or seed data did not satisfy the V2 contract.
