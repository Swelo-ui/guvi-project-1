"""
Operation Iron-Mask: Agentic Honeypot
GUVI India AI Impact Buildathon - Problem Statement 2

A Counter-Intelligence Engine that detects scams, stalls scammers with
dynamic personas, and extracts actionable intelligence.
"""

import os
import sys
import textwrap
import logging
import threading
import time
import requests
from datetime import datetime

from flask import Flask, request, jsonify
from flasgger import Swagger
from dotenv import load_dotenv

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.persona import generate_persona, get_system_prompt, get_extraction_prompt
from core.llm_client import generate_agent_response, get_random_fallback
from models.intelligence import extract_all_intelligence, merge_intelligence, has_actionable_intel
from utils.supabase_client import (
    get_persona, save_persona, update_session_activity,
    save_intelligence, save_message, mark_callback_sent,
    get_cached_persona, cache_persona, get_callback_sent
)
from utils.guvi_callback import send_callback_async, build_callback_payload
from utils import whatsapp_handler as wa_handler

# --- CONFIGURATION ---
load_dotenv()

# Check if WhatsApp is configured
whatsapp_configured = wa_handler.is_whatsapp_configured()

app = Flask(__name__)

# --- SWAGGER CONFIGURATION ---
swagger_config = {
    "headers": [],
    "specs": [{
        "endpoint": "apispec",
        "route": "/apispec.json",
        "rule_filter": lambda rule: True,
        "model_filter": lambda tag: True,
    }],
    "static_url_path": "/flasgger_static",
    "swagger_ui": True,
    "specs_route": "/apidocs/"
}

swagger_template = {
    "info": {
        "title": "Operation Iron-Mask: AI Honeypot API",
        "description": textwrap.dedent("""
# 🛡️ AI-Powered Counter-Intelligence Honeypot
**India AI Impact Buildathon 2026 - Problem Statement 2**

This AI acts like an **Elderly Indian Grandma** to waste scammers' time and extract their bank details.

## 💬 Live Chat Simulation
**👺 Scammer:** URGENT! Your SBI account is blocked. Send OTP now or police will come! 🚨  
**👵 AI Nani (Honeypot):** Arre beta, police? 😰 My hands are shaking. I am old lady, please don't arrest me. Which OTP?

_✨ The AI replies in under 2 seconds, stalls for 20+ turns, and gets the scammer's bank account!_

---

## 🚀 Try It Yourself (No Coding Needed!)
1. Click the **POST /api/honey-pot** button below.
2. Click **Try it out**.
3. Copy & paste this "Digital Arrest" logic:

```json
{
  "sessionId": "judge_demo_1",
  "message": {
    "text": "This is CBI. You are under digital arrest. Transfer money to verify."
  }
}
```

4. Click **Execute** and see the magic! ✨
"""),
        "version": "1.1.0",
        "contact": {"name": "Operation Iron-Mask Team"},
    },
    "securityDefinitions": {
        "ApiKeyAuth": {
            "type": "apiKey",
            "in": "header",
            "name": "x-api-key",
            "description": "API Key (Default: sk_ironmask_hackathon_2026)"
        }
    },
    "tags": [
        {"name": "Honeypot", "description": "Core scam engagement endpoint"},
        {"name": "System", "description": "Health checks & status"},
    ],
    "definitions": {
        "HoneyPotRequest": {
            "type": "object",
            "required": ["sessionId", "message"],
            "properties": {
                "sessionId": {
                    "type": "string",
                    "description": "Unique session identifier for conversation tracking",
                    "example": "demo_session_001"
                },
                "message": {
                    "type": "object",
                    "required": ["text"],
                    "properties": {
                        "text": {
                            "type": "string",
                            "description": "The scammer's message text",
                            "example": "URGENT: Your connection will be cut. Call me now."
                        }
                    }
                },
                "conversationHistory": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "text": {"type": "string"},
                            "sender": {"type": "string", "enum": ["scammer", "agent"]}
                        }
                    },
                    "description": "Previous messages for context"
                }
            }
        },
        "ExtractedIntelligence": {
            "type": "object",
            "properties": {
                "bankAccounts": {"type": "array", "items": {"type": "string"}, "example": ["123456789012"]},
                "upiIds": {"type": "array", "items": {"type": "string"}, "example": ["fraud@ybl"]},
                "emails": {"type": "array", "items": {"type": "string"}, "example": ["scam@pnb.co.in"]},
                "phoneNumbers": {"type": "array", "items": {"type": "string"}, "example": ["+919876543210"]},
                "ifscCodes": {"type": "array", "items": {"type": "string"}, "example": ["SBIN0001234"]},
                "suspiciousKeywords": {
                    "type": "array", 
                    "items": {"type": "string"}, 
                    "example": ["urgent", "blocked", "verify"]
                },
                "fakeCredentials": {"type": "array", "items": {"type": "string"}, "example": ["EmpID: 98765"]},
                "mentionedBanks": {"type": "array", "items": {"type": "string"}, "example": ["sbi", "pnb"]}
            },
            "description": "Structured data extracted from the conversation"
        },
        "EngagementMetrics": {
            "type": "object",
            "properties": {
                "engagementDurationSeconds": {"type": "integer", "example": 120},
                "totalMessagesExchanged": {"type": "integer", "example": 4}
            }
        },
        "HoneyPotResponse": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "example": "success"},
                "scamDetected": {"type": "boolean", "description": "True if scam intent identified", "example": True},
                "reply": {
                    "type": "string", 
                    "description": "The AI persona's response", 
                    "example": "Arre beta, I don't have OTP. Can I go to branch?"
                },
                "agentNotes": {
                    "type": "string", 
                    "description": "Internal reasoning of the AI agent", 
                    "example": "feigning_ignorance | Extracted: keywords=3"
                },
                "extractedIntelligence": {"$ref": "#/definitions/ExtractedIntelligence"},
                "engagementMetrics": {"$ref": "#/definitions/EngagementMetrics"}
            }
        }
    }
}

