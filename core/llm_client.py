"""
OpenRouter LLM Client
Handles API calls to multiple LLM models with parallel execution and smart response selection
"""

import os
import json
import logging
import requests
import time
from typing import List, Dict, Any, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Configuration - Multiple models for parallel execution
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "openai/gpt-oss-120b")
OPENROUTER_MODEL_2 = os.getenv("OPENROUTER_MODEL_2")
OPENROUTER_FALLBACK = os.getenv("OPENROUTER_FALLBACK_MODEL", "google/gemini-2.5-flash-lite")
OPENROUTER_JSON_RETRY = os.getenv("OPENROUTER_JSON_RETRY", "true").lower() == "true"
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1/chat/completions"

MODEL_PRIORITY = {
    "openai/gpt-oss-120b": 120,
    "google/gemini-2.5-flash-lite": 95
}
ALLOWED_MODELS = set(MODEL_PRIORITY.keys())
if OPENROUTER_MODEL not in ALLOWED_MODELS:
    OPENROUTER_MODEL = "openai/gpt-oss-120b"
if OPENROUTER_FALLBACK not in ALLOWED_MODELS:
    OPENROUTER_FALLBACK = "google/gemini-2.5-flash-lite"
OPENROUTER_REPAIR_MODEL = os.getenv("OPENROUTER_REPAIR_MODEL", OPENROUTER_MODEL)


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
            timeout=12
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
# These are stalling messages that work in any context
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
    "Wait, doorbell rang. Let me check who is there.",
    "App is showing loading only. Internet problem.",
    "Phone is heating up. Let me restart it.",
    "My neighbour aunty is calling me. One minute.",
    "I hear beeping sound. Is that from your side?",
    "Wait wait, I dropped my spectacles somewhere.",
]

# Session response tracking to prevent repetition - GLOBAL across all fallbacks
_session_responses: Dict[str, List[str]] = {}
_session_generic_index: Dict[str, int] = {}  # Track index for sequential generic selection

def get_used_responses(session_id: str) -> List[str]:
    """Get list of previously used responses for a session."""
    return _session_responses.get(session_id, [])

def track_response(session_id: str, response: str):
    """Track a response as used for this session."""
    if session_id not in _session_responses:
        _session_responses[session_id] = []
    
    # Only add if not already tracked (avoid duplicates in tracking)
    if response not in _session_responses[session_id]:
        _session_responses[session_id].append(response)
    
    # Keep only last 30 to prevent memory issues
    if len(_session_responses[session_id]) > 30:
        _session_responses[session_id] = _session_responses[session_id][-30:]

def get_random_fallback(session_id: str = "default") -> str:
    """
    Get a fallback message that hasn't been used in this session.
    Uses sequential selection to avoid repetition.
    """
    used = get_used_responses(session_id)
    
    # Filter out already used messages
    available = [msg for msg in GENERIC_FALLBACK_MESSAGES if msg not in used]
    
    if not available:
        # All used, reset but pick least recently used
        # Get the index for this session
        if session_id not in _session_generic_index:
            _session_generic_index[session_id] = 0
        
        idx = _session_generic_index[session_id] % len(GENERIC_FALLBACK_MESSAGES)
        _session_generic_index[session_id] = idx + 1
        response = GENERIC_FALLBACK_MESSAGES[idx]
    else:
        # Pick randomly from available
        response = random.choice(available)
    
    # Track this response
    track_response(session_id, response)
    return response

def get_contextual_fallback(
    scammer_message: str, 
    session_id: str = "default",
    conversation_history: List[Dict[str, str]] = None
) -> str:
    """
    Get a context-aware, human-like fallback based on what the scammer is asking.
    Uses component-based response building with varied response types.
    
    Args:
        scammer_message: The scammer's current message
        session_id: Session ID for tracking used responses
        conversation_history: Previous messages in conversation
        
    Returns:
        Contextually appropriate, varied response
    """
    if conversation_history is None:
        conversation_history = []
    
    used_responses = get_used_responses(session_id)
    
    try:
        # Analyze the conversation for context - pass session_id for smart tracking
        analysis = analyze_conversation(
            scammer_message, 
            conversation_history, 
            used_responses,
            session_id  # Pass session_id for deduplication
        )
        
        # Get the contextual response (already includes extraction if appropriate)
        response = analysis.get("suggested_fallback", "")
        
        # Track this response in our local tracker too
        track_response(session_id, response)
        
        return response
        
    except Exception as e:
        logger.warning(f"Context analysis failed: {e}, using generic fallback")
        return get_random_fallback(session_id)

