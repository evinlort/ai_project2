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
    with op.batch_alter_table("rfo") as batch_op:
        batch_op.add_column(sa.Column("buyer_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_rfo_buyer_id", ["buyer_id"])
        batch_op.create_foreign_key("fk_rfo_buyer_id", "buyer", ["buyer_id"], ["id"])


def downgrade() -> None:
    with op.batch_alter_table("rfo") as batch_op:
        batch_op.drop_constraint("fk_rfo_buyer_id", type_="foreignkey")
        batch_op.drop_index("ix_rfo_buyer_id")
        batch_op.drop_column("buyer_id")
