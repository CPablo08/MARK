#!/usr/bin/env bash
# Stop MARK dev processes started by scripts/start.sh
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
MARK_DIR="$ROOT/.mark"
API_PORT="${MARK_API_PORT:-8000}"
UI_PORT="${MARK_UI_PORT:-5173}"

stop_pid_file() {
  local file="$1"
  local label="$2"
  if [[ -f "$file" ]]; then
    local pid
    pid="$(cat "$file")"
    if kill -0 "$pid" 2>/dev/null; then
      echo "Stopping $label (pid $pid)"
      kill "$pid" 2>/dev/null || true
      sleep 0.3
      kill -9 "$pid" 2>/dev/null || true
    fi
    rm -f "$file"
  fi
}

stop_pid_file "$MARK_DIR/api.pid" "API"
stop_pid_file "$MARK_DIR/worker.pid" "worker"
stop_pid_file "$MARK_DIR/ui.pid" "UI"

for port in "$API_PORT" "$UI_PORT"; do
  pids="$(lsof -ti:"$port" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Freeing port $port"
    kill -9 $pids 2>/dev/null || true
  fi
done

# uvicorn --reload leaves a child; clean common patterns
pkill -f "uvicorn mark_api.main:app" 2>/dev/null || true
pkill -f "mark_core.worker" 2>/dev/null || true

echo "MARK stopped."
