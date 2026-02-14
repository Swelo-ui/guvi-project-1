"""
WhatsApp Integration Handler
Handles WhatsApp Cloud API webhooks for the honeypot system.
Uses Meta's official WhatsApp Business Cloud API (FREE tier: 1000 conversations/month)
"""

import os
import logging
import requests
import hashlib
import hmac
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# WhatsApp Cloud API Configuration
WHATSAPP_PHONE_ID = os.getenv("WHATSAPP_PHONE_ID", "")
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN", "")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "honeypot_verify_2026")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET", "")

# API Base URL
WHATSAPP_API_URL = "https://graph.facebook.com/v21.0"


def verify_webhook_signature(payload: bytes, signature: str) -> bool:
    """
    Verify that the webhook request came from Meta.
    
    Args:
        payload: Raw request body
        signature: X-Hub-Signature-256 header value
    
    Returns:
        True if signature is valid
    """
    if not WHATSAPP_APP_SECRET:
        logger.warning("WHATSAPP_APP_SECRET not set, skipping signature verification")
        return True
    
    if not signature or not signature.startswith("sha256="):
        return False
    
    expected_signature = hmac.new(
        WHATSAPP_APP_SECRET.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(signature[7:], expected_signature)


def verify_webhook_challenge(mode: str, token: str, challenge: str) -> tuple:
    """
    Verify webhook setup challenge from Meta.
    
    Args:
        mode: hub.mode parameter
        token: hub.verify_token parameter
        challenge: hub.challenge parameter
    
    Returns:
        Tuple of (response, status_code)
    """
    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        logger.info("✅ WhatsApp webhook verified successfully")
        return challenge, 200
    
    logger.warning(f"❌ WhatsApp webhook verification failed. Mode: {mode}, Token match: {token == WHATSAPP_VERIFY_TOKEN}")
    return "Forbidden", 403


def parse_webhook_message(data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Parse incoming WhatsApp webhook data to extract message info.
    
    Args:
        data: Raw webhook JSON data
    
    Returns:
        Parsed message dict or None if no message
    """
    try:
        entry = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        
        # Check for messages
        messages = value.get("messages", [])
        if not messages:
            return None
        
        message = messages[0]
        
        # Extract sender info
        contacts = value.get("contacts", [{}])
        sender_name = contacts[0].get("profile", {}).get("name", "Unknown") if contacts else "Unknown"
        
        # Extract message content based on type
        msg_type = message.get("type", "text")
        text = ""
        
        if msg_type == "text":
            text = message.get("text", {}).get("body", "")
        elif msg_type == "button":
            text = message.get("button", {}).get("text", "")
        elif msg_type == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                text = interactive.get("button_reply", {}).get("title", "")
            elif interactive.get("type") == "list_reply":
                text = interactive.get("list_reply", {}).get("title", "")
        
        return {
            "from": message.get("from"),  # Phone number
            "sender_name": sender_name,
            "text": text,
            "message_id": message.get("id"),
            "timestamp": message.get("timestamp"),
            "type": msg_type,
            "channel": "WhatsApp"
        }
        
    except Exception as e:
        logger.error(f"Error parsing WhatsApp message: {e}")
        return None


def send_text_message(to_number: str, message: str) -> bool:
    """
    Send a text message via WhatsApp Cloud API.
    
    Args:
        to_number: Recipient phone number (with country code, no +)
        message: Message text to send
    
    Returns:
        True if sent successfully
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        logger.error("WhatsApp credentials not configured")
        return False
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": to_number,
        "type": "text",
        "text": {
            "preview_url": False,
            "body": message
        }
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            logger.info(f"✅ WhatsApp message sent to {to_number[:6]}***")
            return True
        else:
            logger.error(f"❌ WhatsApp send failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"❌ WhatsApp send exception: {e}")
        return False


def mark_message_read(message_id: str) -> bool:
    """
    Mark a message as read (shows blue ticks to sender).
    
    Args:
        message_id: WhatsApp message ID
    
    Returns:
        True if marked successfully
    """
    if not WHATSAPP_PHONE_ID or not WHATSAPP_ACCESS_TOKEN:
        return False
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_ID}/messages"
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "messaging_product": "whatsapp",
        "status": "read",
        "message_id": message_id
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=5)
        return response.status_code == 200
    except:
        return False


def format_session_id(phone_number: str) -> str:
    """
    Create a consistent session ID from phone number.
    
    Args:
        phone_number: WhatsApp phone number
    
    Returns:
        Session ID string
    """
    return f"whatsapp_{phone_number}"


def build_conversation_history_key(phone_number: str) -> str:
    """
    Build cache key for storing conversation history.
    
    Args:
        phone_number: WhatsApp phone number
    
    Returns:
        Cache key string
    """
    return f"wa_history_{phone_number}"


# In-memory conversation history cache (per phone number)
_conversation_cache: Dict[str, List[Dict[str, str]]] = {}


def get_conversation_history(phone_number: str) -> List[Dict[str, str]]:
    """Get cached conversation history for a phone number."""
    key = build_conversation_history_key(phone_number)
    return _conversation_cache.get(key, [])


def add_to_conversation_history(phone_number: str, sender: str, text: str):
    """Add a message to conversation history cache."""
    key = build_conversation_history_key(phone_number)
    
    if key not in _conversation_cache:
        _conversation_cache[key] = []
    
    _conversation_cache[key].append({
        "sender": sender,
        "text": text,
        "timestamp": int(datetime.now(UTC).timestamp() * 1000)
    })
    
    # Keep only last 20 messages
    if len(_conversation_cache[key]) > 20:
        _conversation_cache[key] = _conversation_cache[key][-20:]


def clear_conversation_history(phone_number: str):
    """Clear conversation history for a phone number."""
    key = build_conversation_history_key(phone_number)
    if key in _conversation_cache:
        del _conversation_cache[key]


def is_whatsapp_configured() -> bool:
    """Check if WhatsApp integration is properly configured."""
    return bool(WHATSAPP_PHONE_ID and WHATSAPP_ACCESS_TOKEN)
