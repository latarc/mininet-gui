#!/usr/bin/env bash
set -euo pipefail

BACKEND_HOST=${BACKEND_HOST:-0.0.0.0}
BACKEND_PORT=${BACKEND_PORT:-8000}
FRONTEND_HOST=${FRONTEND_HOST:-0.0.0.0}
FRONTEND_PORT=${FRONTEND_PORT:-5173}
FRONTEND_DIR=${FRONTEND_DIR:-/app/frontend/dist}
BACKEND_APP=${BACKEND_APP:-mininet_gui_backend.api:app}

# Clean up any stale Mininet state, if present.
mn -c >/dev/null 2>&1 || true

uvicorn "$BACKEND_APP" --host "$BACKEND_HOST" --port "$BACKEND_PORT" --log-level info &
backend_pid=$!

trap 'kill "$backend_pid" >/dev/null 2>&1 || true' SIGINT SIGTERM

exec python -m http.server "$FRONTEND_PORT" --directory "$FRONTEND_DIR" --bind "$FRONTEND_HOST"
