"""Add vendor profile storage

Revision ID: 0012_vendor_profile
Revises: 0011_rfo_awarded_offer
Create Date: 2024-01-01 00:00:11.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0012_vendor_profile"
down_revision = "0011_rfo_awarded_offer"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_profile",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("categories", sa.JSON(), nullable=False),
        sa.Column("regions", sa.JSON(), nullable=False),
        sa.Column("lead_time_days", sa.Integer(), nullable=True),
        sa.Column("min_order_value", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_vendor_profile_vendor_id", "vendor_profile", ["vendor_id"])
    op.create_index(
        "ix_vendor_profile_lead_time_days",
        "vendor_profile",
        ["lead_time_days"],
    )
    op.create_index(
        "ix_vendor_profile_min_order_value",
        "vendor_profile",
        ["min_order_value"],
    )


def downgrade() -> None:
    op.drop_index("ix_vendor_profile_min_order_value", table_name="vendor_profile")
    op.drop_index("ix_vendor_profile_lead_time_days", table_name="vendor_profile")
    op.drop_index("ix_vendor_profile_vendor_id", table_name="vendor_profile")
    op.drop_table("vendor_profile")
