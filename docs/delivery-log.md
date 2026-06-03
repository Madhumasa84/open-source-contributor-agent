# Delivery Log

## Phase 1: Foundation Slice

Files changed:

- Root configuration: `.gitignore`, `.env.example`, `docker-compose.yml`, `README.md`.
- Backend: FastAPI app, provider adapters, workflow orchestration, analyzers, audit, safe tools, tests, Dockerfile.
- Frontend: Next.js app, dashboard components, approval controls, API client, styling, Dockerfile.
- Docs: architecture notes and this delivery log.

Architecture decisions:

- Keep all repository-mutating actions behind explicit service methods and approval checks.
- Use provider-neutral Pydantic contracts so Gemini, Claude, OpenRouter, and Ollama can share workflow logic.
- Use a deterministic planning path before live model calls so the system remains useful without API keys.
- Scope safe file and terminal tools to `OSCA_WORKSPACE_ROOT`.
- Split audit persistence through a sink interface to support both tests and PostgreSQL.

Verification:

- `python -m compileall app tests`: passed.
- `backend\.venv\Scripts\python.exe -m pytest`: 6 passed.
- `backend\.venv\Scripts\python.exe -m ruff check .`: passed.
- `backend\.venv\Scripts\python.exe -c "from app.main import app; print(app.title)"`: imported app successfully.
- `npm run typecheck`: passed.
- `npm run build`: passed.
- `npm audit --omit=dev`: 0 vulnerabilities.
- Docker Compose defines PostgreSQL, Redis, backend, frontend, and optional Ollama.

## Phase 2: Persistence And Approved Clone Slice

Files changed:

- Backend migrations: `backend/alembic.ini`, `backend/alembic/env.py`, initial migration.
- Backend models/services: workflow persistence, clone job model, repository clone service.
- Backend routes/schemas: approved clone endpoint and durable workflow approval updates.
- Frontend: clone URL/target controls and clone job status display.
- Docs: README, architecture notes, delivery log.

Architecture decisions:

- Keep the dashboard usable without a running database by retaining in-memory workflow state as a local fallback.
- Persist workflow plans and approval states to Postgres when the configured database is available.
- Run Alembic migrations automatically in the backend container before Uvicorn starts.
- Treat repository clone as an approved safe-tool action with sanitized GitHub HTTPS inputs and no shell interpolation.

Verification:

- `backend\.venv\Scripts\python.exe -m compileall app tests alembic`: passed.
- `backend\.venv\Scripts\python.exe -m pytest`: 9 passed.
- `backend\.venv\Scripts\python.exe -m ruff check .`: passed.
- `npm run typecheck`: passed.
- `npm run build`: passed.

## Phase 3: GitHub Issue Ingestion Slice

Files changed:

- Backend: GitHub issue ingestion schemas, service, route, settings, and tests.
- Frontend: issue fetch controls, details display, and API client updates.
- Docs: README, architecture notes, delivery log.
- Root configuration: `.env.example`.

Architecture decisions:

- Keep GitHub issue ingestion as a separate endpoint so deterministic planning remains stable.
- Normalize GitHub issue and pull URLs to a single issues API path.
- Allow optional token authentication to reduce GitHub API rate limiting.

Verification:

- `c:/Users/Dell/Downloads/projects_new/masa_oss_tool/.venv/Scripts/python.exe -m pytest`: 13 passed.

## Debug: Windows Clone Execution Fix

Files changed:

- Backend: safe tool execution fallback for Windows subprocess support.

Architecture decisions:

- Fall back to a threaded `subprocess.run` path when the event loop does not support async subprocesses.

Verification:

- `c:/Users/Dell/Downloads/projects_new/masa_oss_tool/.venv/Scripts/python.exe -m pytest`: 13 passed.
