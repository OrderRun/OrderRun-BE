#!/usr/bin/env bash
set -euo pipefail

compose_file="${COMPOSE_FILE:-docker-compose.staging.yml}"
compose_profile="${COMPOSE_PROFILE:-staging}"
app_container="${APP_CONTAINER_NAME:-orderrun-app-staging}"
wait_timeout="${WAIT_TIMEOUT_SECONDS:-180}"

if [[ ! -f "$compose_file" ]]; then
  echo "Compose file not found: $compose_file" >&2
  exit 1
fi

wait_for_health() {
  local container="$1"
  local elapsed=0

  while (( elapsed < wait_timeout )); do
    if ! docker inspect "$container" >/dev/null 2>&1; then
      sleep 5
      elapsed=$((elapsed + 5))
      continue
    fi

    status="$(docker inspect -f '{{if .State.Health}}{{.State.Health.Status}}{{else}}{{.State.Status}}{{end}}' "$container" 2>/dev/null || echo "missing")"
    case "$status" in
      healthy|running)
        return 0
        ;;
      unhealthy|exited|dead)
        echo "Container $container reported status: $status" >&2
        return 1
        ;;
    esac

    sleep 5
    elapsed=$((elapsed + 5))
  done

  echo "Timed out waiting for $container to become healthy" >&2
  return 1
}

docker compose -f "$compose_file" --profile "$compose_profile" pull app
docker compose -f "$compose_file" --profile "$compose_profile" up -d --build --remove-orphans

if ! wait_for_health "$app_container"; then
  docker compose -f "$compose_file" --profile "$compose_profile" logs --tail=100 app || true
  exit 1
fi

docker compose -f "$compose_file" --profile "$compose_profile" ps
