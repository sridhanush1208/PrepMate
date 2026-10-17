"""Concurrency load test: one graph per student vs one shared graph.

Simulates many students, each with 4 agents reading and writing memory at the same time
(80% reads like a context pack, 20% writes like recording an attempt + a message).
No LLM is involved, so it measures the memory layer only.

Run from backend/:  uv run python -m bench.load_test --students 200 --workers 32 --seconds 30
"""
import argparse
import random
import statistics
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

from app import config
from app.db import get_db

TOPICS = [f"t{i}" for i in range(48)]
AGENTS = ["coach", "interviewer", "tutor", "planner"]

# per-student graph: no student filter needed, the graph IS the student
PER_READ = """
MATCH (:Student)-[k:KNOWS]->(t:Topic) WHERE k.attempts > 0 AND k.mastery < 0.5
WITH t, k ORDER BY k.mastery LIMIT 5
RETURN t.id, k.mastery"""
PER_WRITE = """
MATCH (s:Student)-[k:KNOWS]->(t:Topic {id: $tid})
SET k.mastery = 0.6 * k.mastery + 0.4 * $score, k.attempts = k.attempts + 1
CREATE (s)-[:SAID]->(:Message {agent: $agent, text: $text, ts: $now})"""

# shared graph: every query must filter by student id
SHARED_READ = """
MATCH (:Student {id: $sid})-[k:KNOWS]->(t:Topic) WHERE k.attempts > 0 AND k.mastery < 0.5
WITH t, k ORDER BY k.mastery LIMIT 5
RETURN t.id, k.mastery"""
SHARED_WRITE = """
MATCH (s:Student {id: $sid})-[k:KNOWS]->(t:Topic {id: $tid})
SET k.mastery = 0.6 * k.mastery + 0.4 * $score, k.attempts = k.attempts + 1
CREATE (s)-[:SAID]->(:Message {agent: $agent, text: $text, ts: $now})"""

SETUP = """
UNWIND $students AS sid
MERGE (s:Student {id: sid})
WITH s
UNWIND $topics AS tid
MERGE (t:Topic {id: tid})
MERGE (s)-[k:KNOWS]->(t)
ON CREATE SET k.mastery = rand(), k.attempts = toInteger(rand() * 3)"""


def setup(n: int):
    db = get_db()
    for name in db.list_graphs():
        if name.startswith("bench_"):
            db.select_graph(name).delete()
    ids = [f"s{i}" for i in range(n)]
    for sid in ids:
        g = db.select_graph(f"bench_{sid}")
        g.query("CREATE INDEX FOR (t:Topic) ON (t.id)")
        g.query(SETUP, {"students": [sid], "topics": TOPICS})
    shared = db.select_graph("bench_shared")
    shared.query("CREATE INDEX FOR (s:Student) ON (s.id)")
    shared.query("CREATE INDEX FOR (t:Topic) ON (t.id)")
    for i in range(0, n, 50):
        shared.query(SETUP, {"students": ids[i:i + 50], "topics": TOPICS})
    return ids


def run(mode: str, ids: list[str], workers: int, seconds: float, write_ratio: float = 0.2) -> dict:
    db = get_db()
    stop = time.time() + seconds
    lat = {"read": [], "write": []}
    errors = 0
    lock = threading.Lock()

    def worker(seed: int):
        nonlocal errors
        rnd = random.Random(seed)
        local = {"read": [], "write": []}
        while time.time() < stop:
            sid, agent = rnd.choice(ids), rnd.choice(AGENTS)
            g = db.select_graph(f"bench_{sid}" if mode == "per_student" else "bench_shared")
            is_write = rnd.random() < write_ratio
            params = {"sid": sid, "tid": rnd.choice(TOPICS), "score": rnd.random(),
                      "agent": agent, "text": "bench", "now": int(time.time() * 1000)}
            t0 = time.perf_counter()
            try:
                if is_write:
                    g.query(PER_WRITE if mode == "per_student" else SHARED_WRITE, params)
                else:
                    g.ro_query(PER_READ if mode == "per_student" else SHARED_READ, params)
            except Exception:
                with lock:
                    errors += 1
                continue
            local["write" if is_write else "read"].append((time.perf_counter() - t0) * 1000)
        with lock:
            lat["read"] += local["read"]
            lat["write"] += local["write"]

    with ThreadPoolExecutor(max_workers=workers) as ex:
        list(ex.map(worker, range(workers)))

    def pct(xs, p):
        return statistics.quantiles(xs, n=100)[p - 1] if len(xs) >= 100 else (max(xs) if xs else 0)

    total = len(lat["read"]) + len(lat["write"])
    return {
        "mode": mode, "ops": total, "ops_per_sec": total / seconds, "errors": errors,
        "read_p50": pct(lat["read"], 50), "read_p95": pct(lat["read"], 95),
        "write_p50": pct(lat["write"], 50), "write_p95": pct(lat["write"], 95),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--students", type=int, default=200)
    ap.add_argument("--workers", type=int, default=32)
    ap.add_argument("--seconds", type=float, default=30)
    ap.add_argument("--write-ratios", default="0.2,0.8", help="comma-separated, e.g. 0.2,0.8")
    args = ap.parse_args()
    ratios = [float(r) for r in args.write_ratios.split(",")]

    print(f"setting up {args.students} student graphs + 1 shared graph...")
    ids = setup(args.students)
    results = []
    for ratio in ratios:
        for mode in ("per_student", "shared"):
            print(f"running {mode}, {ratio:.0%} writes, {args.seconds}s, {args.workers} workers...")
            r = run(mode, ids, args.workers, args.seconds, ratio)
            r["write_ratio"] = ratio
            print(r)
            results.append(r)

    lines = [
        "# Load test results",
        "",
        f"Run: {datetime.now():%Y-%m-%d %H:%M} · {args.students} students × 4 agents · "
        f"{args.workers} concurrent workers (one Python process) · {args.seconds:.0f}s per run · "
        f"FalkorDB in Docker on a laptop",
        "",
        "| Mode | Writes | Ops/sec | Read p50 (ms) | Read p95 (ms) | Write p50 (ms) | Write p95 (ms) | Errors |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        name = "One graph per student" if r["mode"] == "per_student" else "One shared graph"
        lines.append(f"| {name} | {r['write_ratio']:.0%} | {r['ops_per_sec']:.0f} | {r['read_p50']:.1f} | "
                     f"{r['read_p95']:.1f} | {r['write_p50']:.1f} | {r['write_p95']:.1f} | {r['errors']} |")
    lines += [
        "",
        "How to read this: FalkorDB runs reads in parallel but writes one at a time *per graph*. "
        "With mostly reads, both layouts perform about the same (differences between runs are noise). "
        "With mostly writes, the shared graph makes every student's writes queue behind each other, "
        "while separate graphs let them proceed independently. Compare the write-heavy rows. "
        "One graph per student also gives **isolation** (no query can leak another student's memory) "
        "and **easy deletion** (`GRAPH.DELETE`).",
    ]
    out = config.BACKEND_DIR / "bench" / "results.md"
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"wrote {out}")

    db = get_db()
    for name in db.list_graphs():
        if name.startswith("bench_"):
            db.select_graph(name).delete()


if __name__ == "__main__":
    main()
