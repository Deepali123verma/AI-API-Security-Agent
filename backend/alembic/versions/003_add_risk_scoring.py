"""Add risk scoring fields to findings

Revision ID: 003
Revises: 002
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("findings", sa.Column("structured_evidence", sa.JSON(), nullable=True))
    op.add_column(
        "findings",
        sa.Column("risk_score", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "findings",
        sa.Column("risk_level", sa.String(length=20), nullable=False, server_default="INFO"),
    )
    op.add_column("findings", sa.Column("risk_factors", sa.JSON(), nullable=True))
    op.create_index(op.f("ix_findings_risk_level"), "findings", ["risk_level"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_findings_risk_level"), table_name="findings")
    op.drop_column("findings", "risk_factors")
    op.drop_column("findings", "risk_level")
    op.drop_column("findings", "risk_score")
    op.drop_column("findings", "structured_evidence")
