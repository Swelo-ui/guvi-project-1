"""
Integration Point Tests
Validates GUVI callback payload shape, WhatsApp parsing, and webhook security behavior.
"""

import hashlib
import hmac

import pytest

from utils.guvi_callback import build_callback_payload
from utils import whatsapp_handler as wa_handler


def test_callback_payload_deduplicates_fields():
    """Reality check: duplicate intel is deduplicated before sending to GUVI."""
    payload = build_callback_payload(
        session_id="dedupe-1",
        scam_detected=True,
        total_messages=3,
        intelligence={
            "bank_accounts": ["123", "123"],
            "upi_ids": ["a@upi", "a@upi"],
            "emails": ["x@y.com", "x@y.com"],
            "phishing_links": ["http://bad", "http://bad"],
            "phone_numbers": ["+911234567890", "+911234567890"],
            "ifsc_codes": ["SBIN0000001", "SBIN0000001"],
            "suspicious_keywords": ["urgent", "urgent"],
            "fake_credentials": ["EmpID: 1", "EmpID: 1"],
            "aadhaar_numbers": ["1234 5678 9012", "1234 5678 9012"],
            "pan_numbers": ["ABCDE1234F", "ABCDE1234F"],
            "mentioned_banks": ["sbi", "sbi"],
        },
        agent_notes="notes",
    )
    intel = payload["extractedIntelligence"]
    assert intel["bankAccounts"] == ["123"]
    assert intel["upiIds"] == ["a@upi"]
    assert intel["emails"] == ["x@y.com"]
    assert intel["phishingLinks"] == ["http://bad"]
    assert intel["phoneNumbers"] == ["+911234567890"]
    assert intel["ifscCodes"] == ["SBIN0000001"]
    assert intel["suspiciousKeywords"] == ["urgent"]
    assert intel["fakeCredentials"] == ["EmpID: 1"]
    assert intel["aadhaarNumbers"] == ["1234 5678 9012"]
    assert intel["panNumbers"] == ["ABCDE1234F"]
    assert intel["mentionedBanks"] == ["sbi"]


def test_callback_payload_field_mapping():
    """Reality check: payload field names match GUVI expected schema."""
    payload = build_callback_payload(
        session_id="map-1",
        scam_detected=False,
        total_messages=1,
        intelligence={},
        agent_notes="ok",
    )
    assert payload["sessionId"] == "map-1"
    assert payload["scamDetected"] is False
    assert payload["totalMessagesExchanged"] == 1
    assert "extractedIntelligence" in payload


def test_whatsapp_signature_verification(monkeypatch):
    """Reality check: webhook signatures are verified when secret is configured."""
    secret = "test_secret"
    payload = b'{"entry":[{"changes":[{"value":{"messages":[]}}]}]}'
    signature = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()

    monkeypatch.setattr(wa_handler, "WHATSAPP_APP_SECRET", secret)

    assert wa_handler.verify_webhook_signature(payload, f"sha256={signature}") is True
    assert wa_handler.verify_webhook_signature(payload, "sha256=bad") is False


def test_parse_webhook_message_text():
    """Reality check: WhatsApp text payloads are normalized into a simple dict."""
    data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "919876543210",
                        "text": {"body": "Your account is blocked."},
                        "id": "msg-1",
                        "timestamp": "1234567890",
                        "type": "text"
                    }],
                    "contacts": [{"profile": {"name": "Test Scammer"}}]
                }
            }]
        }]
    }
    parsed = wa_handler.parse_webhook_message(data)
    assert parsed["from"] == "919876543210"
    assert parsed["text"] == "Your account is blocked."
    assert parsed["message_id"] == "msg-1"
    assert parsed["sender_name"] == "Test Scammer"


def test_parse_webhook_message_no_messages():
    """Reality check: empty webhook payload returns None safely."""
    data = {"entry": [{"changes": [{"value": {"messages": []}}]}]}
    assert wa_handler.parse_webhook_message(data) is None


@pytest.mark.parametrize(
    "phone_id,token,expected",
    [
        ("123", "token", True),
        ("", "token", False),
        ("123", "", False),
        ("", "", False),
    ],
)
def test_whatsapp_configured_flag(monkeypatch, phone_id, token, expected):
    """Reality check: WhatsApp configuration requires both phone ID and access token."""
    monkeypatch.setattr(wa_handler, "WHATSAPP_PHONE_ID", phone_id)
    monkeypatch.setattr(wa_handler, "WHATSAPP_ACCESS_TOKEN", token)
    assert wa_handler.is_whatsapp_configured() is expected
