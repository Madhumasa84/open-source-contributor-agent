import json
import uuid
import logging
from sqlalchemy import text
from app.core.database import AsyncSessionLocal
from app.services.audit import AuditLogger, AuditRecord
from app.services.code_indexer import CodeIndexer

logger = logging.getLogger(__name__)

class IssueIndexer:
    def __init__(self, audit_logger: AuditLogger):
        self.audit = audit_logger
        self.code_indexer = CodeIndexer(audit_logger) # reuse embedding logic

    async def index_issue(self, issue_url: str, title: str, body: str):
        content = f"{title}\n{body}"
        embedding = await self.code_indexer.get_embedding(content)
        if not embedding:
            return

        chunk_id = str(uuid.uuid4())
        
        async with AsyncSessionLocal() as session:
            # Check if exists
            res = await session.execute(
                text("SELECT id FROM issue_embeddings WHERE issue_url = :issue_url"),
                {"issue_url": issue_url}
            )
            if res.fetchone():
                return # Already indexed

            await session.execute(
                text("""
                    INSERT INTO issue_embeddings (id, issue_url, title, body, embedding)
                    VALUES (:id, :issue_url, :title, :body, :embedding)
                """),
                {
                    "id": chunk_id,
                    "issue_url": issue_url,
                    "title": title,
                    "body": body,
                    "embedding": json.dumps(embedding)
                }
            )
            await session.commit()
            
            await self.audit.record(AuditRecord(
                action="issue_indexer.index",
                actor="issue_indexer",
                status="completed",
                input_summary=issue_url,
                output_summary="Indexed issue",
                metadata={"issue_url": issue_url}
            ))

    async def find_duplicates(self, issue_url: str, title: str, body: str, threshold: float = 0.85) -> list[dict]:
        content = f"{title}\n{body}"
        query_emb = await self.code_indexer.get_embedding(content)
        if not query_emb:
            return []

        duplicates = []
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT issue_url, title, embedding FROM issue_embeddings WHERE issue_url != :issue_url"),
                {"issue_url": issue_url}
            )
            rows = result.fetchall()
            
            for row in rows:
                row_emb = json.loads(row.embedding) if isinstance(row.embedding, str) else row.embedding
                score = self.code_indexer.cosine_similarity(query_emb, row_emb)
                if score > threshold:
                    duplicates.append({
                        "issue_url": row.issue_url,
                        "title": row.title,
                        "score": score
                    })
                    
        duplicates.sort(key=lambda x: x["score"], reverse=True)
        return duplicates
