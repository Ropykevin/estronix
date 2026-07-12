#!/usr/bin/env bash
# Open APP_PORT in UFW so the app is reachable at http://IP:5060/
# Run on VPS: sudo bash scripts/expose_app_port.sh

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

# shellcheck disable=SC1091
source "${ROOT}/scripts/load_dotenv.sh"
load_dotenv .env

APP_PORT="${APP_PORT:-5060}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/expose_app_port.sh" >&2
  exit 1
fi

ufw allow "${APP_PORT}/tcp"
ufw status

PUBLIC_IP="$(curl -4 -s ifconfig.me 2>/dev/null || hostname -I | awk '{print $1}')"
echo ""
echo "Port ${APP_PORT} opened in UFW."
echo "Test: http://${PUBLIC_IP}:${APP_PORT}/"
echo ""
echo "Also open port ${APP_PORT} in your VPS provider control panel if traffic still fails."
