"""
Performance and Error Handling Tests
Validates realistic throughput expectations and resilience under internal failures.
"""

import time

import pytest

import app as app_module
from core.conversation_analyzer import analyze_conversation
from models.intelligence import extract_all_intelligence


def test_extraction_performance_large_text():
    """Reality check: large scam payloads should extract within a practical time budget."""
    text = (
        "Urgent! Your account is blocked. "
        "Send to fraudster@upi or visit bit.ly/fake-link. "
        "Contact +919876543210 with IFSC SBIN0001234. "
    ) * 200
    start = time.perf_counter()
    intel = extract_all_intelligence(text)
    elapsed = time.perf_counter() - start
    assert "fraudster@upi" in intel.get("upi_ids", [])
    assert elapsed < 1.5


def test_conversation_analyzer_batch_performance():
    """Reality check: analyzer stays responsive across repeated scam messages."""
    start = time.perf_counter()
    for i in range(40):
        analyze_conversation(
            "Your account is blocked. Share OTP now.",
            [],
            [],
            f"perf-session-{i}"
        )
    elapsed = time.perf_counter() - start
    assert elapsed < 2.5


@pytest.fixture
def error_client(monkeypatch):
    """Provide a Flask client where LLM generation fails to exercise fallback path."""
    app_module.app.testing = True
    app_module.API_KEY_SECRET = "test_key"

    monkeypatch.setattr(app_module, "run_async", lambda func, *args, **kwargs: func(*args, **kwargs))
    monkeypatch.setattr(app_module, "get_persona", lambda session_id: None)
    monkeypatch.setattr(app_module, "get_cached_persona", lambda session_id: None)
    monkeypatch.setattr(app_module, "save_persona", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "cache_persona", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "save_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "update_session_activity", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "save_intelligence", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "mark_callback_sent", lambda *args, **kwargs: None)

    def broken_generate_agent_response(**kwargs):
        raise RuntimeError("LLM failed")

    monkeypatch.setattr(app_module, "generate_agent_response", broken_generate_agent_response)
    return app_module.app.test_client()


def test_fallback_response_on_llm_failure(error_client):
    """Reality check: API returns a valid fallback response when LLM fails."""
    response = error_client.post(
        "/api/honey-pot",
        headers={"x-api-key": "test_key", "Content-Type": "application/json"},
        json={
            "sessionId": "fallback-1",
            "message": {"text": "Your account is blocked. Send OTP."},
            "conversationHistory": []
        },
    )
    data = response.get_json()
    assert response.status_code == 200
    assert data["status"] == "success"
    assert "reply" in data


@pytest.mark.parametrize(
    "payload",
    [
        {"entry": []},
        {"entry": [{"changes": []}]},
        {"entry": [{"changes": [{"value": {}}]}]},
    ],
)
def test_whatsapp_parser_tolerates_empty_payloads(payload):
    """Reality check: WhatsApp parser gracefully ignores empty webhook structures."""
    from utils import whatsapp_handler as wa_handler

    assert wa_handler.parse_webhook_message(payload) is None
