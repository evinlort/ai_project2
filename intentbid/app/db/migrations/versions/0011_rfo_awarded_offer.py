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
    with op.batch_alter_table("rfo") as batch_op:
        batch_op.add_column(sa.Column("awarded_offer_id", sa.Integer(), nullable=True))
        batch_op.create_index("ix_rfo_awarded_offer_id", ["awarded_offer_id"])
        batch_op.create_foreign_key(
            "fk_rfo_awarded_offer_id",
            "offer",
            ["awarded_offer_id"],
            ["id"],
        )

    with op.batch_alter_table("offer") as batch_op:
        batch_op.add_column(
            sa.Column("status", sa.String(), nullable=False, server_default="submitted"),
        )
        batch_op.add_column(
            sa.Column(
                "is_awarded",
                sa.Boolean(),
                nullable=False,
                server_default=sa.false(),
            ),
        )
        batch_op.create_index("ix_offer_status", ["status"])
        batch_op.create_index("ix_offer_is_awarded", ["is_awarded"])


def downgrade() -> None:
    with op.batch_alter_table("offer") as batch_op:
        batch_op.drop_index("ix_offer_is_awarded")
        batch_op.drop_index("ix_offer_status")
        batch_op.drop_column("is_awarded")
        batch_op.drop_column("status")

    with op.batch_alter_table("rfo") as batch_op:
        batch_op.drop_constraint("fk_rfo_awarded_offer_id", type_="foreignkey")
        batch_op.drop_index("ix_rfo_awarded_offer_id")
        batch_op.drop_column("awarded_offer_id")
