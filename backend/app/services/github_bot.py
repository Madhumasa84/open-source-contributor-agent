import httpx
import logging
from app.core.config import get_settings
from app.services.audit import AuditLogger, AuditRecord

logger = logging.getLogger(__name__)

class GitHubBot:
    def __init__(self, audit_logger: AuditLogger):
        self.settings = get_settings()
        self.audit = audit_logger
        self.token = self.settings.github_token
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "OSCA-Bot"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

    def _parse_issue_url(self, url: str) -> tuple[str, str, str]:
        # e.g. https://github.com/expressjs/express/issues/5747
        parts = url.rstrip("/").split("/")
        owner = parts[-4]
        repo = parts[-3]
        issue_number = parts[-1]
        return owner, repo, issue_number

    async def apply_labels(self, issue_url: str, labels: list[str]):
        if not self.token:
            logger.warning("No GITHUB_TOKEN set. Cannot apply labels.")
            return

        try:
            owner, repo, issue_number = self._parse_issue_url(issue_url)
            api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/labels"
            
            async with httpx.AsyncClient() as client:
                res = await client.post(api_url, headers=self.headers, json={"labels": labels})
                res.raise_for_status()

            await self.audit.record(AuditRecord(
                action="github_apply_labels",
                actor="github_bot",
                status="completed",
                input_summary=f"Labels: {labels}",
                output_summary=f"Applied to {issue_url}",
                metadata={"labels": labels, "issue": issue_url}
            ))
        except Exception as e:
            logger.error(f"Failed to apply labels to {issue_url}: {e}")

    async def post_comment(self, issue_url: str, body: str):
        if not self.token:
            logger.warning("No GITHUB_TOKEN set. Cannot post comment.")
            return

        try:
            owner, repo, issue_number = self._parse_issue_url(issue_url)
            api_url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_number}/comments"
            
            async with httpx.AsyncClient() as client:
                res = await client.post(api_url, headers=self.headers, json={"body": body})
                res.raise_for_status()

            await self.audit.record(AuditRecord(
                action="github_post_comment",
                actor="github_bot",
                status="completed",
                input_summary=body[:50] + "...",
                output_summary=f"Commented on {issue_url}",
                metadata={"issue": issue_url}
            ))
        except Exception as e:
            logger.error(f"Failed to post comment to {issue_url}: {e}")
