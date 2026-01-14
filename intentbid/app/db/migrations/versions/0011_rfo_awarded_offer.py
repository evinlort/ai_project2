"""Track awarded offers

Revision ID: 0011_rfo_awarded_offer
Revises: 0010_rfo_request_backfill
Create Date: 2024-01-01 00:00:10.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0011_rfo_awarded_offer"
down_revision = "0010_rfo_request_backfill"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("rfo", sa.Column("awarded_offer_id", sa.Integer(), nullable=True))
    op.create_index("ix_rfo_awarded_offer_id", "rfo", ["awarded_offer_id"])
    op.create_foreign_key(
        "fk_rfo_awarded_offer_id",
        "rfo",
        "offer",
        ["awarded_offer_id"],
        ["id"],
    )

    op.add_column(
        "offer",
        sa.Column("status", sa.String(), nullable=False, server_default="submitted"),
    )
    op.add_column(
        "offer",
        sa.Column("is_awarded", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.create_index("ix_offer_status", "offer", ["status"])
    op.create_index("ix_offer_is_awarded", "offer", ["is_awarded"])


def downgrade() -> None:
    op.drop_index("ix_offer_is_awarded", table_name="offer")
    op.drop_index("ix_offer_status", table_name="offer")
    op.drop_column("offer", "is_awarded")
    op.drop_column("offer", "status")

    op.drop_constraint("fk_rfo_awarded_offer_id", "rfo", type_="foreignkey")
    op.drop_index("ix_rfo_awarded_offer_id", table_name="rfo")
    op.drop_column("rfo", "awarded_offer_id")
