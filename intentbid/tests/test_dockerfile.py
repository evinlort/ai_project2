from pathlib import Path


def test_dockerfile_copies_alembic_ini():
    repo_root = Path(__file__).resolve().parents[2]
    dockerfile_path = repo_root / "Dockerfile"

    contents = dockerfile_path.read_text(encoding="utf-8").splitlines()

    has_copy = any(
        line.strip().startswith("COPY") and "alembic.ini" in line
        for line in contents
    )

    assert has_copy