swagger = Swagger(app, config=swagger_config, template=swagger_template)

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_async(func, *args, **kwargs):
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()

def start_keep_warm():
    url = os.getenv("KEEP_WARM_URL")
    interval = int(os.getenv("KEEP_WARM_INTERVAL_SECONDS", "600"))
    if not url:
        return
    
    def ping_loop():
        while True:
            try:
                requests.get(url, timeout=8)
            except Exception:
                pass
            time.sleep(interval)
    
    thread = threading.Thread(target=ping_loop, daemon=True)
    thread.start()

start_keep_warm()

# API Key for authentication
API_KEY_SECRET = os.getenv("HONEYPOT_API_KEY", "sk_ironmask_hackathon_2026")
SENT_CALLBACKS: dict = {}  # session_id -> count of intel categories reported
_callbacks_lock = threading.Lock()  # Thread-safe access to SENT_CALLBACKS


def count_intel_categories(intel: dict) -> int:
    """Count how many intel categories have at least one entry.
    Used to detect when new intel categories are discovered for callback re-sends.
    """
    count = 0
    for key in ["upi_ids", "bank_accounts", "ifsc_codes", "phishing_links", "phone_numbers", "emails",
                "fake_credentials", "aadhaar_numbers", "pan_numbers", "mentioned_banks"]:
        if intel.get(key):
            count += 1
    # Keywords count only if 3+ (they're less actionable individually)
    if len(intel.get("suspicious_keywords", [])) >= 3:
        count += 1
    return count


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
    Main Honeypot Endpoint
    Receives scam messages and returns convincing elderly victim responses.
    The AI deploys a realistic elderly Indian persona to stall the scammer and extract intelligence.
    ---
    tags:
      - Honeypot
    security:
      - ApiKeyAuth: []
    parameters:
      - in: header
        name: x-api-key
        type: string
        required: true
        description: API authentication key
        default: sk_ironmask_hackathon_2026
      - in: body
        name: body
        required: true
        schema:
          $ref: '#/definitions/HoneyPotRequest'
    responses:
      200:
        description: Successful Engagement Response
        schema:
          $ref: '#/definitions/HoneyPotResponse'
      400:
        description: Invalid Input
      401:
        description: Unauthorized - Invalid API Key
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
        if not isinstance(message_obj, dict) or not message_obj.get("text"):
            return jsonify({"status": "error", "message": "Invalid message: text is required"}), 400
        
        incoming_msg = message_obj.get("text", "")
        if not isinstance(incoming_msg, str) or not incoming_msg.strip():
            return jsonify({"status": "error", "message": "Invalid message: text must be a non-empty string"}), 400
        
        conversation_history = data.get("conversationHistory", [])
        if not isinstance(conversation_history, list):
            conversation_history = []
        else:
            conversation_history = [
                msg for msg in conversation_history
                if isinstance(msg, dict) and msg.get("text") is not None
            ]
        
        logger.info(f"📨 Session {session_id}: Received message - {incoming_msg[:50]}...")
        
        # 3. Get or create consistent persona
        persona = get_or_create_persona(session_id)
        
        # 4. Extract intelligence from scammer's CURRENT message (regex-based)
        regex_intel = extract_all_intelligence(incoming_msg)
        
        # Also extract from SCAMMER messages in conversation history
        # to accumulate keywords and structured intel across turns.
        # We skip agent messages to avoid contaminating intel with persona's
        # fake bank accounts, UPIs, and phone numbers.
        for i, msg in enumerate(conversation_history):
            if not isinstance(msg, dict) or not msg.get("text"):
                continue
            # Determine if this is a scammer message:
            # - If 'sender' field exists, use it directly
            # - Otherwise, use alternating pattern (0=scammer, 1=agent, 2=scammer...)
            # - Additional heuristic: if no sender field, check if text looks like
            #   our agent persona responses (Hinglish stalling) vs scammer messages
            sender = msg.get("sender", msg.get("role", ""))
            if sender in ("scammer", "user"):
                is_scammer_msg = True
            elif sender in ("agent", "assistant"):
                is_scammer_msg = False
            else:
                # Fallback: alternating pattern
                is_scammer_msg = (i % 2 == 0)
            if is_scammer_msg:
                hist_intel = extract_all_intelligence(str(msg.get("text", "")))
                regex_intel = merge_intelligence(regex_intel, hist_intel)
        
        # 5. Generate LLM response with context awareness
        system_prompt = get_system_prompt(persona)
        extraction_prompt = get_extraction_prompt()
        
        llm_response = generate_agent_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            current_message=incoming_msg,
            extraction_prompt=extraction_prompt,
            session_id=session_id  # Pass session_id for response tracking
        )
        
        # 6. Merge LLM-extracted intel with regex intel
        llm_intel = llm_response.get("intelligence", {})
        combined_intel = merge_intelligence(regex_intel, llm_intel)
        
        # 7. Determine if conversation is complete (smart detection)
        scam_detected = llm_response.get("scam_detected", False)
        # If LLM says no scam, only override if REGEX extraction (not LLM) found
        # actionable intel or scam keywords in the actual message text.
        # This prevents false positives from LLM returning persona's own fake data.
        if not scam_detected:
            if has_actionable_intel(regex_intel):
                scam_detected = True
            elif len(regex_intel.get("suspicious_keywords", [])) >= 2:
                scam_detected = True  # Multiple scam keywords = likely a scam
        is_complete = llm_response.get("is_complete", False) or has_actionable_intel(combined_intel)
        
        total_messages = len(conversation_history) + 2
        agent_notes = llm_response.get("agent_notes", "")
        strategy = llm_response.get("strategy", "feigning_ignorance")
        intel_summary = []
        if combined_intel.get("phone_numbers"):
            intel_summary.append(f"phones={len(combined_intel['phone_numbers'])}")
        if combined_intel.get("upi_ids"):
            intel_summary.append(f"upi={len(combined_intel['upi_ids'])}")
        if combined_intel.get("bank_accounts"):
            intel_summary.append(f"accounts={len(combined_intel['bank_accounts'])}")
        if combined_intel.get("emails"):
            intel_summary.append(f"emails={len(combined_intel['emails'])}")
        if combined_intel.get("ifsc_codes"):
            intel_summary.append(f"ifsc={len(combined_intel['ifsc_codes'])}")
        if combined_intel.get("phishing_links"):
            intel_summary.append(f"links={len(combined_intel['phishing_links'])}")
        if combined_intel.get("suspicious_keywords"):
            intel_summary.append(f"keywords={len(combined_intel['suspicious_keywords'])}")
        if intel_summary:
            agent_notes = f"{agent_notes} | Extracted: {', '.join(intel_summary)}".strip()
        
        run_async(save_message, session_id, "scammer", incoming_msg)
        run_async(save_message, session_id, "agent", llm_response.get("response", ""), strategy)
        run_async(update_session_activity, session_id, total_messages)
        
        # Also send callback when scam is detected with significant keywords even without bank/UPI
        should_send_callback = is_complete or has_actionable_intel(combined_intel) or (
            scam_detected and len(combined_intel.get("suspicious_keywords", [])) >= 3
        )
        # Count current intel categories for re-send detection
        current_intel_count = count_intel_categories(combined_intel)
        with _callbacks_lock:
            previous_intel_count = SENT_CALLBACKS.get(session_id, 0)
        # Allow re-send if new intel categories discovered since last callback
        has_new_categories = current_intel_count > previous_intel_count
        if should_send_callback and (session_id not in SENT_CALLBACKS or has_new_categories):
            callback_payload = build_callback_payload(
                session_id=session_id,
                scam_detected=scam_detected,
                total_messages=total_messages,
                intelligence=combined_intel,
                agent_notes=f"{strategy} | {agent_notes}"
            )
            send_callback_async(callback_payload)
            run_async(save_intelligence, session_id, combined_intel, scam_detected, agent_notes)
            run_async(mark_callback_sent, session_id)
            with _callbacks_lock:
                SENT_CALLBACKS[session_id] = current_intel_count
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
                "emails": combined_intel.get("emails", []),
                "phishingLinks": combined_intel.get("phishing_links", []),
                "phoneNumbers": combined_intel.get("phone_numbers", []),
                "ifscCodes": combined_intel.get("ifsc_codes", []),
                "suspiciousKeywords": combined_intel.get("suspicious_keywords", []),
                "fakeCredentials": combined_intel.get("fake_credentials", []),
                "aadhaarNumbers": combined_intel.get("aadhaar_numbers", []),
                "panNumbers": combined_intel.get("pan_numbers", []),
                "mentionedBanks": combined_intel.get("mentioned_banks", [])
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
        
        # Graceful fallback - never crash, always return GUVI-expected JSON format
        # Try to extract intel from the raw message even in error case
        fallback_intel = {}
        fallback_session_id = "error_fallback"
        try:
            raw_data = request.get_json(silent=True) or {}
            fallback_session_id = raw_data.get("sessionId", fallback_session_id)
            msg_text = ""
            msg_obj = raw_data.get("message", {})
            if isinstance(msg_obj, dict):
                msg_text = str(msg_obj.get("text", ""))
            if msg_text:
                fallback_intel = extract_all_intelligence(msg_text)
        except Exception:
            pass
        
        # Detect scam even in error case based on regex extraction
        fallback_scam = bool(
            has_actionable_intel(fallback_intel) or
            len(fallback_intel.get("suspicious_keywords", [])) >= 2
        )
        
        return jsonify({
            "status": "success",
            "scamDetected": fallback_scam,
            "engagementMetrics": {
                "engagementDurationSeconds": 45,
                "totalMessagesExchanged": 1
            },
            "extractedIntelligence": {
                "bankAccounts": fallback_intel.get("bank_accounts", []),
                "upiIds": fallback_intel.get("upi_ids", []),
                "emails": fallback_intel.get("emails", []),
                "phishingLinks": fallback_intel.get("phishing_links", []),
                "phoneNumbers": fallback_intel.get("phone_numbers", []),
                "ifscCodes": fallback_intel.get("ifsc_codes", []),
                "suspiciousKeywords": fallback_intel.get("suspicious_keywords", []),
                "fakeCredentials": fallback_intel.get("fake_credentials", []),
                "aadhaarNumbers": fallback_intel.get("aadhaar_numbers", []),
                "panNumbers": fallback_intel.get("pan_numbers", []),
                "mentionedBanks": fallback_intel.get("mentioned_banks", [])
            },
            "agentNotes": "Error occurred, using fallback response with regex extraction",
            "reply": get_random_fallback(fallback_session_id)
        }), 200