def calculate_response_quality(response: str, model: str) -> int:
    """
    Calculate quality score for a response.
    Higher score = better response.
    
    Scoring:
    - Valid JSON format: +50
    - Contains 'response' field: +30
    - Response length > 50 chars: +10
    - Model priority bonus: +N (from MODEL_PRIORITY)
    - No error indicators: +10
    """
    if not response or response.startswith("Error"):
        return 0
    
    score = 0
    
    # Check for valid JSON
    try:
        cleaned = clean_json_string(response) if "{" in response else response
        parsed = json.loads(cleaned)
        score += 50
        
        # Check for response field
        if parsed.get("response") and len(parsed.get("response", "")) > 10:
            score += 30
    except (json.JSONDecodeError, Exception):
        # Not JSON, but might still be usable text
        if len(response) > 50 and not response.startswith("Error"):
            score += 15
    
    # Response length bonus
    if len(response) > 50:
        score += 10
    
    # Model priority bonus
    score += MODEL_PRIORITY.get(model, 50)
    
    # No error indicators
    if "error" not in response.lower()[:50]:
        score += 10
    
    return score


def call_models_parallel(
    messages: List[Dict[str, str]],
    temperature: float = 0.8,
    max_tokens: int = 500,
    timeout_seconds: int = 12
) -> Tuple[Optional[str], str]:
    """
    Call multiple models in parallel and return the best response.
    
    Args:
        messages: List of message dicts
        temperature: Creativity level
        max_tokens: Max tokens per response  
        timeout_seconds: Max time to wait for all models
        
    Returns:
        Tuple of (best_response, model_used) or (None, "none") if all failed
    """
    # Models to try in parallel
    models = [OPENROUTER_MODEL, OPENROUTER_MODEL_2, OPENROUTER_FALLBACK]
    # Filter out duplicates while preserving order
    models = list(dict.fromkeys(m for m in models if m))
    allowed_models = set(MODEL_PRIORITY.keys())
    models = [m for m in models if m in allowed_models]
    if not models and OPENROUTER_FALLBACK in allowed_models:
        models = [OPENROUTER_FALLBACK]
    
    if not models:
        logger.error("No models configured")
        return None, "none"
    
    logger.info(f"🚀 Calling {len(models)} models in parallel: {[m.split('/')[-1] for m in models]}")
    
    results: Dict[str, str] = {}
    
    executor = ThreadPoolExecutor(max_workers=len(models))
    future_to_model = {
        executor.submit(
            call_openrouter,
            messages,
            model,
            temperature,
            max_tokens
        ): model
        for model in models
    }
    start = time.monotonic()
    try:
        for future in as_completed(future_to_model, timeout=timeout_seconds):
            model = future_to_model[future]
            try:
                result = future.result()
                if result and not result.startswith("Error"):
                    results[model] = result
                    logger.info(f"✅ {model.split('/')[-1]} responded ({len(result)} chars)")
                    elapsed = time.monotonic() - start
                    if model == OPENROUTER_MODEL or elapsed >= 4:
                        break
                else:
                    logger.warning(f"⚠️ {model.split('/')[-1]} returned error: {result[:50] if result else 'None'}...")
            except Exception as e:
                logger.warning(f"❌ {model.split('/')[-1]} exception: {str(e)[:50]}")
    except TimeoutError:
        logger.warning(f"⏱️ Parallel call timed out after {timeout_seconds}s")
    finally:
        for future in future_to_model:
            future.cancel()
        executor.shutdown(wait=False)
    
    if not results:
        logger.error("All models failed in parallel execution")
        return None, "none"
    
    # Score and select best response
    scored = []
    for model, response in results.items():
        score = calculate_response_quality(response, model)
        scored.append((score, model, response))
        logger.debug(f"Model {model.split('/')[-1]} scored {score}")
    
    # Sort by score descending
    scored.sort(reverse=True)
    best_score, best_model, best_response = scored[0]
    
    logger.info(f"🏆 Selected {best_model.split('/')[-1]} (score: {best_score}) from {len(results)} responses")
    
    return best_response, best_model


