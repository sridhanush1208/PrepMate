"""PrepMate HTTP API + the built React app.

Run from backend/:  uv run uvicorn app.main:app --reload --port 8000
"""
import logging
import re

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import config, memory, orchestrator
from .db import list_student_ids, slugify
from .llm import is_mock, list_models, pool, probe, providers
from .queries import all_queries

logging.basicConfig(level=logging.INFO)
app = FastAPI(title="PrepMate")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class NewStudent(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    target_role: str = "product_sde"


class ChatIn(BaseModel):
    session_id: str
    text: str = Field(default="", max_length=4000)
    mode: str = "chat"  # chat | mock | teach | plan


def _require(student_id: str) -> None:
    if not memory.student_exists(student_id):
        raise HTTPException(404, "student not found")


@app.get("/api/health")
def health():
    return {"ok": True, "llm": "mock" if is_mock() else providers()}


@app.get("/api/llm/status")
def llm_status():
    """Per-key health for the fallback chain (labels only, never the keys)."""
    return pool().status()


@app.get("/api/llm/models")
def llm_models():
    """Model names your keys can use (to pick GEMINI_MODELS / GROQ_MODELS)."""
    return list_models()


@app.get("/api/llm/probe")
def llm_probe(provider: str, model: str):
    """Time one tiny request to a model, e.g. /api/llm/probe?provider=gemini&model=gemini-3.5-flash"""
    if provider not in ("gemini", "groq") or not re.fullmatch(r"[\w./:-]{1,80}", model):
        raise HTTPException(400, "bad provider or model")
    return probe(provider, model)


@app.get("/api/roles")
def roles():
    return memory.catalog_roles()


@app.get("/api/students")
def students():
    return [p for sid in list_student_ids() if (p := memory.profile(sid))]


@app.post("/api/students")
def create_student(body: NewStudent):
    student_id = slugify(body.name)
    if not memory.student_exists(student_id):
        memory.ensure_student(student_id, body.name.strip(), body.target_role)
    return memory.profile(student_id)


@app.delete("/api/students/{student_id}")
def forget_student(student_id: str):
    memory.forget_student(student_id)
    return {"deleted": student_id}


@app.post("/api/students/{student_id}/sessions")
def start_session(student_id: str):
    _require(student_id)
    session_id, events = orchestrator.start(student_id)
    return {"session_id": session_id, "events": events}


@app.post("/api/students/{student_id}/sessions/{session_id}/end")
def end_session(student_id: str, session_id: str):
    _require(student_id)
    return {"summary": orchestrator.end(student_id, session_id)}


@app.post("/api/students/{student_id}/chat")
def chat(student_id: str, body: ChatIn):
    _require(student_id)
    return {"events": orchestrator.handle(student_id, body.session_id, body.text, body.mode)}


@app.get("/api/students/{student_id}/memory/graph")
def memory_graph(student_id: str):
    _require(student_id)
    return memory.memory_graph(student_id)


@app.get("/api/students/{student_id}/memory/facts")
def memory_facts(student_id: str):
    _require(student_id)
    return memory.facts_and_rules(student_id)


@app.delete("/api/students/{student_id}/memory/{memory_id}")
def delete_memory(student_id: str, memory_id: str):
    _require(student_id)
    memory.delete_memory(student_id, memory_id)
    return {"deleted": memory_id}


@app.get("/api/students/{student_id}/memory/timeline")
def memory_timeline(student_id: str):
    _require(student_id)
    return {"sessions": memory.timeline(student_id), "mastery": memory.mastery_overview(student_id)}


@app.get("/api/students/{student_id}/memory/plan")
def memory_plan(student_id: str):
    _require(student_id)
    return {
        "tasks": memory.open_tasks(student_id),
        "due_for_revision": memory.due_for_revision(student_id),
        "ready_to_learn": memory.ready_to_learn(student_id, limit=5),
        "weak": memory.weak_topics(student_id),
    }


@app.get("/api/queries")
def queries():
    return all_queries()


# ---- serve the built frontend (production / Hugging Face Space)
if config.FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=config.FRONTEND_DIST / "assets"), name="assets")

    @app.get("/{path:path}")
    def spa(path: str):
        file = config.FRONTEND_DIST / path
        if path and file.is_file():
            return FileResponse(file)
        return FileResponse(config.FRONTEND_DIST / "index.html")
