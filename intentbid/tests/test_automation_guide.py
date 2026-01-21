from pathlib import Path


def test_readme_has_automation_guide():
    repo_root = Path(__file__).resolve().parents[2]
    readme_path = repo_root / "README.md"

    contents = readme_path.read_text(encoding="utf-8")

    assert "Automation guide for robots and agents" in contents
    assert "list requests" in contents
    assert "submit offers" in contents
    assert "fetch rankings" in contents
    assert "max_offers_per_vendor_rfo" in contents
    assert "offer_cooldown_seconds" in contents
