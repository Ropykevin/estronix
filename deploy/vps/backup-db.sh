#!/usr/bin/env bash
# Daily PostgreSQL backup (add to cron).
# Example cron (as root): 0 2 * * * /home/estronix/ecommerce/deploy/vps/backup-db.sh
set -euo pipefail

BACKUP_DIR="${BACKUP_DIR:-/home/estronix/backups}"
DB_NAME="${DB_NAME:-estronix_db}"
DB_USER="${DB_USER:-estronix_user}"
RETAIN_DAYS="${RETAIN_DAYS:-14}"

mkdir -p "${BACKUP_DIR}"
STAMP="$(date +%Y%m%d_%H%M%S)"
FILE="${BACKUP_DIR}/${DB_NAME}_${STAMP}.sql.gz"

pg_dump -U "${DB_USER}" -h localhost "${DB_NAME}" | gzip > "${FILE}"
find "${BACKUP_DIR}" -name "${DB_NAME}_*.sql.gz" -mtime +"${RETAIN_DAYS}" -delete

echo "Backup saved: ${FILE}"
