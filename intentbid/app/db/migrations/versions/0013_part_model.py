"""Add part catalog table

Revision ID: 0013_part_model
Revises: 0012_vendor_profile
Create Date: 2026-01-23 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0013_part_model"
down_revision = "0012_vendor_profile"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "part",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("manufacturer", sa.String(), nullable=False),
        sa.Column("mpn", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("key_specs", sa.JSON(), nullable=False),
        sa.Column("aliases", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.UniqueConstraint(
            "manufacturer",
            "mpn",
            name="uq_part_manufacturer_mpn",
        ),
    )
    op.create_index("ix_part_manufacturer", "part", ["manufacturer"])
    op.create_index("ix_part_mpn", "part", ["mpn"])
    op.create_index("ix_part_category", "part", ["category"])


def downgrade() -> None:
    op.drop_index("ix_part_category", table_name="part")
    op.drop_index("ix_part_mpn", table_name="part")
    op.drop_index("ix_part_manufacturer", table_name="part")
    op.drop_table("part")
