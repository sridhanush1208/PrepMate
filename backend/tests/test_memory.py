"""Memory-layer tests. Need a running FalkorDB (docker compose up -d).

Run from backend/:  uv run pytest -v
"""
import pytest

from app import config, llm, memory, orchestrator
from app.db import get_db

DAY = 86_400_000


def _db_up() -> bool:
    try:
        get_db().list_graphs()
        return True
    except Exception:
        return False


pytestmark = pytest.mark.skipif(not _db_up(), reason="FalkorDB is not running")


@pytest.fixture(scope="session", autouse=True)
def catalog_loaded():
    from scripts import seed_catalog
    seed_catalog.main()
    llm._POOL = llm.KeyPool([])  # use the offline mock LLM in tests


@pytest.fixture
def student():
    sid = "test_alice"
    memory.forget_student(sid)
    memory.ensure_student(sid, "Alice", "product_sde")
    yield sid
    memory.forget_student(sid)


def _attempt(sid, session, qid, score, now=None):
    return memory.record_attempt(sid, session, memory.get_question(qid), score, "fb", "ans", now=now)


def test_student_graph_has_topics_and_agents(student):
    assert memory.profile(student)["name"] == "Alice"
    state = memory.topic_state(student, "bfs")
    assert state["mastery"] == 0.0 and state["attempts"] == 0


def test_mastery_update_rule(student):
    s = memory.start_session(student)
    first = _attempt(student, s, "q_bfs_1", 0.5)
    assert first["new_mastery"] == pytest.approx(0.5)            # first attempt = score
    second = _attempt(student, s, "q_bfs_2", 1.0)
    assert second["new_mastery"] == pytest.approx(0.6 * 0.5 + 0.4 * 1.0)


def test_message_chain(student):
    s = memory.start_session(student)
    for text in ("one", "two", "three"):
        memory.add_message(student, s, "user", text)
    assert [m["text"] for m in memory.recent_messages(student, s)] == ["one", "two", "three"]
    chained = memory.student_graph(student).ro_query(
        "MATCH (:Message)-[:NEXT]->(:Message) RETURN count(*)").result_set[0][0]
    assert chained == 2


def test_root_cause_finds_weak_prerequisite(student):
    s = memory.start_session(student)
    _attempt(student, s, "q_queues_1", 0.2)       # queues weak
    _attempt(student, s, "q_graph_basics_1", 0.9)  # graph basics strong
    causes = {c["topic_id"]: c for c in memory.root_cause(student, "bfs")}
    assert causes["queues"]["status"] == "weak"
    assert "graph_basics" not in causes


def test_ready_to_learn_respects_prerequisites(student):
    ready = {r["topic_id"] for r in memory.ready_to_learn(student, limit=50)}
    assert "complexity" in ready and "bfs" not in ready


def test_due_for_revision_uses_forgetting_curve(student):
    s = memory.start_session(student)
    long_ago = memory.now_ms() - 30 * DAY
    _attempt(student, s, "q_sorting_1", 0.9, now=long_ago)
    due = {d["topic_id"] for d in memory.due_for_revision(student)}
    assert "sorting" in due


def test_fact_dedupe_and_provenance(student):
    s = memory.start_session(student)
    m = memory.add_message(student, s, "user", "I code in Java")
    memory.add_fact(student, "coach", "Codes in Java", m, about_id=student)
    memory.add_fact(student, "coach", "codes in java!", m, about_id=student)
    facts = [f for f in memory.facts_and_rules(student) if f["kind"] == "Fact"]
    assert len(facts) == 1
    assert facts[0]["written_by"] == "coach" and facts[0]["source_text"] == "I code in Java"


def test_rule_applies_to_agent(student):
    s = memory.start_session(student)
    m = memory.add_message(student, s, "user", "hint first please")
    memory.add_rule(student, "tutor", "interviewer", "Give a hint before the question", m)
    pack, used = memory.context_pack(student, "interviewer")
    assert pack["rules"][0]["text"] == "Give a hint before the question"
    assert any(u["query"] == "rules_for_agent" for u in used)
    tutor_pack, _ = memory.context_pack(student, "tutor")
    assert tutor_pack["rules"] == []


def test_handoff_and_task_board(student):
    s = memory.start_session(student)
    memory.create_handoff(student, s, "interviewer", "tutor", "struggled", "bfs")
    h = memory.open_handoff(student, "tutor")
    assert h["topic_id"] == "bfs" and h["from_agent"] == "interviewer"
    memory.pick_handoff(student, h["id"])
    assert memory.open_handoff(student, "tutor") is None

    memory.create_task(student, "Retry BFS", "bfs", "interviewer")
    memory.create_task(student, "Retry BFS again", "bfs", "interviewer")  # same key -> no duplicate
    assert len(memory.open_tasks(student)) == 1
    _attempt(student, s, "q_bfs_1", 0.7)  # practising closes the task
    assert memory.open_tasks(student) == []


def test_students_are_isolated(student):
    other = "test_bob"
    memory.forget_student(other)
    memory.ensure_student(other, "Bob", "service_based")
    s = memory.start_session(student)
    m = memory.add_message(student, s, "user", "secret")
    memory.add_fact(student, "coach", "Alice secret fact", m, about_id=student)
    assert memory.facts_and_rules(other) == []
    memory.forget_student(other)
    assert not memory.student_exists(other)


def test_low_score_hands_off_to_tutor_and_plans_retry(student):
    session_id, _ = orchestrator.start(student)
    orchestrator.handle(student, session_id, "bfs", "mock")
    events = orchestrator.handle(student, session_id, "uses a queue", "chat")  # short -> mock scores 0.3
    kinds = [e["type"] for e in events]
    assert "handoff" in kinds
    assert any(e["type"] == "message" and e["agent"] == "tutor" for e in events)
    assert any(t["title"] == "Retry BFS" for t in memory.open_tasks(student))
    assert memory.topic_state(student, "bfs")["attempts"] == 1


def test_welcome_back_mentions_last_session(student):
    s1, _ = orchestrator.start(student)
    _attempt(student, s1, "q_bfs_1", 0.3)
    orchestrator.end(student, s1)
    _, events = orchestrator.start(student)
    assert "BFS" in events[0]["text"] and "Welcome back" in events[0]["text"]


def test_welcome_back_skips_empty_sessions(student):
    s1, _ = orchestrator.start(student)
    _attempt(student, s1, "q_bfs_1", 0.3)
    for _ in range(2):  # opened the app twice without practising
        empty, _ = orchestrator.start(student)
        orchestrator.end(student, empty)
    _, events = orchestrator.start(student)
    assert "BFS" in events[0]["text"] and "0.3" in events[0]["text"]


def test_first_visit_is_not_welcome_back(student):
    _, events = orchestrator.start(student)
    assert "Welcome back" not in events[0]["text"]
