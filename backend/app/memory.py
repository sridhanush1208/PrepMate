"""PrepMate memory layer: every read and write of agent memory goes through here.

Memory lives in one FalkorDB graph per student ("pm_<id>"):
  - episodic:   Session, Message (NEXT chain), Attempt
  - semantic:   (Student)-[:KNOWS {mastery}]->(Topic), Fact
  - procedural: Rule -[:APPLIES_TO]-> Agent
  - shared:     Handoff, Task (the agents' coordination board)
"""
import re
import time
import uuid

from . import config
from .db import catalog, graph_exists, graph_name, rows, student_graph, write
from .queries import q


def now_ms() -> int:
    return int(time.time() * 1000)


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:10]}"


def normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9 ]+", "", text.lower()).strip()


class Recall:
    """Collects which named queries were used to build an agent's context.

    The UI shows this list under each reply as "memories used".
    """

    def __init__(self):
        self.used: list[dict] = []

    def run(self, graph, name: str, params: dict) -> list[dict]:
        result = rows(graph, name, params)
        self.used.append({"query": name, "cypher": q(name), "rows": len(result)})
        return result


# ---------------------------------------------------------------- students

def ensure_student(student_id: str, name: str, target_role: str, now: int | None = None) -> None:
    """Create the student's private graph: topics, prerequisites, agents, KNOWS edges."""
    now = now or now_ms()
    g = student_graph(student_id)
    topics = rows(catalog(), "catalog_topics_for_role", {"role": target_role})
    prereqs = rows(catalog(), "catalog_prereqs")
    for stmt in (
        "CREATE INDEX FOR (t:Topic) ON (t.id)",
        "CREATE INDEX FOR (m:Message) ON (m.id)",
        "CREATE INDEX FOR (s:Session) ON (s.id)",
        "CREATE INDEX FOR (a:Agent) ON (a.name)",
    ):
        try:
            g.query(stmt)
        except Exception:
            pass  # index already exists
    write(g, "student_create", {
        "student": {"id": student_id, "name": name, "target_role": target_role},
        "topics": topics,
        "now": now,
    })
    write(g, "student_create_prereqs", {"prereqs": prereqs})
    write(g, "student_create_agents", {"agents": config.AGENTS})


def student_exists(student_id: str) -> bool:
    return graph_exists(graph_name(student_id))


def profile(student_id: str) -> dict | None:
    result = rows(student_graph(student_id), "student_profile")
    return result[0] if result else None


def forget_student(student_id: str) -> None:
    """'Forget me': the whole memory graph is deleted."""
    if student_exists(student_id):
        student_graph(student_id).delete()


# ---------------------------------------------------------------- sessions + messages

def start_session(student_id: str, now: int | None = None) -> str:
    session_id = new_id("ses")
    write(student_graph(student_id), "session_start", {"session_id": session_id, "now": now or now_ms()})
    return session_id


def get_session(student_id: str, session_id: str) -> dict | None:
    result = rows(student_graph(student_id), "session_get", {"session_id": session_id})
    return result[0] if result else None


def set_pending_question(student_id: str, session_id: str, question_id: str, topic_id: str) -> None:
    write(student_graph(student_id), "session_set_pending",
          {"session_id": session_id, "question_id": question_id, "topic_id": topic_id})


def clear_pending_question(student_id: str, session_id: str) -> None:
    write(student_graph(student_id), "session_clear_pending", {"session_id": session_id})


def end_session(student_id: str, session_id: str, now: int | None = None) -> str:
    """Close a session with a short summary built from its attempts (no LLM needed)."""
    g = student_graph(student_id)
    attempts = rows(g, "session_attempts", {"session_id": session_id})
    if attempts:
        parts = [f"{a['topic']} ({a['score']:.1f})" for a in attempts]
        summary = "Practised " + ", ".join(parts) + "."
    else:
        summary = "Chatted, no mock questions."
    write(g, "session_end", {"session_id": session_id, "summary": summary, "now": now or now_ms()})
    return summary


def add_message(student_id: str, session_id: str, role: str, text: str,
                agent: str | None = None, now: int | None = None) -> str:
    message_id = new_id("msg")
    write(student_graph(student_id), "message_add", {
        "session_id": session_id, "id": message_id, "role": role,
        "agent": agent or "", "text": text, "now": now or now_ms(),
    })
    return message_id


def recent_messages(student_id: str, session_id: str, limit: int = 8) -> list[dict]:
    result = rows(student_graph(student_id), "recent_messages", {"session_id": session_id, "limit": limit})
    return list(reversed(result))


