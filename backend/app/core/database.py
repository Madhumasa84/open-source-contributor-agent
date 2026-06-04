import socket
from collections.abc import AsyncGenerator
from urllib.parse import urlparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def check_postgres_connection(url: str) -> bool:
    try:
        parsed = urlparse(url)
        host = parsed.hostname or "127.0.0.1"
        port = parsed.port or 5432
        with socket.create_connection((host, port), timeout=1.0):
            return True
    except (socket.error, ValueError):
        return False


settings = get_settings()
db_url = settings.database_url

if db_url.startswith("postgresql") and not check_postgres_connection(db_url):
    db_url = "sqlite+aiosqlite:///osca.db"

engine = create_async_engine(db_url, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    from app.models.workflow import WorkflowRun, RepositoryCloneJob
    from app.models.audit import AuditEvent

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