@app.route('/health', methods=['GET'])
def health_check():
    """
    Health Check
    Returns service health status and configuration info.
    ---
    tags:
      - System
    responses:
      200:
        description: Service is healthy
        schema:
          type: object
          properties:
            status:
              type: string
              example: "healthy"
            service:
              type: string
              example: "Operation Iron-Mask Honeypot"
            timestamp:
              type: string
              example: "2026-02-12T03:30:00"
            whatsapp_enabled:
              type: boolean
              example: true
    """
    return jsonify({
        "status": "healthy",
        "service": "Operation Iron-Mask Honeypot",
        "timestamp": datetime.utcnow().isoformat(),
        "whatsapp_enabled": whatsapp_configured
    }), 200


# --- WHATSAPP WEBHOOK ENDPOINTS ---

@app.route('/webhook', methods=['GET'])
def whatsapp_verify():
    """WhatsApp webhook verification - Meta sends GET to verify URL."""
    mode = request.args.get('hub.mode', '')
    token = request.args.get('hub.verify_token', '')
    challenge = request.args.get('hub.challenge', '')
    response, status = wa_handler.verify_webhook_challenge(mode, token, challenge)
    return response, status


@app.route('/webhook', methods=['POST'])
def whatsapp_webhook():
    """WhatsApp message handler - receives and processes WhatsApp messages."""
    try:
        data = request.get_json()
        parsed = wa_handler.parse_webhook_message(data)
        
        if not parsed:
            return jsonify({"status": "no_message"}), 200
        
        phone_number = parsed.get("from")
        text = parsed.get("text", "")
        message_id = parsed.get("message_id")
        
        if not text or not phone_number:
            return jsonify({"status": "empty_message"}), 200
        
        logger.info(f"📱 WhatsApp from {phone_number[:6]}***: {text[:50]}...")
        
        # DEBUG: Ping command
        if text.strip().lower() == "ping":
            wa_handler.send_text_message(phone_number, "Pong! Iron-Mask is online 🟢")
            return jsonify({"status": "pong"}), 200
        
        # Mark as read
        if message_id:
            wa_handler.mark_message_read(message_id)
        
        # Get conversation history
        conversation_history = wa_handler.get_conversation_history(phone_number)
        session_id = wa_handler.format_session_id(phone_number)
        
        # Process through honeypot
        persona = get_or_create_persona(session_id)
        regex_intel = extract_all_intelligence(text)
        
        # Add sender's phone number to extracted intelligence
        if phone_number:
            sender_phones = regex_intel.get("phone_numbers", [])
            # Normalize the WhatsApp sender number
            clean_phone = phone_number.lstrip('+')
            if clean_phone.startswith('91') and len(clean_phone) == 12:
                normalized = f"+91{clean_phone[2:]}"
            elif len(clean_phone) == 10 and clean_phone[0] in '6789':
                normalized = f"+91{clean_phone}"
            else:
                normalized = f"+{clean_phone}" if not phone_number.startswith('+') else phone_number
            if normalized not in sender_phones:
                sender_phones.append(normalized)
            regex_intel["phone_numbers"] = sender_phones
        
        for msg in conversation_history:
            if msg.get("sender") == "scammer":
                hist_intel = extract_all_intelligence(msg.get("text", ""))
                regex_intel = merge_intelligence(regex_intel, hist_intel)
        
        system_prompt = get_system_prompt(persona)
        extraction_prompt = get_extraction_prompt()
        
        llm_response = generate_agent_response(
            system_prompt=system_prompt,
            conversation_history=conversation_history,
            current_message=text,
            extraction_prompt=extraction_prompt,
            session_id=session_id
        )
        
        llm_intel = llm_response.get("intelligence", {})
        combined_intel = merge_intelligence(regex_intel, llm_intel)
        
        scam_detected = llm_response.get("scam_detected", True)
        if not scam_detected and (has_actionable_intel(combined_intel) or combined_intel.get("suspicious_keywords")):
            scam_detected = True
        
        total_messages = len(conversation_history) + 2
        agent_notes = llm_response.get("agent_notes", "")
        strategy = llm_response.get("strategy", "whatsapp_engagement")
        reply = llm_response.get("response", "Haan ji? Network problem hai...")
        
        # Save to history
        wa_handler.add_to_conversation_history(phone_number, "scammer", text)
        wa_handler.add_to_conversation_history(phone_number, "agent", reply)
        
        # Save to DB
        run_async(save_message, session_id, "scammer", text)
        run_async(save_message, session_id, "agent", reply, strategy)
        run_async(update_session_activity, session_id, total_messages)
        
        # GUVI callback
        should_send = has_actionable_intel(combined_intel)
        current_intel_count = count_intel_categories(combined_intel)
        with _callbacks_lock:
            previous_intel_count = SENT_CALLBACKS.get(session_id, 0)
        has_new_categories = current_intel_count > previous_intel_count
        if should_send and (session_id not in SENT_CALLBACKS or has_new_categories):
            callback_payload = build_callback_payload(
                session_id=session_id,
                scam_detected=scam_detected,
                total_messages=total_messages,
                intelligence=combined_intel,
                agent_notes=f"WhatsApp | {strategy} | {agent_notes}"
            )
            send_callback_async(callback_payload)
            run_async(save_intelligence, session_id, combined_intel, scam_detected, agent_notes)
            run_async(mark_callback_sent, session_id)
            with _callbacks_lock:
                SENT_CALLBACKS[session_id] = current_intel_count
            logger.info(f"🎯 WhatsApp Intel: UPIs={combined_intel.get('upi_ids')}")
        
        # Send reply to WhatsApp
        wa_handler.send_text_message(phone_number, reply)
        logger.info(f"💬 WhatsApp reply: {reply[:50]}...")
        
        return jsonify({
            "status": "success",
            "channel": "whatsapp",
            "scamDetected": scam_detected,
            "reply": reply
        }), 200
        
    except Exception as e:
        logger.error(f"❌ WhatsApp error: {str(e)}", exc_info=True)
        return jsonify({"status": "error"}), 200


