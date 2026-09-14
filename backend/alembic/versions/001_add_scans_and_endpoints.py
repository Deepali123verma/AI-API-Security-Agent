"""Add scans and endpoints tables

Revision ID: 001
Revises:
Create Date: 2026-03-23

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_filename", sa.String(length=255), nullable=False),
        sa.Column("specification_version", sa.String(length=20), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("version", sa.String(length=50), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_scans_status"), "scans", ["status"], unique=False)
    op.create_index(op.f("ix_scans_user_id"), "scans", ["user_id"], unique=False)

    op.create_table(
        "endpoints",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("scan_id", sa.Integer(), nullable=False),
        sa.Column("path", sa.String(length=512), nullable=False),
        sa.Column("method", sa.String(length=10), nullable=False),
        sa.Column("summary", sa.String(length=512), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("operation_id", sa.String(length=255), nullable=True),
        sa.Column("tags", sa.JSON(), nullable=True),
        sa.Column("parameters", sa.JSON(), nullable=True),
        sa.Column("request_body", sa.JSON(), nullable=True),
        sa.Column("responses", sa.JSON(), nullable=True),
        sa.Column("security_defined", sa.Boolean(), nullable=False),
        sa.Column("security_requirements", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["scan_id"], ["scans.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_endpoints_scan_id"), "endpoints", ["scan_id"], unique=False)
    op.create_index(
        "ix_endpoints_scan_path_method",
        "endpoints",
        ["scan_id", "path", "method"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_endpoints_scan_path_method", table_name="endpoints")
    op.drop_index(op.f("ix_endpoints_scan_id"), table_name="endpoints")
    op.drop_table("endpoints")
    op.drop_index(op.f("ix_scans_user_id"), table_name="scans")
    op.drop_index(op.f("ix_scans_status"), table_name="scans")
    op.drop_table("scans")