# ---------------------------------------------------------------- attempts + mastery

def record_attempt(student_id: str, session_id: str, question: dict, score: float,
                   feedback: str, answer: str, now: int | None = None) -> dict:
    """Save an Attempt and update mastery: first try = score, then 0.6*old + 0.4*score."""
    now = now or now_ms()
    g = student_graph(student_id)
    score = max(0.0, min(1.0, float(score)))
    result = write(g, "record_attempt", {
        "topic_id": question["topic_id"],
        "session_id": session_id,
        "question": {"id": question["id"], "text": question["text"], "difficulty": question.get("difficulty", 1)},
        "attempt_id": new_id("att"),
        "score": score,
        "feedback": feedback,
        "answer": answer,
        "new_weight": config.NEW_WEIGHT,
        "now": now,
    })
    write(g, "tasks_complete_for_topic", {"topic_id": question["topic_id"], "now": now})
    return result[0] if result else {}


def attempted_question_ids(student_id: str) -> list[str]:
    result = rows(student_graph(student_id), "attempted_question_ids")
    return result[0]["ids"] if result else []


# ---------------------------------------------------------------- facts + rules

def add_fact(student_id: str, agent: str, text: str, message_id: str,
             about_id: str, confidence: float = 0.8, now: int | None = None) -> str | None:
    result = write(student_graph(student_id), "fact_add", {
        "agent": agent, "message_id": message_id, "about_id": about_id,
        "key": normalise(text), "id": new_id("fact"), "text": text,
        "confidence": confidence, "now": now or now_ms(),
    })
    return result[0]["id"] if result else None


def add_rule(student_id: str, agent: str, applies_to: str, text: str,
             message_id: str, now: int | None = None) -> str | None:
    result = write(student_graph(student_id), "rule_add", {
        "agent": agent, "applies_to": applies_to, "message_id": message_id,
        "key": f"{applies_to}:{normalise(text)}", "id": new_id("rule"),
        "text": text, "now": now or now_ms(),
    })
    return result[0]["id"] if result else None


def delete_memory(student_id: str, memory_id: str) -> None:
    write(student_graph(student_id), "memory_delete", {"id": memory_id})


# ---------------------------------------------------------------- handoffs + tasks

def create_handoff(student_id: str, session_id: str, from_agent: str, to_agent: str,
                   reason: str, topic_id: str | None, now: int | None = None) -> str:
    handoff_id = new_id("ho")
    write(student_graph(student_id), "handoff_create", {
        "id": handoff_id, "session_id": session_id, "from_agent": from_agent,
        "to_agent": to_agent, "reason": reason, "topic_id": topic_id or "", "now": now or now_ms(),
    })
    return handoff_id


def open_handoff(student_id: str, agent: str) -> dict | None:
    result = rows(student_graph(student_id), "handoff_open", {"agent": agent})
    return result[0] if result else None


def pick_handoff(student_id: str, handoff_id: str) -> None:
    write(student_graph(student_id), "handoff_pick", {"id": handoff_id, "now": now_ms()})


def create_task(student_id: str, title: str, topic_id: str, assign_to: str,
                due_in_days: float = 1, agent: str = "planner", now: int | None = None) -> str | None:
    now = now or now_ms()
    result = write(student_graph(student_id), "task_create", {
        "assign_to": assign_to, "agent": agent, "topic_id": topic_id,
        "key": f"{assign_to}:{topic_id}", "id": new_id("task"), "title": title,
        "due": now + int(due_in_days * 86_400_000), "now": now,
    })
    return result[0]["id"] if result else None


def open_tasks(student_id: str) -> list[dict]:
    return rows(student_graph(student_id), "tasks_open")


# ---------------------------------------------------------------- recall

def topic_state(student_id: str, topic_id: str) -> dict | None:
    result = rows(student_graph(student_id), "topic_state", {"topic_id": topic_id})
    return result[0] if result else None


def root_cause(student_id: str, topic_id: str) -> list[dict]:
    return rows(student_graph(student_id), "root_cause", {"topic_id": topic_id, "weak": config.WEAK_BELOW})


def weak_topics(student_id: str, limit: int = 5) -> list[dict]:
    return rows(student_graph(student_id), "weak_topics", {"weak": config.WEAK_BELOW, "limit": limit})


def ready_to_learn(student_id: str, limit: int = 5) -> list[dict]:
    return rows(student_graph(student_id), "ready_to_learn", {"mastered": config.MASTERED_AT, "limit": limit})


