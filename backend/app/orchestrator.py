"""One chat turn: route -> recall memory -> (LLM) -> write memory -> handoff.

Every function returns a list of events for the UI:
  {"type": "message", "agent", "text", "memories_used", "provider"}
  {"type": "handoff", "from", "to", "reason", "topic"}
  {"type": "memory",  "agent", "kind", "text"}
"""
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache

from . import config, memory
from .agents import AGENT_LABELS, build_prompt
from .llm import LLMUnavailable, chat_json

log = logging.getLogger("prepmate.orchestrator")

LLM_DOWN = ("I couldn't reach the AI model just now (free-tier limit or network). "
            "Your memory is safe, so please try again in a minute.")

# Agent writes that run in the background (e.g. the Planner adding a task while the Tutor replies)
_background = ThreadPoolExecutor(max_workers=8)


# ---------------------------------------------------------------- helpers

@lru_cache(maxsize=1)
def _topics() -> list[dict]:
    return memory.catalog_topics()


def topic_ids() -> set[str]:
    return {t["id"] for t in _topics()}


def topic_name(topic_id: str | None) -> str:
    return next((t["name"] for t in _topics() if t["id"] == topic_id), topic_id or "")


def find_topic(text: str) -> str | None:
    """Find a topic mentioned in free text (longest match wins)."""
    text = f" {re.sub(r'[^a-z0-9+ ]+', ' ', text.lower())} "
    best, best_len = None, 0
    for t in _topics():
        variants = {t["id"].replace("_", " "), t["name"].lower()}
        variants |= {p.strip().lower() for p in re.split(r"[/&()]", t["name"]) if len(p.strip()) >= 3}
        for v in variants:
            v = re.sub(r"[^a-z0-9+ ]+", " ", v).strip()
            if v and f" {v} " in text and len(v) > best_len:
                best, best_len = t["id"], len(v)
    return best


def _message(agent: str, text: str, used: list[dict] | None = None, provider: str = "") -> dict:
    return {"type": "message", "agent": agent, "text": text, "memories_used": used or [], "provider": provider}


def _say(student_id: str, session_id: str, agent: str, text: str,
         used: list[dict] | None = None, provider: str = "") -> dict:
    memory.add_message(student_id, session_id, "agent", text, agent=agent)
    return _message(agent, text, used, provider)


def apply_updates(student_id: str, agent: str, updates, message_id: str) -> list[dict]:
    """Write the LLM's memory_updates to the graph (validated; bad items are skipped)."""
    events = []
    valid_topics = topic_ids()
    for u in updates if isinstance(updates, list) else []:
        if not isinstance(u, dict) or not str(u.get("text", "")).strip():
            continue
        kind, text = u.get("kind"), str(u["text"]).strip()[:200]
        try:
            if kind == "fact":
                about = u.get("about_topic_id") if u.get("about_topic_id") in valid_topics else student_id
                memory.add_fact(student_id, agent, text, message_id, about_id=about)
                events.append({"type": "memory", "agent": agent, "kind": "fact", "text": text})
            elif kind == "rule":
                applies_to = u.get("applies_to") if u.get("applies_to") in config.AGENTS else agent
                memory.add_rule(student_id, agent, applies_to, text, message_id)
                events.append({"type": "memory", "agent": agent, "kind": "rule",
                               "text": f"{text} (for {AGENT_LABELS[applies_to]})"})
            elif kind == "task" and u.get("topic_id") in valid_topics:
                assign_to = u.get("assign_to") if u.get("assign_to") in ("interviewer", "tutor") else "interviewer"
                days = float(u.get("due_in_days") or 1)
                memory.create_task(student_id, text, u["topic_id"], assign_to, due_in_days=max(0.5, min(days, 14)))
                events.append({"type": "memory", "agent": agent, "kind": "task",
                               "text": f"{text} → {AGENT_LABELS[assign_to]}"})
        except Exception as e:  # never let one bad update break the turn
            log.warning("skipped memory update %s: %s", u, e)
    return events


