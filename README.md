# 🎯 PrepMate

**A team of 4 AI agents that helps you prepare for placement interviews. They remember you across sessions and share one memory graph in [FalkorDB](https://www.falkordb.com/).**

> Built for **Graph Hacks: Context for AI Agents** (WeMakeDevs × FalkorDB), **Track 02: Agent Memory and Coordination**.

Most prep chatbots forget you the moment the tab closes. PrepMate's agents don't:

- 🟢 **Coach**: greets you with what happened last time and routes you
- 🔵 **Interviewer**: picks a mock question from your memory, then grades your answer
- 🟣 **Tutor**: explains topics *your* way and finds the root cause of a weakness
- 🟠 **Planner**: keeps a shared task board for the other agents

> 🎬 Demo video: _add link_ · 🌐 Live demo: _add Render link_ (free tier: the first visit after idle takes ~1 minute to wake up)

---

## What a session looks like

1. Riya presses **Mock interview**. The Interviewer reads the shared task board, sees "Try your first BFS question" and asks a BFS question.
2. Riya's answer is weak (score 0.3). The attempt is saved and BFS mastery drops.
3. **Handoff:** Interviewer → Tutor ("struggled with BFS").
4. The Tutor runs a **multi-hop root-cause query**: BFS ← Queues, and Riya's Queues mastery is also low. It explains Queues → BFS **with Java code**, because of a rule Riya gave two days ago.
5. In parallel, the Planner writes "Retry BFS tomorrow" to the task board.
6. Riya says "next time give me a hint before the question". That becomes a **procedural memory** rule for the Interviewer.
7. **Restart the server.** Next session the Coach says: *"Welcome back Riya! BFS was tricky: you scored 0.3. Your plan says: Retry BFS."* The Interviewer now gives a hint first.
8. Arjun logs in and sees none of Riya's memory. **Forget me** deletes a student's whole graph.

Under every agent reply, **"memories used"** shows exactly which graph queries were run (with the Cypher).

---

## How each Track 2 focus area is covered

| Track 2 focus | PrepMate |
|---|---|
| Episodic memory | `Session`, `Attempt`, `Message` nodes: what happened, when |
| Semantic memory | `(Student)-[:KNOWS {mastery}]->(Topic)` + `Fact` nodes ("Codes mostly in Java") |
| Procedural memory | `Rule` nodes `-[:APPLIES_TO]->(Agent)`: how each agent must behave for this student |
| Persistent conversation history | `Message` nodes chained with `NEXT` in each session, stored in FalkorDB (survive restarts) |
| Shared state + handoffs | `Handoff` nodes (from, to, reason, topic) + a shared `Task` board all agents read and write |
| High-concurrency reads/writes | One graph per student (see [load test](#load-test)), background agent writes |
| Separate memory per user | Each student = their own FalkorDB graph `pm_<id>`; "Forget me" deletes it |
| Provenance | Every fact and rule links to the message it was `LEARNED_FROM` and the agent that `WROTE` it |

---

## Architecture

```
React (Vite + TS)  ──HTTP──▶  FastAPI
                                 │
                       Orchestrator (hand-written, no framework)
                       route ─▶ recall (Cypher) ─▶ 1 LLM call ─▶ write memory ─▶ handoff
                                 │                     │
                                 ▼                     ▼
                     FalkorDB (one instance)     Gemini / Groq (OpenAI-compatible)
                     ├─ catalog          shared  multi-key fallback chain
                     ├─ pm_riya          private
                     └─ pm_arjun         private
```

- **Memory-first, LLM-light.** Routing, question choice, handoffs on low scores and retry tasks are decided from the graph **without** an LLM. The LLM is used only to grade, teach, plan and chat. About 1 call per turn keeps it within free tiers.
- **Multi-key LLM fallback.** Put several keys in `GEMINI_API_KEYS` / `GROQ_API_KEYS` (comma-separated). Calls go round-robin across the keys. A rate-limited key cools down for 60 s, a rejected key is disabled, and when all Gemini keys are busy it falls back to Groq. Status: `GET /api/llm/status`.

---

## Graph data model

**Shared `catalog` graph** (read-only knowledge)

```
(:Topic {id, name, area, foundational})-[:PREREQ_OF]->(:Topic)
(:Topic)-[:DEPENDS_ON]->(:Topic)                 reverse edge, used for PageRank
(:Question {id, text, hint, points[], difficulty})-[:TESTS]->(:Topic)
(:Role {id, name})-[:FOCUSES_ON {weight}]->(:Topic)
```

**One private graph per student: `pm_<student_id>`**

```
(:Student {id, name, target_role})-[:KNOWS {mastery, attempts, last_practiced}]->(:Topic)
(:Topic)-[:PREREQ_OF]->(:Topic)                                   copied from catalog
(:Student)-[:HAD]->(:Session {started_at, summary})-[:HAS_MSG]->(:Message {seq, role, agent, text})
(:Message)-[:NEXT]->(:Message)
(:Session)-[:INCLUDED]->(:Attempt {score, feedback})-[:ON]->(:Question)-[:TESTS]->(:Topic)
(:Fact {text})-[:ABOUT]->(:Topic | :Student)
(:Rule {text, active})-[:APPLIES_TO]->(:Agent)
(:Fact | :Rule)-[:LEARNED_FROM]->(:Message)
(:Agent)-[:WROTE]->(:Fact | :Rule | :Attempt | :Task)
(:Handoff {reason, status})-[:FROM|TO]->(:Agent), -[:ABOUT]->(:Topic), -[:IN]->(:Session)
(:Task {title, due, status})-[:ASSIGNED_TO]->(:Agent), -[:PRACTICES]->(:Topic)
```

**Memory rules** (simple and explainable):
- Mastery after an attempt: first try = score, then `new = 0.6 × old + 0.4 × score`
- Forgetting curve: `effective = mastery × 0.5 ^ (days_since_practice / 14)`. A topic is "due for revision" when effective < 0.5.

---

## Cypher queries the product depends on

All queries live in [`backend/queries/`](backend/queries), one file each. The most important:

| Query | What it does |
|---|---|
| [`root_cause`](backend/queries/root_cause.cypher) | **Multi-hop**: walks `PREREQ_OF*1..3` back from a weak topic and returns prerequisites that are weak or untested |
| [`ready_to_learn`](backend/queries/ready_to_learn.cypher) | Topics whose prerequisites are all mastered, ranked by role weight and PageRank |
| [`due_for_revision`](backend/queries/due_for_revision.cypher) | Forgetting curve computed in Cypher: `mastery * 0.5 ^ (days / 14)` |
| [`pagerank_foundational`](backend/queries/pagerank_foundational.cypher) | **Graph algorithm** `algo.pageRank('Topic', 'DEPENDS_ON')`: how foundational each topic is |
| [`record_attempt`](backend/queries/record_attempt.cypher) | Saves an Attempt and updates `KNOWS.mastery` in one query |
| [`rules_for_agent`](backend/queries/rules_for_agent.cypher) | Procedural memory an agent must follow |
| [`fact_add`](backend/queries/fact_add.cypher) / [`rule_add`](backend/queries/rule_add.cypher) | `MERGE` on a normalised key (no duplicates) + provenance edges |
| [`handoff_create`](backend/queries/handoff_create.cypher) / [`handoff_open`](backend/queries/handoff_open.cypher) | Agent-to-agent handoffs |
| [`task_create`](backend/queries/task_create.cypher) / [`tasks_open`](backend/queries/tasks_open.cypher) | Shared task board |
| [`welcome_back`](backend/queries/welcome_back.cypher) | Episodic recall of the previous session |
| [`message_add`](backend/queries/message_add.cypher) | Conversation history as a `NEXT` chain |
| [`student_create`](backend/queries/student_create.cypher) | Builds a student's private graph from the catalog |

Example, root cause:

```cypher
MATCH p = (pre:Topic)-[:PREREQ_OF*1..3]->(:Topic {id: $topic_id})
MATCH (:Student)-[k:KNOWS]->(pre)
WHERE k.attempts = 0 OR k.mastery < $weak
WITH pre, k, min(length(p)) AS hops
RETURN pre.id AS topic_id, pre.name AS topic, k.mastery AS mastery,
       CASE WHEN k.attempts = 0 THEN 'untested' ELSE 'weak' END AS status, hops
ORDER BY status DESC, hops, mastery
LIMIT 5
```

---

## Load test

`backend/bench/load_test.py` simulates many students × 4 agents reading and writing memory at once (80% reads / 20% writes, no LLM), and compares **one graph per student** against **one shared graph**.

Latest run (200 students, 32 concurrent workers, laptop + Docker, 0 errors in every run):

| Layout | 20% writes | 80% writes | Write p50 (80% writes) |
|---|---|---|---|
| One graph per student | 4,744 ops/s | **5,007 ops/s** | **6.0 ms** |
| One shared graph | 4,651 ops/s | 3,972 ops/s | 9.3 ms |

With mostly reads, both layouts perform about the same. With mostly writes, per-student graphs do **~26% more operations per second**, because FalkorDB queues writes per graph. Full table: [`backend/bench/results.md`](backend/bench/results.md).

---

## Run it locally

**Needs:** Docker Desktop, Python 3.11+ with [uv](https://docs.astral.sh/uv/), Node 20+.

```bash
git clone https://github.com/sridhanush1208/PrepMate.git
cd PrepMate
cp .env.example .env          # then paste your Gemini (and optional Groq) keys
docker compose up -d          # FalkorDB on :6379, FalkorDB Browser on :3000

cd backend
uv sync
uv run python -m scripts.seed_catalog
uv run python -m scripts.seed_demo_students
uv run uvicorn app.main:app --port 8000

# in another terminal
cd frontend
npm install
npm run dev                   # open http://localhost:5173
```

Without any API key the app still runs with an offline mock model, so you can explore the memory features.

**Terminal chat:** `uv run python -m app.cli --student riya` (commands: `/mock`, `/teach`, `/plan`, `/memory`, `/end`)
**Tests:** `uv run python -m pytest` (needs FalkorDB running)
**Single container (same as the live demo):** `docker build -t prepmate . && docker run -p 7860:7860 --env-file .env prepmate`

### Deploy (free, Render)

The repo includes a [`render.yaml`](render.yaml) blueprint: one free Docker web service running FalkorDB, the API and the UI together (about 100 MB RAM).
On Render: **New → Blueprint →** pick this repo, then enter `GEMINI_API_KEYS` / `GEMINI_MODEL` (and the optional Groq values) when asked.
The free tier has no persistent disk, so the container re-seeds the catalog and demo students when it starts. Memory persistence across restarts is shown locally with the Docker volume in `docker-compose.yml`.

---

## Project layout

```
catalog/            topics, prerequisites, role tracks, 96 self-written questions
backend/app/        memory.py (all memory reads/writes), orchestrator.py (agents), llm.py, main.py (API), cli.py
backend/queries/    every Cypher query, one file each
backend/scripts/    seed catalog (+ PageRank), seed demo students
backend/bench/      concurrency load test
backend/tests/      memory, orchestration and LLM-fallback tests
frontend/           React UI: chat, handoff banners, memory panel
```

## AI usage

See [AI_USAGE.md](AI_USAGE.md).

## License

MIT
