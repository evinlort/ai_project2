#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "${repo_root}"

compose_cmd=(docker-compose)
if ! command -v docker-compose >/dev/null 2>&1; then
  compose_cmd=(docker compose)
fi

"${compose_cmd[@]}" up --build -d db
"${compose_cmd[@]}" build api
"${compose_cmd[@]}" run --rm api alembic upgrade head
"${compose_cmd[@]}" up --build api
