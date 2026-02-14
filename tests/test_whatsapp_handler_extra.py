"""
WhatsApp Handler Tests
Validates config checks, history caching, and send/read behavior.
"""

import pytest

from utils import whatsapp_handler as wa_handler


def test_verify_webhook_challenge_success(monkeypatch):
    """Reality check: valid verify token returns challenge."""
    monkeypatch.setattr(wa_handler, "WHATSAPP_VERIFY_TOKEN", "token123")
    response, status = wa_handler.verify_webhook_challenge("subscribe", "token123", "challenge")
    assert response == "challenge"
    assert status == 200


def test_verify_webhook_challenge_failure(monkeypatch):
    """Reality check: invalid token returns forbidden."""
    monkeypatch.setattr(wa_handler, "WHATSAPP_VERIFY_TOKEN", "token123")
    response, status = wa_handler.verify_webhook_challenge("subscribe", "wrong", "challenge")
    assert response == "Forbidden"
    assert status == 403


def test_send_text_message_requires_credentials(monkeypatch):
    """Reality check: missing credentials prevents sending."""
    monkeypatch.setattr(wa_handler, "WHATSAPP_PHONE_ID", "")
    monkeypatch.setattr(wa_handler, "WHATSAPP_ACCESS_TOKEN", "")
    assert wa_handler.send_text_message("919000000000", "hello") is False


def test_mark_message_read_requires_credentials(monkeypatch):
    """Reality check: missing credentials prevents read receipt."""
    monkeypatch.setattr(wa_handler, "WHATSAPP_PHONE_ID", "")
    monkeypatch.setattr(wa_handler, "WHATSAPP_ACCESS_TOKEN", "")
    assert wa_handler.mark_message_read("msg-1") is False


def test_conversation_history_cache_roundtrip():
    """Reality check: WhatsApp history cache stores and trims entries."""
    phone = "919999999999"
    wa_handler.clear_conversation_history(phone)
    for i in range(25):
        wa_handler.add_to_conversation_history(phone, "agent", f"msg-{i}")
    history = wa_handler.get_conversation_history(phone)
    assert len(history) == 20
    assert history[-1]["text"] == "msg-24"


def test_format_session_id():
    """Reality check: session id is normalized consistently."""
    assert wa_handler.format_session_id("919123456789") == "whatsapp_919123456789"
