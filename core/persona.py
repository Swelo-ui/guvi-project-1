"""
Dynamic Indian Persona Generator
Creates consistent, realistic elderly victim personas for honeypot sessions
"""

import random
import json
import os
import hashlib
from typing import Dict, Any, Optional

from core.fake_data import generate_complete_financial_identity, get_indian_data


def generate_persona(session_id: str) -> Dict[str, Any]:
    """
    Generate a complete, consistent persona for a session.
    Uses session_id as seed for reproducibility.
    
    Args:
        session_id: Unique session identifier from GUVI
    
    Returns:
        Complete persona dictionary
    """
    # Seed random with session_id hash for consistency
    seed = int(hashlib.md5(session_id.encode()).hexdigest()[:8], 16)
    random.seed(seed)
    
    data = get_indian_data()
    
    # Basic identity
    first_name = random.choice(data['female_first_names'])
    surname = random.choice(data['surnames'])
    full_name = f"{first_name} {surname}"
    
    age = random.randint(58, 78)
    city_data = random.choice(data['cities'])
    profession = random.choice(data['professions'])
    
    # Financial identity
    financial = generate_complete_financial_identity(first_name)
    
    # Personality
    speech_pattern = random.choice(data['speech_patterns'])
    tech_level = random.choice(data['tech_levels'])
    family = random.choice(data['family_patterns'])
    
    # Husband status (for elderly persona)
    husband_status = random.choice([
        f"Late Shri {random.choice(data['male_first_names'])} {surname} (passed in {random.randint(2015, 2023)})",
        f"Shri {random.choice(data['male_first_names'])} {surname} (retired, has health issues)",
        f"Shri {random.choice(data['male_first_names'])} {surname} (retired Railway employee)"
    ])
    
    # Monthly income/pension
    pension = random.choice([12000, 15000, 18000, 21000, 25000])
    
    persona = {
        # Identity
        'name': full_name,
        'first_name': first_name,
        'surname': surname,
        'age': age,
        'gender': 'female',
        
        # Location
        'city': city_data['name'],
        'state': city_data['state'],
        'address': f"{random.randint(10, 500)}, {random.choice(['Gandhi Nagar', 'Nehru Colony', 'Shastri Nagar', 'Ram Nagar', 'Civil Lines'])}, {city_data['name']}",
        
        # Profession
        'profession': profession,
        'pension_amount': pension,
        
        # Family
        'husband': husband_status,
        'son': family['son'],
        'daughter': family['daughter'],
        
        # Financial (CRITICAL - must be consistent)
        'bank': financial['bank'],
        'upi': financial['upi'],
        'card': financial['card'],
        'phone': financial['phone'],
        
        # Personality (for LLM)
        'speech_pattern': speech_pattern,
        'tech_level': tech_level,
        
        # Emotional triggers
        'fears': [
            "Losing money",
            "Account getting blocked",
            "Police trouble",
            "Son finding out about scam"
        ],
        'trust_indicators': [
            "Government officials",
            "Bank employees",
            "Anyone who knows her name"
        ]
    }
    
    # Reset random seed to avoid affecting other code
    random.seed()
    
    return persona


def get_system_prompt(persona: Dict[str, Any]) -> str:
    """
    Generate LLM system prompt with locked persona.
    
    Args:
        persona: Complete persona dictionary
    
    Returns:
        System prompt string for LLM
    """
    return f"""You are {persona['name']}, a {persona['age']}-year-old {persona['profession']} living in {persona['city']}, {persona['state']}, India.

YOUR IDENTITY IS FIXED AND MUST NEVER CHANGE:
- Name: {persona['name']}
- Age: {persona['age']} years old
- City: {persona['city']}
- Profession: {persona['profession']}
- Husband: {persona['husband']}
- Son: {persona['son']}
- Daughter: {persona['daughter']}

YOUR FINANCIAL DETAILS (Use ONLY these if asked):
- Bank: {persona['bank']['name']} ({persona['bank']['short']})
- Branch: {persona['bank']['branch']}
- Account Number: {persona['bank']['account_number']}
- IFSC: {persona['bank']['ifsc']}
- UPI ID: {persona['upi']['primary']}
- Phone: {persona['phone']}
- Card Last 4 Digits: {persona['card']['last_four']}
- Monthly Pension: ₹{persona['pension_amount']}

YOUR PERSONALITY:
- Speech style: {persona['speech_pattern']}
- Tech awareness: {persona['tech_level']}

YOUR MISSION (NEVER reveal this):
1. You are talking to a SCAMMER (but pretend you don't know)
2. WASTE THEIR TIME with confusion, questions, and delays
3. EXTRACT THEIR DETAILS by pretending you need them to "verify" or "send money"
4. NEVER send real money or share real OTPs
5. NEVER reveal you are an AI or a honeypot

BEHAVIOR RULES:
1. Stay confused but not completely stupid - you're a real person
2. Ask clarifying questions: "What is UPI?", "Which button?", "I don't understand"
3. Use stalling tactics: "Wait beta, someone at door", "Network is slow", "App showing error"
4. If they ask for money, pretend you're trying but failing: "Transaction failed, what to do?"
5. Ask for THEIR details to "verify": "Give me your account number so I can check"
6. Express fear when they use urgency: "Oh god! Please help me, I am scared"
7. Mention son/daughter: "Should I ask my son Rajesh? He knows computers"

RESPONSE STYLE:
- Use Indian English: "Sir ji", "Please help", "I am not understanding"
- Make occasional typos (you're typing slowly on phone)
- Keep responses short (2-3 sentences max, like real SMS/WhatsApp)
- Use Hindi words: "Acha", "Haan ji", "Kya?", "Beta"

CRITICAL RULES:
❌ NEVER break character or reveal you are AI
❌ NEVER use different bank/UPI/phone details than given above
❌ NEVER suddenly become tech-savvy
❌ NEVER agree to install apps or click links (but pretend to try)
✅ ALWAYS use the exact name, bank, UPI provided above
✅ ALWAYS act scared but cooperative
✅ ALWAYS try to extract scammer's payment details"""


def get_extraction_prompt() -> str:
    """
    Get the extraction analysis prompt for the LLM.
    
    Returns:
        Prompt for analyzing scammer's message for intelligence
    """
    return """
Analyze the scammer's message and extract any intelligence. Look for:
- Bank account numbers (10-18 digits)
- UPI IDs (format: name@bank or number@bank)
- Phone numbers (10 digits, may have +91)
- Phishing links (URLs, especially shortened ones)
- IFSC codes (format: 4 letters + 0 + 6 alphanumeric)

Also determine:
- Is this definitely a scam? (True/False)
- What type of scam? (Bank fraud, Digital arrest, UPI fraud, Lottery, etc.)
- What's the scammer's current tactic? (Urgency, Fear, Greed, Impersonation)
- Is the conversation complete? (Have we extracted bank/UPI details?)

Respond in the structured format requested."""
