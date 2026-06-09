"""add code chunks table

Revision ID: 95d9fc2f18c2
Revises: 5d1560981896
Create Date: 2026-06-09 12:22:03.100137
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa


revision: str = '95d9fc2f18c2'
down_revision: str | None = '5d1560981896'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    if conn.engine.dialect.name == "postgresql":
        try:
            op.execute("CREATE EXTENSION IF NOT EXISTS vector;")
        except Exception:
            print("NOTICE: Could not create pgvector extension. Falling back.")

    op.create_table(
        'code_chunks',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('workflow_id', sa.String(36), nullable=False, index=True),
        sa.Column('file_path', sa.Text(), nullable=False),
        sa.Column('start_line', sa.Integer(), nullable=False),
        sa.Column('end_line', sa.Integer(), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('embedding', sa.JSON(), nullable=False),
    )

def downgrade() -> None:
    op.drop_table('code_chunks')
