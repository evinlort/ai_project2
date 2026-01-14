"""Add buyer ownership to RFO

Revision ID: 0008_rfo_buyer_owner
Revises: 0007_billing_limits
Create Date: 2024-01-01 00:00:07.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0008_rfo_buyer_owner"
down_revision = "0007_billing_limits"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("buyer_id", sa.Integer(), nullable=True))
    op.create_index("ix_rfo_buyer_id", "rfo", ["buyer_id"])
    op.create_foreign_key("fk_rfo_buyer_id", "rfo", "buyer", ["buyer_id"], ["id"])


def downgrade() -> None:
    op.drop_constraint("fk_rfo_buyer_id", "rfo", type_="foreignkey")
    op.drop_index("ix_rfo_buyer_id", table_name="rfo")
    op.drop_column("rfo", "buyer_id")
