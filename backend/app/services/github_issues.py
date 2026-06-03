from __future__ import annotations

from dataclasses import dataclass
from urllib.parse import urlparse

import httpx

from app.core.config import Settings, get_settings
from app.schemas.github import GitHubIssueDetails
from app.services.audit import AuditLogger, AuditRecord


class GitHubIssueError(RuntimeError):
    def __init__(self, message: str, status_code: int = 400) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass(slots=True)
class IssueReference:
    owner: str
    repo: str
    number: int
    kind: str

    @property
    def api_url(self) -> str:
        return f"https://api.github.com/repos/{self.owner}/{self.repo}/issues/{self.number}"

    @property
    def html_url(self) -> str:
        return f"https://github.com/{self.owner}/{self.repo}/{self.kind}/{self.number}"


class GitHubIssueService:
    def __init__(
        self,
        settings: Settings | None = None,
        audit: AuditLogger | None = None,
    ) -> None:
        self.settings = settings or get_settings()
        self.audit = audit or AuditLogger()

    def parse_issue_url(self, issue_url: str) -> IssueReference:
        parsed = urlparse(issue_url)
        if parsed.scheme != "https" or parsed.netloc.lower() != "github.com":
            raise GitHubIssueError("Only HTTPS GitHub issue URLs are supported.")

        parts = [part for part in parsed.path.split("/") if part]
        if len(parts) < 4:
            raise GitHubIssueError("GitHub issue URL must include owner, repo, and issue number.")

        owner, repo, kind, number = parts[0], parts[1], parts[2], parts[3]
        if kind not in {"issues", "pull"}:
            raise GitHubIssueError("GitHub URL must point to an issue or pull request.")

        repo = repo.removesuffix(".git")
        if not number.isdigit():
            raise GitHubIssueError("GitHub issue number must be numeric.")

        return IssueReference(owner=owner, repo=repo, number=int(number), kind=kind)

    async def fetch_issue(self, issue_url: str) -> GitHubIssueDetails:
        reference = self.parse_issue_url(issue_url)
        headers = {
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.settings.github_token:
            headers["Authorization"] = f"Bearer {self.settings.github_token}"

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(reference.api_url, headers=headers)
        except httpx.HTTPError as exc:
            raise GitHubIssueError("GitHub API request failed.", status_code=502) from exc

        if response.status_code == 404:
            raise GitHubIssueError("GitHub issue was not found.", status_code=404)
        if response.status_code in {401, 403}:
            raise GitHubIssueError(
                "GitHub API access denied. Check token or rate limits.", status_code=403
            )
        if response.status_code >= 400:
            raise GitHubIssueError("GitHub API request failed.", status_code=502)

        data = response.json()
        labels = [
            label.get("name")
            for label in data.get("labels", [])
            if isinstance(label, dict) and label.get("name")
        ]
        author = data.get("user", {}).get("login") or "unknown"
        title = data.get("title") or ""
        body = data.get("body") or ""
        is_pull_request = "pull_request" in data

        await self.audit.record(
            AuditRecord(
                action="github.issue.fetched",
                input_summary=reference.html_url,
                output_summary=title,
                metadata={
                    "repository": f"{reference.owner}/{reference.repo}",
                    "number": reference.number,
                    "state": data.get("state"),
                    "labels": labels,
                },
            )
        )

        return GitHubIssueDetails(
            repository=f"{reference.owner}/{reference.repo}",
            number=reference.number,
            title=title,
            body=body,
            state=data.get("state") or "unknown",
            labels=labels,
            author=author,
            comments=int(data.get("comments") or 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            url=data.get("url") or reference.api_url,
            html_url=data.get("html_url") or reference.html_url,
            is_pull_request=is_pull_request,
        )
