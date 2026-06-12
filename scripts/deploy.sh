#!/usr/bin/env bash
set -euo pipefail

compose_file="${COMPOSE_FILE:-docker-compose.staging.yml}"
compose_env_file="${COMPOSE_ENV_FILE:-}"
compose_profile="${COMPOSE_PROFILE:-staging}"
deploy_target="${DEPLOY_TARGET:-}"
app_service="${APP_SERVICE_NAME:-app}"
app_container="${APP_CONTAINER_NAME:-orderrun-app-staging}"
wait_timeout="${WAIT_TIMEOUT_SECONDS:-180}"

if [[ ! -f "$compose_file" ]]; then
  echo "Compose file not found: $compose_file" >&2
  exit 1
fi

case "$deploy_target" in
  "")
    ;;
  staging)
    app_service="${APP_SERVICE_NAME:-app-staging}"
    app_container="${APP_CONTAINER_NAME:-orderrun-app-staging}"
    compose_profile="${COMPOSE_PROFILE:-}"
    ;;
  prod|production)
    app_service="${APP_SERVICE_NAME:-app-prod}"
    app_container="${APP_CONTAINER_NAME:-orderrun-app-prod}"
    compose_profile="${COMPOSE_PROFILE:-}"
    ;;
  *)
    echo "Unsupported DEPLOY_TARGET: $deploy_target. Use prod or staging." >&2
    exit 1
    ;;
esac

compose_cmd=(docker compose)
if [[ -n "$compose_env_file" ]]; then
  compose_cmd+=(--env-file "$compose_env_file")
fi
compose_cmd+=(-f "$compose_file")
if [[ -n "$compose_profile" ]]; then
  compose_cmd+=(--profile "$compose_profile")
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

"${compose_cmd[@]}" pull "$app_service"
if [[ -n "$deploy_target" ]]; then
  "${compose_cmd[@]}" up -d --build --remove-orphans "$app_service"
else
  "${compose_cmd[@]}" up -d --build --remove-orphans
fi

if ! wait_for_health "$app_container"; then
  "${compose_cmd[@]}" logs --tail=100 "$app_service" || true
  exit 1
fi

echo "Running database migrations..."
docker exec "$app_container" alembic upgrade head

"${compose_cmd[@]}" ps
