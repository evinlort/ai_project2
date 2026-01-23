"""Add quote deadline hours to RFO

Revision ID: 0016_rfo_quote_deadline
Revises: 0015_vendor_verification_reputation
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0016_rfo_quote_deadline"
down_revision = "0015_vendor_verification_reputation"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("quote_deadline_hours", sa.Integer(), nullable=True))
    op.create_index(
        "ix_rfo_quote_deadline_hours",
        "rfo",
        ["quote_deadline_hours"],
    )


def downgrade() -> None:
    op.drop_index("ix_rfo_quote_deadline_hours", table_name="rfo")
    op.drop_column("rfo", "quote_deadline_hours")
