#!/bin/bash
set -e

echo "============================================"
echo "Starting IPVA Server"
echo "PORT: ${PORT:-8080}"
echo "============================================"

exec gunicorn server:app \
  --bind "0.0.0.0:${PORT:-8080}" \
  --workers 1 \
  --threads 4 \
  --timeout 120 \
  --log-level debug \
  --access-logfile - \
  --error-logfile -
