"""initial schema

Revision ID: 20260601_0001
Revises:
Create Date: 2026-06-01
"""

from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision: str = "20260601_0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("action", sa.String(length=120), nullable=False),
        sa.Column("actor", sa.String(length=120), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("provider", sa.String(length=80), nullable=True),
        sa.Column("model", sa.String(length=160), nullable=True),
        sa.Column("prompt_hash", sa.String(length=64), nullable=True),
        sa.Column("approval_id", sa.String(length=80), nullable=True),
        sa.Column("input_summary", sa.Text(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("event_metadata", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_events_action", "audit_events", ["action"])
    op.create_index("ix_audit_events_created_at", "audit_events", ["created_at"])

    op.create_table(
        "workflow_runs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("issue_url", sa.Text(), nullable=False),
        sa.Column("repository_path", sa.Text(), nullable=True),
        sa.Column("mode", sa.String(length=40), nullable=False),
        sa.Column("stage", sa.String(length=80), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("plan_approval_status", sa.String(length=40), nullable=False),
        sa.Column("final_approval_status", sa.String(length=40), nullable=False),
        sa.Column("repository", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("difficulty", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("mentor", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("plan", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("consensus", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("audit_events", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("review_report", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "repository_clone_jobs",
        sa.Column("id", postgresql.UUID(as_uuid=False), primary_key=True),
        sa.Column("workflow_id", postgresql.UUID(as_uuid=False), nullable=False),
        sa.Column("repository_url", sa.Text(), nullable=False),
        sa.Column("target_path", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=40), nullable=False),
        sa.Column("approved_by", sa.String(length=120), nullable=False),
        sa.Column("stdout", sa.Text(), nullable=True),
        sa.Column("stderr", sa.Text(), nullable=True),
        sa.Column("exit_code", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(["workflow_id"], ["workflow_runs.id"], ondelete="CASCADE"),
    )
    op.create_index(
        "ix_repository_clone_jobs_workflow_id",
        "repository_clone_jobs",
        ["workflow_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_repository_clone_jobs_workflow_id", table_name="repository_clone_jobs")
    op.drop_table("repository_clone_jobs")
    op.drop_table("workflow_runs")
    op.drop_index("ix_audit_events_created_at", table_name="audit_events")
    op.drop_index("ix_audit_events_action", table_name="audit_events")
    op.drop_table("audit_events")
