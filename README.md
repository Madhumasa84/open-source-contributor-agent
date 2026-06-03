# Open Source Contributor Agent (OSCA)

OSCA is a human-controlled, multi-model platform for helping developers contribute to open-source projects safely. It analyzes repositories, estimates issue difficulty, drafts fix plans, records auditable actions, and blocks commits or draft PR creation until required approval gates are satisfied.

This repository is a production-grade foundation that emphasizes auditability, deterministic planning, and safe tool execution before any code changes or GitHub actions are allowed.

## Highlights

- Multi-provider model abstraction (Gemini, Anthropic, OpenRouter, Ollama).
- Repository analyzer for languages, frameworks, dependencies, tests, build systems, risks, entry points, and quality metrics.
- Difficulty estimator, mentor-mode explanation, deterministic fix plan generation, and consensus-model assignment.
- Safe tool executor with workspace permission checks and audit events.
- Security, impact, and test-execution service modules.
- GitHub issue ingestion with optional token authentication.
- Approved repository clone orchestration for HTTPS GitHub repositories inside the configured workspace root.
- Postgres-backed workflow records, audit events, and clone jobs via Alembic migrations.
- Next.js dashboard with issue input, model selection, workflow rail, approval status, review tabs, and audit display.

PR creation remains guarded: draft PR creation is blocked until final human approval is present.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the module map and workflow design. The system is split into an API layer, domain services, provider adapters, and safe tooling with audit logging.

## Workflow

1. GitHub issue ingestion
2. Repository analysis
3. Difficulty estimate and mentor explanation
4. Fix plan generation
5. Human approval gate (plan)
6. Generate changes (future phase)
7. Tests and security checks (future phase)
8. Review report
9. Human approval gate (final)
10. Draft PR creation (future phase)

## Quickstart (Docker)

1. Copy the environment template.

```bash
cp .env.example .env
```

2. Start the stack.

```bash
docker compose up --build
```

3. Open the dashboard.

```text
http://localhost:3010
```

The backend API is available at:

```text
http://localhost:8010/docs
```

If you need different ports, update `docker-compose.yml` and `ALLOWED_ORIGINS` in `.env`.

## Local Development

Backend:

```bash
cd backend
python -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

On Windows PowerShell:

```powershell
cd backend
python -m venv .venv
\.venv\Scripts\Activate.ps1
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8010
```

Run migrations:

```powershell
alembic -c alembic.ini upgrade head
```

Frontend:

```bash
cd frontend
npm install
npm run dev -- --port 3010
```

## Configuration

Set only the providers you want to use:

```env
GOOGLE_API_KEY=
ANTHROPIC_API_KEY=
OPENROUTER_API_KEY=
OLLAMA_BASE_URL=http://localhost:11434
GITHUB_TOKEN=
```

The dashboard works without remote API keys. Ollama is treated as local-capable when a base URL is configured.

## Safety Model

- Gate 1: Human approves the generated plan before code changes.
- Gate 2: Human approves the review report before branch, commit, or PR actions.

All file and terminal tools are scoped to `OSCA_WORKSPACE_ROOT`. Each action records an audit event with actor, status, inputs, and outputs. Repository clone requests require an explicit `approved_by` actor and only allow HTTPS GitHub URLs.

## API Endpoints

- `POST /api/repositories/analyze`
- `POST /api/repositories/onboarding`
- `POST /api/repositories/security-review`
- `POST /api/repositories/impact`
- `POST /api/repositories/test-plan`
- `POST /api/repositories/visualization`
- `GET /api/providers`
- `POST /api/workflows/plan`
- `POST /api/workflows/{workflow_id}/approvals/plan`
- `POST /api/workflows/{workflow_id}/approvals/final`
- `POST /api/workflows/{workflow_id}/repository/clone`
- `POST /api/workflows/{workflow_id}/pr-draft`
- `POST /api/workflows/{workflow_id}/github/draft-pr`
- `POST /api/github/issue`

## Roadmap

1. Execute multi-model consensus calls and normalize model outputs.
2. Add patch generation in isolated worktrees.
3. Add test, lint, type-check, coverage, and security execution reports.
4. Add draft PR creation through a final approval gate.
5. Expand repository knowledge graph and architecture visualization.

## Contributing

Issues and pull requests are welcome. Please keep changes auditable and aligned with the approval-gated workflow design.

## License

MIT License. See [LICENSE](LICENSE).