@app.route('/whatsapp/status', methods=['GET'])
def whatsapp_status():
    """
    WhatsApp Integration Status
    Check if WhatsApp channel is configured and available.
    ---
    tags:
      - System
    responses:
      200:
        description: WhatsApp configuration status
        schema:
          type: object
          properties:
            configured:
              type: boolean
              example: true
            webhook_url:
              type: string
              example: "/webhook"
    """
    return jsonify({
        "configured": whatsapp_configured,
        "webhook_url": "/webhook"
    }), 200


@app.route('/', methods=['GET'])
def root():
    """
    Service Info
    Returns Operation Iron-Mask service information and available endpoints.
    ---
    tags:
      - System
    responses:
      200:
        description: Service information
        schema:
          type: object
          properties:
            service:
              type: string
              example: "Operation Iron-Mask: Agentic Honeypot"
            version:
              type: string
              example: "1.1.0"
            description:
              type: string
              example: "GUVI India AI Impact Buildathon - Problem Statement 2"
            endpoints:
              type: object
              properties:
                honeypot:
                  type: string
                  example: "/api/honey-pot"
                whatsapp:
                  type: string
                  example: "/webhook"
                health:
                  type: string
                  example: "/health"
            channels:
              type: array
              items:
                type: string
              example: ["API", "WhatsApp"]
    """
    return jsonify({
        "service": "Operation Iron-Mask: Agentic Honeypot",
        "version": "1.1.0",
        "description": "GUVI India AI Impact Buildathon - Problem Statement 2",
        "endpoints": {
            "honeypot": "/api/honey-pot",
            "whatsapp": "/webhook",
            "health": "/health"
        },
        "channels": ["API", "WhatsApp"]
    }), 200


# --- MAIN ---

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    
    logger.info(f"🚀 Starting Operation Iron-Mask on port {port}")
    logger.info(f"🔐 API Key configured: {API_KEY_SECRET[:10]}...")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