def _llm_turn(role_key: str, agent: str, student_id: str, session_id: str, pack: dict,
              used: list[dict], user_text: str, message_id: str, extra: str = "") -> tuple[list[dict], dict]:
    """Run one LLM call for an agent, save its reply and memory updates."""
    student = memory.profile(student_id) or {}
    recent = memory.recent_messages(student_id, session_id, limit=8)
    system, prompt = build_prompt(role_key, student, pack, recent, user_text, extra)
    try:
        data, provider = chat_json(system, prompt)
    except LLMUnavailable:
        return [_say(student_id, session_id, agent, LLM_DOWN, used)], {}
    reply = str(data.get("reply") or "").strip() or "…"
    events = [_say(student_id, session_id, agent, reply, used, provider)]
    events += apply_updates(student_id, agent, data.get("memory_updates"), message_id)
    return events, data


# ---------------------------------------------------------------- session start

def start(student_id: str) -> tuple[str, list[dict]]:
    """New session: the Coach greets the student using episodic memory (no LLM needed)."""
    session_id = memory.start_session(student_id)
    student = memory.profile(student_id) or {}
    g = memory.student_graph(student_id)
    recall = memory.Recall()
    last = recall.run(g, "welcome_back", {"session_id": session_id})
    tasks = recall.run(g, "tasks_open", {})
    due = recall.run(g, "due_for_revision", {"weak": config.WEAK_BELOW,
                                            "half_life": config.HALF_LIFE_DAYS, "now": memory.now_ms()})
    name = student.get("name", "there")
    lines = []
    attempts = [a for a in (last[0].get("attempts") or []) if a] if last else []
    if last and last[0].get("previous"):
        lines.append(f"Welcome back, **{name}**! 👋")
        if attempts:
            worst = min(attempts, key=lambda a: a["score"])
            practised = ", ".join(f"{a['topic']} ({a['score']:.1f})" for a in attempts)
            lines.append(f"Last time you practised {practised}.")
            if worst["score"] < config.WEAK_BELOW:
                lines.append(f"**{worst['topic']}** was tricky: you scored {worst['score']:.1f}.")
    else:
        lines.append(f"Hi **{name}**! I'm your Coach. 🎯 I'll remember how you do across sessions, "
                     "and so will the rest of the team: Interviewer, Tutor and Planner.")
    if tasks:
        t = tasks[0]
        lines.append(f"Your plan says: **{t['title']}** (with the {AGENT_LABELS.get(t['agent'], t['agent'])}).")
    if due:
        d = due[0]
        lines.append(f"Also, **{d['topic']}** is fading from memory. A quick revision would help.")
    lines.append("Pick **Mock interview**, **Teach me** or **Plan my week**, or just chat.")
    text = " ".join(lines)
    return session_id, [_say(student_id, session_id, "coach", text, recall.used)]


def end(student_id: str, session_id: str) -> str:
    return memory.end_session(student_id, session_id)


# ---------------------------------------------------------------- routing

def route(text: str, mode: str, session: dict) -> str:
    t = text.lower()
    if mode == "mock":
        return "interviewer_ask"
    if mode == "teach":
        return "tutor"
    if mode == "plan":
        return "planner"
    if session.get("pending_question"):
        return "interviewer_skip" if t.strip() in ("skip", "next", "pass") else "interviewer_grade"
    # "next time please give me a hint" is a preference -> Coach saves it as a rule
    if re.search(r"\b(next time|from now on|in future|i prefer|i like|i learn better|always|never)\b", t):
        return "coach"
    if re.search(r"\b(mock|interview|quiz|test me|ask me)\b", t):
        return "interviewer_ask"
    if re.search(r"\b(plan|schedule|roadmap|this week|timetable)\b", t):
        return "planner"
    if re.search(r"\b(explain|teach|what is|what are|how does|how do|why|help me understand)\b", t):
        return "tutor"
    return "coach"


