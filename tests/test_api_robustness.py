"""
API Robustness and Real-World Behavior Tests
Validates request validation, history handling, callback triggering, and core endpoint behavior.
"""

import pytest

import app as app_module


@pytest.fixture
def client(monkeypatch):
    """Provide a Flask test client with external integrations stubbed out."""
    app_module.app.testing = True
    app_module.API_KEY_SECRET = "test_key"
    app_module.SENT_CALLBACKS.clear()

    monkeypatch.setattr(app_module, "run_async", lambda func, *args, **kwargs: func(*args, **kwargs))
    monkeypatch.setattr(app_module, "whatsapp_configured", False)

    monkeypatch.setattr(app_module, "get_persona", lambda session_id: None)
    monkeypatch.setattr(app_module, "get_cached_persona", lambda session_id: None)
    monkeypatch.setattr(app_module, "save_persona", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "cache_persona", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "save_message", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "update_session_activity", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "save_intelligence", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "mark_callback_sent", lambda *args, **kwargs: None)
    monkeypatch.setattr(app_module, "get_callback_sent", lambda *args, **kwargs: False)

    def fake_generate_agent_response(**kwargs):
        return {
            "intelligence": {},
            "scam_detected": False,
            "agent_notes": "test",
            "strategy": "stalling",
            "response": "Haan ji, ek minute."
        }

    monkeypatch.setattr(app_module, "generate_agent_response", fake_generate_agent_response)
    return app_module.app.test_client()


@pytest.fixture
def headers():
    """Provide API headers for authenticated requests."""
    return {"x-api-key": "test_key", "Content-Type": "application/json"}


def test_honeypot_requires_api_key(client):
    """Reality check: public requests without API key must be rejected."""
    response = client.post("/api/honey-pot", json={"sessionId": "s1", "message": {"text": "Hi"}})
    assert response.status_code == 401
    assert response.get_json().get("message") == "Unauthorized: Invalid API Key"


def test_honeypot_handles_missing_json_gracefully(client, headers):
    """Reality check: malformed requests are handled safely without crashing."""
    response = client.post("/api/honey-pot", headers=headers, data="not-json", content_type="text/plain")
    data = response.get_json()
    assert response.status_code == 200
    assert data.get("status") == "success"
    assert data.get("reply")


@pytest.mark.parametrize(
    "payload,expected_message",
    [
        ({"sessionId": "s1", "message": {}}, "Invalid message: text is required"),
        ({"sessionId": "s1", "message": {"text": "   "}}, "Invalid message: text must be a non-empty string"),
        ({"sessionId": "s1", "message": {"text": 123}}, "Invalid message: text must be a non-empty string"),
    ],
)
def test_honeypot_validates_message_text(client, headers, payload, expected_message):
    """Reality check: invalid message payloads are blocked with clear errors."""
    response = client.post("/api/honey-pot", headers=headers, json=payload)
    assert response.status_code == 400
    assert response.get_json().get("message") == expected_message


def test_honeypot_accepts_non_list_history(client, headers):
    """Reality check: non-list history inputs are sanitized and do not crash the API."""
    payload = {
        "sessionId": "s1",
        "message": {"text": "Hello"},
        "conversationHistory": "bad-history"
    }
    response = client.post("/api/honey-pot", headers=headers, json=payload)
    data = response.get_json()
    assert response.status_code == 200
    assert data.get("status") == "success"
    assert "engagementMetrics" in data


def test_history_intelligence_merges_across_turns(client, headers):
    """Reality check: scammer intel in history should carry into current extraction."""
    payload = {
        "sessionId": "merge-history-1",
        "message": {"text": "Hello"},
        "conversationHistory": [
            {"sender": "scammer", "text": "Send to fraud123@upi immediately"},
            {"sender": "agent", "text": "Haan ji?"},
        ],
    }
    response = client.post("/api/honey-pot", headers=headers, json=payload)
    data = response.get_json()
    extracted = data.get("extractedIntelligence", {})
    assert response.status_code == 200
    assert "fraud123@upi" in extracted.get("upiIds", [])


def test_callback_triggers_on_actionable_intel(client, headers, monkeypatch):
    """Reality check: GUVI callback triggers when actionable intel is detected."""
    calls = []

    def fake_callback(payload):
        calls.append(payload)

    monkeypatch.setattr(app_module, "send_callback_async", fake_callback)

    payload = {
        "sessionId": "callback-1",
        "message": {"text": "Pay to scammer@upi to verify."},
        "conversationHistory": []
    }
    response = client.post("/api/honey-pot", headers=headers, json=payload)
    assert response.status_code == 200
    assert len(calls) == 1
    assert calls[0]["sessionId"] == "callback-1"


def test_honeypot_get_redirects_to_docs(client):
    """Reality check: browser GET to honeypot endpoint redirects to docs."""
    response = client.get("/api/honey-pot")
    assert response.status_code in {301, 302}
    assert "/apidocs" in response.headers.get("Location", "")


def test_whatsapp_status_not_configured(client):
    """Reality check: WhatsApp status returns not configured when env is missing."""
    response = client.get("/whatsapp/status")
    assert response.status_code == 404
    assert response.get_json().get("status") == "not_configured"
