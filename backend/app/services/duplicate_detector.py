import json
import logging

from sqlalchemy import text

from app.core.database import AsyncSessionLocal
from app.services.audit import AuditLogger, AuditRecord
from app.services.code_indexer import CodeIndexer

logger = logging.getLogger(__name__)


class DuplicateIssueDetector:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.indexer = CodeIndexer(audit_logger)

    async def detect_duplicates(
        self, new_issue_summary: str, current_issue_url: str, workflow_id: str
    ) -> list[dict]:
        """
        Embeds the new issue and queries the database for other open issues that are similar.
        Returns a list of duplicate issue candidates without auto-closing anything.
        """
        query_emb = await self.indexer.get_embedding(new_issue_summary)
        if not query_emb:
            return []

        candidates = []

        # Here we mock retrieving embeddings of other issues.
        # In a real environment, we'd query an `issue_embeddings` table.
        # Let's use the code_indexer's cosine_similarity to compare with existing records.
        async with AsyncSessionLocal() as session:
            # MVP: We assume there's a table `issue_embeddings` storing previously ingested issues.
            # Table schema (url, summary, embedding).
            try:
                result = await session.execute(
                    text(
                        "SELECT url, summary, embedding FROM issue_embeddings "
                        "WHERE url != :current_url"
                    ),
                    {"current_url": current_issue_url},
                )
                rows = result.fetchall()

                for row in rows:
                    if isinstance(row.embedding, str):
                        row_emb = json.loads(row.embedding)
                    else:
                        row_emb = row.embedding

                    score = self.indexer.cosine_similarity(query_emb, row_emb)
                    if score > 0.85:
                        candidates.append(
                            {"url": row.url, "summary": row.summary, "similarity": score}
                        )
            except Exception as e:
                logger.warning(f"issue_embeddings table not available or error: {e}")

        # Sort by similarity descending
        candidates.sort(key=lambda x: x["similarity"], reverse=True)

        if candidates:
            await self.audit.record(
                AuditRecord(
                    action="issue.duplicate_detected",
                    actor="duplicate_detector",
                    status="completed",
                    input_summary=new_issue_summary[:50] + "...",
                    output_summary=f"Found {len(candidates)} potential duplicates",
                    metadata={"workflow_id": workflow_id, "candidates": candidates},
                )
            )

        return candidates