def handle(student_id: str, session_id: str, text: str, mode: str = "chat") -> list[dict]:
    text = (text or "").strip()
    session = memory.get_session(student_id, session_id) or {}
    message_id = memory.add_message(student_id, session_id, "user", text or f"[{mode}]")
    action = route(text, mode, session)
    topic = find_topic(text) if text else None

    if action == "interviewer_ask":
        return interviewer_ask(student_id, session_id, topic)
    if action == "interviewer_skip":
        memory.clear_pending_question(student_id, session_id)
        return [_say(student_id, session_id, "interviewer", "No problem, skipped. Press **Mock interview** for another one.")]
    if action == "interviewer_grade":
        return interviewer_grade(student_id, session_id, session, text, message_id)
    if action == "tutor":
        return tutor_turn(student_id, session_id, topic, text, message_id)
    if action == "planner":
        return planner_turn(student_id, session_id, text, message_id)
    return coach_turn(student_id, session_id, text, message_id)


# ---------------------------------------------------------------- agents

def _choose_topic(student_id: str) -> tuple[str, str]:
    """Interviewer topic choice, all from memory: task board > fading > weak > ready-to-learn."""
    for t in memory.open_tasks(student_id):
        if t["agent"] == "interviewer":
            return t["topic_id"], f"From your plan: **{t['title']}**."
    due = memory.due_for_revision(student_id)
    if due:
        return due[0]["topic_id"], f"**{due[0]['topic']}** is fading from memory, so let's revise it."
    weak = memory.weak_topics(student_id, limit=1)
    if weak:
        return weak[0]["topic_id"], f"Let's retry **{weak[0]['topic']}** (mastery {weak[0]['mastery']:.1f})."
    ready = memory.ready_to_learn(student_id, limit=1)
    if ready:
        return ready[0]["topic_id"], f"**{ready[0]['topic']}** is next: you're ready for it and it matters for your role."
    return "arrays", "Let's start with Arrays."


def interviewer_ask(student_id: str, session_id: str, topic_id: str | None) -> list[dict]:
    reason = ""
    if not topic_id:
        topic_id, reason = _choose_topic(student_id)
    question = memory.pick_question(student_id, topic_id)
    if not question:
        return [_say(student_id, session_id, "interviewer", "I couldn't find a question for that topic.")]
    memory.set_pending_question(student_id, session_id, question["id"], topic_id)
    pack, used = memory.context_pack(student_id, "interviewer", topic_id)

    if pack["rules"]:  # procedural memory changes how the question is asked
        extra = (f"QUESTION ({question['topic']}): {question['text']}\nHINT: {question['hint']}\n"
                 f"WHY THIS TOPIC: {reason}")
        student = memory.profile(student_id) or {}
        system, prompt = build_prompt("interviewer_ask", student, pack, [], "(asked for a mock question)", extra)
        try:
            data, provider = chat_json(system, prompt, temperature=0.2)
            return [_say(student_id, session_id, "interviewer", str(data.get("reply", "")).strip(), used, provider)]
        except LLMUnavailable:
            pass  # fall back to the plain question below
    text = f"{reason} 🎤 **{question['topic']}** question:\n\n{question['text']}\n\n_Type your answer, or 'skip'._".strip()
    return [_say(student_id, session_id, "interviewer", text, used)]


def _read_score(data: dict) -> float:
    """Score from the JSON field; if the model forgot it, read "Score: 0.4" / "4/10" from the reply text."""
    value = data.get("score")
    if value is None:
        text = str(data.get("reply", ""))
        m = re.search(r"(\d+(?:\.\d+)?)\s*/\s*(10|1(?:\.0)?)\b", text) or \
            re.search(r"score[^0-9]{0,15}(\d+(?:\.\d+)?)", text, re.I)
        if m:
            value = float(m.group(1))
            if m.lastindex == 2 and float(m.group(2)) == 10:
                value /= 10
    try:
        value = float(value)
    except (TypeError, ValueError):
        return 0.0
    if value > 1:  # model answered on a 0-10 or 0-100 scale
        value = value / 100 if value > 10 else value / 10
    return max(0.0, min(1.0, value))


