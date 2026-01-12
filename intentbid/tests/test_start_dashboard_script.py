from pathlib import Path


def test_start_dashboard_script_contains_expected_commands():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "start_dashboard.sh"

    assert script_path.exists()

    contents = script_path.read_text(encoding="utf-8")

    assert "alembic upgrade head" in contents
    assert "up --build -d db" in contents
    assert "up --build api" in contents
    assert "docker-compose" in contents or "docker compose" in contents
