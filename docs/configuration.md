# Configuration Architecture

This document is the single source of truth for how the Openclaw Recruiting Platform is configured. It complements `docs/setup.md` (workflow) and `docs/OPENCLAW_INTEGRATION.md` (OpenClaw specifics).

The active runtime is defined in `docker/docker-compose.dev.yml`. Every configuration value below is scoped to exactly one owner file to remove ambiguity.

---

## 1. Configuration Files (Sources)

| File | Owner | Purpose |
| --- | --- | --- |
| `docker/.env` | Docker / infrastructure | Values consumed by `docker-compose.dev.yml` for Twenty CRM, PostgreSQL, Redis, and the OpenClaw gateway. |
| `docker/.env.example` | Docker template | Committed template documenting the active Docker stack. |
| `backend/.env` | FastAPI backend | Values loaded by `backend/app/settings.py` via `python-dotenv` + `pydantic-settings`. Also mounted into the `backend` container via `env_file: ../backend/.env`. |
| `backend/.env.example` | Backend template | Committed template documenting every variable supported by `Settings` in `settings.py`. |
| `frontend/.env` (optional) | Vite frontend | Vite-prefixed variables (`VITE_*`) for the React app. In development these are also injected via compose. |
| `frontend/.env.example` | Frontend template | Committed template for the two Vite variables. |
| `openclaw/data/openclaw.json` | OpenClaw runtime | Generated at OpenClaw onboarding time. Gitignored. Owned by the OpenClaw gateway itself. |
| `docker-compose.dev.yml` | Docker | Wires the files above into the running services and applies internal overrides (e.g. hostnames like `twenty-server`, `openclaw`). |

`docker/archive/docker-compose.yml` and `docker/archive/docker-compose.openclaw.yml` are retained for historical reference only and are not part of the active configuration.

---

## 2. Ownership Map

Each variable has exactly one owning file. Other files must not redeclare it.

### Docker-only (owned by `docker/.env`)

Consumed by `docker-compose.dev.yml` to build the Twenty CRM stack and start the OpenClaw gateway.

- `TWENTY_TAG`
- `PG_DATABASE_USER`
- `PG_DATABASE_PASSWORD`
- `TWENTY_SERVER_URL`
- `TWENTY_ENCRYPTION_KEY`
- `OPENCLAW_GATEWAY_TOKEN`

### Backend-only (owned by `backend/.env`)

Loaded by `Settings` in `backend/app/settings.py` and also passed into the `backend` container via `env_file`.

- `APP_NAME`, `APP_ENV`, `DEBUG`
- `SECRET_KEY`
- `TWENTY_API_KEY`
- `TWENTY_API_URL`
- `LLM_PROVIDER`
- `GEMINI_API_KEY`
- `OPENAI_API_KEY`
- `OPENROUTER_API_KEY`
- `OPENCLAW_URL` (only used when `LLM_PROVIDER=openclaw`)
- `ELEVENLABS_API_KEY`, `ELEVENLABS_VOICE_ID`, `ELEVENLABS_AGENT_ID`, `ELEVENLABS_PHONE_NUMBER_ID`, `ELEVENLABS_MODEL`
- `DATABASE_URL` (informational; not currently read by `Settings`)

### Frontend-only (owned by `frontend/.env` / compose `environment`)

- `VITE_API_URL`
- `VITE_APP_NAME`

### OpenClaw-only (owned by the OpenClaw gateway)

- Everything inside `openclaw/data/openclaw.json` (provider selection, auth profiles, model IDs, etc.) is written by the OpenClaw onboarding flow. Do not hand-edit.

### Shared but derived (owned by `docker-compose.dev.yml`)

These are set as literal `environment:` values inside the compose file so they are not part of any `.env`:

- `NODE_PORT`, `PG_DATABASE_URL`, `REDIS_URL`, `STORAGE_TYPE`, `DISABLE_DB_MIGRATIONS`, `DISABLE_CRON_JOBS_REGISTRATION` (Twenty services)
- `OPENCLAW_STATE_DIR`, `OPENCLAW_CONFIG_PATH`, `OPENCLAW_CONFIG_DIR`, `OPENCLAW_WORKSPACE_DIR`, `OPENCLAW_HOME`, `OPENCLAW_DISABLE_BONJOUR`, `HOME`, `TERM`, `TZ` (OpenClaw container)

---

## 3. Variable Matrix

Legend: **Req** = required, **Opt** = optional, **Dup?** = duplicated across files today, **Move?** = suggested relocation.

### Docker