def due_for_revision(student_id: str, now: int | None = None) -> list[dict]:
    return rows(student_graph(student_id), "due_for_revision", {
        "weak": config.WEAK_BELOW, "half_life": config.HALF_LIFE_DAYS, "now": now or now_ms(),
    })


def welcome_back(student_id: str, session_id: str) -> dict | None:
    result = rows(student_graph(student_id), "welcome_back", {"session_id": session_id})
    if not result or not result[0].get("previous"):
        return None
    last = result[0]
    last["attempts"] = [a for a in (last.get("attempts") or []) if a]
    return last


def context_pack(student_id: str, agent: str, topic_id: str | None = None,
                 now: int | None = None) -> tuple[dict, list[dict]]:
    """Everything an agent should remember before replying, plus which queries were used."""
    g = student_graph(student_id)
    recall = Recall()
    pack: dict = {
        "rules": recall.run(g, "rules_for_agent", {"agent": agent}),
        "all_saved_rules": recall.run(g, "rules_all", {}),
        "facts": recall.run(g, "student_facts", {}),
        "open_handoff": next(iter(recall.run(g, "handoff_open", {"agent": agent})), None),
        "open_tasks": recall.run(g, "tasks_open", {}),
        "weak_topics": recall.run(g, "weak_topics", {"weak": config.WEAK_BELOW, "limit": 5}),
    }
    if topic_id:
        pack["topic"] = next(iter(recall.run(g, "topic_state", {"topic_id": topic_id})), None)
        pack["recent_attempts"] = recall.run(g, "recent_attempts", {"topic_id": topic_id})
        pack["root_cause"] = recall.run(g, "root_cause", {"topic_id": topic_id, "weak": config.WEAK_BELOW})
    if agent in ("planner", "coach"):
        pack["due_for_revision"] = recall.run(g, "due_for_revision", {
            "weak": config.WEAK_BELOW, "half_life": config.HALF_LIFE_DAYS, "now": now or now_ms(),
        })
        pack["ready_to_learn"] = recall.run(g, "ready_to_learn", {"mastered": config.MASTERED_AT, "limit": 6})
    return pack, recall.used


# ---------------------------------------------------------------- catalog helpers

def pick_question(student_id: str, topic_id: str) -> dict | None:
    exclude = attempted_question_ids(student_id)
    result = rows(catalog(), "catalog_pick_question", {"topic_id": topic_id, "exclude": exclude})
    if not result:
        result = rows(catalog(), "catalog_any_question", {"topic_id": topic_id})
    return result[0] if result else None


def get_question(question_id: str) -> dict | None:
    result = rows(catalog(), "catalog_question", {"id": question_id})
    return result[0] if result else None


def catalog_topics() -> list[dict]:
    return rows(catalog(), "catalog_topics")


def catalog_roles() -> list[dict]:
    return rows(catalog(), "catalog_roles")


# ---------------------------------------------------------------- memory panel (UI)

def facts_and_rules(student_id: str) -> list[dict]:
    return rows(student_graph(student_id), "facts_and_rules")


def timeline(student_id: str) -> list[dict]:
    result = rows(student_graph(student_id), "timeline")
    for row in result:
        row["attempts"] = [a for a in (row.get("attempts") or []) if a]
    return result


def mastery_overview(student_id: str) -> list[dict]:
    return rows(student_graph(student_id), "mastery_overview")


def memory_graph(student_id: str) -> dict:
    """Nodes + links for the UI graph view. Hides untouched topics to keep it readable."""
    result = student_graph(student_id).ro_query(q("memory_graph"))
    nodes: dict[int, dict] = {}
    edges = []
    used_topics: set[int] = set()

    def add_node(n):
        label = n.labels[0] if n.labels else "Node"
        props = dict(n.properties)
        nodes[n.id] = {
            "id": n.id,
            "label": label,
            "name": str(props.get("name") or props.get("text") or props.get("title")
                        or props.get("reason") or props.get("id") or label)[:60],
            "props": {k: v for k, v in props.items() if k not in ("key",)},
        }

    for a, r, b in result.result_set:
        add_node(a)
        add_node(b)
        edges.append({"source": a.id, "target": b.id, "type": r.relation, "props": dict(r.properties)})
        if r.relation == "KNOWS" and r.properties.get("attempts", 0) > 0:
            used_topics.add(b.id)
        if r.relation in ("ABOUT", "PRACTICES", "TESTS"):
            used_topics.add(b.id)

    keep = {nid for nid, n in nodes.items() if n["label"] != "Topic" or nid in used_topics}
    return {
        "nodes": [n for nid, n in nodes.items() if nid in keep],
        "links": [e for e in edges if e["source"] in keep and e["target"] in keep],
    }
