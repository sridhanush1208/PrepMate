# Demo story + video script

## Characters (synthetic demo users)
- **Riya**: final-year student, targets *Product SDE*. Has 2 seeded past sessions: good at Arrays and Hashing, weak at Queues, has never tried BFS. Once said "I understand better with code examples."
- **Arjun**: brand-new user, targets *Service-based*. Empty memory.

## The story
**Session 1 (Riya)**
1. Riya clicks **Mock interview**. The Coach routes to the **Interviewer**.
2. The Interviewer picks a BFS question (ready to learn + important for Product SDE).
3. Riya gives a half-correct answer → **score 0.3** → Attempt saved, BFS mastery set.
4. **Handoff banner:** "Interviewer → Tutor: struggled with BFS level order".
5. The **Tutor** finds the root cause: *Queues* mastery is also low (multi-hop). It explains Queues → BFS **with code**, because of Riya's procedural rule.
6. Riya says "please give me a hint before the full answer next time" → new **Rule** saved for the Interviewer.
7. The **Planner** adds task: "Retry BFS, tomorrow (Interviewer)".

**Restart the app** (`docker compose restart`): memory must survive.

**Session 2 (Riya, "next day")**
8. The Coach: "Welcome back Riya! Yesterday BFS was tricky (0.3). Your plan says retry BFS today. Ready?"
9. The Interviewer asks a BFS question and **gives a hint first** (it followed the new rule).
10. Riya does better → score 0.8 → mastery goes up, visible in the memory panel.

**Isolation check**
11. Switch to **Arjun**: the Coach knows nothing about Riya. The memory panel is empty.
12. Click **Forget me** on a test user → its graph is deleted.

## 3-minute video script
| Time | Show | Say (roughly) |
|---|---|---|
| 0:00–0:20 | Title + problem | "Placement-prep chatbots forget you every time. PrepMate is a team of 4 agents with shared, persistent graph memory in FalkorDB." |
| 0:20–0:45 | Architecture + data model diagram | "Each student gets their own graph. Episodic, semantic and procedural memory, plus handoffs and a task board." |
| 0:45–1:40 | Session 1 live | Mock interview → low score → handoff banner → Tutor root cause → code explanation → new rule |
| 1:40–1:55 | Terminal: restart | "Restarting the server: memory lives in FalkorDB, not in RAM." |
| 1:55–2:25 | Session 2 live | Welcome back → hint first → score up → memory panel updates |
| 2:25–2:40 | Arjun + Forget me | Isolation per user |
| 2:40–2:55 | Load test + eval numbers | "X ops/sec, p95 Y ms at 200 users; recall A% → B%." |
| 2:55–3:00 | Links | Repo, live demo, blog |

Tips: record at 1080p, use a big browser zoom, and pre-seed so nothing depends on luck. Do 2 takes and keep the better one.
