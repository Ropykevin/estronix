#!/usr/bin/env bash
# One-time VPS setup: PostgreSQL + host Nginx reverse proxy (+ optional SSL).
#
# Usage:
#   cp .env.example .env && nano .env   # set POSTGRES_USER=estronix, POSTGRES_PASSWORD
#   sudo bash mypostgresql.sh
#   sudo INSTALL_SSL=true bash mypostgresql.sh
#
# Then set DATABASE_URL in .env (or run: python3 scripts/print_database_url.py)

if [ -z "${BASH_VERSION:-}" ]; then
  exec bash "$0" "$@"
fi

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "${ROOT}"

if [[ ! -f .env ]]; then
  echo "Missing .env — copy from .env.example and edit values first." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${ROOT}/scripts/load_dotenv.sh"
load_dotenv .env

: "${POSTGRES_DB:?POSTGRES_DB is required in .env}"
: "${POSTGRES_USER:?POSTGRES_USER is required in .env}"
: "${POSTGRES_PASSWORD:?POSTGRES_PASSWORD is required in .env}"
: "${DOMAIN:?DOMAIN is required in .env}"

POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
APP_PORT="${APP_PORT:-5060}"
EMAIL="${CERTBOT_EMAIL:-${EMAIL:-${COMPANY_EMAIL:-admin@example.com}}}"
NGINX_CONF="/etc/nginx/sites-available/${DOMAIN}"
ESCAPED_PASS="${POSTGRES_PASSWORD//\'/\'\'}"

if [[ "${EUID:-$(id -u)}" -ne 0 ]]; then
  echo "Run with sudo: sudo bash mypostgresql.sh" >&2
  exit 1
fi

echo "==> Ensuring PostgreSQL is installed..."
export DEBIAN_FRONTEND=noninteractive
if ! command -v psql >/dev/null 2>&1; then
  apt-get update -qq
  apt-get install -y postgresql postgresql-contrib
fi
systemctl enable postgresql
systemctl start postgresql

PG_CONF="$(find /etc/postgresql -name postgresql.conf 2>/dev/null | head -1)"
PG_HBA="$(find /etc/postgresql -name pg_hba.conf 2>/dev/null | head -1)"

if [[ -n "${PG_CONF}" ]]; then
  echo "==> Configuring PostgreSQL to accept Docker connections..."
  sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/" "${PG_CONF}" || true
  if ! grep -q "^listen_addresses = '\*'" "${PG_CONF}"; then
    echo "listen_addresses = '*'" >> "${PG_CONF}"
  fi
fi

if [[ -n "${PG_HBA}" ]]; then
  if ! grep -q "# estronix docker" "${PG_HBA}"; then
    cat >> "${PG_HBA}" <<'HBA'

# estronix docker
host    all             all             172.16.0.0/12           scram-sha-256
host    all             all             172.17.0.0/16           scram-sha-256
HBA
  fi
fi

systemctl restart postgresql

echo "==> Creating role '${POSTGRES_USER}' and database '${POSTGRES_DB}'..."
sudo -u postgres psql -v ON_ERROR_STOP=1 <<SQL
DO \$\$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
    CREATE ROLE ${POSTGRES_USER} LOGIN PASSWORD '${ESCAPED_PASS}';
  ELSE
    ALTER ROLE ${POSTGRES_USER} WITH LOGIN PASSWORD '${ESCAPED_PASS}';
  END IF;
END
\$\$;

SELECT 'CREATE DATABASE ${POSTGRES_DB} OWNER ${POSTGRES_USER}'
WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '${POSTGRES_DB}')\gexec

ALTER DATABASE ${POSTGRES_DB} OWNER TO ${POSTGRES_USER};
GRANT ALL PRIVILEGES ON DATABASE ${POSTGRES_DB} TO ${POSTGRES_USER};
SQL

sudo -u postgres psql -v ON_ERROR_STOP=1 -d "${POSTGRES_DB}" <<SQL
GRANT ALL ON SCHEMA public TO ${POSTGRES_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_USER};
SQL

echo "==> Testing login as ${POSTGRES_USER}..."
PGPASSWORD="${POSTGRES_PASSWORD}" psql -h 127.0.0.1 -U "${POSTGRES_USER}" -d "${POSTGRES_DB}" -c "SELECT 1;" >/dev/null

echo "==> Writing Nginx site config for ${DOMAIN} -> 127.0.0.1:${APP_PORT}..."
cat > "${NGINX_CONF}" <<NGINX
server {
    listen 80;
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

ln -sf "${NGINX_CONF}" "/etc/nginx/sites-enabled/${DOMAIN}"
nginx -t
systemctl reload nginx

DB_URL="$(python3 "${ROOT}/scripts/print_database_url.py")"

echo ""
echo "PostgreSQL ready."
echo "  Host     : ${POSTGRES_HOST}:${POSTGRES_PORT}"
echo "  Database : ${POSTGRES_DB}"
echo "  User     : ${POSTGRES_USER}"
echo ""
echo "Set this in .env as DATABASE_URL:"
echo "  ${DB_URL}"
echo ""
echo "Nginx proxy: http://${DOMAIN} -> http://127.0.0.1:${APP_PORT}"
echo "Deploy app:  bash deployment.sh"

if [[ "${INSTALL_SSL:-false}" == "true" ]]; then
  echo "==> Installing Let's Encrypt certificate..."
  apt-get install -y certbot python3-certbot-nginx
  certbot --nginx \
    -d "${DOMAIN}" -d "www.${DOMAIN}" \
    --non-interactive --agree-tos -m "${EMAIL}" \
    --redirect
  systemctl reload nginx
  echo "SSL enabled for ${DOMAIN}"
fi

echo ""
echo "Setup complete."
