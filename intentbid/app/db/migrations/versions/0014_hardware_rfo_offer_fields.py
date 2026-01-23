"""Add hardware RFQ and offer fields

Revision ID: 0014_hardware_rfo_offer_fields
Revises: 0013_part_model
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0014_hardware_rfo_offer_fields"
down_revision = "0013_part_model"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("line_items", sa.JSON(), nullable=True))
    op.add_column("rfo", sa.Column("compliance", sa.JSON(), nullable=True))
    op.add_column("rfo", sa.Column("scoring_profile", sa.String(), nullable=True))

    op.add_column("offer", sa.Column("unit_price", sa.Float(), nullable=True))
    op.add_column("offer", sa.Column("available_qty", sa.Integer(), nullable=True))
    op.add_column("offer", sa.Column("lead_time_days", sa.Integer(), nullable=True))
    op.add_column("offer", sa.Column("shipping_cost", sa.Float(), nullable=True))
    op.add_column("offer", sa.Column("tax_estimate", sa.Float(), nullable=True))
    op.add_column("offer", sa.Column("condition", sa.String(), nullable=True))
    op.add_column("offer", sa.Column("traceability", sa.JSON(), nullable=True))
    op.add_column("offer", sa.Column("valid_until", sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column("offer", "valid_until")
    op.drop_column("offer", "traceability")
    op.drop_column("offer", "condition")
    op.drop_column("offer", "tax_estimate")
    op.drop_column("offer", "shipping_cost")
    op.drop_column("offer", "lead_time_days")
    op.drop_column("offer", "available_qty")
    op.drop_column("offer", "unit_price")

    op.drop_column("rfo", "scoring_profile")
    op.drop_column("rfo", "compliance")
    op.drop_column("rfo", "line_items")
