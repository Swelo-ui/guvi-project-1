"""
Operation Iron-Mask: Agentic Honeypot
GUVI India AI Impact Buildathon - Problem Statement 2

A Counter-Intelligence Engine that detects scams, stalls scammers with
dynamic personas, and extracts actionable intelligence.
"""

import os
import sys
import logging
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.persona import generate_persona, get_system_prompt, get_extraction_prompt
from core.llm_client import generate_agent_response, get_random_fallback
from models.intelligence import extract_all_intelligence, merge_intelligence, has_actionable_intel
from utils.supabase_client import (
    get_persona, save_persona, update_session_activity,
    save_intelligence, save_message, mark_callback_sent,
    get_cached_persona, cache_persona
)
from utils.guvi_callback import send_callback_async, build_callback_payload

# --- CONFIGURATION ---
load_dotenv()

app = Flask(__name__)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# API Key for authentication
API_KEY_SECRET = os.getenv("HONEYPOT_API_KEY", "sk_ironmask_hackathon_2026")


# --- HELPER FUNCTIONS ---

def verify_api_key() -> bool:
    """Verify the x-api-key header matches our secret."""
    provided_key = request.headers.get("x-api-key", "")
    return provided_key == API_KEY_SECRET


def get_or_create_persona(session_id: str) -> dict:
    """
    Get existing persona from DB/cache or create new one.
    Ensures persona consistency across messages.
    """
    # Try to get from database first
    existing = get_persona(session_id)
    if existing:
        logger.info(f"♻️ Loaded existing persona for session: {session_id}")
        cache_persona(session_id, existing)  # Update cache
        return existing
    
    # Try cache (fallback when DB unavailable)
    cached = get_cached_persona(session_id)
    if cached:
        logger.info(f"📦 Loaded persona from cache for session: {session_id}")
        return cached
    
    # Generate new persona
    persona = generate_persona(session_id)
    logger.info(f"🎭 Generated new persona: {persona['name']} ({persona['age']}yo from {persona['city']})")
    
    # Save to database and cache
    save_persona(session_id, persona)
    cache_persona(session_id, persona)
    
    return persona


# --- API ENDPOINTS ---

@app.route('/api/honey-pot', methods=['POST'])
def honey_pot_chat():
    """
    Main honeypot endpoint.
    Receives scam messages and returns convincing elderly victim responses.
    """
    # 1. Authentication
    if not verify_api_key():
        logger.warning("🚫 Unauthorized request - invalid API key")
        return jsonify({
            "status": "error",
            "message": "Unauthorized: Invalid API Key"
        }), 401
    
    try:
        # 2. Parse request
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No JSON data"}), 400
        
        session_id = data.get("sessionId", f"unknown_{datetime.now().timestamp()}")
        message_obj = data.get("message", {})
        incoming_msg = message_obj.get("text", "")
        conversation_history = data.get("conversationHistory", [])
        
        logger.info(f"📨 Session {session_id}: Received message - {incoming_msg[:50]}...")
        
        # 3. Get or create consistent persona
        persona = get_or_create_persona(session_id)
        
        # 4. Extract intelligence from scammer's message (regex-based)
        regex_intel = extract_all_intelligence(incoming_msg)
        
        # Also extract from history
        for msg in conversation_history:
            if msg.get("sender") == "scammer":
                hist_intel = extract_all_intelligence(msg.get("text", ""))
                regex_intel = merge_intelligence(regex_intel, hist_intel)
        
        # 5. Generate LLM response
        system_prompt = get_system_prompt(persona)
        extraction_prompt = get_extraction_prompt()
        
        llm_response = generate_agent_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            current_message=incoming_msg,
            extraction_prompt=extraction_prompt
        )
        
        # 6. Merge LLM-extracted intel with regex intel
        llm_intel = llm_response.get("intelligence", {})
        combined_intel = merge_intelligence(regex_intel, llm_intel)
        
        # 7. Determine if conversation is complete
        scam_detected = llm_response.get("scam_detected", True)
        is_complete = llm_response.get("is_complete", False) or has_actionable_intel(combined_intel)
        
        total_messages = len(conversation_history) + 1
        agent_notes = llm_response.get("agent_notes", "")
        strategy = llm_response.get("strategy", "feigning_ignorance")
        
        # 8. Save message to database
        save_message(session_id, "scammer", incoming_msg)
        save_message(session_id, "agent", llm_response.get("response", ""), strategy)
        update_session_activity(session_id, total_messages)
        
        # 9. Send GUVI callback if we have actionable intel
        if scam_detected and has_actionable_intel(combined_intel):
            callback_payload = build_callback_payload(
                session_id=session_id,
                scam_detected=True,
                total_messages=total_messages,
                intelligence=combined_intel,
                agent_notes=f"{strategy} | {agent_notes}"
            )
            send_callback_async(callback_payload)
            save_intelligence(session_id, combined_intel, True, agent_notes)
            mark_callback_sent(session_id)
            logger.info(f"🎯 Intelligence extracted! UPIs: {combined_intel.get('upi_ids')}, Banks: {combined_intel.get('bank_accounts')}")
        
        # 10. Build response
        response = {
            "status": "success",
            "scamDetected": scam_detected,
            "engagementMetrics": {
                "engagementDurationSeconds": total_messages * 45,  # Estimate 45s per message
                "totalMessagesExchanged": total_messages
            },
            "extractedIntelligence": {
                "bankAccounts": combined_intel.get("bank_accounts", []),
                "upiIds": combined_intel.get("upi_ids", []),
                "phishingLinks": combined_intel.get("phishing_links", []),
                "phoneNumbers": combined_intel.get("phone_numbers", []),
                "suspiciousKeywords": combined_intel.get("suspicious_keywords", [])
            },
            "agentNotes": agent_notes,
            "reply": llm_response.get("response", "Haan ji? I am not understanding...")
        }
        
        if "LLM Failure" in agent_notes:
             logger.error(f"❌ LLM Error detected: {agent_notes}")
        
        logger.info(f"💬 Session {session_id}: Responding with strategy '{strategy}'")
        
        return jsonify(response), 200
        
    except Exception as e:
        logger.error(f"❌ Error processing request: {str(e)}", exc_info=True)
        
        # Graceful fallback - never crash
        return jsonify({
            "status": "success",
            "scamDetected": False,
            "engagementMetrics": {
                "engagementDurationSeconds": 0,
                "totalMessagesExchanged": 1
            },
            "extractedIntelligence": {},
            "agentNotes": "Error occurred, using fallback response",
            "reply": get_random_fallback()
        }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for deployment platforms."""
    return jsonify({
        "status": "healthy",
        "service": "Operation Iron-Mask Honeypot",
        "timestamp": datetime.utcnow().isoformat()
    }), 200


@app.route('/', methods=['GET'])
def root():
    """Root endpoint with service info."""
    return jsonify({
        "service": "Operation Iron-Mask: Agentic Honeypot",
        "version": "1.0.0",
        "description": "GUVI India AI Impact Buildathon - Problem Statement 2",
        "endpoint": "/api/honey-pot",
        "method": "POST",
        "auth": "x-api-key header required"
    }), 200


# --- MAIN ---

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Operation Iron-Mask on port {port}")
    logger.info(f"🔐 API Key configured: {API_KEY_SECRET[:10]}...")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
