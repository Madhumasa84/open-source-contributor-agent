"""add_issue_embeddings_pgvector

Revision ID: 3b52a123f111
Revises: 2a51976806cf
Create Date: 2026-07-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3b52a123f111'
down_revision = '2a51976806cf'
branch_labels = None
depends_on = None

def upgrade() -> None:
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
        op.execute("ALTER TABLE issue_embeddings ALTER COLUMN embedding TYPE vector(384) USING embedding::text::vector")

def downgrade() -> None:
    bind = op.get_bind()
    if bind.engine.name == 'postgresql':
        op.execute("ALTER TABLE issue_embeddings ALTER COLUMN embedding TYPE VARCHAR USING embedding::text")
