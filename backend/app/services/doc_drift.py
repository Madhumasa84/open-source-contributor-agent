import logging
from app.services.github_bot import GitHubBot
from app.services.audit import AuditLogger, AuditRecord

logger = logging.getLogger(__name__)

class DocDriftDetector:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.bot = GitHubBot(audit_logger)

    async def detect_and_report(self, repo_url: str, patch_diff: str, files_changed: list[str]):
        """
        In a real implementation, this would use an LLM or AST to compare the old docstrings
        with the new patch logic. Here we simulate the detection for the MVP.
        """
        if not patch_diff or not files_changed:
            return

        # MVP: simple heuristic check for demonstration. If the diff removes/adds a lot
        # but no 'doc' or 'readme' changes exist, we flag it.
        has_doc_changes = any("readme" in f.lower() or ".md" in f.lower() for f in files_changed)
        
        if not has_doc_changes and len(patch_diff.split('\n')) > 50:
            logger.info("Doc drift detected. Creating follow-up issue.")
            
            # Use bot to create a new issue (if token exists)
            # Since bot currently only has apply_labels and post_comment, we add create_issue directly here
            # or extend the bot. Let's extend it inline here for simplicity.
            
            if not self.bot.token:
                logger.warning("No GITHUB_TOKEN to create doc drift issue.")
                return
                
            try:
                owner, repo, _ = self.bot._parse_issue_url(repo_url + "/issues/0") # hack to get owner/repo
                api_url = f"https://api.github.com/repos/{owner}/{repo}/issues"
                
                body = (
                    "🤖 **OSCA Doc Drift Detector**\n\n"
                    f"A recent patch by OSCA modified logic in `{', '.join(files_changed)}` significantly "
                    "without updating corresponding documentation or docstrings. "
                    "Please review and update the docs to reflect these changes."
                )
                
                import httpx
                async with httpx.AsyncClient() as client:
                    res = await client.post(api_url, headers=self.bot.headers, json={
                        "title": "Update Documentation for Recent Patch",
                        "body": body,
                        "labels": ["documentation", "osca-bot"]
                    })
                    res.raise_for_status()
                    
                await self.audit.record(AuditRecord(
                    action="doc_drift.report",
                    actor="doc_drift_detector",
                    status="completed",
                    input_summary="Detected missing docs",
                    output_summary="Created follow-up issue",
                    metadata={"files": files_changed}
                ))
            except Exception as e:
                logger.error(f"Failed to create doc drift issue: {e}")
