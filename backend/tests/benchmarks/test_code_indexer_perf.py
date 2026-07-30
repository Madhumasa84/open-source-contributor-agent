import pytest
import time
import asyncio
from pathlib import Path
import uuid
import os
from sqlalchemy import text

from app.core.database import AsyncSessionLocal, init_db, engine, Base
from app.services.code_indexer import CodeIndexer
from app.services.audit import AuditLogger

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.execute(text("""
            CREATE TABLE IF NOT EXISTS code_chunks (
                id VARCHAR PRIMARY KEY,
                workflow_id VARCHAR,
                file_path VARCHAR,
                start_line INTEGER,
                end_line INTEGER,
                content TEXT,
                embedding TEXT
            )
        """))
    yield
    async with engine.begin() as conn:
        await conn.execute(text("DROP TABLE IF EXISTS code_chunks"))

@pytest.fixture
def mock_repo(tmp_path):
    repo_path = tmp_path / "mock_repo"
    repo_path.mkdir()

    # 50 dirs x 100 files = 5000 files
    for i in range(50):
        d = repo_path / f"dir_{i}"
        d.mkdir()
        for j in range(100):
            f = d / f"file_{j}.py"
            # 50 lines to create at least 1 chunk
            f.write_text("def test():\n    pass\n" * 25, encoding='utf-8')

    return repo_path

@pytest.mark.asyncio
async def test_indexer_perf(mock_repo):
    class DummyAudit:
        async def record(self, *args, **kwargs):
            pass

    indexer = CodeIndexer(DummyAudit())

    start = time.perf_counter()
    res = await indexer.index_repo(mock_repo, uuid.uuid4())
    end = time.perf_counter()

    print(f"\nIndexed {res.file_count} files, {res.chunk_count} chunks in {end - start:.4f} seconds")
