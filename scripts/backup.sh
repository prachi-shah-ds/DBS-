#!/usr/bin/env bash
set -e
OUT_DIR="${1:-/backups}"
mkdir -p "$OUT_DIR"
TIMESTAMP=$(date +%Y%m%d%H%M)
pg_dump -U "${PGUSER:-postgres}" -h "${PGHOST:-localhost}" -F c -b -v -f "${OUT_DIR}/db_${TIMESTAMP}.dump" "${PGDATABASE:-jodo_dev}"
echo "Backup saved to ${OUT_DIR}/db_${TIMESTAMP}.dump"
