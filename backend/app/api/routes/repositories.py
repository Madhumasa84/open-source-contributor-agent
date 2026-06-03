from fastapi import APIRouter, HTTPException

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
    return ContributorOnboardingService().generate(overview)


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
