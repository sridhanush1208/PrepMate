# Interview notes: things you must be able to explain

The rules say you must be able to explain the graph model, queries, architecture and decisions, and so will interviewers. Fill in the answers **in your own words** as you build.

## Concepts
- [ ] Why use a **graph database** for agent memory instead of a SQL table or a vector DB?
  - Hint: memory is about *connections* (topic prerequisites, which message a fact came from, who handed off to whom). Multi-hop questions are easy in Cypher and painful as SQL joins.
- [ ] What are **episodic, semantic and procedural** memory? Give a PrepMate example of each.
- [ ] What is a **handoff**? Why store it in the graph instead of just passing a string?
- [ ] Why **one graph per student**? (isolation, concurrency, easy deletion)
- [ ] How does FalkorDB handle **concurrent reads and writes**? (parallel reads; one write at a time per graph)

## Your design decisions
- [ ] Why copy topics into each student graph instead of querying the catalog?
- [ ] Mastery formula `0.6 × old + 0.4 × score`: why these weights?
- [ ] Forgetting formula with a 14-day half-life: why?
- [ ] Why a hand-written orchestrator instead of LangGraph?
- [ ] How do you stop the LLM from writing junk memory? (JSON contract, retry, fallback, MERGE)
- [ ] Why free-tier Gemini + Groq, and how do you switch?

## Queries (paste your final Cypher here and explain each line)
- [ ] Context pack
- [ ] Root-cause weakness (variable-length path)
- [ ] Ready to learn
- [ ] Due for revision
- [ ] PageRank foundational topics

## Results
- [ ] Load test numbers and what they mean
- [ ] Memory eval numbers and what they mean
- [ ] One thing that went wrong and how you fixed it
