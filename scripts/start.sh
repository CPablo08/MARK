#!/usr/bin/env bash
# Start MARK: API + task worker + web UI (local dev).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

MARK_DIR="$ROOT/.mark"
LOG_DIR="$MARK_DIR/logs"
API_PID_FILE="$MARK_DIR/api.pid"
WORKER_PID_FILE="$MARK_DIR/worker.pid"
UI_PID_FILE="$MARK_DIR/ui.pid"
API_PORT="${MARK_API_PORT:-8000}"
UI_PORT="${MARK_UI_PORT:-5173}"
WITH_DOCKER=0
OPEN_BROWSER=0

usage() {
  cat <<'EOF'
Usage: ./scripts/start.sh [options]

  Starts MARK backend API, background worker, and Vite UI.

Options:
  --docker       Start postgres, redis, qdrant via docker compose
  --open         Open http://127.0.0.1:5173 in the default browser
  --no-worker    Skip the task worker process
  -h, --help     Show this help

Stop everything:  ./scripts/stop.sh
Logs:             tail -f .mark/logs/api.log .mark/logs/ui.log
EOF
}

SKIP_WORKER=0
while [[ $# -gt 0 ]]; do
  case "$1" in
    --docker) WITH_DOCKER=1 ;;
    --open) OPEN_BROWSER=1 ;;
    --no-worker) SKIP_WORKER=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown option: $1" >&2; usage; exit 1 ;;
  esac
  shift
done

if [[ ! -f "$ROOT/.env" ]]; then
  echo "Missing .env — copy .env.example to .env and add your API keys." >&2
  exit 1
fi

free_port() {
  local port="$1"
  local pids
  pids="$(lsof -ti:"$port" 2>/dev/null || true)"
  if [[ -n "$pids" ]]; then
    echo "Stopping process on port $port ($pids)"
    kill -9 $pids 2>/dev/null || true
    sleep 0.5
  fi
}

mkdir -p "$LOG_DIR"

echo "==> Stopping any existing MARK processes"
"$ROOT/scripts/stop.sh" 2>/dev/null || true
free_port "$API_PORT"
free_port "$UI_PORT"

echo "==> Syncing environment"
cp "$ROOT/.env" "$ROOT/backend/.env"
mkdir -p "$ROOT/apps/desktop"
grep -q VITE_API_URL "$ROOT/apps/desktop/.env" 2>/dev/null \
  || echo "VITE_API_URL=http://127.0.0.1:${API_PORT}" > "$ROOT/apps/desktop/.env"

if [[ "$WITH_DOCKER" -eq 1 ]]; then
  echo "==> Starting Docker services (postgres, redis, qdrant)"
  if command -v docker >/dev/null 2>&1; then
    docker compose -f "$ROOT/docker/docker-compose.yml" up -d postgres redis qdrant
  else
    echo "Docker not found — continuing without infra containers." >&2
  fi
fi

if [[ ! -d "$ROOT/node_modules" ]]; then
  echo "==> Installing Node dependencies"
  pnpm install
fi

if ! python3 -c "import mark_api" 2>/dev/null; then
  echo "==> Installing Python backend"
  (cd "$ROOT/backend" && pip3 install -e . -q)
fi

echo "==> Running database migrations"
(cd "$ROOT/backend" && alembic -c alembic.ini upgrade head) >/dev/null 2>&1 || true

echo "==> Starting API on http://127.0.0.1:${API_PORT}"
(
  cd "$ROOT/backend"
  export PYTHONPATH=.
  nohup python3 -m uvicorn mark_api.main:app \
    --reload \
    --host 127.0.0.1 \
    --port "$API_PORT" \
    >>"$LOG_DIR/api.log" 2>&1 &
  echo $! >"$API_PID_FILE"
)

if [[ "$SKIP_WORKER" -eq 0 ]]; then
  echo "==> Starting task worker"
  (
    cd "$ROOT/backend"
    export PYTHONPATH=.
    nohup python3 -m mark_core.worker >>"$LOG_DIR/worker.log" 2>&1 &
    echo $! >"$WORKER_PID_FILE"
  )
fi

echo "==> Starting UI on http://127.0.0.1:${UI_PORT}"
(
  cd "$ROOT"
  nohup pnpm dev >>"$LOG_DIR/ui.log" 2>&1 &
  echo $! >"$UI_PID_FILE"
)

wait_for_url() {
  local url="$1"
  local name="$2"
  local i
  for i in $(seq 1 60); do
    if curl -sf "$url" >/dev/null 2>&1; then
      echo "    $name ready"
      return 0
    fi
    sleep 0.5
  done
  echo "    WARNING: $name did not respond at $url (check logs)" >&2
  return 1
}

echo "==> Waiting for services"
wait_for_url "http://127.0.0.1:${API_PORT}/health" "API" || true
wait_for_url "http://127.0.0.1:${UI_PORT}/" "UI" \
  || wait_for_url "http://localhost:${UI_PORT}/" "UI" || true

echo ""
echo "MARK is running"
echo "  UI:      http://127.0.0.1:${UI_PORT}"
echo "  API:     http://127.0.0.1:${API_PORT}"
echo "  Health:  http://127.0.0.1:${API_PORT}/health"
echo "  Logs:    tail -f $LOG_DIR/api.log $LOG_DIR/ui.log"
echo "  Stop:    ./scripts/stop.sh"
echo ""

if [[ "$OPEN_BROWSER" -eq 1 ]] && command -v open >/dev/null 2>&1; then
  open "http://localhost:${UI_PORT}"
fi
