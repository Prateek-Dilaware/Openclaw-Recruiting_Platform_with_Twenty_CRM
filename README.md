# OpenClaw Integration & Runtime

This directory contains the integration skills and isolated runtime structure for the OpenClaw CRM integration.

## Canonical Local Development Workflow

Use the integrated Docker stack defined in docker/docker-compose.dev.yml.

```bash
cd docker
docker compose -f docker-compose.dev.yml up --build
```

This starts the full local stack, including OpenClaw, the FastAPI backend, the React frontend, Twenty CRM, PostgreSQL, and Redis.

## First-Time Setup & Onboarding

After the stack is running, OpenClaw starts unconfigured until you complete onboarding.

1. Open your browser to http://localhost:18789
2. You will be greeted by an Auth Required page.
3. In the Gateway Token box, paste your configured token.
   - If you copied docker/.env.example to docker/.env, check the OPENCLAW_GATEWAY_TOKEN value.
   - If you did not set a token, the fallback value is openclaw-dev-token.
4. Click Connect and follow the onboarding wizard.

Once onboarding is finished, OpenClaw generates its openclaw.json configuration inside the data/ directory, which is safely gitignored.

> The legacy compose files docker/docker-compose.yml and docker/docker-compose.openclaw.yml are retained for rollback/reference only; they are not the default development entry point.