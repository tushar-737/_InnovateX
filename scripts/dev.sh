#!/usr/bin/env bash
# One-command local run (without Docker):  bash scripts/dev.sh
# Starts FastAPI backend (:8000) + Vite frontend (:5173) with a single command.
set -euo pipefail
cd "$(dirname "$0")/.."

echo "▶ Setting up backend (venv + deps)…"
if [ ! -d .venv ]; then python3 -m venv .venv; fi
.venv/bin/pip install -q -r backend/requirements.txt

echo "▶ Setting up frontend (npm)…"
if [ ! -d frontend/node_modules ]; then (cd frontend && npm install --no-audit --no-fund); fi

echo "▶ Starting backend on http://0.0.0.0:8000 …"
.venv/bin/uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

echo "▶ Starting frontend on http://0.0.0.0:5173 …"
(cd frontend && npm run dev) &
FRONTEND_PID=$!

trap 'kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true' EXIT INT TERM
echo ""
echo "✅ Kaushal Saathi is running:"
echo "   • Open the app:     http://localhost:5173"
echo "   • API health:       http://localhost:8000/api/health"
echo "   • API docs:         http://localhost:8000/docs"
echo ""
wait
