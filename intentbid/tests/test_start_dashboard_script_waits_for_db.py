from pathlib import Path


def test_start_dashboard_script_waits_for_db():
    repo_root = Path(__file__).resolve().parents[2]
    script_path = repo_root / "scripts" / "start_dashboard.sh"

    contents = script_path.read_text(encoding="utf-8")

    assert "wait_for_db" in contents
    assert "pg_isready" in contents
