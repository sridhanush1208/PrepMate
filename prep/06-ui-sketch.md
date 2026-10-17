# UI sketch (one page, two halves)

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ PrepMate 🎯            Student: [ Riya ▾ ]   target: Product SDE   [Forget me]│
├───────────────────────────────────────┬──────────────────────────────────────┤
│ CHAT                                  │ MEMORY  [Graph] [Facts&Rules]        │
│                                       │         [Timeline] [Plan]            │
│ 🟢 Coach: Welcome back Riya! Yesterday│                                      │
│    BFS was tricky (0.3)...            │   (force graph: Student in centre,   │
│                                       │    topics coloured by mastery        │
│ 🔵 Interviewer: Here's a hint first...│    red→green, sessions, facts,       │
│   ▸ memories used (3)  ▸ cypher       │    rules, handoffs)                  │
│                                       │                                      │
│ ┄┄┄ Interviewer → Tutor: struggled ┄┄ │  Facts & Rules tab:                  │
│ ┄┄┄ with BFS level order       ┄┄┄┄┄ │  • "Targets Product SDE" (Coach,     │
│                                       │     from msg #12)  [🗑]               │
│ 🟣 Tutor: Your Queues basics look     │  • RULE → Interviewer: "hint before  │
│    weak too, let's start there...     │     full answer" (from msg #31) [🗑]  │
│                                       │                                      │
│ [🎤 Mock interview] [📘 Teach me]      │  Plan tab: ☐ Retry BFS (tomorrow)    │
│ [🗓 Plan my week]                      │            ☐ Revise Hashing (due)    │
│ ┌───────────────────────────┐ [Send]  │                                      │
│ └───────────────────────────┘         │                                      │
└───────────────────────────────────────┴──────────────────────────────────────┘
```

## Pieces
- **Student picker**: demo users (Riya, Arjun) + "new student"
- **Agent colours**: Coach 🟢, Interviewer 🔵, Tutor 🟣, Planner 🟠
- **Handoff banner**: a dashed line between messages showing from → to and the reason
- **"memories used"** (expandable under each agent reply): which memory nodes were read + the Cypher query. This is the explainability bit.
- **Memory panel tabs**
  - Graph: `react-force-graph-2d`, click a node to see its details
  - Facts & Rules: each with source message + writing agent + delete button
  - Timeline: sessions and attempts with scores (episodic)
  - Plan: task board from the Planner
- Keep it simple: Tailwind, no fancy design system. It should look clean in the video.
