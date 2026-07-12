#!/usr/bin/env bash
# Fix Nginx proxy port and enable domain + IP access on port 80.
# Run on VPS: sudo bash scripts/fix_site_access.sh

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

if [[ ! -f .env ]]; then
  echo "Missing .env" >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT}/scripts/load_dotenv.sh"
load_dotenv .env

: "${DOMAIN:?DOMAIN is required in .env}"
APP_PORT="${APP_PORT:-5060}"
SERVER_IP="${SERVER_IP:-}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo: sudo bash scripts/fix_site_access.sh" >&2
  exit 1
fi

if ! command -v nginx >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y nginx
fi

NGINX_SITE="/etc/nginx/sites-available/${DOMAIN}"
DEFAULT_SITE="/etc/nginx/sites-available/estronix-default"

echo "==> Writing Nginx site: ${DOMAIN} -> 127.0.0.1:${APP_PORT}"
cat > "${NGINX_SITE}" <<NGINX
server {
    listen 80;
    listen [::]:80;
    server_name ${DOMAIN} www.${DOMAIN};

    client_max_body_size 64M;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;

        add_header X-Frame-Options "DENY" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header Referrer-Policy "strict-origin-when-cross-origin" always;
        add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
    }
}
NGINX

echo "==> Writing default site for bare IP access on port 80"
cat > "${DEFAULT_SITE}" <<NGINX
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;

    client_max_body_size 64M;

    location / {
        proxy_pass http://127.0.0.1:${APP_PORT};
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

ln -sf "${NGINX_SITE}" "/etc/nginx/sites-enabled/${DOMAIN}"
ln -sf "${DEFAULT_SITE}" "/etc/nginx/sites-enabled/estronix-default"
rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable nginx
systemctl restart nginx

echo ""
echo "==> Checking app on 127.0.0.1:${APP_PORT}..."
if curl -fsS "http://127.0.0.1:${APP_PORT}/" >/dev/null 2>&1; then
  echo "App responds on port ${APP_PORT}."
else
  echo "WARNING: App NOT responding on 127.0.0.1:${APP_PORT}" >&2
  echo "  Check: docker compose ps && docker compose logs --tail=30 web" >&2
  echo "  Ensure .env APP_PORT matches docker (currently ${APP_PORT})." >&2
fi

echo ""
echo "==> Firewall (allow HTTP/HTTPS only)..."
ufw allow OpenSSH || true
ufw allow 'Nginx Full' || true
ufw --force enable || true

echo ""
echo "Done."
echo "  Domain : http://${DOMAIN}"
echo "  IP     : http://$(curl -4 -s ifconfig.me 2>/dev/null || echo 'YOUR_VPS_IP')/"
echo ""
echo "Do NOT use :${APP_PORT} in the browser — that port is internal."
echo "HTTPS    : sudo INSTALL_SSL=true bash mypostgresql.sh"
