#!/usr/bin/env bash
set -eu

PORT="${PORT:-8000}"
exec gunicorn --workers "${WEB_CONCURRENCY:-2}" \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile - \
  --error-logfile - \
  app:app