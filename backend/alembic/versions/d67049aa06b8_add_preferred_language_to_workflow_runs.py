"""add preferred language to workflow runs

Revision ID: d67049aa06b8
Revises: 5d8541ad3fbe
Create Date: 2026-06-09 12:49:50.721026
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = 'd67049aa06b8'
down_revision: str | None = '5d8541ad3fbe'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('workflow_runs', sa.Column('preferred_language', sa.String(length=8), server_default='en', nullable=False))


def downgrade() -> None:
    op.drop_column('workflow_runs', 'preferred_language')
