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
OPENROUTER_MODEL = os.getenv("OPENROUTER_MODEL", "meta-llama/llama-3.1-405b-instruct:free")
OPENROUTER_FALLBACK = os.getenv("OPENROUTER_FALLBACK_MODEL", "arcee-ai/trinity-large-preview:free")
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
            return data['choices'][0]['message']['content']
        else:
            logger.error(f"OpenRouter error: {response.status_code} - {response.text}")
            return None
            
    except requests.exceptions.Timeout:
        logger.error("OpenRouter request timed out")
        return None
    except Exception as e:
        logger.error(f"OpenRouter exception: {str(e)}")
        return None


def call_with_fallback(
    messages: List[Dict[str, str]],
    temperature: float = 0.8
) -> str:
    """
    Call primary model, fallback to secondary if failed.
    
    Args:
        messages: List of message dicts
        temperature: Creativity level
    
    Returns:
        Response text or fallback message
    """
    # Try primary model
    response = call_openrouter(messages, model=OPENROUTER_MODEL, temperature=temperature)
    
    if response:
        return response
    
    # Try fallback model
    logger.warning("Primary model failed, trying fallback...")
    response = call_openrouter(messages, model=OPENROUTER_FALLBACK, temperature=temperature)
    
    if response:
        return response
    
    # Emergency fallback response
    logger.error("Both models failed, using emergency fallback")
    return "Acha ji, network is very slow. Please wait, I am trying..."


def generate_agent_response(
    system_prompt: str,
    conversation_history: List[Dict[str, str]],
    current_message: str,
    extraction_prompt: str
) -> Dict[str, Any]:
    """
    Generate agent response with structured thinking.
    
    Args:
        system_prompt: Persona-locked system prompt
        conversation_history: Previous messages
        current_message: Current scammer message
        extraction_prompt: Instructions for intelligence extraction
    
    Returns:
        Parsed response dict with thinking and reply
    """
    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history:
        role = "user" if msg.get("sender") == "scammer" else "assistant"
        messages.append({"role": role, "content": msg.get("text", "")})
    
    # Add current message
    messages.append({"role": "user", "content": current_message})
    
    # Add extraction instructions
    structured_prompt = f"""
{extraction_prompt}

RESPONSE FORMAT (respond in this exact JSON format):
{{
    "scam_detected": true/false,
    "scam_type": "bank_fraud/upi_fraud/digital_arrest/lottery_scam/unknown",
    "scammer_tactic": "urgency/fear/greed/impersonation",
    "strategy": "feigning_ignorance/technical_confusion/stalling/baiting/panic_mode/reverse_extraction",
    "intelligence": {{
        "bank_accounts": [],
        "upi_ids": [],
        "phishing_links": [],
        "phone_numbers": [],
        "suspicious_keywords": []
    }},
    "is_complete": true/false,
    "agent_notes": "Brief analysis of scammer behavior",
    "response": "Your reply to the scammer (2-3 sentences, Indian English, confused elderly person style)"
}}

Now analyze the scammer's message and respond:"""
    
    messages.append({"role": "user", "content": structured_prompt})
    
    # Get response
    raw_response = call_with_fallback(messages, temperature=0.8)
    
    # Parse JSON from response
    try:
        # Try to extract JSON from response
        json_start = raw_response.find('{')
        json_end = raw_response.rfind('}') + 1
        
        if json_start != -1 and json_end > json_start:
            json_str = raw_response[json_start:json_end]
            return json.loads(json_str)
    except json.JSONDecodeError:
        logger.warning("Failed to parse JSON, using raw response")
    
    # Fallback: just use the response as-is
    return {
        "scam_detected": True,
        "scam_type": "unknown",
        "scammer_tactic": "unknown",
        "strategy": "feigning_ignorance",
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "suspicious_keywords": []
        },
        "is_complete": False,
        "agent_notes": "Response parsing failed",
        "response": raw_response if len(raw_response) < 200 else "Haan ji? I am not understanding. Please explain slowly."
    }
