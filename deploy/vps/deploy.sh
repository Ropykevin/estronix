#!/usr/bin/env bash
# Pull latest code and restart the app on the VPS.
# Run as the estronix user: bash deploy/vps/deploy.sh
set -euo pipefail

APP_DIR="${APP_DIR:-/home/estronix/ecommerce}"
BRANCH="${BRANCH:-main}"

cd "${APP_DIR}"

echo "==> Pulling latest code (${BRANCH})..."
git fetch origin
git checkout "${BRANCH}"
git pull origin "${BRANCH}"

echo "==> Installing dependencies..."
source venv/bin/activate
pip install -r requirements.txt

echo "==> Running migrations..."
export FLASK_APP=run.py
flask db upgrade

echo "==> Restarting application..."
sudo systemctl restart estronix

echo "==> Status:"
sudo systemctl --no-pager status estronix

echo "Deploy finished."
