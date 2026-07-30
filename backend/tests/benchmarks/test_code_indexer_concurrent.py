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

    for i in range(20):
        d = repo_path / f"dir_{i}"
        d.mkdir()
        for j in range(50):
            f = d / f"file_{j}.py"
            # create larger files to trigger more I/O and processing
            f.write_text("def test():\n    pass\n" * 100, encoding='utf-8')

    return repo_path

@pytest.mark.asyncio
async def test_indexer_perf(mock_repo):
    class DummyAudit:
        async def record(self, *args, **kwargs):
            pass

    indexer = CodeIndexer(DummyAudit())

    # Run once to warm up
    await indexer.index_repo(mock_repo, uuid.uuid4())

    # Measure event loop blocking
    async def loop_monitor():
        delays = []
        # monitor for a long time
        for _ in range(500):
            start = time.perf_counter()
            await asyncio.sleep(0.01)
            delays.append(time.perf_counter() - start - 0.01)
        return max(delays)

    start = time.perf_counter()
    monitor_task = asyncio.create_task(loop_monitor())
    res = await indexer.index_repo(mock_repo, uuid.uuid4())
    max_delay = await monitor_task
    end = time.perf_counter()

    print(f"\nIndexed {res.file_count} files, {res.chunk_count} chunks in {end - start:.4f} seconds")
    print(f"Max event loop delay: {max_delay:.4f} seconds")
