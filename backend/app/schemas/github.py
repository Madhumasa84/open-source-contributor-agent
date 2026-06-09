from datetime import datetime

from pydantic import AnyUrl, BaseModel


class GitHubIssueRequest(BaseModel):
    issue_url: AnyUrl
    preferred_language: str = "en"


class GitHubIssueDetails(BaseModel):
    repository: str
    number: int
    title: str
    body: str
    state: str
    labels: list[str]
    author: str
    comments: int
    created_at: datetime | None = None
    updated_at: datetime | None = None
    url: AnyUrl
    html_url: AnyUrl
    is_pull_request: bool = False
