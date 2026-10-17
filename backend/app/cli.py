"""Chat with PrepMate in the terminal (handy for testing without the UI).

Run from backend/:  uv run python -m app.cli --student riya
Commands: /mock [topic]  /teach [topic]  /plan  /memory  /end  /quit
"""
import argparse

from . import memory, orchestrator
from .agents import AGENT_LABELS

COLORS = {"coach": "32", "interviewer": "34", "tutor": "35", "planner": "33"}


def show(events: list[dict]) -> None:
    for e in events:
        if e["type"] == "message":
            c = COLORS.get(e["agent"], "37")
            print(f"\n\033[{c}m{AGENT_LABELS.get(e['agent'], e['agent'])}:\033[0m {e['text']}")
            if e["memories_used"]:
                names = ", ".join(u["query"] for u in e["memories_used"])
                print(f"\033[90m   memories used: {names}\033[0m")
        elif e["type"] == "handoff":
            print(f"\n\033[36m   ↪ handoff {e['from']} → {e['to']}: {e['reason']}\033[0m")
        elif e["type"] == "memory":
            print(f"\033[90m   💾 {e['kind']} saved by {e['agent']}: {e['text']}\033[0m")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--student", default="riya")
    parser.add_argument("--name", default=None)
    parser.add_argument("--role", default="product_sde")
    args = parser.parse_args()

    if not memory.student_exists(args.student):
        memory.ensure_student(args.student, args.name or args.student.title(), args.role)
    session_id, events = orchestrator.start(args.student)
    show(events)

    while True:
        try:
            line = input("\n\033[1mYou:\033[0m ").strip()
        except (EOFError, KeyboardInterrupt):
            line = "/quit"
        if not line:
            continue
        if line in ("/quit", "/end"):
            print("session summary:", orchestrator.end(args.student, session_id))
            break
        if line == "/memory":
            for f in memory.facts_and_rules(args.student):
                print(f" - [{f['kind']}] {f['text']}  (by {f['written_by']}, from: {f['source_text']!r})")
            for t in memory.open_tasks(args.student):
                print(f" - [task] {t['title']} → {t['agent']}")
            continue
        mode, text = "chat", line
        for cmd in ("mock", "teach", "plan"):
            if line.startswith(f"/{cmd}"):
                mode, text = cmd, line[len(cmd) + 1:].strip()
        show(orchestrator.handle(args.student, session_id, text, mode))


if __name__ == "__main__":
    main()
