from pathlib import Path


def test_readme_has_aggregator_overview():
    repo_root = Path(__file__).resolve().parents[2]
    readme_path = repo_root / "README.md"

    contents = readme_path.read_text(encoding="utf-8")

    assert "Aggregator overview" in contents
    assert "Buyer request = RFO" in contents
    assert "Vendor offer = Offer" in contents
    assert (
        "Buyer posts a request -> vendors submit offers -> ranking returns the best offers."
        in contents
    )
    assert "UI calls the same API endpoints used by automation." in contents
