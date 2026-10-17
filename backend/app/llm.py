"""Free-tier LLM access through the OpenAI-compatible APIs of Gemini and Groq.

You can give several API keys per provider (comma-separated in .env).
Every call walks a fallback chain:

    Gemini key 1 -> Gemini key 2 -> ... -> Groq key 1 -> Groq key 2 -> ...

- A key that hits a rate limit (HTTP 429) is put on cooldown for a while and skipped.
- A key that is rejected (HTTP 401/403) is disabled until the server restarts.
- Bad JSON from the model gets one retry on the same key.
- Successful keys are rotated round-robin, so the free quota is spread across keys.
If no key is set at all, a small offline "mock" model is used so the app still runs.
"""
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field

from openai import APIStatusError, OpenAI, RateLimitError

from . import config

log = logging.getLogger("prepmate.llm")

RATE_LIMIT_COOLDOWN_S = 60


class LLMUnavailable(Exception):
    pass


@dataclass
class KeySlot:
    provider: str          # "gemini" | "groq"
    label: str             # e.g. "gemini#2" (never the key itself)
    client: OpenAI
    model: str
    cooldown_until: float = 0.0
    disabled: bool = False
    uses: int = 0
    failures: int = 0
    last_error: str = field(default="")

    def available(self) -> bool:
        return not self.disabled and time.time() >= self.cooldown_until


class KeyPool:
    def __init__(self, slots: list[KeySlot]):
        self.slots = slots
        self._next = {p: 0 for p in config.LLM_PROVIDER_ORDER}
        self._lock = threading.Lock()

    def chain(self) -> list[KeySlot]:
        """Keys to try, in order: providers in configured order, each rotated round-robin."""
        ordered = []
        with self._lock:
            for provider in config.LLM_PROVIDER_ORDER:
                keys = [s for s in self.slots if s.provider == provider]
                if not keys:
                    continue
                start = self._next[provider] % len(keys)
                self._next[provider] = start + 1
                ordered += keys[start:] + keys[:start]
        return [s for s in ordered if s.available()]

    def status(self) -> list[dict]:
        now = time.time()
        return [{
            "key": s.label, "model": s.model, "uses": s.uses, "failures": s.failures,
            "state": "disabled" if s.disabled else
                     f"cooldown {int(s.cooldown_until - now)}s" if s.cooldown_until > now else "ready",
            "last_error": s.last_error[:120],
        } for s in self.slots]


def _build_pool() -> KeyPool:
    slots = []
    for provider, keys, model, base_url in (
        ("gemini", config.GEMINI_API_KEYS, config.GEMINI_MODEL, config.GEMINI_BASE_URL),
        ("groq", config.GROQ_API_KEYS, config.GROQ_MODEL, config.GROQ_BASE_URL),
    ):
        if not model:
            continue
        for i, key in enumerate(keys, start=1):
            client = OpenAI(api_key=key, base_url=base_url, timeout=40, max_retries=0)
            slots.append(KeySlot(provider, f"{provider}#{i}", client, model))
    return KeyPool(slots)


_POOL: KeyPool | None = None


def pool() -> KeyPool:
    global _POOL
    if _POOL is None:
        _POOL = _build_pool()
    return _POOL


def is_mock() -> bool:
    return not pool().slots


def providers() -> list[str]:
    """Labels of configured keys, e.g. ['gemini#1', 'gemini#2', 'groq#1']."""
    return [s.label for s in pool().slots]


def _parse_json(text: str) -> dict:
    text = text.strip()
    fenced = re.search(r"```(?:json)?\s*(\{.*\})\s*```", text, re.S)
    if fenced:
        text = fenced.group(1)
    elif not text.startswith("{"):
        start, end = text.find("{"), text.rfind("}")
        if start != -1 and end > start:
            text = text[start:end + 1]
    data = json.loads(text)
    if not isinstance(data, dict):
        raise ValueError("expected a JSON object")
    return data


def chat_json(system: str, user: str, temperature: float = 0.4) -> tuple[dict, str]:
    """Ask for a JSON object, falling back across every configured key. Returns (data, key_label)."""
    if is_mock():
        return _mock_reply(user), "mock"
    errors = []
    for slot in pool().chain():
        for attempt in range(2):
            try:
                resp = slot.client.chat.completions.create(
                    model=slot.model,
                    messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
                    response_format={"type": "json_object"},
                    temperature=temperature,
                )
                data = _parse_json(resp.choices[0].message.content or "")
                slot.uses += 1
                return data, slot.label
            except (json.JSONDecodeError, ValueError) as e:
                errors.append(f"{slot.label}: bad JSON")
                slot.last_error = f"bad JSON: {e}"
                if attempt == 0:
                    continue  # one retry on the same key
            except RateLimitError as e:
                slot.cooldown_until = time.time() + RATE_LIMIT_COOLDOWN_S
                slot.failures += 1
                slot.last_error = "rate limited"
                errors.append(f"{slot.label}: rate limited")
                log.info("%s rate limited, cooling down %ss", slot.label, RATE_LIMIT_COOLDOWN_S)
            except APIStatusError as e:
                slot.failures += 1
                slot.last_error = f"HTTP {e.status_code}"
                if e.status_code in (401, 403):
                    slot.disabled = True  # bad or revoked key
                elif e.status_code == 404:
                    slot.disabled = True  # model name not available for this key
                else:
                    slot.cooldown_until = time.time() + 15
                errors.append(f"{slot.label}: HTTP {e.status_code}")
            except Exception as e:  # network errors, timeouts
                slot.failures += 1
                slot.last_error = type(e).__name__
                slot.cooldown_until = time.time() + 15
                errors.append(f"{slot.label}: {type(e).__name__}")
            break  # move on to the next key
    log.warning("all LLM keys failed: %s", errors)
    raise LLMUnavailable("; ".join(errors) or "no API key is currently available (all cooling down)")


def _mock_reply(user: str) -> dict:
    """Deterministic offline stand-in so the app works without API keys."""
    if "GRADE THIS ANSWER" in user:
        answer = user.split("STUDENT ANSWER:", 1)[-1].lower()
        score = 0.3 if len(answer.split()) < 25 else 0.75
        return {
            "reply": f"(mock) I'd score that {score}. Key points to mention next time are listed in the question.",
            "score": score,
            "feedback": "mock feedback",
            "memory_updates": [],
        }
    return {"reply": "(mock) No LLM key configured, so this is a placeholder reply.", "memory_updates": []}
