import logging

from app.core.config import get_settings
from app.schemas.repository import DifficultyEstimate, DifficultyLevel
from app.services.audit import AuditLogger, AuditRecord
from app.services.github_bot import GitHubBot

logger = logging.getLogger(__name__)

class AutoIssueLabeler:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.bot = GitHubBot(audit_logger)
        self.settings = get_settings()

    async def _is_enabled(self) -> bool:
        # In a real environment, read from settings/db, default off
        # Just use env variable
        import os
        return os.getenv("ENABLE_AUTO_LABELER", "false").lower() == "true"

    def _map_labels(self, difficulty: DifficultyEstimate, triage_data: dict) -> list[str]:
        labels = []
        if difficulty.level == DifficultyLevel.easy:
            labels.append("difficulty:easy")
            labels.append("good-first-issue")
        elif difficulty.level == DifficultyLevel.medium:
            labels.append("difficulty:medium")
        elif difficulty.level == DifficultyLevel.hard:
            labels.append("difficulty:hard")
        elif difficulty.level == DifficultyLevel.expert:
            labels.append("difficulty:expert")

        # Example mapping other triage data to labels
        if triage_data and triage_data.get("is_bug", False):
            labels.append("bug")

        return labels

    async def label_issue(self, workflow_id: str, issue_url: str, difficulty: DifficultyEstimate, triage_data: dict = None) -> None:
        if not await self._is_enabled():
            logger.info("AutoIssueLabeler is disabled. Skipping label application.")
            return

        labels = self._map_labels(difficulty, triage_data)
        if not labels:
            return

        await self.bot.apply_labels(issue_url, labels)

        await self.audit.record(AuditRecord(
            action="issue.auto_labeled",
            actor="auto_labeler",
            status="completed",
            input_summary=issue_url,
            output_summary=f"Applied labels: {labels}",
            metadata={"workflow_id": workflow_id, "labels": labels}
        ))
