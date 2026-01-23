"""Add buyer subscription and usage tables

Revision ID: 0019_buyer_billing
Revises: 0018_idempotency_keys
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0019_buyer_billing"
down_revision = "0018_idempotency_keys"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("plan_limit", sa.Column("max_rfos_per_month", sa.Integer(), nullable=True))
    op.add_column("plan_limit", sa.Column("max_awards_per_month", sa.Integer(), nullable=True))

    op.create_table(
        "buyer_subscription",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["buyer_id"], ["buyer.id"]),
    )
    op.create_index("ix_buyer_subscription_buyer_id", "buyer_subscription", ["buyer_id"])
    op.create_index("ix_buyer_subscription_status", "buyer_subscription", ["status"])

    op.create_table(
        "buyer_usage_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["buyer_id"], ["buyer.id"]),
    )
    op.create_index("ix_buyer_usage_event_buyer_id", "buyer_usage_event", ["buyer_id"])


def downgrade() -> None:
    op.drop_index("ix_buyer_usage_event_buyer_id", table_name="buyer_usage_event")
    op.drop_table("buyer_usage_event")

    op.drop_index("ix_buyer_subscription_status", table_name="buyer_subscription")
    op.drop_index("ix_buyer_subscription_buyer_id", table_name="buyer_subscription")
    op.drop_table("buyer_subscription")

    op.drop_column("plan_limit", "max_awards_per_month")
    op.drop_column("plan_limit", "max_rfos_per_month")
