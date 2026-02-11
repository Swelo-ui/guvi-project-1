"""
Supabase Client (HTTP-based)
Handles database operations using direct REST API calls
"""

import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json

import httpx
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_SERVICE_KEY") or os.getenv("SUPABASE_KEY", "")

# REST API base URL
REST_URL = f"{SUPABASE_URL}/rest/v1" if SUPABASE_URL else ""


def get_headers() -> Dict[str, str]:
    """Get headers for Supabase REST API."""
    return {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }


def get_persona(session_id: str) -> Optional[Dict[str, Any]]:
    """
    Get existing persona for a session.
    
    Args:
        session_id: Unique session identifier
    
    Returns:
        Persona dict or None if not found
    """
    if not REST_URL:
        logger.warning("Supabase not configured")
        return None
    
    try:
        url = f"{REST_URL}/personas?session_id=eq.{session_id}&select=persona_json"
        response = httpx.get(url, headers=get_headers(), timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data and len(data) > 0:
                return data[0].get("persona_json")
        
        return None
    except Exception as e:
        logger.error(f"Error fetching persona: {e}")
        return None


def save_persona(session_id: str, persona: Dict[str, Any]) -> bool:
    """
    Save persona to database.
    
    Args:
        session_id: Unique session identifier
        persona: Complete persona dictionary
    
    Returns:
        True if saved successfully
    """
    if not REST_URL:
        logger.warning("Supabase not configured, persona saved locally only")
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
            "created_at": datetime.utcnow().isoformat()
        }
        
        url = f"{REST_URL}/personas"
        response = httpx.post(url, headers=get_headers(), json=data, timeout=10)
        
        if response.status_code in [200, 201]:
            logger.info(f"Saved persona for session: {session_id}")
            return True
        else:
            logger.warning(f"Failed to save persona: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        logger.error(f"Error saving persona: {e}")
        return False


def update_session_activity(session_id: str, message_count: int) -> bool:
    """
    Update session activity timestamp and message count.
    
    Args:
        session_id: Unique session identifier
        message_count: Total messages exchanged
    
    Returns:
        True if updated successfully
    """
    if not REST_URL:
        return False
    
    try:
        data = {
            "message_count": message_count,
            "last_activity": datetime.utcnow().isoformat()
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
    """
    Save extracted intelligence to database.
    
    Args:
        session_id: Unique session identifier
        intelligence: Extracted intelligence dict
        scam_detected: Whether scam was detected
        agent_notes: Agent's analysis notes
    
    Returns:
        True if saved successfully
    """
    if not REST_URL:
        return False
    
    try:
        # Deduplicate and clean data before saving
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
            "created_at": datetime.utcnow().isoformat()
        }
        
        # Check if we already have intelligence for this session to update instead of insert
        # This prevents duplicate rows in the intelligence table for the same session
        check_url = f"{REST_URL}/intelligence?session_id=eq.{session_id}&select=id"
        check_resp = httpx.get(check_url, headers=get_headers(), timeout=5)
        
        if check_resp.status_code == 200 and check_resp.json():
            # Update existing record
            intel_id = check_resp.json()[0]['id']
            url = f"{REST_URL}/intelligence?id=eq.{intel_id}"
            response = httpx.patch(url, headers=get_headers(), json=data, timeout=10)
        else:
            # Insert new record
            url = f"{REST_URL}/intelligence"
            response = httpx.post(url, headers=get_headers(), json=data, timeout=10)
        
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
    """
    Mark that GUVI callback has been sent for this session.
    
    Args:
        session_id: Unique session identifier
    
    Returns:
        True if updated successfully
    """
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
    """
    Save a conversation message.
    
    Args:
        session_id: Unique session identifier
        sender: 'scammer' or 'agent'
        message: Message text
        strategy_used: Strategy used by agent (if sender is agent)
    
    Returns:
        True if saved successfully
    """
    if not REST_URL:
        return False
    
    try:
        data = {
            "session_id": session_id,
            "sender": sender,
            "message": message,
            "strategy_used": strategy_used,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        url = f"{REST_URL}/conversations"
        response = httpx.post(url, headers=get_headers(), json=data, timeout=10)
        return response.status_code in [200, 201]
        
    except Exception as e:
        logger.error(f"Error saving message: {e}")
        return False


# In-memory cache for when Supabase is not available
_persona_cache: Dict[str, Dict[str, Any]] = {}


def get_cached_persona(session_id: str) -> Optional[Dict[str, Any]]:
    """Get persona from cache (fallback when DB unavailable)."""
    return _persona_cache.get(session_id)


def cache_persona(session_id: str, persona: Dict[str, Any]) -> None:
    """Store persona in cache."""
    _persona_cache[session_id] = persona
