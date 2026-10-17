"""Settings read from environment variables (and the repo-root .env file)."""
import os
from pathlib import Path

from dotenv import load_dotenv

BACKEND_DIR = Path(__file__).resolve().parents[1]
ROOT_DIR = BACKEND_DIR.parent
load_dotenv(ROOT_DIR / ".env")

FALKORDB_HOST = os.getenv("FALKORDB_HOST", "localhost")
FALKORDB_PORT = int(os.getenv("FALKORDB_PORT", "6379"))
FALKORDB_USERNAME = os.getenv("FALKORDB_USERNAME") or None
FALKORDB_PASSWORD = os.getenv("FALKORDB_PASSWORD") or None

def _keys(*names: str) -> list[str]:
    """Collect API keys from comma/newline-separated env vars, without duplicates."""
    keys: list[str] = []
    for name in names:
        for k in os.getenv(name, "").replace("\n", ",").split(","):
            k = k.strip()
            if k and k not in keys:
                keys.append(k)
    return keys


# Several keys per provider are allowed: GEMINI_API_KEYS=key1,key2,key3
# Several models too, in priority order: GEMINI_MODELS=gemini-3.8-flash,gemini-3.8-flash-lite
GEMINI_API_KEYS = _keys("GEMINI_API_KEYS", "GEMINI_API_KEY")
GEMINI_MODELS = _keys("GEMINI_MODELS", "GEMINI_MODEL") or ["gemini-3.8-flash"]
GEMINI_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/openai/"
# Gemini 3 models "think" before answering; low effort keeps replies fast. Empty = model default.
GEMINI_REASONING_EFFORT = os.getenv("GEMINI_REASONING_EFFORT", "low").strip()

GROQ_API_KEYS = _keys("GROQ_API_KEYS", "GROQ_API_KEY")
GROQ_MODELS = _keys("GROQ_MODELS", "GROQ_MODEL")
GROQ_BASE_URL = "https://api.groq.com/openai/v1"

LLM_TIMEOUT_S = float(os.getenv("LLM_TIMEOUT_S", "20"))

# Which provider is tried first. All keys of the first provider are tried before the next one.
LLM_PROVIDER_ORDER = [p.strip() for p in os.getenv("LLM_PROVIDER_ORDER", "gemini,groq").split(",") if p.strip()]

CATALOG_DIR = ROOT_DIR / "catalog"
QUERIES_DIR = BACKEND_DIR / "queries"
FRONTEND_DIST = ROOT_DIR / "frontend" / "dist"

CATALOG_GRAPH = "catalog"
STUDENT_GRAPH_PREFIX = "pm_"

# Memory rules (see README "Memory rules")
WEAK_BELOW = 0.5          # mastery below this = weak
MASTERED_AT = 0.6         # mastery at/above this = mastered
HALF_LIFE_DAYS = 14.0     # forgetting curve half-life
NEW_WEIGHT = 0.4          # new_mastery = (1 - NEW_WEIGHT) * old + NEW_WEIGHT * score

AGENTS = ["coach", "interviewer", "tutor", "planner"]
