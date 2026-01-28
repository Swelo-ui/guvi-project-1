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

# Fallback messages to use when LLM fails or is stalling
FALLBACK_MESSAGES = [
    "Acha ji, network is very slow. Please wait, I am trying...",
    "Hello? Can you hear me? My phone is breaking up.",
    "Wait beta, my glasses are not here. Let me find them.",
    "Babu, this app is showing 'Loading'... what to do?",
    "One minute, someone is at the door. I will just check.",
    "My son is calling on other line... wait one second.",
    "Screen is stuck. Should I restart the phone?",
    "I am not understanding. Explain slowly beta.",
    "Why is it asking for password? I am confused.",
    "Wait, my hands are shaking, hard to type.",
    "Beta, can I call you? This typing is difficult.",
    "The screen went black. Is it working?",
    "I forgot my reading glasses, let me ask my neighbour.",
    "Battery is 2%, let me find charger.",
    "Is this the bank? Why is the logo different?",
    "Something went wrong, it says 'Service Unavailable'.",
    "Wait, I am looking for my passbook.",
    "My grandson is crying, one moment please.",
    "Sorry beta, I pressed the wrong button I think.",
    "Can you send a photo? I can't read this text.",
    "It is asking for some PIN, I don't remember."
]

def get_random_fallback():
    """Get a random fallback message to avoid repetition."""
    return random.choice(FALLBACK_MESSAGES)

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
    extraction_prompt: str
) -> Dict[str, Any]:
    """
    Generate agent response with structured thinking.
    """
    # Build messages array
    messages = [{"role": "system", "content": system_prompt}]
    
    # Add conversation history
    for msg in conversation_history:
        role = "user" if msg.get("sender") == "scammer" else "assistant"
        content = msg.get("text", "")
        # Add context from previous turns to help consistency
        messages.append({"role": role, "content": content})
    
    # Add current message
    messages.append({"role": "user", "content": current_message})
    
    # Add extraction instructions AND Consistency Reminder
    structured_prompt = f"""
{extraction_prompt}

IMPORTANT GUIDELINES:
1. CONSISTENCY IS CRITICAL: You must NEVER contradict facts you stated earlier in the conversation (name, age, family, bank).
2. MEMORY: Check the conversation history above. If you said your son is Rajesh, he remains Rajesh.
3. REALISM: Do not be repetitive. If you already said "Network error", use a different excuse like "Doorbell" or "Glasses".
4. TONE: Stay fearful and confused.
5. FORMAT: **Output VALID JSON without any trailing commas.**

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
    
    return {
        "scam_detected": True,
        "scam_type": "unknown",
        "scammer_tactic": "unknown",
        "strategy": "technical_confusion" if is_error else "feigning_ignorance",
        "intelligence": {
            "bank_accounts": [],
            "upi_ids": [],
            "phishing_links": [],
            "phone_numbers": [],
            "suspicious_keywords": []
        },
        "is_complete": False,
        "agent_notes": f"LLM Failure: {raw_response[:50]}..." if is_error else "Response parsing failed",
        "response": get_random_fallback() # Use fallback if totally failed
    }
