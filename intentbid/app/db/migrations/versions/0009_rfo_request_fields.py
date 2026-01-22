"""Add explicit RFO request fields

Revision ID: 0009_rfo_request_fields
Revises: 0008_rfo_buyer_owner
Create Date: 2024-01-01 00:00:08.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0009_rfo_request_fields"
down_revision = "0008_rfo_buyer_owner"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("title", sa.String(), nullable=True))
    op.add_column("rfo", sa.Column("summary", sa.String(), nullable=True))
    op.add_column("rfo", sa.Column("budget_max", sa.Float(), nullable=True))
    op.add_column("rfo", sa.Column("currency", sa.String(), nullable=True))
    op.add_column("rfo", sa.Column("delivery_deadline_days", sa.Integer(), nullable=True))
    op.add_column("rfo", sa.Column("quantity", sa.Integer(), nullable=True))
    op.add_column("rfo", sa.Column("location", sa.String(), nullable=True))
    op.add_column("rfo", sa.Column("expires_at", sa.DateTime(), nullable=True))

    op.create_index("ix_rfo_title", "rfo", ["title"])
    op.create_index("ix_rfo_budget_max", "rfo", ["budget_max"])
    op.create_index("ix_rfo_currency", "rfo", ["currency"])
    op.create_index("ix_rfo_delivery_deadline_days", "rfo", ["delivery_deadline_days"])
    op.create_index("ix_rfo_quantity", "rfo", ["quantity"])
    op.create_index("ix_rfo_location", "rfo", ["location"])
    op.create_index("ix_rfo_expires_at", "rfo", ["expires_at"])


def downgrade() -> None:
    with op.batch_alter_table("rfo") as batch_op:
        batch_op.drop_index("ix_rfo_expires_at")
        batch_op.drop_index("ix_rfo_location")
        batch_op.drop_index("ix_rfo_quantity")
        batch_op.drop_index("ix_rfo_delivery_deadline_days")
        batch_op.drop_index("ix_rfo_currency")
        batch_op.drop_index("ix_rfo_budget_max")
        batch_op.drop_index("ix_rfo_title")

        batch_op.drop_column("expires_at")
        batch_op.drop_column("location")
        batch_op.drop_column("quantity")
        batch_op.drop_column("delivery_deadline_days")
        batch_op.drop_column("currency")
        batch_op.drop_column("budget_max")
        batch_op.drop_column("summary")
        batch_op.drop_column("title")
