#!/usr/bin/env bash
# First-time VPS setup for Estronix (Ubuntu 22.04+).
# Run as root: sudo bash deploy/vps/setup-vps.sh
set -euo pipefail

APP_USER="${APP_USER:-estronix}"
APP_DIR="${APP_DIR:-/home/${APP_USER}/ecommerce}"
DOMAIN="${DOMAIN:-}"
REPO_URL="${REPO_URL:-}"
DB_PASSWORD="${DB_PASSWORD:-}"

if [[ "${EUID}" -ne 0 ]]; then
  echo "Run as root: sudo bash deploy/vps/setup-vps.sh"
  exit 1
fi

if [[ -z "${DOMAIN}" ]]; then
  read -r -p "Domain (e.g. estronix.com): " DOMAIN
fi
if [[ -z "${REPO_URL}" ]]; then
  read -r -p "Git repository URL: " REPO_URL
fi
if [[ -z "${DB_PASSWORD}" ]]; then
  read -r -s -p "PostgreSQL password for estronix_user: " DB_PASSWORD
  echo
fi

echo "==> Installing system packages..."
apt-get update
apt-get upgrade -y
apt-get install -y \
  python3 python3-venv python3-pip \
  nginx postgresql postgresql-contrib \
  certbot python3-certbot-nginx \
  git ufw

echo "==> Creating application user..."
if ! id "${APP_USER}" &>/dev/null; then
  adduser --disabled-password --gecos "" "${APP_USER}"
fi
usermod -aG www-data "${APP_USER}"

echo "==> Configuring PostgreSQL..."
sudo -u postgres psql -tc "SELECT 1 FROM pg_roles WHERE rolname='estronix_user'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE USER estronix_user WITH PASSWORD '${DB_PASSWORD}';"
sudo -u postgres psql -tc "SELECT 1 FROM pg_database WHERE datname='estronix_db'" | grep -q 1 \
  || sudo -u postgres psql -c "CREATE DATABASE estronix_db OWNER estronix_user;"

echo "==> Cloning application..."
if [[ ! -d "${APP_DIR}/.git" ]]; then
  sudo -u "${APP_USER}" git clone "${REPO_URL}" "${APP_DIR}"
else
  echo "Repository already exists at ${APP_DIR}, skipping clone."
fi

echo "==> Installing Python dependencies..."
sudo -u "${APP_USER}" bash -lc "
  cd '${APP_DIR}'
  python3 -m venv venv
  source venv/bin/activate
  pip install --upgrade pip
  pip install -r requirements.txt
"

echo "==> Creating environment file..."
if [[ ! -f "${APP_DIR}/.env" ]]; then
  cp "${APP_DIR}/deploy/vps/env.production.example" "${APP_DIR}/.env"
  chown "${APP_USER}:${APP_USER}" "${APP_DIR}/.env"
  chmod 600 "${APP_DIR}/.env"
  sed -i "s|STRONG_DB_PASSWORD|${DB_PASSWORD}|g" "${APP_DIR}/.env"
  sed -i "s|YOUR_DOMAIN|${DOMAIN}|g" "${APP_DIR}/.env"
  echo "Edit ${APP_DIR}/.env with SECRET_KEY, mail, and M-Pesa credentials before going live."
else
  echo ".env already exists, skipping."
fi

echo "==> Preparing upload directory..."
mkdir -p "${APP_DIR}/app/static/uploads"
chown -R "${APP_USER}:www-data" "${APP_DIR}/app/static/uploads"
chmod -R 775 "${APP_DIR}/app/static/uploads"

echo "==> Running database migrations..."
sudo -u "${APP_USER}" bash -lc "
  cd '${APP_DIR}'
  source venv/bin/activate
  export FLASK_APP=run.py
  flask db upgrade
  flask init-db
"

echo "==> Installing systemd service..."
cp "${APP_DIR}/deploy/vps/estronix.service" /etc/systemd/system/estronix.service
systemctl daemon-reload
systemctl enable estronix
systemctl restart estronix

echo "==> Configuring Nginx..."
NGINX_SITE="/etc/nginx/sites-available/estronix"
cp "${APP_DIR}/deploy/vps/nginx-estronix.conf" "${NGINX_SITE}"
sed -i "s/YOUR_DOMAIN/${DOMAIN}/g" "${NGINX_SITE}"
ln -sf "${NGINX_SITE}" /etc/nginx/sites-enabled/estronix
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl restart nginx

echo "==> Configuring firewall..."
ufw allow OpenSSH
ufw allow 'Nginx Full'
ufw --force enable

echo "==> Requesting SSL certificate..."
certbot --nginx -d "${DOMAIN}" -d "www.${DOMAIN}" --non-interactive --agree-tos -m "admin@${DOMAIN}" || {
  echo "Certbot failed. Run manually after DNS points to this server:"
  echo "  sudo certbot --nginx -d ${DOMAIN} -d www.${DOMAIN}"
}

echo
echo "Deployment complete."
echo "  Site:    https://${DOMAIN}"
echo "  Admin:   https://${DOMAIN}/admin"
echo "  Default: admin@estronix.com / Admin@123  (change immediately)"
echo
echo "Next steps:"
echo "  1. Edit ${APP_DIR}/.env with production secrets"
echo "  2. sudo systemctl restart estronix"
echo "  3. Verify M-Pesa callback: https://${DOMAIN}/payments/mpesa/callback"
