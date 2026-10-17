"""Create demo students with a believable past.

Riya (Product SDE): two earlier sessions. Good at Arrays/Hashing, weak at Queues,
Sorting is fading (practised 20 days ago), likes code examples, has a "Try BFS" task.
Arjun (Service-based): brand new, empty memory.

Run from backend/:  uv run python -m scripts.seed_demo_students
"""
import sys

from app import memory

DAY = 86_400_000


def seed_riya() -> None:
    sid = "riya"
    memory.forget_student(sid)
    base = memory.now_ms()
    memory.ensure_student(sid, "Riya", "product_sde", now=base - 21 * DAY)

    # Session A: 20 days ago, sorting went well
    t = base - 20 * DAY
    s1 = memory.start_session(sid, now=t)
    memory.add_message(sid, s1, "user", "Hi! I'm preparing for product company SDE roles.", now=t)
    m = memory.add_message(sid, s1, "user", "I code in Java mostly.", now=t + 1000)
    memory.add_fact(sid, "coach", "Targets Product SDE roles", m, about_id=sid, now=t + 2000)
    memory.add_fact(sid, "coach", "Codes mostly in Java", m, about_id=sid, now=t + 3000)
    for qid, score in (("q_sorting_1", 0.8), ("q_sorting_2", 0.7)):
        memory.record_attempt(sid, s1, memory.get_question(qid), score, "Good answer.", "(seeded)", now=t + 5000)
    memory.end_session(sid, s1, now=t + 60_000)

    # Session B: 2 days ago, arrays/hashing strong, queues weak, asked for code examples
    t = base - 2 * DAY
    s2 = memory.start_session(sid, now=t)
    for qid, score in (("q_arrays_1", 0.8), ("q_hashing_1", 0.9), ("q_queues_1", 0.3)):
        memory.record_attempt(sid, s2, memory.get_question(qid), score,
                              "Seeded attempt.", "(seeded)", now=t + 5000)
    m = memory.add_message(sid, s2, "user",
                           "I understand much better when you explain with code examples.", now=t + 6000)
    memory.add_rule(sid, "tutor", "tutor", "Explain concepts with short Java code examples", m, now=t + 7000)
    memory.create_task(sid, "Try your first BFS question", "bfs", "interviewer",
                       due_in_days=1, agent="planner", now=t + 8000)
    memory.end_session(sid, s2, now=t + 60_000)


def seed_arjun() -> None:
    memory.forget_student("arjun")
    memory.ensure_student("arjun", "Arjun", "service_based")


def main() -> None:
    if "--if-missing" in sys.argv and memory.student_exists("riya"):
        print("demo students already exist, skipping")
        return
    seed_riya()
    seed_arjun()
    print("seeded demo students: riya, arjun")


if __name__ == "__main__":
    main()
