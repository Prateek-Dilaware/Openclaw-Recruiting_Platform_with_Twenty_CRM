# OpenClaw CRM Integration & Fallback Router Setup

This repository has been integrated with the OpenClaw orchestration engine. We have implemented a transparent `CRMService` fallback router which allows developers to run the application either directly connected to Twenty CRM or bridged through OpenClaw.

## Prerequisites
- Docker & Docker Compose installed
- Self-hosted Twenty CRM instance running locally at `http://localhost:3000`

---

## Setup Steps

### 1. Launch the OpenClaw Service Container
Navigate to the `docker` directory and start the OpenClaw container in background mode:
```bash
cd docker
docker-compose -f docker-compose.openclaw.yml up -d
```

### 2. Configure Backend Environment Settings
Open `backend/.env` and update the OpenClaw configuration fields:
```bash
# Switch to true when you want to route requests via the OpenClaw container
USE_OPENCLAW=false

# API routing destinations
OPENCLAW_API_URL=http://localhost:8080
OPENCLAW_API_KEY=your-openclaw-api-key-here
```

### 3. Verify Health Check
Ensure the OpenClaw API container is up and running successfully:
```bash
curl http://localhost:8080/health
```

### 4. Run the Recruiting Platform
Start your FastAPI backend as usual:
```bash
cd backend
python -m uvicorn app.main:app --reload
```
The skills located in the `openclaw/skills/twenty_skill/` directory will automatically mount into the container.

---

## Verification & Fallback Design
* **Direct CRM (Fallback)**: When `USE_OPENCLAW=false` (default), the platform uses the internal `TwentySkill` client library to perform direct mutations on the CRM database.
* **OpenClaw Route**: When `USE_OPENCLAW=true`, the platform delegates all CRM operations (`write_field` and `trigger_workflow`) as remote tool calls executed by the OpenClaw API.
* **Error Resilience**: If the OpenClaw service suffers a connection outage, toggle the flag back to `false` in `.env` to fall back instantly to direct API calls.

---

## Twenty CRM Workflow Automation Setup

To automate outbound calls using Twenty CRM's built-in workflow engine without manually triggering them:

1. **Open Twenty CRM:** Go to **Settings → Workflows** in the UI.
2. **Create a Workflow:** Name it "Automate Outbound Screening Call".
3. **Trigger:** Select **Record updated** for the `Candidate` object.
4. **Condition:** Add a logic branch checking if the updated field `interviewStatus` transitions to `SCREENING` (or similar initial stage).
5. **Action:** Select **Webhook** (POST request).
   * Set the target URL to: `http://host.docker.internal:8000/api/v1/webhooks/workflow-trigger` (or `http://localhost:8000/api/v1/webhooks/workflow-trigger` if outside Docker).
   * Set the body content type to `application/json`.
   * Pass the following JSON payload template:
     ```json
     {
       "candidate_id": "{{candidate.id}}",
       "phone": "{{candidate.phone.primaryPhoneNumber}}",
       "name": "{{candidate.name}}"
     }
     ```

Once configured and activated, any candidate status update will automatically prompt the backend to trigger the outbound Conversational AI call via ElevenLabs.

