# Open Source Contributor Agent (OSCA)

OSCA is a human-controlled, multi-model platform for helping developers contribute to open-source projects safely. It analyzes repositories, estimates issue difficulty, drafts fix plans, records auditable actions, and blocks commits or draft PR creation until required approval gates are satisfied.

This repository is a production-grade foundation that emphasizes auditability, deterministic planning, and safe tool execution before any code changes or GitHub actions are allowed.

## Highlights

- Multi-provider model abstraction (Gemini, Anthropic, OpenRouter, Ollama).
- Repository analyzer for languages, frameworks, dependencies, tests, build systems, risks, entry points, and quality metrics.
- Deterministic fixability and difficulty scoring on ingestion via IssueTriager.
- Fully automated multilingual support via LangDetect (translating outputs without affecting core planning).
- Semantic search using pgvector embeddings for code snippets (CodeIndexer).
- Ephemeral Docker Sandbox for isolated script and test execution (--network none, 512MB limits).
- PatchAgent with self-correction loop (max 3 iterations) and test feedback evaluation.
- Safe tool executor with workspace permission checks and audit events via DefaultDatabaseAuditSink.
- Security, impact, and test-execution service modules.
- GitHub issue ingestion with optional token authentication.
- Approved repository clone orchestration for HTTPS GitHub repositories inside the configured workspace root.
- Postgres-backed workflow records, audit events, and clone jobs via Alembic migrations.
- Next.js dashboard with issue input, model selection, workflow rail, approval status, review tabs, advanced diff viewer, and comprehensive audit display.

PR creation remains guarded: draft PR creation is blocked until final human approval is present.

## Architecture

See [docs/architecture.md](docs/architecture.md) for the module map and workflow design. The system is split into an API layer, domain services, provider adapters, and safe tooling with audit logging.

## Workflow

1. GitHub issue ingestion & Issue Triage
2. Repository analysis
3. Difficulty estimate and mentor explanation
4. Fix plan generation
5. Human approval gate (plan)
6. Generate code patches iteratively (PatchAgent)
7. Tests and security checks within Docker Sandbox
8. Review report & Diff Viewer evaluation
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
OSCA_USE_DOCKER_SANDBOX=true     # default false
DOCKER_SOCKET_PATH=              # default /var/run/docker.sock
```

The dashboard works without remote API keys. Ollama is treated as local-capable when a base URL is configured.

## Safety Model

- Gate 1: Human approves the generated plan before code changes.
- Gate 2: Human approves the review report before branch, commit, or PR actions.

All file and terminal tools are scoped to `OSCA_WORKSPACE_ROOT`. Each action records an audit event with actor, status, inputs, and outputs. Repository clone requests require an explicit `approved_by` actor and only allow HTTPS GitHub URLs.

## New in v2
| Variable | Default | Description |
|---|---|---|
| `OSCA_USE_DOCKER_SANDBOX` | `false` | Enable ephemeral Docker containers for test execution |
| `DOCKER_SOCKET_PATH` | `/var/run/docker.sock` | Docker socket path |

## API Endpoints

- `POST /api/repositories/analyze`
- `POST /api/repositories/onboarding`
- `POST /api/repositories/security-review`
- `POST /api/repositories/impact`
- `POST /api/repositories/test-plan`
- `POST /api/repositories/visualization`
- `POST /api/repositories/search`
- `POST /api/repositories/sandbox-run`
- `GET /api/providers`
- `GET /api/workflows`
- `POST /api/workflows/plan`
- `POST /api/workflows/{workflow_id}/approvals/plan`
- `POST /api/workflows/{workflow_id}/approvals/final`
- `POST /api/workflows/{workflow_id}/repository/clone`
- `POST /api/workflows/{workflow_id}/patch`
- `POST /api/workflows/{workflow_id}/pr-draft`
- `POST /api/workflows/{workflow_id}/github/draft-pr`
- `POST /api/github/issue`

## Roadmap

1. Draft PR creation through final approval gate.
2. Multi-model consensus voting — run plans across models, flag disagreements for human review.
3. Repository knowledge graph and architecture visualization.
4. Contributor profiles and contribution history across projects.
5. IDE integration (VS Code extension / MCP server).
6. GitHub App for maintainers — auto-label issues, pre-screen PRs.
7. Advanced telemetry and success-rate tracking (which fix plans got merged).
8. **🏷 Auto Issue Labeler**: After triage, auto-apply GitHub labels (e.g. good-first-issue, difficulty:hard) via the API to provide maintainers a fully labeled backlog.
9. **🔁 Duplicate Issue Detector**: Embed new issues and compare against open issues (using CodeIndexer). If similarity > 0.85, suggest closing the duplicate.
10. **📋 PR Pre-Check Bot**: Contributors run OSCA locally before submitting PRs to check tests, secrets, diff plan matching, and style conventions.
11. **📊 Repo Health Dashboard**: Public URL per repo showing open issue counts by difficulty, contributor funnel, test coverage trends, and stale issue metrics.
12. **💬 Issue Comment Bot**: On triage, auto-post a structured comment with difficulty score, suggested entry points, and an OSCA deep link.
13. **📚 Doc Drift Detector**: Diff changed functions against their docstrings and README. Open follow-up doc-fix issues if divergence is detected.
14. **🎖 Contributor Leaderboard**: Public leaderboard highlighting top contributors by patches merged, issues resolved, and review quality score.
15. **⏱ Stale Issue Closer**: Auto-comment and close issues inactive for 90 days with low fixability scores to reduce backlog noise.

## Contributing

Issues and pull requests are welcome. Please keep changes auditable and aligned with the approval-gated workflow design.

## License

MIT License. See [LICENSE](LICENSE).
