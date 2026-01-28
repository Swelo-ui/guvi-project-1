"""
OpenRouter LLM Client
Handles API calls to LLaMA 3.1 405B with fallback to Trinity
"""

import os
import json
import logging
import requests
from typing import List, Dict, Any, Optional

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "tngtech/deepseek-r1t2-chimera:free")
OPENROUTER_FALLBACK = os.getenv("OPENROUTER_FALLBACK_MODEL", "nvidia/nemotron-3-nano-30b-a3b:free")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"


def call_openrouter(
    messages: List[Dict[str, str]],
    model: Optional[str] = None,
    temperature: float = 0.8,
    max_tokens: int = 500
) -> Optional[str]:
    """
    Call OpenRouter API with the given messages.
    
    Args:
        messages: List of message dicts with 'role' and 'content'
        model: Model to use (defaults to primary model)
        temperature: Creativity level (0.0-1.0)
        max_tokens: Maximum response tokens
    
    Returns:
        Response text or None if failed
    """
    if not OPENROUTER_API_KEY:
        logger.error("OPENROUTER_API_KEY not set")
        return None
    
    model = model or OPENROUTER_MODEL
    
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://guvi-honeypot.onrender.com",
        "X-Title": "GUVI Honeypot Agent"
    }
    
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": max_tokens
    }
    
    try:
        response = requests.post(
            OPENROUTER_BASE_URL,
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if 'choices' in data and data['choices']:
                 return data['choices'][0]['message']['content']
            else:
                 logger.error(f"OpenRouter empty choices: {data}")
                 return f"Error: Empty response from model"
        else:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            return f"Error: API {response.status_code} - {response.text}"
            
    except requests.exceptions.Timeout:
        logger.error("OpenRouter request timed out")
        return "Error: Request Timed Out"
    except Exception as e:
        logger.error(f"OpenRouter exception: {str(e)}")
        return f"Error: {str(e)}"


import random

# Fallback messages to use when LLM fails or is stalling
import re

from core.conversation_analyzer import (
    analyze_conversation, 
    get_contextual_response,
    detect_intents,
    ScammerIntent,
    CONTEXTUAL_RESPONSES
)

# Generic fallback messages (used only when context detection fails)
GENERIC_FALLBACK_MESSAGES = [
    "Acha ji, network is very slow. Please wait, I am trying...",
    "Hello? Can you hear me? My phone is breaking up.",
    "One minute, someone is at the door. I will just check.",
    "My son is calling on other line... wait one second.",
    "Screen is stuck. Should I restart the phone?",
    "The screen went black. Is it working?",
    "Battery is 2%, let me find charger.",
    "My grandson is crying, one moment please.",
    "Sorry beta, I pressed the wrong button I think.",
]

# Session response tracking to prevent repetition
_session_responses: Dict[str, List[str]] = {}

def get_used_responses(session_id: str) -> List[str]:
    """Get list of previously used responses for a session."""
    return _session_responses.get(session_id, [])

def track_response(session_id: str, response: str):
    """Track a response as used for this session."""
    if session_id not in _session_responses:
        _session_responses[session_id] = []
    _session_responses[session_id].append(response)
    # Keep only last 20 to prevent memory issues
    if len(_session_responses[session_id]) > 20:
        _session_responses[session_id] = _session_responses[session_id][-20:]

def get_random_fallback():
    """Get a random generic fallback message."""
    return random.choice(GENERIC_FALLBACK_MESSAGES)

def get_contextual_fallback(
    scammer_message: str, 
    session_id: str = "default",
    conversation_history: List[Dict[str, str]] = None
) -> str:
    """
    Get a context-aware fallback based on what the scammer is asking.
    
    Args:
        scammer_message: The scammer's current message
        session_id: Session ID for tracking used responses
        conversation_history: Previous messages in conversation
        
    Returns:
        Contextually appropriate response
    """
    if conversation_history is None:
        conversation_history = []
    
    used_responses = get_used_responses(session_id)
    
    try:
        # Analyze the conversation for context
        analysis = analyze_conversation(
            scammer_message, 
            conversation_history, 
            used_responses
        )
        
        # Get the contextual response
        response = analysis.get("suggested_fallback", "")
        
        # Optionally append reverse extraction if appropriate
        if analysis.get("should_reverse_extract") and random.random() > 0.5:
            reverse_prompt = analysis.get("reverse_extraction_prompt", "")
            if reverse_prompt:
                response = f"{response} {reverse_prompt}"
        
        # Track this response
        track_response(session_id, response)
        
        return response
        
    except Exception as e:
        logger.warning(f"Context analysis failed: {e}, using generic fallback")
        return get_random_fallback()

def call_with_fallback(
    messages: List[Dict[str, str]],
    temperature: float = 0.8
) -> str:
    """
    Call primary model, fallback to secondary if failed.
    """
    # Try primary model
    response = call_openrouter(messages, model=OPENROUTER_MODEL, temperature=temperature)
    
    if response and not response.startswith("Error"):
        return response
    
    # Try fallback model
    if response:
        logger.warning(f"Primary model failed ({response}), trying fallback...")
    else:
        logger.warning("Primary model failed, trying fallback...")

    response = call_openrouter(messages, model=OPENROUTER_FALLBACK, temperature=temperature)
    
    if response and not response.startswith("Error"):
        return response
    
    # Emergency fallback response (Randomized)
    logger.error("Both models failed, using emergency fallback")
    return get_random_fallback()


def clean_json_string(json_str: str) -> str:
    """
    Clean up JSON string to handle common LLM errors.
    - Remove markdown code blocks
    - Remove text before/after JSON
    - Fix trailing commas
    - Fix single quotes to double quotes (cautiously)
    """
    # 1. Remove markdown code blocks
    if "```" in json_str:
        json_str = re.sub(r'```json\s*|\s*```', '', json_str)
        # Handle generic code blocks
        json_str = re.sub(r'```\s*|\s*```', '', json_str)
    
    # 2. Extract content between first { and last }
    start = json_str.find('{')
    end = json_str.rfind('}') + 1
    
    if start != -1 and end > start:
        json_str = json_str[start:end]
    else:
        # If no braces found, cannot parse
        return json_str

    # 3. Fix trailing commas (common error)
    # Replaces ", }" with "}" and ", ]" with "]"
    json_str = re.sub(r',\s*}', '}', json_str)
    json_str = re.sub(r',\s*]', ']', json_str)
    
    # 4. Attempt to fix single quotes to double quotes for keys/values
    # This is risky but matches many LLM python-style dict outputs
    # Match 'key': or 'value', avoiding 's (like it's)
    # A simple but useful fix for {'key': 'value'} style
    if "'" in json_str and '"' not in json_str:
        json_str = json_str.replace("'", '"')
        # Revert changes for 's or I'm (basic heuristic)
        json_str = json_str.replace('I"m', "I'm").replace('it"s', "it's")

    # 5. Fix Python constants to JSON constants
    # Only do this if we are reasonable sure it's not part of a string
    # Simple replace is risky but effective for "scam_detected": True
    if "True" in json_str or "False" in json_str or "None" in json_str:
        json_str = json_str.replace(": True", ": true").replace(": False", ": false").replace(": None", ": null")
        json_str = json_str.replace(":True", ": true").replace(":False", ": false").replace(":None", ": null")

    return json_str


def generate_agent_response(
    system_prompt: str,
    conversation_history: List[Dict[str, str]],
    current_message: str,
    extraction_prompt: str,
    session_id: str = "default"
) -> Dict[str, Any]:
    """
    Generate agent response with structured thinking and context awareness.
    
    Args:
        system_prompt: The persona system prompt
        conversation_history: Previous messages
        current_message: Current scammer message
        extraction_prompt: Intelligence extraction prompt
        session_id: Session ID for response tracking
    """
    # Analyze conversation context for smarter responses
    used_responses = get_used_responses(session_id)
    
    try:
        context_analysis = analyze_conversation(
            current_message,
            conversation_history,
            used_responses
        )
    except Exception as e:
        logger.warning(f"Context analysis failed: {e}")
        context_analysis = {"detected_intents": ["unknown"], "conversation_phase": "unknown"}
    
    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history:
        role = "user" if msg.get("sender") == "scammer" else "assistant"
        content = msg.get("text", "")
        messages.append({"role": role, "content": content})
    
    # Add current message
    messages.append({"role": "user", "content": current_message})
    
    # Build context-aware structured prompt
    intent_hint = context_analysis.get("primary_intent", "unknown")
    phase_hint = context_analysis.get("conversation_phase", "unknown")
    
    structured_prompt = f"""
{extraction_prompt}

CONTEXT ANALYSIS (use this to guide your response):
- Scammer's likely intent: {intent_hint.upper()}
- Conversation phase: {phase_hint}
- Message count: {len(conversation_history) + 1}

CRITICAL STRATEGIC GUIDELINES:

1. **RESPOND TO CONTEXT:** The scammer is asking about {intent_hint}. Your response MUST address this specifically:
   - If asking for OTP → Talk about the OTP, ask clarifying questions
   - If asking for account → Express confusion about which account
   - If threatening arrest → Show fear, but ask for official documents
   - If asking for money → Pretend to try, ask for THEIR account details

2. **REVERSE EXTRACTION:** Try to get scammer's details:
   - "But sir, what is YOUR account? I need to verify you first."
   - "Give me YOUR UPI, I'll confirm with my son before sharing."
   - "What is your employee ID? I'm noting down for safety."

3. **CONSISTENCY:** Never contradict facts from earlier (name, bank, family).

4. **VARIETY:** Never repeat an exact response. Check conversation history.

5. **NATURAL STALLING:** Use believable delays relevant to the context.

RESPONSE FORMAT (respond in this exact JSON format):
{{
    "scam_detected": true/false,
    "scam_type": "bank_fraud/upi_fraud/digital_arrest/lottery_scam/kyc_fraud/investment_scam/unknown",
    "scammer_tactic": "urgency/fear/greed/impersonation/authority",
    "strategy": "contextual_engagement/reverse_extraction/stalling/panic_mode/baiting/probing",
    "intelligence": {{
        "bank_accounts": [],
        "upi_ids": [],
        "phishing_links": [],
        "phone_numbers": [],
        "suspicious_keywords": []
    }},
    "is_complete": true/false,
    "agent_notes": "Brief analysis of what scammer wants and your strategy",
    "response": "Your contextual reply (2-3 sentences, address what they asked, try to extract their details)"
}}

Now analyze the scammer's message and respond contextually:"""
    
    messages.append({"role": "user", "content": structured_prompt})
    
    # Get response
    raw_response = call_with_fallback(messages, temperature=0.85) # Increased temp for variety
    
    # Parse JSON from response
    try:
        # Clean the response first
        cleaned_json = clean_json_string(raw_response)
        return json.loads(cleaned_json)
            
    except json.JSONDecodeError as e:
        logger.warning(f"Failed to parse JSON: {e}. Raw: {raw_response[:100]}...")
    except Exception as e:
        logger.error(f"Error during JSON processing: {e}")
    
    # Fallback: just use the response as-is or randomized fallback logic
    # If the raw response looks like a normal sentence (no JSON structure), use it directly
    if "{" not in raw_response and len(raw_response) < 200 and not raw_response.startswith("Error"):
         # The LLM ignored instructions and just spoke - that's fine for the 'response'
         return {
            "scam_detected": True,
            "scam_type": "unknown",
            "scammer_tactic": "unknown",
            "strategy": "conversation_flow",
            "intelligence": {},
            "is_complete": False,
            "agent_notes": "LLM output non-JSON text",
            "response": raw_response
        }

    is_error = raw_response.startswith("Error:")
    
    # Use contextual fallback instead of random
    contextual_response = get_contextual_fallback(
        current_message, 
        session_id, 
        conversation_history
    )
    
    return {
        "scam_detected": True,
        "scam_type": "unknown",
        "scammer_tactic": "unknown",
        "strategy": "contextual_stalling" if not is_error else "technical_confusion",
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "suspicious_keywords": []
        },
        "is_complete": False,
        "agent_notes": f"LLM Failure: {raw_response[:50]}..." if is_error else "Response parsing failed - using contextual fallback",
        "response": contextual_response
    }
