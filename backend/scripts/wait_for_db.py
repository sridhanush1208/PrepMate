"""Block until FalkorDB answers (used by start.sh in the container)."""
import sys
import time

from app.db import get_db

for _ in range(60):
    try:
        get_db().list_graphs()
        print("FalkorDB is up")
        sys.exit(0)
    except Exception:
        time.sleep(0.5)
print("FalkorDB did not start in 30s", file=sys.stderr)
sys.exit(1)
