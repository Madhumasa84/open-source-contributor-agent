from fastapi import APIRouter, HTTPException

from app.schemas.github import GitHubIssueDetails, GitHubIssueRequest
from app.services.github_issues import GitHubIssueError, GitHubIssueService

router = APIRouter(prefix="/github", tags=["github"])


@router.post("/issue", response_model=GitHubIssueDetails)
async def fetch_issue(request: GitHubIssueRequest) -> GitHubIssueDetails:
    try:
        return await GitHubIssueService().fetch_issue(str(request.issue_url))
    except GitHubIssueError as exc:
        raise HTTPException(status_code=exc.status_code, detail=str(exc)) from exc
