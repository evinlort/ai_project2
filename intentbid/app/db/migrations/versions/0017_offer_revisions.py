"""Add offer revisions and versioning

Revision ID: 0017_offer_revisions
Revises: 0016_rfo_quote_deadline
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0017_offer_revisions"
down_revision = "0016_rfo_quote_deadline"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "offer",
        sa.Column(
            "offer_version",
            sa.Integer(),
            nullable=False,
            server_default="1",
        ),
    )
    op.add_column("offer", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_offer_offer_version", "offer", ["offer_version"])

    op.create_table(
        "offer_revision",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("offer_id", sa.Integer(), nullable=False),
        sa.Column("offer_version", sa.Integer(), nullable=False),
        sa.Column("snapshot", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["offer_id"], ["offer.id"]),
    )
    op.create_index("ix_offer_revision_offer_id", "offer_revision", ["offer_id"])


def downgrade() -> None:
    op.drop_index("ix_offer_revision_offer_id", table_name="offer_revision")
    op.drop_table("offer_revision")

    op.drop_index("ix_offer_offer_version", table_name="offer")
    op.drop_column("offer", "updated_at")
    op.drop_column("offer", "offer_version")
