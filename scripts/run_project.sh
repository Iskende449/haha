#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR"
FRONTEND_DIR="$ROOT_DIR/frontend"
BACKEND_PORT=8000
FRONTEND_PORT=5173

echo "[heritage] Starting full stack..."

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[heritage] frontend directory not found at $FRONTEND_DIR"
  exit 1
fi

if [[ ! -d "$BACKEND_DIR/venv" ]]; then
  echo "[heritage] Python venv not found. Create it first:"
  echo "python -m venv venv && source venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source "$BACKEND_DIR/venv/bin/activate"

echo "[heritage] Installing missing backend dependencies..."
pip install -q python-jose passlib email-validator python-multipart >/dev/null

echo "[heritage] Applying database migrations..."
(cd "$BACKEND_DIR" && PYTHONPATH="$BACKEND_DIR" alembic upgrade head >/dev/null)

echo "[heritage] Ensuring frontend dependencies..."
(cd "$FRONTEND_DIR" && npm install >/dev/null)

cleanup() {
  echo ""
  echo "[heritage] Stopping services..."
  [[ -n "${BACKEND_PID:-}" ]] && kill "$BACKEND_PID" >/dev/null 2>&1 || true
  [[ -n "${FRONTEND_PID:-}" ]] && kill "$FRONTEND_PID" >/dev/null 2>&1 || true
}

trap cleanup EXIT INT TERM

kill_port_if_busy() {
  local port="$1"
  local pids
  local attempt=0

  while true; do
    pids="$(ss -ltnpH "sport = :$port" | rg -o 'pid=[0-9]+' | awk -F '=' '{print $2}' | sort -u || true)"
    [[ -z "$pids" ]] && break

    if [[ $attempt -eq 0 ]]; then
      echo "[heritage] Port $port is busy. Stopping old process(es): $pids"
    fi

    while IFS= read -r pid; do
      [[ -n "$pid" ]] && kill "$pid" >/dev/null 2>&1 || true
    done <<<"$pids"

    sleep 1
    attempt=$((attempt + 1))

    if [[ $attempt -ge 5 ]]; then
      pids="$(ss -ltnpH "sport = :$port" | rg -o 'pid=[0-9]+' | awk -F '=' '{print $2}' | sort -u || true)"
      if [[ -n "$pids" ]]; then
        echo "[heritage] Force killing stubborn process(es) on port $port: $pids"
        while IFS= read -r pid; do
          [[ -n "$pid" ]] && kill -9 "$pid" >/dev/null 2>&1 || true
        done <<<"$pids"
      fi
      break
    fi
  done
}

kill_port_if_busy "$BACKEND_PORT"
kill_port_if_busy "$FRONTEND_PORT"

echo "[heritage] Starting backend on http://127.0.0.1:${BACKEND_PORT}"
(cd "$BACKEND_DIR" && PYTHONPATH="$BACKEND_DIR" uvicorn app.main:app --reload --port "$BACKEND_PORT") &
BACKEND_PID=$!

sleep 2

echo "[heritage] Starting frontend on http://localhost:${FRONTEND_PORT}"
(cd "$FRONTEND_DIR" && npm run dev) &
FRONTEND_PID=$!

echo "[heritage] Ready."
echo "[heritage] Press Ctrl+C to stop both services."

wait
