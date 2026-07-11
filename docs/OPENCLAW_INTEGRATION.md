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
