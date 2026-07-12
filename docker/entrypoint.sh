#!/bin/sh
set -e

export FLASK_APP=run.py
export FLASK_ENV="${FLASK_ENV:-production}"

echo "==> Running database migrations..."
flask db upgrade

echo "==> Starting Gunicorn on port ${PORT:-5060}..."
exec gunicorn \
  --bind "0.0.0.0:${PORT:-5060}" \
  --workers "${WEB_CONCURRENCY:-2}" \
  --threads "${GUNICORN_THREADS:-2}" \
  --timeout "${GUNICORN_TIMEOUT:-120}" \
  --access-logfile - \
  --error-logfile - \
  wsgi:app
