"""Backfill RFO request fields from constraints

Revision ID: 0010_rfo_request_backfill
Revises: 0009_rfo_request_fields
Create Date: 2024-01-01 00:00:09.000000

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0010_rfo_request_backfill"
down_revision = "0009_rfo_request_fields"
branch_labels = None
depends_on = None


def _backfill_postgres() -> None:
    op.execute(
        """
        UPDATE rfo
        SET budget_max = (constraints->>'budget_max')::double precision
        WHERE budget_max IS NULL
          AND constraints->>'budget_max' IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE rfo
        SET delivery_deadline_days = (constraints->>'delivery_deadline_days')::integer
        WHERE delivery_deadline_days IS NULL
          AND constraints->>'delivery_deadline_days' IS NOT NULL
        """
    )


def _backfill_sqlite() -> None:
    op.execute(
        """
        UPDATE rfo
        SET budget_max = json_extract(constraints, '$.budget_max')
        WHERE budget_max IS NULL
          AND json_extract(constraints, '$.budget_max') IS NOT NULL
        """
    )
    op.execute(
        """
        UPDATE rfo
        SET delivery_deadline_days = json_extract(constraints, '$.delivery_deadline_days')
        WHERE delivery_deadline_days IS NULL
          AND json_extract(constraints, '$.delivery_deadline_days') IS NOT NULL
        """
    )


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == "postgresql":
        _backfill_postgres()
    elif dialect == "sqlite":
        _backfill_sqlite()


def downgrade() -> None:
    pass
