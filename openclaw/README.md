# OpenClaw Integration & Runtime

This directory contains the integration skills and isolated runtime structure for the OpenClaw CRM integration.

## First-Time Setup & Onboarding

When a developer starts the project for the first time using `docker compose -f docker-compose.dev.yml up -d`, the OpenClaw container starts entirely unconfigured.

To perform the initial setup:
1. Open your browser to **http://localhost:18789**
2. You will be greeted by an **Auth Required** page.
3. In the **Gateway Token** box, paste your configured token.
   - If you copied `.env.example` to `.env`, check your `OPENCLAW_GATEWAY_TOKEN` variable.
   - If you didn't set a token, it falls back to the default: `openclaw-dev-token`
4. Click **Connect** and follow the onboarding wizard.

Once onboarding is finished, OpenClaw will generate its `openclaw.json` config inside `data/` (which is safely gitignored so it doesn't pollute the repository).
