#!/bin/sh
# Start FalkorDB in the background, seed data, then run the API (serves the UI too).
set -e

DATA_DIR="${FALKORDB_DATA_PATH:-/var/lib/falkordb/data}"
mkdir -p "$DATA_DIR"
redis-server --protected-mode no --dir "$DATA_DIR" --appendonly yes \
    --loadmodule /var/lib/falkordb/bin/falkordb.so &

cd /app/backend
PY=/app/backend/.venv/bin/python
$PY -m scripts.wait_for_db
$PY -m scripts.seed_catalog
$PY -m scripts.seed_demo_students --if-missing

exec /app/backend/.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-7860}"