| Variable | Purpose | Consumer | Location | Default | Req/Opt | Runtime | Dup? | Unused? | Move? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `TWENTY_TAG` | Twenty image tag | `twenty-server`, `twenty-worker` | `docker/.env` | `latest` | Opt | Docker | No | No | — |
| `PG_DATABASE_USER` | Postgres user | `twenty-db`, `twenty-server`, `twenty-worker` | `docker/.env` | `postgres` | Opt | Docker | No | No | — |
| `PG_DATABASE_PASSWORD` | Postgres password | `twenty-db`, `twenty-server`, `twenty-worker` | `docker/.env` | `postgres` | Req | Docker | No | No | — |
| `TWENTY_SERVER_URL` | Public Twenty URL | `twenty-server`, `twenty-worker` | `docker/.env` | `http://localhost:3000` | Opt | Docker | No | No | — |
| `TWENTY_ENCRYPTION_KEY` | Twenty encryption key | `twenty-server`, `twenty-worker` | `docker/.env` | — | Req | Docker | No | No | — |
| `OPENCLAW_GATEWAY_TOKEN` | OpenClaw gateway auth token | `openclaw` container | `docker/.env` | `openclaw-dev-token` | Req | Docker + OpenClaw | Mirrors `OPENCLAW_API_KEY` in `backend/.env` | No | Keep, but must match `OPENCLAW_API_KEY` |

### Backend

| Variable | Purpose | Consumer | Location | Default | Req/Opt | Runtime | Dup? | Unused? | Move? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `APP_NAME` | App name label | `Settings` (implicit via env) | `backend/.env` | `Openclaw Recruiting Platform` | Opt | Backend | No | No | — |
| `APP_ENV` | Environment name | `Settings` (implicit via env) | `backend/.env` | `development` | Opt | Backend | No | No | — |
| `DEBUG` | Debug flag | Backend + compose `environment: DEBUG=true` | `backend/.env` | `true` | Opt | Backend | Compose forces `DEBUG=true` | No | Leave; compose override is intentional |
| `SECRET_KEY` | Internal signing key | Backend | `backend/.env` | — | Req | Backend | No | No | — |
| `TWENTY_API_KEY` | Twenty API auth | `TwentyService`, `TwentySkill`, OpenClaw skills | `backend/.env` | `""` | Req for CRM calls | Backend + OpenClaw (mirrored via compose) | Yes (also referenced in OpenClaw `environment:`) | No | Keep single source in `backend/.env`; compose references it |
| `TWENTY_API_URL` | Twenty API base URL | `TwentyService`, `TwentySkill` | `backend/.env` | `http://localhost:3000` | Opt | Backend | No | No | — |
| `LLM_PROVIDER` | Selects LLM backend | `LLMService` | `backend/.env` | `gemini` | Opt | Backend | No | No | — |
| `GEMINI_API_KEY` | Gemini key | `LLMService` | `backend/.env` | `""` | Req if `LLM_PROVIDER=gemini` | Backend | No | No | — |
| `OPENAI_API_KEY` | OpenAI key | `LLMService` | `backend/.env` | `""` | Req if `LLM_PROVIDER=openai` | Backend | No | No | — |
| `OPENROUTER_API_KEY` | OpenRouter key | `LLMService` | `backend/.env` | `""` | Req if `LLM_PROVIDER=openrouter` | Backend | Referenced by `llm_service.py`; missing from `Settings` today | No | **Add to `Settings`** (see inconsistencies) |
| `OPENCLAW_URL` | OpenClaw completion endpoint | `LLMService` (`openclaw` provider) | `backend/.env` | `""` | Req if `LLM_PROVIDER=openclaw` | Backend | Naming clash with `OPENCLAW_API_URL` | Rarely used | Consider renaming to `OPENCLAW_LLM_URL` |
| `ELEVENLABS_API_KEY` | ElevenLabs API key | `ElevenLabsService` | `backend/.env` | `""` | Opt | Backend | No | No | — |
| `ELEVENLABS_VOICE_ID` | Default voice | `ElevenLabsService`, `voice.py` | `backend/.env` | `""` | Opt | Backend | No | No | — |
| `ELEVENLABS_AGENT_ID` | ElevenLabs agent | `ElevenLabsService`, `webhook.py` | `backend/.env` | `""` | Req for outbound calls | Backend | No | No | — |
| `ELEVENLABS_PHONE_NUMBER_ID` | Registered phone number | `ElevenLabsService` | `backend/.env` | `""` | Opt (auto-detected) | Backend | No | No | — |
| `ELEVENLABS_MODEL` | ElevenLabs TTS model | `ElevenLabsService` | `backend/.env` | `eleven_multilingual_v2` | Opt | Backend | No | No | — |
| `DATABASE_URL` | Backend DB URL | Not currently read by `Settings` | `backend/.env` | `postgresql://user:password@localhost:5432/openclaw` | Opt | Backend | No | Yes (not in `Settings`) | Keep as documentation; consider removing if never wired up |

### Frontend

