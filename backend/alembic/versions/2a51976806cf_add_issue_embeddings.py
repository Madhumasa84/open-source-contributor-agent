"""add_issue_embeddings

Revision ID: 2a51976806cf
Revises: d67049aa06b8
Create Date: 2026-07-30 00:00:00.000000

"""

import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = "2a51976806cf"
down_revision = "d67049aa06b8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # MVP mock table creation for issue_embeddings
    op.create_table(
        "issue_embeddings",
        sa.Column("url", sa.String(), primary_key=True),
        sa.Column("summary", sa.String(), nullable=False),
        sa.Column("embedding", sa.String(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("issue_embeddings")
