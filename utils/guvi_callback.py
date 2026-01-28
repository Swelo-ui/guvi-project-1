"""
GUVI Callback Handler
Sends intelligence reports to GUVI evaluation endpoint
"""

import os
import logging
import threading
import requests
from typing import Dict, Any

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

GUVI_CALLBACK_URL = os.getenv("GUVI_CALLBACK_URL", "https://hackathon.guvi.in/api/updateHoneyPotFinalResult")


def send_callback(payload: Dict[str, Any]) -> bool:
    """
    Send intelligence callback to GUVI.
    
    Args:
        payload: Callback payload with session ID, intelligence, etc.
    
    Returns:
        True if sent successfully
    """
    try:
        response = requests.post(
            GUVI_CALLBACK_URL,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        if response.status_code == 200:
            logger.info(f"✅ GUVI callback sent successfully for session: {payload.get('sessionId')}")
            return True
        else:
            logger.warning(f"⚠️ GUVI callback returned {response.status_code}: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error("❌ GUVI callback timed out")
        return False
    except Exception as e:
        logger.error(f"❌ GUVI callback failed: {str(e)}")
        return False


def send_callback_async(payload: Dict[str, Any]) -> None:
    """
    Send GUVI callback in background thread.
    Ensures API response is not delayed by callback.
    
    Args:
        payload: Callback payload
    """
    thread = threading.Thread(target=send_callback, args=(payload,))
    thread.daemon = True
    thread.start()
    logger.info(f"🚀 GUVI callback queued for session: {payload.get('sessionId')}")


def build_callback_payload(
    session_id: str,
    scam_detected: bool,
    total_messages: int,
    intelligence: Dict[str, Any],
    agent_notes: str
) -> Dict[str, Any]:
    """
    Build the callback payload in GUVI-expected format.
    
    Args:
        session_id: Unique session identifier
        scam_detected: Whether scam was detected
        total_messages: Total messages exchanged
        intelligence: Extracted intelligence
        agent_notes: Agent's analysis notes
    
    Returns:
        GUVI-formatted callback payload
    """
    return {
        "sessionId": session_id,
        "scamDetected": scam_detected,
        "totalMessagesExchanged": total_messages,
        "extractedIntelligence": {
            "bankAccounts": intelligence.get("bank_accounts", []),
            "upiIds": intelligence.get("upi_ids", []),
            "phishingLinks": intelligence.get("phishing_links", []),
            "phoneNumbers": intelligence.get("phone_numbers", []),
            "suspiciousKeywords": intelligence.get("suspicious_keywords", [])
        },
        "agentNotes": agent_notes
    }