| Variable | Purpose | Consumer | Location | Default | Req/Opt | Runtime | Dup? | Unused? | Move? |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `VITE_API_URL` | Backend base URL | React app | `frontend/.env` and compose `environment:` on `frontend` | `http://localhost:8000` | Req | Frontend | Set in two places | No | Keep compose override; `frontend/.env` mirrors it |
| `VITE_APP_NAME` | App display name | React app | `frontend/.env` and compose `environment:` on `frontend` | `Openclaw Recruiting Platform` | Opt | Frontend | Set in two places | No | Same as above |

---

## 4. Duplicate Variable Report

- `TWENTY_API_KEY` — canonical value lives in `backend/.env`. `docker-compose.dev.yml` references it (`TWENTY_API_KEY: ${TWENTY_API_KEY:-}`) so that OpenClaw skills can see the same token. **No change required**; keep `backend/.env` as the single source.
- `OPENCLAW_GATEWAY_TOKEN` (Docker) vs `OPENCLAW_API_KEY` (backend) — two names for the same secret. They must match. Documented above; renaming is deferred to avoid runtime changes.
- `VITE_API_URL` / `VITE_APP_NAME` — declared in both `frontend/.env` and `docker-compose.dev.yml`. The compose values win at runtime; `frontend/.env` is used only when running the frontend outside Docker.
- `DEBUG` — present in `backend/.env` but hard-set to `true` in compose. Compose wins.

## 5. Unused / Missing Variable Report

- **Missing declaration:** `OPENROUTER_API_KEY` is used by `backend/app/services/llm_service.py` but is not declared in `Settings` (`backend/app/settings.py`). Today Pydantic raises `AttributeError` if `LLM_PROVIDER=openrouter` is selected without the field. This is a code-level fix and is out of scope for Phase 3, but is now called out in `backend/.env.example`.
- **Unused in `Settings`:** `APP_NAME`, `APP_ENV`, `DEBUG`, `SECRET_KEY`, `DATABASE_URL` are present in `backend/.env` but never referenced by `Settings`. They are picked up by anything using `os.getenv` directly and are safe to keep as documentation for future use.
- **Retired:** `TAG`, `SERVER_URL`, `ENCRYPTION_KEY` in the real `docker/.env` are only consumed by the archived `docker/archive/docker-compose.yml`. They are no longer read by the active stack but remain in `docker/.env` for rollback (as per Phase 2 policy). They are intentionally absent from `docker/.env.example`.
- **Never wired up:** `OPENCLAW_URL` (used only when `LLM_PROVIDER=openclaw`) is defined in `Settings` but no environment currently sets it.

## 6. Inconsistencies Identified

1. `OPENROUTER_API_KEY` is referenced in code but missing from `Settings` (see above).
2. `OPENCLAW_URL` vs `OPENCLAW_API_URL` — visually similar names with different meanings (LLM completion endpoint vs gateway URL). Rename recommended in a future refactor.
3. `TWENTY_API_URL` default in the backend template was `https://api.twenty.com`, which is incorrect for local development. Now corrected to `http://localhost:3000` and documented that compose overrides it to `http://twenty-server:3000` inside Docker.
4. `docker/.env.example` previously advertised backend variables (`TWENTY_API_KEY`) that are actually owned by `backend/.env`. Now removed and replaced with a "Not Configured Here" note.

## 7. Updated Template Files

- `backend/.env.example` — now documents every variable read by `Settings` and by `os.getenv` in the backend, grouped by concern (app, Twenty, OpenClaw, LLM, ElevenLabs).
- `docker/.env.example` — now documents only Docker/infrastructure variables and explicitly points to `backend/.env` and `frontend/.env` for values it does not own.

Real `.env` files were **not** modified.

## 8. Recommended Future Configuration Architecture

```
docker/
    .env             # Twenty CRM + Postgres + Redis + OpenClaw gateway
    .env.example
    archive/         # Legacy compose files (read-only reference)
backend/
    .env             # FastAPI + Twenty API + OpenClaw client + LLM + ElevenLabs
    .env.example
frontend/
    .env             # Vite variables
    .env.example
openclaw/
    data/openclaw.json  # Generated by OpenClaw at onboarding (do not edit)
```

Rules going forward:

1. Each variable is declared in exactly one `.env.example` file.
2. `docker-compose.dev.yml` may reference variables from `docker/.env` (directly) and `backend/.env` (via `env_file`), but must not redefine credentials that already live in a `.env`.
3. `Settings` in `backend/app/settings.py` is the authoritative Python-side view of backend configuration. Any new backend variable must be added there before being consumed elsewhere.
4. Secrets never live in `docker/.env.example`, `backend/.env.example`, or `frontend/.env.example`.

## 9. Verification

- `docker compose -f docker-compose.dev.yml config` resolves successfully (see Phase 2 verification, unchanged here).
- No runtime behaviour changed: only template files (`*.env.example`) and this documentation were touched.
