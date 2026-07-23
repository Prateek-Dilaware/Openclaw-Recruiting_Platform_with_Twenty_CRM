# Setup Guide

This guide covers the canonical local development workflow for the OpenClaw Recruiting Platform. The active stack is defined in docker/docker-compose.dev.yml.

## Prerequisites

- Docker Desktop installed and running
- Optional: OpenSSL if you want to generate local secrets manually

## Quick Start

### 1. Configure Environment Variables

```bash
cd docker
cp .env.example .env
cp ../backend/.env.example ../backend/.env
```

Edit docker/.env and fill in the required values:
- PG_DATABASE_PASSWORD — set a secure password
- TWENTY_ENCRYPTION_KEY — generate with `openssl rand -base64 32` or use the default for local development
- OPENCLAW_GATEWAY_TOKEN — optional, but recommended for first-time OpenClaw onboarding

Then edit backend/.env and configure the backend API keys you need. The repo supports different LLM providers; set the credentials that match your chosen provider, for example OPENROUTER_API_KEY or GEMINI_API_KEY, plus ELEVENLABS_API_KEY if you want voice features.

> TWENTY_API_URL is set automatically inside Docker to point at the Twenty CRM container, so you normally do not need to change it.

For a full breakdown of every configuration file and variable ownership, see [docs/configuration.md](configuration.md).

### 2. Start the Full Stack

```bash
docker compose -f docker-compose.dev.yml up --build
```

Wait for the containers to become healthy. The first run can take a few minutes while images are pulled.

### 3. Access the Services

| Service | URL |
| --- | --- |
| Twenty CRM | http://localhost:3000 |
| Backend API | http://localhost:8000 |
| API Docs | http://localhost:8000/docs |
| Frontend | http://localhost:5173 |
| OpenClaw UI | http://localhost:18789 |

### 4. First-Time Twenty CRM Setup

1. Open http://localhost:3000
2. Create your workspace and admin account
3. Go to Settings → API & Webhooks and generate an API key
4. Copy the key into backend/.env as TWENTY_API_KEY
5. Restart the backend container: `docker compose -f docker-compose.dev.yml restart backend`

### 5. Provision CRM Schema V2

Do not create recruiting objects manually. Schema V2 is provisioned by the
idempotent scripts in [`../scripts/schema_v2/README.md`](../scripts/schema_v2/README.md).
Follow the documented order to remove the legacy prototype schema, recreate the
six Schema V2 objects, configure workflow drafts, seed demo data, and verify the
result.

> The historical prototype scripts are retained under `scripts/archive/` for
> reference only. Do not run them against Schema V2.

## Hot Reload

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

- Backend cannot connect to Twenty CRM: confirm TWENTY_API_KEY is present in backend/.env and that the twenty-server container is healthy with `docker compose -f docker-compose.dev.yml ps`.
- Frontend shows Cannot connect to backend: make sure the backend container is running and that port 8000 is reachable.
- Port conflicts: Twenty CRM uses port 3000, the backend uses 8000, the frontend uses 5173, and OpenClaw uses 18789. Adjust the mappings in docker/docker-compose.dev.yml if any of those ports are already in use.
