#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
repo_root="$(cd "${script_dir}/.." && pwd)"
cd "${repo_root}"

compose_cmd=()
if command -v docker-compose >/dev/null 2>&1; then
  compose_cmd=(docker-compose)
elif command -v docker >/dev/null 2>&1 && docker compose version >/dev/null 2>&1; then
  compose_cmd=(docker compose)
else
  echo "Docker Compose is required but was not found." >&2
  exit 1
fi

wait_for_db() {
  local max_attempts=30
  local attempt=1

  while (( attempt <= max_attempts )); do
    if "${compose_cmd[@]}" exec -T db pg_isready -U intentbid -d intentbid >/dev/null 2>&1; then
      return 0
    fi

    sleep 1
    ((attempt++))
  done

  echo "Database did not become ready after ${max_attempts}s." >&2
  return 1
}

"${compose_cmd[@]}" up --build -d db
wait_for_db
"${compose_cmd[@]}" build api
"${compose_cmd[@]}" run --rm api alembic upgrade head
"${compose_cmd[@]}" up --build api
