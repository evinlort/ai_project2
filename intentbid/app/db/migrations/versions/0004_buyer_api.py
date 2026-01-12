"""Add buyer API keys

Revision ID: 0004_buyer_api
Revises: 0003_rfo_audit_log
Create Date: 2024-01-01 00:00:03.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0004_buyer_api"
down_revision = "0003_rfo_audit_log"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "buyer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "buyer_api_key",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("buyer_id", sa.Integer(), nullable=False),
        sa.Column("hashed_key", sa.String(), nullable=False, unique=True),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("last_used_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("revoked_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["buyer_id"], ["buyer.id"]),
    )
    op.create_index("ix_buyer_api_key_buyer_id", "buyer_api_key", ["buyer_id"])
    op.create_index("ix_buyer_api_key_hashed_key", "buyer_api_key", ["hashed_key"])
    op.create_index("ix_buyer_api_key_status", "buyer_api_key", ["status"])


def downgrade() -> None:
    op.drop_index("ix_buyer_api_key_status", table_name="buyer_api_key")
    op.drop_index("ix_buyer_api_key_hashed_key", table_name="buyer_api_key")
    op.drop_index("ix_buyer_api_key_buyer_id", table_name="buyer_api_key")
    op.drop_table("buyer_api_key")
    op.drop_table("buyer")
