import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, UTC

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

INSFORGE_BASE_URL = os.getenv("INSFORGE_BASE_URL", "").rstrip("/")
INSFORGE_KEY = os.getenv("INSFORGE_ANON_KEY") or os.getenv("INSFORGE_API_KEY", "")

REST_URL = f"{INSFORGE_BASE_URL}/api/database/records" if INSFORGE_BASE_URL else ""


def get_headers() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {INSFORGE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }


def get_persona(session_id: str) -> Optional[Dict[str, Any]]:
    if not REST_URL:
        logger.warning("InsForge not configured")
        return None

    try:
        url = f"{REST_URL}/personas?session_id=eq.{session_id}&select=persona_json&limit=1"
        response = httpx.get(url, headers=get_headers(), timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                return data[0].get("persona_json")

        return None
    except Exception as e:
        logger.error(f"Error fetching persona: {e}")
        return None


def save_persona(session_id: str, persona: Dict[str, Any]) -> bool:
    if not REST_URL:
        logger.warning("InsForge not configured, persona saved locally only")
        return False

    try:
        data = {
            "session_id": session_id,
            "name": persona.get("name"),
            "age": persona.get("age"),
            "city": persona.get("city"),
            "bank_name": persona.get("bank", {}).get("name"),
            "account_number": persona.get("bank", {}).get("account_number"),
            "ifsc": persona.get("bank", {}).get("ifsc"),
            "upi_id": persona.get("upi", {}).get("primary"),
            "phone": persona.get("phone"),
            "persona_json": persona,
            "created_at": datetime.now(UTC).isoformat()
        }

        url = f"{REST_URL}/personas"
        response = httpx.post(url, headers=get_headers(), json=[data], timeout=10)

        if response.status_code in [200, 201]:
            logger.info(f"Saved persona for session: {session_id}")
            return True
        logger.warning(f"Failed to save persona: {response.status_code} - {response.text}")
        return False

    except Exception as e:
        logger.error(f"Error saving persona: {e}")
        return False


def update_session_activity(session_id: str, message_count: int) -> bool:
    if not REST_URL:
        return False

    try:
        data = {
            "message_count": message_count,
            "last_activity": datetime.now(UTC).isoformat()
        }

        url = f"{REST_URL}/personas?session_id=eq.{session_id}"
        headers = get_headers()
        headers["Prefer"] = "return=minimal"

        response = httpx.patch(url, headers=headers, json=data, timeout=10)
        return response.status_code in [200, 204]

    except Exception as e:
        logger.error(f"Error updating session: {e}")
        return False


def save_intelligence(
    session_id: str,
    intelligence: Dict[str, Any],
    scam_detected: bool = True,
    agent_notes: str = ""
) -> bool:
    if not REST_URL:
        return False

    try:
        data = {
            "session_id": session_id,
            "scammer_upi": list(set(intelligence.get("upi_ids", []))),
            "scammer_bank": list(set(intelligence.get("bank_accounts", []))),
            "scammer_phone": list(set(intelligence.get("phone_numbers", []))),
            "phishing_links": list(set(intelligence.get("phishing_links", []))),
            "scam_keywords": list(set(intelligence.get("suspicious_keywords", []))),
            "scam_detected": scam_detected,
            "agent_notes": agent_notes,
            "callback_sent": False,
            "created_at": datetime.now(UTC).isoformat()
        }

        check_url = f"{REST_URL}/intelligence?session_id=eq.{session_id}&select=id&limit=1"
        check_resp = httpx.get(check_url, headers=get_headers(), timeout=5)

        if check_resp.status_code == 200 and check_resp.json():
            intel_id = check_resp.json()[0]["id"]
            url = f"{REST_URL}/intelligence?id=eq.{intel_id}"
            response = httpx.patch(url, headers=get_headers(), json=data, timeout=10)
        else:
            url = f"{REST_URL}/intelligence"
            response = httpx.post(url, headers=get_headers(), json=[data], timeout=10)

        if response.status_code in [200, 201, 204]:
            logger.info(f"Saved intelligence for session: {session_id}")
            return True
        return False

    except Exception as e:
        logger.error(f"Error saving intelligence: {e}")
        return False


def get_callback_sent(session_id: str) -> bool:
    if not REST_URL:
        return False

    try:
        url = f"{REST_URL}/intelligence?session_id=eq.{session_id}&select=callback_sent&order=created_at.desc&limit=1"
        response = httpx.get(url, headers=get_headers(), timeout=10)

        if response.status_code == 200:
            data = response.json()
            if data:
                return bool(data[0].get("callback_sent"))
        return False

    except Exception as e:
        logger.error(f"Error checking callback status: {e}")
        return False


def mark_callback_sent(session_id: str) -> bool:
    if not REST_URL:
        return False

    try:
        data = {"callback_sent": True}
        url = f"{REST_URL}/intelligence?session_id=eq.{session_id}"
        headers = get_headers()
        headers["Prefer"] = "return=minimal"

        response = httpx.patch(url, headers=headers, json=data, timeout=10)
        return response.status_code in [200, 204]

    except Exception as e:
        logger.error(f"Error marking callback sent: {e}")
        return False


def save_message(
    session_id: str,
    sender: str,
    message: str,
    strategy_used: Optional[str] = None
) -> bool:
    if not REST_URL:
        return False

    try:
        data = {
            "session_id": session_id,
            "sender": sender,
            "message": message,
            "strategy_used": strategy_used,
            "timestamp": datetime.now(UTC).isoformat()
        }

        url = f"{REST_URL}/conversations"
        response = httpx.post(url, headers=get_headers(), json=[data], timeout=10)
        return response.status_code in [200, 201]

    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return False


_persona_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_persona(session_id: str) -> Optional[Dict[str, Any]]:
    return _persona_cache.get(session_id)


def cache_persona(session_id: str, persona: Dict[str, Any]) -> None:
    _persona_cache[session_id] = persona
