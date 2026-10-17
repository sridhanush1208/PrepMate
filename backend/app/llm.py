"""Free-tier LLM access through the OpenAI-compatible APIs of Gemini and Groq.

You can give several API keys AND several models per provider (comma-separated in .env).
Every (model, key) pair is a "slot". A call walks this fallback chain:

    gemini model 1: key 1, key 2, ...   (keys rotated round-robin)
    gemini model 2: key 1, key 2, ...
    groq   model 1: key 1, ...

- 429 rate limit      -> that slot cools down for 60s, try the next key
- 503 / 500 / timeout -> the MODEL is overloaded: skip that model's other keys for this call
- 401 / 403           -> bad key: disabled until restart
- 404                 -> model not available: disabled until restart
- bad JSON            -> one retry on the same slot
If no key is set at all, a small offline "mock" model is used so the app still runs.
"""
import json
import logging
import re
import threading
import time
from dataclasses import dataclass, field

from openai import APIStatusError, APITimeoutError, OpenAI, RateLimitError

from . import config

log = logging.getLogger("prepmate.llm")

RATE_LIMIT_COOLDOWN_S = 60
OVERLOAD_COOLDOWN_S = 20


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
        self._next: dict[tuple, int] = {}
        self._lock = threading.Lock()

    def chain(self) -> list[KeySlot]:
        """Slots to try: provider order, then model order, keys rotated round-robin per model."""
        groups: dict[tuple, list[KeySlot]] = {}
        for s in self.slots:  # slots are built in priority order, dicts keep insertion order
            groups.setdefault((s.provider, s.model), []).append(s)
        ordered = []
        with self._lock:
            for provider in config.LLM_PROVIDER_ORDER:
                for (p, model), keys in groups.items():
                    if p != provider:
                        continue
                    start = self._next.get((p, model), 0) % len(keys)
                    self._next[(p, model)] = start + 1
                    ordered += keys[start:] + keys[:start]
        return [s for s in ordered if s.available()]

    def status(self) -> list[dict]:
        now = time.time()
        return [{
            "key": s.label, "model": s.model, "uses": s.uses, "failures": s.failures,
            "state": "disabled" if s.disabled else
                     f"cooldown {int(s.cooldown_until - now)}s" if s.cooldown_until > now else "ready",
            "last_error": s.last_error[:160],
        } for s in self.slots]


def _build_pool() -> KeyPool:
    slots = []
    for provider, keys, models, base_url in (
        ("gemini", config.GEMINI_API_KEYS, config.GEMINI_MODELS, config.GEMINI_BASE_URL),
        ("groq", config.GROQ_API_KEYS, config.GROQ_MODELS, config.GROQ_BASE_URL),
    ):
        clients = [OpenAI(api_key=k, base_url=base_url, timeout=config.LLM_TIMEOUT_S, max_retries=0) for k in keys]
        for model in models:
            for i, client in enumerate(clients, start=1):
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
    """Short summary for the UI, e.g. ['gemini-3.8-flash ×4', 'llama-x ×1']."""
    counts: dict[str, int] = {}
    for s in pool().slots:
        if not s.disabled:
            counts[s.model] = counts.get(s.model, 0) + 1
    return [f"{m} ×{n}" for m, n in counts.items()]


def list_models() -> dict:
    """Which models each provider's first working key can use (for choosing model names)."""
    out = {}
    seen = set()
    for s in pool().slots:
        if s.provider in seen or s.disabled:
            continue
        seen.add(s.provider)
        try:
            out[s.provider] = sorted(m.id for m in s.client.models.list())
        except Exception as e:
            out[s.provider] = f"error: {type(e).__name__}"
    return out


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


def _call(slot: KeySlot, system: str, user: str, temperature: float):
    kwargs = {}
    if slot.provider == "gemini" and config.GEMINI_REASONING_EFFORT:
        kwargs["reasoning_effort"] = config.GEMINI_REASONING_EFFORT
    return slot.client.chat.completions.create(
        model=slot.model,
        messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
        response_format={"type": "json_object"},
        temperature=temperature,
        **kwargs,
    )


def chat_json(system: str, user: str, temperature: float = 0.4) -> tuple[dict, str]:
    """Ask for a JSON object, falling back across every configured model and key."""
    if is_mock():
        return _mock_reply(user), "mock"
    errors = []
    overloaded: set[tuple[str, str]] = set()  # models that failed server-side during THIS call
    for slot in pool().chain():
        if (slot.provider, slot.model) in overloaded:
            continue
        for attempt in range(2):
            try:
                resp = _call(slot, system, user, temperature)
                data = _parse_json(resp.choices[0].message.content or "")
                slot.uses += 1
                return data, f"{slot.label} {slot.model}"
            except (json.JSONDecodeError, ValueError) as e:
                errors.append(f"{slot.label}: bad JSON")
                slot.last_error = f"bad JSON: {e}"
                if attempt == 0:
                    continue  # one retry on the same slot
            except RateLimitError:
                slot.cooldown_until = time.time() + RATE_LIMIT_COOLDOWN_S
                slot.failures += 1
                slot.last_error = "429 rate limited"
                errors.append(f"{slot.label}/{slot.model}: rate limited")
            except APITimeoutError:
                slot.failures += 1
                slot.last_error = "timeout"
                overloaded.add((slot.provider, slot.model))
                errors.append(f"{slot.label}/{slot.model}: timeout")
            except APIStatusError as e:
                slot.failures += 1
                slot.last_error = f"HTTP {e.status_code}: {str(e)[:120]}"
                if e.status_code in (401, 403, 404):
                    slot.disabled = True          # bad key, or model not available for it
                elif e.status_code >= 500:
                    slot.cooldown_until = time.time() + OVERLOAD_COOLDOWN_S
                    overloaded.add((slot.provider, slot.model))
                else:
                    slot.cooldown_until = time.time() + 15
                errors.append(f"{slot.label}/{slot.model}: HTTP {e.status_code}")
            except Exception as e:  # network errors
                slot.failures += 1
                slot.last_error = type(e).__name__
                slot.cooldown_until = time.time() + 15
                errors.append(f"{slot.label}/{slot.model}: {type(e).__name__}")
            break  # move on to the next slot
    log.warning("all LLM slots failed: %s", errors)
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
