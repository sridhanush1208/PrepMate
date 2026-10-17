# Learning checklist: Fri Oct 9 → Wed Oct 14

Do all practice in a **throwaway folder** (e.g. `D:\scratch\falkor-practice`), not in this project.

## Fri Oct 9 – Sat Oct 10: setup + Cypher basics
- [ ] Register: https://www.wemakedevs.org/hackathons/falkordb
- [ ] Join the FalkorDB Discord: https://discord.com/invite/Y2mMT9VdMy
- [ ] Install **Docker Desktop** for Windows (turn on WSL2 when it asks): https://docs.docker.com/desktop/
- [ ] Install the GitHub CLI: https://cli.github.com/ (optional, but handy)
- [ ] Run FalkorDB and open the Browser:
  ```bash
  docker run -p 6379:6379 -p 3000:3000 -it --rm falkordb/falkordb:latest
  ```
  Then open http://localhost:3000
- [ ] Read: Getting started https://docs.falkordb.com/getting-started/
- [ ] Read: Cypher reference https://docs.falkordb.com/cypher/
- [ ] Watch: "Write effective Cypher queries" https://www.youtube.com/watch?v=emUQmEitSGY
- [ ] Practice in the Browser on a toy "friends + courses" graph, writing these yourself:
  - [ ] Create people and courses with `CREATE`
  - [ ] Find a person's friends with `MATCH`
  - [ ] Add a node only if it doesn't exist, with `MERGE` (run it twice and check for no duplicate)
  - [ ] Update a property with `SET` (e.g. a score)
  - [ ] Insert a list of 10 items in one query with `UNWIND`
  - [ ] Friends-of-friends with a variable-length path `*1..3`
  - [ ] Use two separate graphs (e.g. `alice_graph`, `bob_graph`) and check they don't see each other's data
  - [ ] Run `CALL algo.pageRank(...)` on a small "course prerequisite" graph: https://docs.falkordb.com/algorithms/pagerank
- [ ] Python client: install `falkordb` in a venv and run one query from Python: https://docs.falkordb.com/getting-started/clients

## Sun Oct 11: free LLM access
- [ ] Get a Gemini API key: https://aistudio.google.com/
- [ ] Read Gemini's OpenAI-compatibility page: https://ai.google.dev/gemini-api/docs/openai
- [ ] Get a Groq API key (backup): https://console.groq.com/
- [ ] Practice (throwaway): use the `openai` Python package with Gemini's `base_url`:
  - [ ] Get a normal reply
  - [ ] Get a **JSON-only** reply such as `{ "reply": "...", "score": 0.7 }` and parse it
  - [ ] Switch to Groq by changing only `base_url`, key and model name
  - [ ] Note the free-tier limits you see (requests per minute and per day)

## Mon Oct 12: memory concepts
- [ ] Read the CoALA paper (just the memory section): "Cognitive Architectures for Language Agents", https://arxiv.org/abs/2309.02427
  - **Episodic** = what happened (sessions, attempts)
  - **Semantic** = facts (Riya knows Arrays well, targets SDE)
  - **Procedural** = how to behave (explain with code for Riya)
- [ ] FalkorDB Agentic Memory docs: https://docs.falkordb.com/agentic-memory/
- [ ] mem0 + FalkorDB blog (the one-graph-per-user idea): https://www.falkordb.com/blog/graph-memory-llm-agents-mem0-falkordb/
- [ ] FalkorDB concurrency (reads in parallel, writes one at a time **per graph**): https://docs.falkordb.com/design/concurrency
- [ ] Spaced repetition basics: why revising just before you forget works

## Tue Oct 13 – Wed Oct 14: finish notes, then rest
- [ ] Review and tweak [02-data-model.md](02-data-model.md). Draw it in Excalidraw if you like.
- [ ] Review [03-agent-flow.md](03-agent-flow.md) and [04-demo-story.md](04-demo-story.md)
- [ ] Edit [05-topic-list-draft.md](05-topic-list-draft.md): add or remove topics you care about
- [ ] Create accounts: GitHub (if needed), Hugging Face https://huggingface.co/join
- [ ] Skim HF Docker Spaces: https://huggingface.co/docs/hub/spaces-sdks-docker
- [ ] Install OBS (screen recorder for the demo video): https://obsproject.com/
- [ ] Sleep well on Oct 14 😴
