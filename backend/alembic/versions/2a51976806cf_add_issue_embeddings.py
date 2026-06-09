"""add_issue_embeddings

Revision ID: 2a51976806cf
Revises: d67049aa06b8
Create Date: 2026-06-09 16:06:48.965617
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '2a51976806cf'
down_revision: str | None = 'd67049aa06b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # We will use JSON for sqlite and generic fallback.
    op.create_table(
        'issue_embeddings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('issue_url', sa.String(), index=True),
        sa.Column('title', sa.String()),
        sa.Column('body', sa.Text()),
        sa.Column('embedding', sa.JSON()), # In postgres this could be vector, using JSON for sqlite compatibility
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'))
    )


def downgrade() -> None:
    op.drop_table('issue_embeddings')
