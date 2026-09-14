"""Add findings table and scan spec metadata

Revision ID: 002
Revises: 001
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("scans", sa.Column("spec_metadata", sa.JSON(), nullable=True))

    op.create_table(
        "findings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("endpoint_id", sa.Integer(), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("owasp_category", sa.String(length=100), nullable=True),
        sa.Column("evidence", sa.Text(), nullable=False),
        sa.Column("remediation", sa.Text(), nullable=False),
        sa.Column("confidence", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["endpoint_id"], ["endpoints.id"]),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_findings_scan_id"), "findings", ["scan_id"], unique=False)
    op.create_index(op.f("ix_findings_endpoint_id"), "findings", ["endpoint_id"], unique=False)
    op.create_index(op.f("ix_findings_severity"), "findings", ["severity"], unique=False)
    op.create_index(op.f("ix_findings_category"), "findings", ["category"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_findings_category"), table_name="findings")
    op.drop_index(op.f("ix_findings_severity"), table_name="findings")
    op.drop_index(op.f("ix_findings_endpoint_id"), table_name="findings")
    op.drop_index(op.f("ix_findings_scan_id"), table_name="findings")
    op.drop_table("findings")
    op.drop_column("scans", "spec_metadata")
