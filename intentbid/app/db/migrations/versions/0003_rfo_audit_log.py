"""Add RFO audit log and status reason

Revision ID: 0003_rfo_audit_log
Revises: 0002_vendor_api_keys
Create Date: 2024-01-01 00:00:02.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0003_rfo_audit_log"
down_revision = "0002_vendor_api_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("status_reason", sa.String(), nullable=True))
    op.create_table(
        "audit_log",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("entity_type", sa.String(), nullable=False),
        sa.Column("entity_id", sa.Integer(), nullable=False),
        sa.Column("action", sa.String(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_audit_log_entity_type", "audit_log", ["entity_type"])
    op.create_index("ix_audit_log_entity_id", "audit_log", ["entity_id"])


def downgrade() -> None:
    op.drop_index("ix_audit_log_entity_id", table_name="audit_log")
    op.drop_index("ix_audit_log_entity_type", table_name="audit_log")
    op.drop_table("audit_log")
    op.drop_column("rfo", "status_reason")
