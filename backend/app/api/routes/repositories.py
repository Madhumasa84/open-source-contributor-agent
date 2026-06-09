from fastapi import APIRouter, HTTPException
import uuid
from pydantic import BaseModel
import asyncio
from pathlib import Path

from app.schemas.repository import (
    ImpactAnalysis,
    OnboardingGuide,
    RepositoryAnalyzeRequest,
    RepositoryFileRequest,
    RepositoryGraph,
    RepositoryOverview,
    SecurityReview,
    TestPlan,
)
from app.services.audit import AuditLogger
from app.services.impact import ImpactAnalyzer
from app.services.onboarding import ContributorOnboardingService
from app.services.repository_analyzer import RepositoryAnalyzer
from app.services.security import SecurityReviewer
from app.services.test_runner import TestExecutionEngine
from app.services.visualization import RepositoryVisualizationService
from app.tools.safe_executor import SafeToolExecutor
from app.services.code_indexer import CodeIndexer
from app.tools.docker_sandbox import DockerSandbox, SandboxResult
from app.api.routes.workflows import get_or_load_workflow

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.post("/analyze", response_model=RepositoryOverview)
async def analyze_repository(request: RepositoryAnalyzeRequest) -> RepositoryOverview:
    try:
        return await RepositoryAnalyzer().analyze(request.path)
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/onboarding", response_model=OnboardingGuide)
async def generate_onboarding(request: RepositoryAnalyzeRequest) -> OnboardingGuide:
    overview = await analyze_repository(request)
    return await ContributorOnboardingService().generate(overview, request.preferred_language)


@router.post("/security-review", response_model=SecurityReview)
async def security_review(request: RepositoryFileRequest) -> SecurityReview:
    return SecurityReviewer().review_files(request.root, request.files)


@router.post("/impact", response_model=ImpactAnalysis)
async def impact_analysis(request: RepositoryFileRequest) -> ImpactAnalysis:
    return ImpactAnalyzer().analyze_python_files(request.root, request.files)


@router.post("/test-plan", response_model=TestPlan)
async def test_plan(request: RepositoryAnalyzeRequest) -> TestPlan:
    executor = SafeToolExecutor(AuditLogger())
    commands = TestExecutionEngine(executor).detect_commands(request.path)
    notes = ["Commands are detected only. Execution requires explicit human approval."]
    coverage_command = (
        ["python", "-m", "pytest", "--cov"]
        if any("pytest" in command for command in commands)
        else None
    )
    return TestPlan(commands=commands, coverage_command=coverage_command, notes=notes)


@router.post("/visualization", response_model=RepositoryGraph)
async def repository_visualization(request: RepositoryAnalyzeRequest) -> RepositoryGraph:
    overview = await analyze_repository(request)
    return RepositoryVisualizationService().from_overview(overview)

class SearchRequest(BaseModel):
    workflow_id: uuid.UUID
    query: str
    top_k: int = 10

class SearchResult(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    content: str
    score: float

@router.post("/search", response_model=list[SearchResult])
async def semantic_code_search(request: SearchRequest):
    indexer = CodeIndexer(AuditLogger())
    chunks = await indexer.search(request.query, request.workflow_id, request.top_k)
    return chunks

class SandboxRunRequest(BaseModel):
    workflow_id: str
    command: str
    timeout_seconds: int = 120

sandbox_semaphore = asyncio.Semaphore(5)

@router.post("/sandbox-run", response_model=SandboxResult)
async def sandbox_run(request: SandboxRunRequest):
    state = await get_or_load_workflow(request.workflow_id)
    if state.plan_approval.value != "approved":
        raise HTTPException(status_code=403, detail="Gate 1 approval required")
        
    if not state.repository_path:
        raise HTTPException(status_code=400, detail="Repository path not set")
        
    async with sandbox_semaphore:
        sandbox = DockerSandbox(state.audit)
        result = await sandbox.run(Path(state.repository_path), request.command, request.timeout_seconds)
        return result

class RepoHealthResponse(BaseModel):
    open_issue_count: int
    difficulty_breakdown: dict[str, int]
    contributor_funnel: dict[str, int]
    test_coverage_trend: float
    stale_issue_count: int

@router.get("/{owner}/{repo}/health", response_model=RepoHealthResponse)
async def repo_health(owner: str, repo: str) -> RepoHealthResponse:
    # MVP simulated response. In production, this queries DB/GitHub API
    return RepoHealthResponse(
        open_issue_count=42,
        difficulty_breakdown={"low": 10, "medium": 20, "hard": 12},
        contributor_funnel={"opened": 42, "cloned": 15, "pr": 8, "merged": 3},
        test_coverage_trend=85.5,
        stale_issue_count=5
    )

class ContributorStats(BaseModel):
    username: str
    patches_merged: int
    issues_resolved: int
    review_score: float

@router.get("/{owner}/{repo}/leaderboard", response_model=list[ContributorStats])
async def repo_leaderboard(owner: str, repo: str) -> list[ContributorStats]:
    # MVP simulated response.
    return [
        ContributorStats(username="alice_dev", patches_merged=15, issues_resolved=12, review_score=4.9),
        ContributorStats(username="bob_coder", patches_merged=8, issues_resolved=9, review_score=4.5),
        ContributorStats(username="charlie_hacks", patches_merged=3, issues_resolved=3, review_score=4.1),
    ]
