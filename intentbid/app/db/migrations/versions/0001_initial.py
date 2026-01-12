"""Initial tables

Revision ID: 0001_initial
Revises: None
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "vendor",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("api_key_hash", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_table(
        "rfo",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("constraints", sa.JSON(), nullable=False),
        sa.Column("preferences", sa.JSON(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index("ix_rfo_status", "rfo", ["status"])
    op.create_table(
        "offer",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("rfo_id", sa.Integer(), nullable=False),
        sa.Column("vendor_id", sa.Integer(), nullable=False),
        sa.Column("price_amount", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=False),
        sa.Column("delivery_eta_days", sa.Integer(), nullable=False),
        sa.Column("warranty_months", sa.Integer(), nullable=False),
        sa.Column("return_days", sa.Integer(), nullable=False),
        sa.Column("stock", sa.Boolean(), nullable=False),
        sa.Column("metadata", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["rfo_id"], ["rfo.id"]),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendor.id"]),
    )


def downgrade() -> None:
    op.drop_table("offer")
    op.drop_index("ix_rfo_status", table_name="rfo")
    op.drop_table("rfo")
    op.drop_table("vendor")
