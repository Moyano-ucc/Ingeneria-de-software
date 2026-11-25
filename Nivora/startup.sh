#!/usr/bin/env bash
set -eu

PORT="${PORT:-8000}"
# --timeout 120: on Azure's free plan (F1) the first request after the app
# sleeps can be slow; the default 30 s could kill the worker while it starts.
exec gunicorn --workers "${WEB_CONCURRENCY:-2}" \
  --worker-class uvicorn.workers.UvicornWorker \
  --timeout 120 \
  --bind "0.0.0.0:${PORT}" \
  --access-logfile - \
  --error-logfile - \
  app:app
