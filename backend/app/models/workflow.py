from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WorkflowRun(Base):
    __tablename__ = "workflow_runs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    issue_url: Mapped[str] = mapped_column(Text)
    repository_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    mode: Mapped[str] = mapped_column(String(40), default="learn")
    stage: Mapped[str] = mapped_column(String(80), default="created")
    status: Mapped[str] = mapped_column(String(40), default="pending")
    plan_approval_status: Mapped[str] = mapped_column(String(40), default="pending")
    final_approval_status: Mapped[str] = mapped_column(String(40), default="pending")
    repository: Mapped[dict] = mapped_column(JSONB, default=dict)
    difficulty: Mapped[dict] = mapped_column(JSONB, default=dict)
    mentor: Mapped[dict] = mapped_column(JSONB, default=dict)
    plan: Mapped[dict] = mapped_column(JSONB, default=dict)
    consensus: Mapped[dict] = mapped_column(JSONB, default=dict)
    audit_events: Mapped[list] = mapped_column(JSONB, default=list)
    review_report: Mapped[dict] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )


class RepositoryCloneJob(Base):
    __tablename__ = "repository_clone_jobs"

    id: Mapped[str] = mapped_column(
        UUID(as_uuid=False), primary_key=True, default=lambda: str(uuid4())
    )
    workflow_id: Mapped[str] = mapped_column(
        UUID(as_uuid=False),
        ForeignKey("workflow_runs.id", ondelete="CASCADE"),
        index=True,
    )
    repository_url: Mapped[str] = mapped_column(Text)
    target_path: Mapped[str] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(40), default="pending")
    approved_by: Mapped[str] = mapped_column(String(120))
    stdout: Mapped[str | None] = mapped_column(Text, nullable=True)
    stderr: Mapped[str | None] = mapped_column(Text, nullable=True)
    exit_code: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC)
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
    )