def call_with_fallback(
    messages: List[Dict[str, str]],
    temperature: float = 0.8
) -> str:
    """
    Call models in parallel and return the best response.
    Falls back to emergency response if all models fail.
    """
    # Try parallel execution
    response, model_used = call_models_parallel(messages, temperature=temperature)
    
    if response:
        return response
    
    # Emergency fallback response - all models failed
    logger.error("All parallel models failed, using emergency fallback")
    return random.choice(GENERIC_FALLBACK_MESSAGES)


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


def parse_response_json(raw_response: str) -> Optional[Dict[str, Any]]:
    if not raw_response:
        return None
    try:
        cleaned_json = clean_json_string(raw_response)
        return json.loads(cleaned_json)
    except Exception:
        return None


def repair_json_response(raw_response: str, schema_block: str) -> Optional[Dict[str, Any]]:
    repair_messages = [
        {"role": "system", "content": "You return only valid JSON and nothing else."},
        {"role": "user", "content": f"Return valid JSON matching this schema:\n{schema_block}\n\nRaw output:\n{raw_response}"}
    ]
    repaired = call_openrouter(repair_messages, model=OPENROUTER_REPAIR_MODEL, temperature=0.0, max_tokens=700)
    return parse_response_json(repaired)


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
    
    schema_block = """{
    "scam_detected": true/false,
    "scam_type": "bank_fraud/upi_fraud/digital_arrest/lottery_scam/kyc_fraud/investment_scam/unknown",
    "scammer_tactic": "urgency/fear/greed/impersonation/authority",
    "strategy": "contextual_engagement/reverse_extraction/stalling/panic_mode/baiting/probing",
    "intelligence": {
        "bank_accounts": [],
        "upi_ids": [],
        "phishing_links": [],
        "phone_numbers": [],
        "suspicious_keywords": []
    },
    "is_complete": true/false,
    "agent_notes": "Brief analysis of what scammer wants and your strategy",
    "response": "Your contextual reply (2-4 sentences, address what they asked, ask for their details when it fits)"
}"""

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

2. **REVERSE EXTRACTION:** Try to get scammer's details gradually:
   - "But sir, what is YOUR account? I need to verify you first."
   - "Give me YOUR UPI, I'll confirm with my son before sharing."
   - "What is your employee ID? I'm noting down for safety."
   - Do not ask for details in every message

3. **CONSISTENCY:** Never contradict facts from earlier (name, bank, family).

4. **VARIETY:** Never repeat an exact response. Check conversation history.

5. **NATURAL STALLING:** Use believable delays relevant to the context.

RESPONSE FORMAT (respond in this exact JSON format):
{schema_block}

Now analyze the scammer's message and respond contextually:"""
    
    messages.append({"role": "user", "content": structured_prompt})
    
    # Get response
    raw_response = call_with_fallback(messages, temperature=0.85) # Increased temp for variety
    
    parsed = parse_response_json(raw_response)
    if parsed:
        return parsed

    if OPENROUTER_JSON_RETRY:
        repaired = repair_json_response(raw_response, schema_block)
        if repaired:
            return repaired
    
    # Fallback: use contextual response when LLM doesn't return proper JSON
    # Even if LLM returns plain text, use our controlled contextual responses for consistency
    
    # Check if LLM output looks like a reasonable response (not JSON attempt, not error)
    llm_gave_text = "{" not in raw_response and len(raw_response) < 200 and not raw_response.startswith("Error")
    
    # Always use our contextual fallback for anti-repetition and context awareness
    contextual_response = get_contextual_fallback(
        current_message, 
        session_id, 
        conversation_history
    )
    
    if llm_gave_text:
        # LLM spoke naturally but in wrong format - log for debugging
        logger.info(f"LLM non-JSON response: {raw_response[:80]}...")
        # Still use our contextual fallback for consistency
        return {
            "scam_detected": True,
            "scam_type": "unknown",
            "scammer_tactic": "unknown",
            "strategy": "contextual_engagement",
            "intelligence": {},
            "is_complete": False,
            "agent_notes": "LLM output non-JSON text - using contextual fallback",
            "response": contextual_response  # Use contextual instead of raw LLM text
        }

    is_error = raw_response.startswith("Error:")
    
    # contextual_response already obtained above, reuse it
    
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
