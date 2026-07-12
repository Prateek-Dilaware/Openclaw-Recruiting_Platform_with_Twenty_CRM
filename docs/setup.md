# Setup Guide

This guide covers how to get the full Openclaw Recruiting Platform stack running locally using Docker.

## Prerequisites

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) installed and running
- That's it — no Python or Node.js required on your host machine!

---

## Quick Start (Recommended — Full Docker Setup)

All services (Twenty CRM, Backend, Frontend) run together with a single command.

### 1. Configure Environment Variables

```bash
# Copy the template
cp docker/.env.example docker/.env
```

Open `docker/.env` and fill in the required values:
- `PG_DATABASE_PASSWORD` — set a secure password
- `TWENTY_ENCRYPTION_KEY` — generate with: `openssl rand -base64 32` (or use the default for local dev)

Then copy the backend env template:
```bash
cp backend/.env.example backend/.env
```

Open `backend/.env` and fill in your API keys:
- `GEMINI_API_KEY` — your Google Gemini key
- `ELEVENLABS_API_KEY` — your ElevenLabs key
- `TWENTY_API_KEY` — generated from Twenty CRM settings after first boot

> **Note:** `TWENTY_API_URL` is automatically set to `http://twenty-server:3000` inside Docker — you don't need to change it.

### 2. Start All Services

```bash
cd docker
docker compose -f docker-compose.dev.yml up --build
```

Wait for all containers to become healthy (first run takes ~2-3 minutes to pull images).

### 3. Access the Services

| Service      | URL                       |
|-------------|---------------------------|
| Twenty CRM  | http://localhost:3000     |
| Backend API | http://localhost:8000     |
| API Docs    | http://localhost:8000/docs|
| Frontend    | http://localhost:5173     |

### 4. First-Time Twenty CRM Setup

1. Open http://localhost:3000
2. Create your workspace and admin account
3. Go to **Settings → API & Webhooks** and generate an API key
4. Copy the key into `backend/.env` as `TWENTY_API_KEY`
5. Restart the backend container: `docker compose -f docker-compose.dev.yml restart backend`

### 5. Set Up Custom Objects in Twenty CRM

After first boot, manually create the required custom objects in the Twenty CRM UI under **Settings → Data Model**:
- `Candidate` — with fields: name, email, phone, resumeUrl, transcript, sentiment, interviewStatus, overallScore
- `Requistion` — with fields: name, jobTitle, department, jobDescription, requiredSkills, experience, location, employmentType, status
- `Interview` — with fields: name, candidateId

---

## Hot Reload (Development)

Both backend and frontend support live reloading without rebuilding the container:

- **Backend**: Edit files in `backend/` → uvicorn detects the change and restarts in ~1 second
- **Frontend**: Edit files in `frontend/src/` → Vite Hot Module Replacement updates the browser in <1 second

This works because the source folders are **bind-mounted** into the containers, so file changes on your computer are immediately visible inside the container.

---

## Stopping the Stack

```bash
# Stop all containers
docker compose -f docker-compose.dev.yml down

# Stop and remove volumes (WARNING: this deletes the CRM database!)
docker compose -f docker-compose.dev.yml down -v
```

---

## Troubleshooting

**Backend can't connect to Twenty CRM:**
- Make sure `TWENTY_API_KEY` is set in `backend/.env`
- Check that the `twenty-server` container is healthy: `docker compose -f docker-compose.dev.yml ps`

**Frontend shows "Cannot connect to backend":**
- The frontend uses `VITE_API_URL=http://localhost:8000` which points to your host machine
- Make sure the backend container is running and port 8000 is accessible

**Port conflicts:**
- Twenty CRM uses port `3000`, backend uses `8000`, frontend uses `5173`
- If any are taken, edit the port mappings in `docker-compose.dev.yml`
