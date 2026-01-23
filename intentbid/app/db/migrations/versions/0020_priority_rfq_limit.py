"""Add priority RFQ plan limit

Revision ID: 0020_priority_rfq_limit
Revises: 0019_buyer_billing
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0020_priority_rfq_limit"
down_revision = "0019_buyer_billing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "plan_limit",
        sa.Column("max_priority_rfos_per_month", sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("plan_limit", "max_priority_rfos_per_month")
