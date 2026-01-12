"""Add vendor API keys

Revision ID: 0002_vendor_api_keys
Revises: 0001_initial
Create Date: 2024-01-01 00:00:01.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0002_vendor_api_keys"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_api_key",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("hashed_key", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_vendor_api_key_vendor_id", "vendor_api_key", ["vendor_id"])
    op.create_index("ix_vendor_api_key_hashed_key", "vendor_api_key", ["hashed_key"])
    op.create_index("ix_vendor_api_key_status", "vendor_api_key", ["status"])


def downgrade() -> None:
    op.drop_index("ix_vendor_api_key_status", table_name="vendor_api_key")
    op.drop_index("ix_vendor_api_key_hashed_key", table_name="vendor_api_key")
    op.drop_index("ix_vendor_api_key_vendor_id", table_name="vendor_api_key")
    op.drop_table("vendor_api_key")
