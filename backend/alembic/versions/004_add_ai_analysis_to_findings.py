"""Add AI analysis fields to findings

Revision ID: 004
Revises: 003
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("ai_summary", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_why_it_matters", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_technical_reasoning", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_validation_guidance", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_remediation", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_priority", sa.String(length=20), nullable=True))
    op.add_column("findings", sa.Column("ai_limitations", sa.Text(), nullable=True))
    op.add_column("findings", sa.Column("ai_model", sa.String(length=100), nullable=True))
    op.add_column("findings", sa.Column("ai_analyzed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("findings", "ai_analyzed_at")
    op.drop_column("findings", "ai_model")
    op.drop_column("findings", "ai_limitations")
    op.drop_column("findings", "ai_priority")
    op.drop_column("findings", "ai_remediation")
    op.drop_column("findings", "ai_validation_guidance")
    op.drop_column("findings", "ai_technical_reasoning")
    op.drop_column("findings", "ai_why_it_matters")
    op.drop_column("findings", "ai_summary")
