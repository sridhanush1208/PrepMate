"""Fallback chain tests with fake clients (no network, no database)."""
import pytest

try:  # openai >= 3 ships httpx2
    import httpx2 as httpx
except ImportError:
    import httpx
from openai import AuthenticationError, RateLimitError

from app import llm


def _err(cls, status):
    req = httpx.Request("POST", "http://test")
    return cls("err", response=httpx.Response(status, request=req), body=None)


class FakeClient:
    """Mimics client.chat.completions.create with scripted outcomes."""

    def __init__(self, outcomes):
        self.outcomes = list(outcomes)
        self.calls = 0
        self.chat = self
        self.completions = self

    def create(self, **_):
        self.calls += 1
        out = self.outcomes.pop(0) if self.outcomes else '{"reply": "ok"}'
        if isinstance(out, Exception):
            raise out
        msg = type("M", (), {"content": out})
        return type("R", (), {"choices": [type("C", (), {"message": msg})]})


def _pool(*slots):
    return llm.KeyPool([llm.KeySlot(p, label, client, "model") for p, label, client in slots])


@pytest.fixture(autouse=True)
def restore_pool():
    saved = llm._POOL
    yield
    llm._POOL = saved


def test_falls_back_to_next_key_on_rate_limit():
    g1 = FakeClient([_err(RateLimitError, 429)])
    g2 = FakeClient(['{"reply": "from key 2"}'])
    llm._POOL = _pool(("gemini", "gemini#1", g1), ("gemini", "gemini#2", g2))
    data, used = llm.chat_json("s", "u")
    assert data["reply"] == "from key 2" and used == "gemini#2"
    assert not llm._POOL.slots[0].available()  # key 1 is cooling down


def test_falls_back_from_gemini_to_groq():
    g = FakeClient([_err(RateLimitError, 429)])
    q = FakeClient(['{"reply": "groq"}'])
    llm._POOL = _pool(("gemini", "gemini#1", g), ("groq", "groq#1", q))
    data, used = llm.chat_json("s", "u")
    assert used == "groq#1"


def test_bad_key_is_disabled():
    bad = FakeClient([_err(AuthenticationError, 401)])
    good = FakeClient(['{"reply": "ok"}'])
    llm._POOL = _pool(("gemini", "gemini#1", bad), ("gemini", "gemini#2", good))
    llm.chat_json("s", "u")
    assert llm._POOL.slots[0].disabled


def test_bad_json_retries_same_key_once():
    c = FakeClient(["not json", '```json\n{"reply": "fixed"}\n```'])
    llm._POOL = _pool(("gemini", "gemini#1", c))
    data, _ = llm.chat_json("s", "u")
    assert data["reply"] == "fixed" and c.calls == 2


def test_round_robin_spreads_load():
    a, b = FakeClient([]), FakeClient([])
    llm._POOL = _pool(("gemini", "gemini#1", a), ("gemini", "gemini#2", b))
    for _ in range(4):
        llm.chat_json("s", "u")
    assert a.calls == 2 and b.calls == 2


def test_all_keys_down_raises():
    llm._POOL = _pool(("gemini", "gemini#1", FakeClient([_err(RateLimitError, 429)])))
    with pytest.raises(llm.LLMUnavailable):
        llm.chat_json("s", "u")


def test_multiple_keys_parsed_from_env(monkeypatch):
    from app import config
    monkeypatch.setenv("GEMINI_API_KEYS", "k1, k2,k1\nk3")
    monkeypatch.setenv("GEMINI_API_KEY", "k4")
    assert config._keys("GEMINI_API_KEYS", "GEMINI_API_KEY") == ["k1", "k2", "k3", "k4"]
