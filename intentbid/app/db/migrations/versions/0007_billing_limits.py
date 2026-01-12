"""Add billing limits and usage events

Revision ID: 0007_billing_limits
Revises: 0006_webhooks_outbox
Create Date: 2024-01-01 00:00:06.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0007_billing_limits"
down_revision = "0006_webhooks_outbox"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "plan_limit",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("plan_code", sa.String(), nullable=False),
        sa.Column("max_offers_per_month", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_plan_limit_plan_code", "plan_limit", ["plan_code"])

    op.create_table(
        "subscription",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("plan_code", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("started_at", sa.DateTime(), nullable=False),
        sa.Column("ended_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_subscription_vendor_id", "subscription", ["vendor_id"])
    op.create_index("ix_subscription_status", "subscription", ["status"])

    op.create_table(
        "usage_event",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_usage_event_vendor_id", "usage_event", ["vendor_id"])


def downgrade() -> None:
    op.drop_index("ix_usage_event_vendor_id", table_name="usage_event")
    op.drop_table("usage_event")
    op.drop_index("ix_subscription_status", table_name="subscription")
    op.drop_index("ix_subscription_vendor_id", table_name="subscription")
    op.drop_table("subscription")
    op.drop_index("ix_plan_limit_plan_code", table_name="plan_limit")
    op.drop_table("plan_limit")
