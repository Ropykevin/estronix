#!/usr/bin/env bash
# Repeatable app deploy — run after: sudo bash scripts/reset_claid_db_user.sh
#
# Usage (on the VPS):
#   bash deployment.sh

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from .env.example first." >&2
  exit 1
fi

command -v docker >/dev/null 2>&1 || { echo "Docker is not installed." >&2; exit 1; }
docker compose version >/dev/null 2>&1 || { echo "Docker Compose plugin is not available." >&2; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required." >&2; exit 1; }

# shellcheck disable=SC1091
source "${ROOT}/scripts/load_dotenv.sh"
load_dotenv .env

echo "==> Pre-flight: testing Postgres on host..."
if ! PGPASSWORD="${POSTGRES_PASSWORD}" psql -h 127.0.0.1 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" >/dev/null 2>&1; then
  echo "ERROR: Cannot log in to Postgres as ${POSTGRES_USER} on 127.0.0.1" >&2
  echo "Fix the database first:" >&2
  echo "  sudo bash scripts/reset_claid_db_user.sh" >&2
  exit 1
fi
echo "Postgres login OK."

echo "==> Pulling latest code..."
if git rev-parse --git-dir >/dev/null 2>&1; then
  git pull origin main 2>/dev/null || git pull origin master 2>/dev/null || echo "Git pull skipped."
fi

echo "==> Syncing DATABASE_URL for Docker..."
python3 scripts/sync_database_url.py

echo "==> Building and starting container (host network, port ${APP_PORT:-5060})..."
docker compose build
docker compose up -d --force-recreate --remove-orphans

echo "==> Waiting for app to start..."
OK=0
for _ in $(seq 1 60); do
  STATUS="$(docker inspect -f '{{.State.Status}}' claid 2>/dev/null || echo missing)"
  if [[ "${STATUS}" == "restarting" ]]; then
    echo "Container is crash-looping. Recent logs:" >&2
    docker compose logs --tail=50 web >&2 || true
    echo "" >&2
    echo "Run: sudo bash scripts/reset_claid_db_user.sh && bash deployment.sh" >&2
    exit 1
  fi
  if curl -fsS "http://127.0.0.1:${APP_PORT:-5060}/" >/dev/null 2>&1; then
    OK=1
    break
  fi
  sleep 2
done

if [[ "${OK}" -ne 1 ]]; then
  echo "App did not respond on port ${APP_PORT:-5060}. Recent logs:" >&2
  docker compose logs --tail=50 web >&2 || true
  exit 1
fi

echo ""
echo "Deploy complete."
docker compose ps
echo ""
echo "  App (local) : http://127.0.0.1:${APP_PORT:-5060}"
echo "  Site        : http://${DOMAIN:-your-domain}"
echo "  Logs        : docker compose logs -f web"

