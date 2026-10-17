# AI usage disclosure

The hackathon rules allow AI coding assistants as long as they are disclosed. This file is that disclosure.

## Tools used
- **Claude Code (Anthropic)** as a pair-programming assistant during the hackathon.

## What the AI helped with
- Researching the hackathon rules and FalkorDB documentation (Cypher, algorithms, concurrency model)
- Drafting the scaffolding: FastAPI routes, React components, Dockerfile, test setup
- Drafting the interview question bank (all questions are original wording, reviewed by me)
- Drafting Cypher queries, which I then ran against FalkorDB, tested and adjusted

## What I designed and decided
- The idea (PrepMate), the agent roles, and the demo story
- The graph data model: one graph per student, the three memory types, provenance edges, handoffs and the task board
- The memory rules (mastery update, forgetting curve) and the choice to keep routing and handoffs LLM-free
- The multi-key LLM fallback requirement

## How I verified it
- 28 automated tests (memory layer, orchestration, LLM fallback) against a real FalkorDB
- Manual end-to-end runs of the demo story in the CLI and the browser
- A concurrency load test against FalkorDB

At runtime, the app itself uses an LLM (Google Gemini, with Groq as fallback) for grading answers, teaching, planning and chat.
