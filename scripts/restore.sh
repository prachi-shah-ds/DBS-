#!/usr/bin/env bash
set -e
DUMP_FILE="$1"
if [ -z "$DUMP_FILE" ]; then
  echo "Usage: $0 /path/to/dump"
  exit 1
fi
pg_restore -U "${PGUSER:-postgres}" -h "${PGHOST:-localhost}" -d "${PGDATABASE:-jodo_dev}" -v "$DUMP_FILE"
echo "Restore completed"
