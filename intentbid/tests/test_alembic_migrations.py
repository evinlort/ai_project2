from pathlib import Path

from alembic import command
from alembic.config import Config

from intentbid.app.core.config import settings


def _make_alembic_config(db_url: str) -> Config:
    config = Config("alembic.ini")
    config.set_main_option("script_location", "intentbid/app/db/migrations")
    config.set_main_option("sqlalchemy.url", db_url)
    return config


def test_alembic_upgrade_and_downgrade(tmp_path, monkeypatch):
    db_path = tmp_path / "intentbid_test.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setattr(settings, "database_url", db_url)

    config = _make_alembic_config(db_url)
    command.upgrade(config, "head")

    assert db_path.exists()

    command.downgrade(config, "base")


def test_alembic_offline_upgrade_generates_sql(tmp_path, monkeypatch, capsys):
    db_path = tmp_path / "intentbid_offline.db"
    db_url = f"sqlite:///{db_path}"
    monkeypatch.setattr(settings, "database_url", db_url)

    config = _make_alembic_config(db_url)
    command.upgrade(config, "0007_billing_limits", sql=True)

    captured = capsys.readouterr()
    assert "CREATE TABLE" in captured.out.upper()
