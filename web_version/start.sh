#!/usr/bin/env bash
set -e

PORT="${PORT:-8000}"

exec gunicorn main:app \
  -k uvicorn.workers.UvicornWorker \
  -b "0.0.0.0:${PORT}" \
  -w 2 \
  --timeout 120 \
  --access-logfile -
