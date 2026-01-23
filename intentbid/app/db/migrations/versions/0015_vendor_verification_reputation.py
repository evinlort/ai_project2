"""Add vendor verification and reputation fields

Revision ID: 0015_vendor_verification_reputation
Revises: 0014_hardware_rfo_offer_fields
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0015_vendor_verification_reputation"
down_revision = "0014_hardware_rfo_offer_fields"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "vendor",
        sa.Column(
            "verification_status",
            sa.String(),
            nullable=False,
            server_default="UNVERIFIED",
        ),
    )
    op.add_column("vendor", sa.Column("verification_notes", sa.String(), nullable=True))
    op.add_column("vendor", sa.Column("verified_at", sa.DateTime(), nullable=True))
    op.create_index(
        "ix_vendor_verification_status",
        "vendor",
        ["verification_status"],
    )

    op.add_column(
        "vendor_profile",
        sa.Column("on_time_delivery_rate", sa.Float(), nullable=True),
    )
    op.add_column("vendor_profile", sa.Column("dispute_rate", sa.Float(), nullable=True))
    op.add_column(
        "vendor_profile",
        sa.Column(
            "verified_distributor",
            sa.Boolean(),
            nullable=False,
            server_default=sa.false(),
        ),
    )


def downgrade() -> None:
    op.drop_column("vendor_profile", "verified_distributor")
    op.drop_column("vendor_profile", "dispute_rate")
    op.drop_column("vendor_profile", "on_time_delivery_rate")

    op.drop_index("ix_vendor_verification_status", table_name="vendor")
    op.drop_column("vendor", "verified_at")
    op.drop_column("vendor", "verification_notes")
    op.drop_column("vendor", "verification_status")
