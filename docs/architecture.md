# Architecture

## System Shape

OSCA is organized as a monorepo with a FastAPI backend and a Next.js frontend.

```text
frontend -> backend API -> domain services -> safe tools / model providers
                         -> PostgreSQL audit and workflow records
                         -> Redis job and rate-limit coordination
```

The backend keeps the contribution workflow explicit. Agent steps do not directly mutate repositories or publish PRs. They produce plans, reports, and tool requests that pass through approval gates.

## Backend Modules

- `app/api/routes`: HTTP boundary for health, providers, repository analysis, GitHub issue ingestion, and workflows.
- `app/agents`: OSCA workflow orchestration and approval gate enforcement.
- `app/ai/providers`: Provider abstraction and concrete Gemini, Anthropic, OpenRouter, and Ollama adapters.
- `app/services`: Repository analysis, difficulty estimation, security review, impact analysis, tests, and audit logging.
- `app/services/github_issues`: GitHub issue ingestion and normalization.
- `app/tools`: Permission-checked file and terminal execution.
- `app/models`: SQLAlchemy models for audit events and workflow runs.
- `app/schemas`: Pydantic request and response contracts.

## Workflow

```text
GitHub issue URL
Clone/open repository
Analyze repository
Estimate difficulty
Generate mentor explanation
Generate fix plan
Human approval gate 1
Generate changes
Run tests
Run security checks
Generate review report
Human approval gate 2
Create branch
Create commit
Create draft PR
```

The current slice implements planning, analysis, onboarding, provider selection, audit records, security review, impact analysis, test planning, repository visualization, approved GitHub repository cloning, PR draft body generation, and the final PR guard. Code mutation and GitHub publishing are left for later phases so they can be built with durable approvals and isolated worktrees.

## Approval Gates

Plan approval is required before code generation. Final approval is required before branch, commit, and PR actions. The backend raises `ApprovalRequiredError` if draft PR creation is attempted without final approval.

## Audit Trail

Audit records capture:

- Action name.
- Actor.
- Status.
- Provider and model.
- Prompt hash.
- Approval identifier.
- Input and output summaries.
- Structured metadata.

The in-memory audit sink supports deterministic tests and local planning responses. The database sink maps the same record shape to PostgreSQL.

## Provider Abstraction

All providers implement:

- `descriptor()`
- `complete(request)`
- `stream(request)`

The shared request and response contracts keep dynamic model selection provider-neutral. New providers can be added by implementing `BaseModelProvider` and registering them in `ProviderRegistry`.

## Safe Tool Execution

`SafeToolExecutor` resolves all paths through `OSCA_WORKSPACE_ROOT`. File reads, file writes, and terminal commands are audited. Terminal commands record start and finish events, timeout status, exit code, and bounded stdout/stderr.

## Repository Intelligence

Repository intelligence is split into small services:

- `RepositoryAnalyzer` detects languages, frameworks, dependencies, tests, build systems, entry points, risks, and quality metrics.
- `ContributorOnboardingService` converts analyzer output into build instructions, learning paths, and good-first-issue signals.
- `RepositoryVisualizationService` generates service/module/dependency graphs and issue knowledge graphs.
- `SecurityReviewer` scans selected files for secrets, traversal, command injection, SQL injection, and auth boundary markers.
- `ImpactAnalyzer` extracts touched Python functions, classes, and dependency-sensitive files.
- `TestExecutionEngine` detects commands first; execution requires explicit approval.

## Frontend

The dashboard is an operational interface, not a landing page. It provides:

- Issue and repository input.
- Learn and auto-fix mode selection.
- Multi-provider model selection.
- Workflow stage rail.
- Approval status.
- Review tabs for summary, files, tests, security, and audit data.

## Data Stores

PostgreSQL stores workflow runs, audit events, and repository clone jobs through Alembic-managed tables. The local API keeps an in-memory fallback for development so the dashboard remains usable when Postgres is not running. Redis is reserved for asynchronous job coordination, rate limits, and future streaming state.

## Migrations

The backend Docker image runs:

```text
alembic -c alembic.ini upgrade head
```

before starting Uvicorn. The initial migration creates:

- `audit_events`
- `workflow_runs`
- `repository_clone_jobs`

## Clone Orchestration

The clone endpoint accepts only HTTPS GitHub repository URLs and requires an explicit human actor in `approved_by`. The target directory name is sanitized and resolved through `SafeToolExecutor`, keeping clones inside `OSCA_WORKSPACE_ROOT`. Clone commands are executed as structured argv, not shell strings.
