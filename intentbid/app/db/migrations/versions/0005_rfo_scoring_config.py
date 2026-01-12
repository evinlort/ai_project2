"""Add RFO scoring config

Revision ID: 0005_rfo_scoring_config
Revises: 0004_buyer_api
Create Date: 2024-01-01 00:00:04.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0005_rfo_scoring_config"
down_revision = "0004_buyer_api"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "rfo",
        sa.Column("scoring_version", sa.String(), nullable=False, server_default="v1"),
    )
    op.add_column(
        "rfo",
        sa.Column("weights", sa.JSON(), nullable=False, server_default="{}"),
    )


def downgrade() -> None:
    op.drop_column("rfo", "weights")
    op.drop_column("rfo", "scoring_version")
