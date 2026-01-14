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
    op.drop_index("ix_rfo_expires_at", table_name="rfo")
    op.drop_index("ix_rfo_location", table_name="rfo")
    op.drop_index("ix_rfo_quantity", table_name="rfo")
    op.drop_index("ix_rfo_delivery_deadline_days", table_name="rfo")
    op.drop_index("ix_rfo_currency", table_name="rfo")
    op.drop_index("ix_rfo_budget_max", table_name="rfo")
    op.drop_index("ix_rfo_title", table_name="rfo")

    op.drop_column("rfo", "expires_at")
    op.drop_column("rfo", "location")
    op.drop_column("rfo", "quantity")
    op.drop_column("rfo", "delivery_deadline_days")
    op.drop_column("rfo", "currency")
    op.drop_column("rfo", "budget_max")
    op.drop_column("rfo", "summary")
    op.drop_column("rfo", "title")
