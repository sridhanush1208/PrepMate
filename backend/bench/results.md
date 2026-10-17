# Load test results

Run: 2026-10-17 20:05 · 200 students × 4 agents · 32 concurrent workers (one Python process) · 15s per run · FalkorDB in Docker on a laptop

| Mode | Writes | Ops/sec | Read p50 (ms) | Read p95 (ms) | Write p50 (ms) | Write p95 (ms) | Errors |
|---|---|---|---|---|---|---|---|
| One graph per student | 20% | 4744 | 5.9 | 14.3 | 6.1 | 14.6 | 0 |
| One shared graph | 20% | 4651 | 6.0 | 14.2 | 6.5 | 14.9 | 0 |
| One graph per student | 80% | 5007 | 5.1 | 11.3 | 6.0 | 12.2 | 0 |
| One shared graph | 80% | 3972 | 1.4 | 2.4 | 9.3 | 12.8 | 0 |

How to read this: FalkorDB runs reads in parallel but writes one at a time *per graph*. With mostly reads, both layouts perform about the same (differences between runs are noise). With mostly writes, the shared graph makes every student's writes queue behind each other, while separate graphs let them proceed independently. Compare the write-heavy rows. One graph per student also gives **isolation** (no query can leak another student's memory) and **easy deletion** (`GRAPH.DELETE`).
