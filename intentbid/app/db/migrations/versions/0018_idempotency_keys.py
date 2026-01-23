"""Add idempotency keys table

Revision ID: 0018_idempotency_keys
Revises: 0017_offer_revisions
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0018_idempotency_keys"
down_revision = "0017_offer_revisions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "idempotency_key",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("key", sa.String(), nullable=False),
        sa.Column("endpoint", sa.String(), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("response_body", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint("key", "endpoint", name="uq_idempotency_key_endpoint"),
    )
    op.create_index("ix_idempotency_key_key", "idempotency_key", ["key"])
    op.create_index("ix_idempotency_key_endpoint", "idempotency_key", ["endpoint"])


def downgrade() -> None:
    op.drop_index("ix_idempotency_key_endpoint", table_name="idempotency_key")
    op.drop_index("ix_idempotency_key_key", table_name="idempotency_key")
    op.drop_table("idempotency_key")
