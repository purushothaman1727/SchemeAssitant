import httpx
import pytest

from app.services import llm as llm_mod
from app.services.llm import ChatCompletionsClient, LLMUnavailable


def _resp(status, json_body=None, headers=None):
    return httpx.Response(status, json=json_body or {}, headers=headers or {},
                          request=httpx.Request("POST", "https://x/chat/completions"))


OK = {"choices": [{"message": {"content": "  hello  "}}]}


@pytest.fixture
def client_obj():
    return ChatCompletionsClient("https://x", "openai/gpt-oss-120b", "k", 5, "groq")


def test_retries_once_after_429_then_succeeds(monkeypatch, client_obj):
    calls, slept = [], []
    seq = iter([_resp(429, headers={"retry-after": "2"}), _resp(200, OK)])
    monkeypatch.setattr(httpx, "post", lambda *a, **k: calls.append(k["json"]) or next(seq))
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: slept.append(s))
    assert client_obj.complete([{"role": "user", "content": "x"}]) == "hello"
    assert len(calls) == 2 and slept == [2.0]


def test_gives_up_after_second_429(monkeypatch, client_obj):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _resp(429))
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: None)
    with pytest.raises(LLMUnavailable):
        client_obj.complete([{"role": "user", "content": "x"}])


def test_retry_wait_is_capped(monkeypatch, client_obj):
    slept = []
    seq = iter([_resp(429, headers={"retry-after": "3600"}), _resp(200, OK)])
    monkeypatch.setattr(httpx, "post", lambda *a, **k: next(seq))
    monkeypatch.setattr(llm_mod.time, "sleep", lambda s: slept.append(s))
    client_obj.complete([{"role": "user", "content": "x"}])
    assert slept == [20.0]


def test_low_reasoning_effort_only_for_gpt_oss(monkeypatch):
    seen = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: seen.append(k["json"]) or _resp(200, OK))
    ChatCompletionsClient("https://x", "openai/gpt-oss-120b", "k", 5, "groq").complete([])
    ChatCompletionsClient("https://x", "llama3.1:8b", "", 5, "ollama").complete([])
    assert seen[0]["reasoning_effort"] == "low"
    assert "reasoning_effort" not in seen[1]


@pytest.mark.parametrize("status", [401, 404, 500])
def test_other_errors_raise_without_retry(monkeypatch, client_obj, status):
    n = []
    monkeypatch.setattr(httpx, "post", lambda *a, **k: n.append(1) or _resp(status))
    with pytest.raises(LLMUnavailable):
        client_obj.complete([])
    assert len(n) == 1


def test_network_errors_become_llm_unavailable(monkeypatch, client_obj):
    def boom(*a, **k):
        raise httpx.ConnectTimeout("t")

    monkeypatch.setattr(httpx, "post", boom)
    with pytest.raises(LLMUnavailable):
        client_obj.complete([])


def test_malformed_body_is_handled(monkeypatch, client_obj):
    monkeypatch.setattr(httpx, "post", lambda *a, **k: _resp(200, {"nope": 1}))
    with pytest.raises(LLMUnavailable):
        client_obj.complete([])
