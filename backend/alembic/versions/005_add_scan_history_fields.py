"""Add scan history fields

Revision ID: 005
Revises: 004
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "005"
down_revision: Union[str, None] = "004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("overall_risk_score", sa.Integer(), nullable=True))
    op.add_column("scans", sa.Column("overall_risk_level", sa.String(length=20), nullable=True))
    op.add_column(
        "scans",
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=False,
        ),
    )
    op.add_column("scans", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index(op.f("ix_scans_overall_risk_level"), "scans", ["overall_risk_level"], unique=False)

    # Normalize legacy lowercase / parse-complete statuses.
    op.execute("UPDATE scans SET status = UPPER(status)")
    op.execute(
        "UPDATE scans SET status = 'PENDING' "
        "WHERE status IN ('PARSING', 'COMPLETED') "
        "AND NOT EXISTS (SELECT 1 FROM findings WHERE findings.scan_id = scans.id)"
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_scans_overall_risk_level"), table_name="scans")
    op.drop_column("scans", "completed_at")
    op.drop_column("scans", "updated_at")
    op.drop_column("scans", "overall_risk_level")
    op.drop_column("scans", "overall_risk_score")
