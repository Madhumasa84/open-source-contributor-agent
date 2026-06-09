"""add patch columns

Revision ID: 5d1560981896
Revises: 20260601_0001
Create Date: 2026-06-09 12:17:40.557649
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '5d1560981896'
down_revision: str | None = '20260601_0001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('workflow_runs', sa.Column('patch_diff', sa.Text(), nullable=True))
    op.add_column('workflow_runs', sa.Column('patch_iterations', sa.Integer(), nullable=True))
    op.add_column('workflow_runs', sa.Column('patch_test_status', sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column('workflow_runs', 'patch_test_status')
    op.drop_column('workflow_runs', 'patch_iterations')
    op.drop_column('workflow_runs', 'patch_diff')
