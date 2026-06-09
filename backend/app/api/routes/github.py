from fastapi import APIRouter, HTTPException
import uuid
from pydantic import BaseModel

from app.schemas.github import GitHubIssueDetails, GitHubIssueRequest
from app.services.github_issues import GitHubIssueError, GitHubIssueService
from app.services.issue_triager import IssueTriager, TriageResult
from app.services.audit import AuditLogger
from app.services.language_service import LanguageService
from app.schemas.repository import RepositoryOverview, DifficultyLevel
from app.models.workflow import WorkflowRun
from app.core.database import AsyncSessionLocal

router = APIRouter(prefix="/github", tags=["github"])

class GitHubIssueTriageResponse(BaseModel):
    issue: GitHubIssueDetails
    triage: TriageResult
    workflow_id: str
    detected_language: str | None = None
    translation_warning: str | None = None

@router.post("/issue", response_model=GitHubIssueTriageResponse)
async def fetch_issue(request: GitHubIssueRequest) -> GitHubIssueTriageResponse:
    try:
        issue = await GitHubIssueService().fetch_issue(str(request.issue_url))
        
        empty_repo = RepositoryOverview(
            root="",
            languages={},
            frameworks=[],
            dependencies={},
            test_frameworks=[],
            build_systems=[],
            architecture=[],
            important_files=[],
            entry_points=[],
            risks=[],
            code_quality_metrics={},
            contribution_difficulty=DifficultyLevel.medium
        )
        
        triager = IssueTriager(AuditLogger())
        triage_res = await triager.triage(issue, empty_repo, request.preferred_language)
        
        lang_service = LanguageService(AuditLogger())
        detected_lang = await lang_service.detect(issue.title + "\n" + issue.body)
        
        workflow_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            workflow = WorkflowRun(
                id=workflow_id,
                issue_url=str(request.issue_url),
                mode="autonomous",
                stage="triage",
                status="triaged",
                plan_approval_status="pending",
                final_approval_status="pending",
                triage_data=triage_res.model_dump(mode="json"),
                preferred_language=request.preferred_language
            )
            session.add(workflow)
            await session.commit()
            
        # Extract translation_warning if it was attached to TriageResult implicitly, or if we translate something here. Wait, triage_res will contain the warning if we translate there.
        # But for now, let's just pass whatever we have.
        warning = getattr(triage_res, "translation_warning", None)
            
        return GitHubIssueTriageResponse(
            issue=issue,
            triage=triage_res,
            workflow_id=workflow_id,
            detected_language=detected_lang,
            translation_warning=warning
        )
    except GitHubIssueError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
