from pathlib import Path


def test_compose_api_build_uses_host_network():
    repo_root = Path(__file__).resolve().parents[2]
    compose_path = repo_root / "docker-compose.yml"

    contents = compose_path.read_text(encoding="utf-8")
    lines = contents.splitlines()

    api_index = next(i for i, line in enumerate(lines) if line.strip() == "api:")
    api_block = []
    for line in lines[api_index + 1 :]:
        if line.startswith("  ") and not line.startswith("    "):
            break
        if line and not line.startswith(" "):
            break
        api_block.append(line)

    assert any(line.strip() == "network: host" for line in api_block)
