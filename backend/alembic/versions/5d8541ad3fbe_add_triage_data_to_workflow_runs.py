"""add triage data to workflow runs

Revision ID: 5d8541ad3fbe
Revises: 95d9fc2f18c2
Create Date: 2026-06-09 12:32:18.835399
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '5d8541ad3fbe'
down_revision: str | None = '95d9fc2f18c2'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('workflow_runs', sa.Column('triage_data', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('workflow_runs', 'triage_data')