def interviewer_grade(student_id: str, session_id: str, session: dict, answer: str, message_id: str) -> list[dict]:
    question = memory.get_question(session["pending_question"])
    topic_id = session.get("pending_topic") or question["topic_id"]
    pack, used = memory.context_pack(student_id, "interviewer", topic_id)
    points = "\n".join(f"- {p}" for p in question["points"])
    extra = (f"GRADE THIS ANSWER\nQUESTION ({question['topic']}): {question['text']}\n"
             f"IDEAL POINTS:\n{points}\nSTUDENT ANSWER: {answer}")
    events, data = _llm_turn("interviewer_grade", "interviewer", student_id, session_id,
                             pack, used, answer, message_id, extra)
    if not data:
        return events  # LLM unavailable: keep the question pending so the student can retry

    score = _read_score(data)
    feedback = str(data.get("feedback") or "")[:300]
    result = memory.record_attempt(student_id, session_id, question, score, feedback, answer)
    memory.clear_pending_question(student_id, session_id)
    old, new = result.get("old_mastery"), result.get("new_mastery")
    events.append({"type": "memory", "agent": "interviewer", "kind": "attempt",
                   "text": f"{question['topic']}: score {score:.1f}, mastery {old or 0:.2f} → {new or 0:.2f}"})

    if score >= config.WEAK_BELOW:
        return events

    # Low score -> hand off to the Tutor. Meanwhile the Planner schedules a retry
    # (a concurrent write to the same student graph, done in the background).
    reason = f"Struggled with {question['topic']}" + (f": {feedback}" if feedback else "")
    memory.create_handoff(student_id, session_id, "interviewer", "tutor", reason, topic_id)
    events.append({"type": "handoff", "from": "interviewer", "to": "tutor",
                   "reason": reason, "topic": question["topic"]})
    retry = _background.submit(memory.create_task, student_id, f"Retry {question['topic']}",
                               topic_id, "interviewer", 1, "planner")
    events += tutor_turn(student_id, session_id, topic_id, answer, message_id)
    retry.result()
    events.append({"type": "memory", "agent": "planner", "kind": "task",
                   "text": f"Retry {question['topic']} tomorrow → Interviewer"})
    return events


def tutor_turn(student_id: str, session_id: str, topic_id: str | None, text: str, message_id: str) -> list[dict]:
    handoff = memory.open_handoff(student_id, "tutor")
    if not topic_id and handoff:
        topic_id = handoff.get("topic_id")
    if not topic_id:
        weak = memory.weak_topics(student_id, limit=1)
        topic_id = weak[0]["topic_id"] if weak else None
    pack, used = memory.context_pack(student_id, "tutor", topic_id)
    extra = f"TOPIC TO TEACH: {topic_name(topic_id) or 'whatever the student asks about'}"
    if handoff:
        extra += f"\nHANDOFF from {handoff['from_agent']}: {handoff['reason']}"
    events, _ = _llm_turn("tutor", "tutor", student_id, session_id, pack, used,
                          text or "Please teach me.", message_id, extra)
    if handoff:
        memory.pick_handoff(student_id, handoff["id"])
    return events


def planner_turn(student_id: str, session_id: str, text: str, message_id: str) -> list[dict]:
    pack, used = memory.context_pack(student_id, "planner")
    valid = ", ".join(sorted(topic_ids()))
    extra = f"VALID TOPIC IDS: {valid}"
    events, _ = _llm_turn("planner", "planner", student_id, session_id, pack, used,
                          text or "Plan my week.", message_id, extra)
    return events


def coach_turn(student_id: str, session_id: str, text: str, message_id: str) -> list[dict]:
    pack, used = memory.context_pack(student_id, "coach")
    events, data = _llm_turn("coach", "coach", student_id, session_id, pack, used, text, message_id,
                             f"VALID TOPIC IDS: {', '.join(sorted(topic_ids()))}")
    handoff = data.get("handoff") if isinstance(data.get("handoff"), dict) else None
    if handoff and handoff.get("to") in ("tutor", "planner"):
        to, topic_id = handoff["to"], handoff.get("topic_id") if handoff.get("topic_id") in topic_ids() else None
        reason = str(handoff.get("reason") or "Coach handoff")[:200]
        memory.create_handoff(student_id, session_id, "coach", to, reason, topic_id)
        events.append({"type": "handoff", "from": "coach", "to": to, "reason": reason,
                       "topic": topic_name(topic_id)})
        if to == "tutor":
            events += tutor_turn(student_id, session_id, topic_id, text, message_id)
        else:
            events += planner_turn(student_id, session_id, text, message_id)
    return events
