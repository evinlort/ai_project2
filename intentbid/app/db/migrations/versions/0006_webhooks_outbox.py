"""Add vendor webhooks and outbox

Revision ID: 0006_webhooks_outbox
Revises: 0005_rfo_scoring_config
Create Date: 2024-01-01 00:00:05.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0006_webhooks_outbox"
down_revision = "0005_rfo_scoring_config"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor_webhook",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.String(), nullable=False),
        sa.Column("secret", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("last_delivery_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_vendor_webhook_vendor_id", "vendor_webhook", ["vendor_id"])
    op.create_index("ix_vendor_webhook_is_active", "vendor_webhook", ["is_active"])

    op.create_table(
        "event_outbox",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("payload", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("last_error", sa.String(), nullable=True),
        sa.Column("next_attempt_at", sa.DateTime(), nullable=True),
        sa.Column("delivered_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )
    op.create_index("ix_event_outbox_vendor_id", "event_outbox", ["vendor_id"])
    op.create_index("ix_event_outbox_status", "event_outbox", ["status"])


def downgrade() -> None:
    op.drop_index("ix_event_outbox_status", table_name="event_outbox")
    op.drop_index("ix_event_outbox_vendor_id", table_name="event_outbox")
    op.drop_table("event_outbox")
    op.drop_index("ix_vendor_webhook_is_active", table_name="vendor_webhook")
    op.drop_index("ix_vendor_webhook_vendor_id", table_name="vendor_webhook")
    op.drop_table("vendor_webhook")
