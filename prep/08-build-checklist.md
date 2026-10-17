# Build checklist: Oct 15–18 (start ONLY after Oct 15, 12:01 AM IST)

## Day 1: Thu Oct 15, memory foundation
- [ ] Create the GitHub repo `prepmate` (public) + first commit
- [ ] `docker-compose.yml` with FalkorDB + data volume
- [ ] `catalog/topics.yaml`, `roles.yaml`, `questions.yaml` (from [05-topic-list-draft.md](05-topic-list-draft.md))
- [ ] `scripts/seed_catalog.py` → `catalog` graph loaded
- [ ] `backend/app/db.py`: connection + pick a graph by name
- [ ] `backend/app/memory.py`:
  - [ ] create student graph (copy topics + prerequisites)
  - [ ] add message (chained with NEXT)
  - [ ] record attempt + mastery update
  - [ ] add fact / rule (with LEARNED_FROM + WROTE)
  - [ ] create handoff / task, mark picked / done
  - [ ] context pack, root cause, ready to learn, due for revision, welcome back
- [ ] `backend/queries/*.cypher` (one file per named query)
- [ ] `backend/tests/test_memory.py` passes
- [ ] Look at a student graph in FalkorDB Browser (screenshot for the README)
- [ ] Evening: HF Space smoke test (FalkorDB + hello FastAPI in one container)
- [ ] Commit + push

## Day 2: Fri Oct 16, agents + handoffs
- [ ] `llm.py`: Gemini / Groq switch, JSON reply + one retry + fallback
- [ ] Role prompts for Coach, Interviewer, Tutor, Planner
- [ ] `orchestrator.py`: route → context pack → LLM → batched write → handoff
- [ ] Session start ("welcome back") + session end (summary)
- [ ] `app/cli.py`: chat in the terminal as a chosen student
- [ ] Play the full Riya story in the CLI
- [ ] `docker compose restart` → Riya is still remembered ✅
- [ ] Commit + push

## Day 3: Sat Oct 17, UI + numbers
- [ ] FastAPI endpoints: students, chat, memory graph / facts / timeline / plan, delete fact, forget me
- [ ] React app (Vite + TS + Tailwind): student picker, chat, handoff banners, "memories used"
- [ ] Memory panel: graph view, facts & rules, timeline, plan
- [ ] `scripts/seed_demo_students.py` (Riya with history, Arjun empty)
- [ ] `bench/load_test.py` → `bench/results.md`
- [ ] `eval/memory_eval.py` → `eval/results.md` (drop first if short on time)
- [ ] Full demo works in the browser
- [ ] Commit + push

## Day 4: Sun Oct 18, ship (submit by 8 PM IST)
- [ ] Dockerfile (single container) → deploy to the HF Space, API key as a secret
- [ ] Test the live link in incognito + on a phone
- [ ] README (see [07-readme-blog-outline.md](07-readme-blog-outline.md)) incl. data model + Cypher table
- [ ] `AI_USAGE.md`
- [ ] Record the demo video (see [04-demo-story.md](04-demo-story.md)) → YouTube unlisted
- [ ] Blog post
- [ ] **Submit on WeMakeDevs: repo, video, live link, Track 02**
- [ ] Post on LinkedIn 🎉

## If behind, drop in this order
1. memory eval → 2. PageRank foundational topics → 3. plan-board UI → 4. LLM session summaries

## Never drop
per-student graphs · 3 memory types · handoffs · cross-session recall · memory panel with sources · load test · Cypher table · demo video
