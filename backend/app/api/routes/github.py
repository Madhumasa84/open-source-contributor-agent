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
            
        # Background or inline actions
        from app.services.issue_indexer import IssueIndexer
        from app.services.github_bot import GitHubBot
        import asyncio
        
        indexer = IssueIndexer(AuditLogger())
        bot = GitHubBot(AuditLogger())
        
        async def post_triage_actions():
            # Check for duplicates
            duplicates = await indexer.find_duplicates(str(request.issue_url), issue.title, issue.body)
            if duplicates:
                dup = duplicates[0]
                await bot.post_comment(str(request.issue_url), f"This may be related to {dup['issue_url']} and could be a duplicate.")
            else:
                await indexer.index_issue(str(request.issue_url), issue.title, issue.body)
            
            # Apply labels
            labels = ["osca-triaged"]
            if triage_res.good_first_issue:
                labels.append("good-first-issue")
            if any("bug" in l.lower() for l in issue.labels):
                labels.append("bug")
            elif any("enhancement" in l.lower() for l in issue.labels):
                labels.append("enhancement")
            
            if triage_res.fixability_score < 4:
                labels.append("needs-reproduction")
            if triage_res.difficulty_score >= 8:
                labels.append("difficulty:hard")
                
            await bot.apply_labels(str(request.issue_url), list(set(labels)))
            
            # Post triage comment
            comment_body = (
                f"🤖 **OSCA Triage Complete**\n"
                f"- **Difficulty Score:** {triage_res.difficulty_score}/10\n"
                f"- **Fixability Score:** {triage_res.fixability_score}/10\n"
                f"- **Contributor Level:** {triage_res.contributor_level.capitalize()}\n"
                f"- **Entry Points:** {', '.join(triage_res.suggested_entry_points) if triage_res.suggested_entry_points else 'None suggested'}\n\n"
                f"[Click here to open this in OSCA](http://localhost:3010/workflows/{workflow_id})"
            )
            await bot.post_comment(str(request.issue_url), comment_body)
            
        # Fire and forget (or await directly if we want to block)
        asyncio.create_task(post_triage_actions())

        # Extract translation_warning if it was attached to TriageResult implicitly
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
