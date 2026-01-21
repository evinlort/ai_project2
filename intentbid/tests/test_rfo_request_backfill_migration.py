import importlib
from unittest.mock import MagicMock, patch


def test_postgres_backfill_uses_text_extraction_checks():
    migration = importlib.import_module(
        "intentbid.app.db.migrations.versions.0010_rfo_request_backfill"
    )
    executed = []
    op = MagicMock()
    op.execute.side_effect = executed.append

    with patch.object(migration, "op", op):
        migration._backfill_postgres()

    assert any(
        "constraints->>'budget_max' IS NOT NULL" in statement
        for statement in executed
    )
    assert any(
        "constraints->>'delivery_deadline_days' IS NOT NULL" in statement
        for statement in executed
    )
    assert all("constraints ?" not in statement for statement in executed)
