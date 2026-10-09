import httpx
import pytest

from app.core.config import settings
from app.services import llm


def configure(monkeypatch, api_key="secret-key-123"):
    monkeypatch.setattr(settings, "llm_base_url", "https://llm.example/v1/")
    monkeypatch.setattr(settings, "llm_model", "test-model")
    monkeypatch.setattr(settings, "llm_api_key", api_key)
    monkeypatch.setattr(llm.time, "sleep", lambda seconds: None)


def reply(status_code=200, content='{"ok": true}'):
    body = {"choices": [{"message": {"content": content}}]}
    return httpx.Response(
        status_code, json=body, request=httpx.Request("POST", "https://llm.example")
    )


def test_not_configured_raises():
    with pytest.raises(llm.LlmNotConfigured):
        llm.chat([{"role": "user", "content": "hi"}])


def test_chat_sends_expected_request_and_returns_text(monkeypatch):
    configure(monkeypatch)
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen.update(url=url, json=json, headers=headers)
        return reply()

    monkeypatch.setattr(llm.httpx, "post", fake_post)

    assert llm.chat([{"role": "user", "content": "hi"}]) == '{"ok": true}'
    assert seen["url"] == "https://llm.example/v1/chat/completions"
    assert seen["headers"]["Authorization"] == "Bearer secret-key-123"
    assert seen["json"]["model"] == "test-model"
    assert seen["json"]["temperature"] == 0
    assert seen["json"]["response_format"] == {"type": "json_object"}


def test_no_auth_header_when_no_key(monkeypatch):
    configure(monkeypatch, api_key=None)
    seen = {}

    def fake_post(url, json, headers, timeout):
        seen["headers"] = headers
        return reply()

    monkeypatch.setattr(llm.httpx, "post", fake_post)
    llm.chat([{"role": "user", "content": "hi"}])
    assert "Authorization" not in seen["headers"]


def test_http_error_is_reported_without_leaking_the_key(monkeypatch):
    configure(monkeypatch)
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: reply(status_code=401))

    with pytest.raises(llm.LlmError) as excinfo:
        llm.chat([{"role": "user", "content": "hi"}])
    assert "401" in str(excinfo.value)
    assert "secret-key-123" not in str(excinfo.value)


def test_server_errors_are_retried(monkeypatch):
    configure(monkeypatch)
    responses = iter([reply(status_code=503), reply(status_code=200)])
    monkeypatch.setattr(llm.httpx, "post", lambda *a, **k: next(responses))

    assert llm.chat([{"role": "user", "content": "hi"}]) == '{"ok": true}'