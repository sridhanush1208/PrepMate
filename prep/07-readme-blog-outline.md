# README outline (final repo)

1. **PrepMate**: one-line pitch + demo GIF + badges (live demo, video, blog)
2. **Track:** 02, Agent Memory and Coordination
3. **The problem**: prep chatbots forget you; agents don't share what they know
4. **What it does**: the 4 agents + the Riya story in 5 bullets
5. **Architecture diagram** (`docs/agent-flow.png`)
6. **Graph data model** (`docs/data-model.png` + node/relationship tables), *required*
7. **How each Track 2 focus is covered** (table)
8. **Cypher queries we depend on** (table: name · purpose · query), *required*
9. **Memory rules**: mastery + forgetting formulas
10. **Results**: load test table (per-student vs shared graph) + memory recall eval
11. **Run locally**: prerequisites, `.env` keys, `docker compose up`, seed, open the URL
12. **Live demo** link + note about re-seeding on restart
13. **Use with your own LLM key**: Gemini / Groq switch
14. **AI usage disclosure** (link to `AI_USAGE.md`), *required by the rules*
15. **Limitations & future work**
16. **License** (MIT)

---

# Blog post outline (Hashnode / dev.to), for the "Best blog" side prize

**Title idea:** "I gave my AI study buddies a shared brain: graph memory with FalkorDB"

1. Hook: the "Groundhog Day" chatbot that forgets you every session
2. Why a **graph** for memory (prerequisites! "BFS is hard because Queues are weak")
3. The 3 memory types, explained with Riya's example
4. Data model walkthrough (diagram)
5. How agents hand off work (sequence diagram)
6. One graph per student: isolation + concurrency (with load-test numbers)
7. 3 Cypher queries I'm proud of (root cause, ready to learn, due for revision)
8. What went wrong / what I learned in 4 days
9. Links: repo, demo, video
