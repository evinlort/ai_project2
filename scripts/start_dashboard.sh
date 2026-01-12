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

run_migrations() {
  local output

  if ! output=$("${compose_cmd[@]}" run --rm api alembic upgrade head 2>&1); then
    if echo "$output" | grep -qi "DuplicateTable\\|already exists"; then
      printf '%s\n' "$output"
      printf '%s\n' "Existing schema detected; stamping Alembic head." >&2
      "${compose_cmd[@]}" run --rm api alembic stamp head
      return 0
    fi

    printf '%s\n' "$output" >&2
    return 1
  fi

  printf '%s\n' "$output"
}

"${compose_cmd[@]}" up --build -d db
wait_for_db
"${compose_cmd[@]}" build api
run_migrations
"${compose_cmd[@]}" up --build api
