"""
Conversation Analyzer Module
Provides context-aware analysis for intelligent honeypot responses.

Features:
- Scammer intent detection (what they're asking for)
- Conversation phase tracking
- Contextual response selection
- Anti-repetition system
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from enum import Enum


class ScammerIntent(Enum):
    """What the scammer is currently asking for."""
    OTP = "otp"
    ACCOUNT_NUMBER = "account_number"
    UPI_ID = "upi_id"
    MONEY_TRANSFER = "money_transfer"
    CLICK_LINK = "click_link"
    INSTALL_APP = "install_app"
    PERSONAL_INFO = "personal_info"
    CARD_DETAILS = "card_details"
    FEAR_TACTIC = "fear_tactic"
    URGENCY = "urgency"
    GREETING = "greeting"
    UNKNOWN = "unknown"


class ConversationPhase(Enum):
    """Current phase of the scam conversation."""
    INITIAL_CONTACT = "initial"      # Scammer making first contact
    BUILDING_TRUST = "trust"         # Scammer establishing credibility
    CREATING_URGENCY = "urgency"     # Scammer creating panic
    EXTRACTION_ATTEMPT = "extraction" # Scammer actively asking for info
    PERSISTENCE = "persistence"       # Scammer pushing harder
    FINAL_PUSH = "final"             # Scammer getting desperate


# Intent detection patterns
INTENT_PATTERNS = {
    ScammerIntent.OTP: [
        r'\botp\b', r'\bone.?time.?password\b', r'\bverification.?code\b',
        r'\bcode.?sent\b', r'\bsms.?code\b', r'\b\d{4,6}\b.*share', r'share.*\b\d{4,6}\b'
    ],
    ScammerIntent.ACCOUNT_NUMBER: [
        r'\baccount\s*(number|no\.?|#)?\b', r'\bbank\s*account\b', 
        r'\baccount\s*details\b', r'\bsavings\s*account\b'
    ],
    ScammerIntent.UPI_ID: [
        r'\bupi\b', r'\b\w+@\w+\b', r'\bpay\s*tm\b', r'\bgoogle\s*pay\b',
        r'\bphone\s*pe\b', r'\bbhim\b'
    ],
    ScammerIntent.MONEY_TRANSFER: [
        r'\btransfer\b', r'\bsend\s*(money|amount|rs|₹)\b', r'\bpay\s*(rs|₹|amount)\b',
        r'\bdeposit\b', r'\bprocessing\s*fee\b'
    ],
    ScammerIntent.CLICK_LINK: [
        r'\bclick\b', r'\blink\b', r'\burl\b', r'https?://', r'\bbit\.ly\b',
        r'\btinyurl\b', r'\bopen\b.*\bwebsite\b'
    ],
    ScammerIntent.INSTALL_APP: [
        r'\binstall\b', r'\bdownload\b', r'\bapp\b', r'\banydesk\b',
        r'\bteamviewer\b', r'\bquickshare\b', r'\bapk\b'
    ],
    ScammerIntent.PERSONAL_INFO: [
        r'\baadhaar\b', r'\bpan\b', r'\baddress\b', r'\bdate\s*of\s*birth\b',
        r'\bdob\b', r'\bfather.?s?\s*name\b', r'\bmother.?s?\s*name\b'
    ],
    ScammerIntent.CARD_DETAILS: [
        r'\bcard\s*(number|no\.?)?\b', r'\bcvv\b', r'\bexpiry\b', 
        r'\bdebit\s*card\b', r'\bcredit\s*card\b', r'\batm\s*pin\b'
    ],
    ScammerIntent.FEAR_TACTIC: [
        r'\barrested?\b', r'\bblocked?\b', r'\bsuspended?\b', r'\bpolice\b',
        r'\bcbi\b', r'\bcourt\b', r'\bjail\b', r'\bwarrant\b', r'\billegal\b',
        r'\bfraud\b', r'\bfir\b'
    ],
    ScammerIntent.URGENCY: [
        r'\burgent\b', r'\bimmediately\b', r'\bnow\b', r'\btoday\b',
        r'\b\d+\s*(hour|minute|min)\b', r'\bexpire\b', r'\blast\s*chance\b'
    ],
    ScammerIntent.GREETING: [
        r'^(hello|hi|namaste|dear|sir|madam|customer)\b'
    ]
}

# Contextual response pools based on scammer intent
CONTEXTUAL_RESPONSES = {
    ScammerIntent.OTP: [
        "OTP? Let me check my phone... one minute beta.",
        "It came! Wait... it says 6 numbers, which one to give?",
        "The message came but it's saying 'Do not share'. Should I still tell?",
        "Acha, OTP... my eyes are weak. Let me get glasses.",
        "Beta, it's showing some number. But my son said never share OTP?",
        "Wait wait, phone was on silent. Let me check now.",
        "OTP... yes I got something. But first tell me your employee ID for verification?",
    ],
    ScammerIntent.ACCOUNT_NUMBER: [
        "Account number? I have two accounts... which bank you need?",
        "Let me find my passbook. Where did I keep it...",
        "Account number is there in passbook. But beta, what is YOUR account? For my records?",
        "Wait, I am confused. You give me YOUR account number first, then I verify.",
        "Savings or current? I have both. Also, what is your branch sir?",
        "Acha acha, let me see... my son handles all this. He is coming in 10 minutes.",
        "Account number... okay wait. But sir, what is YOUR official bank account? I should cross-check.",
    ],
    ScammerIntent.UPI_ID: [
        "UPI? What is UPI? I use bank only.",
        "My grandson made some GPay. But I don't remember the password.",
        "UPI ID... it was something like my phone number? Let me check.",
        "Beta, I don't know UPI. Can you give YOUR UPI? I'll ask my son to send.",
        "PhonePe is not working. It shows error. What is YOUR UPI, I'll try from son's phone?",
        "App is asking for PIN. I forgot it. What should I do?",
        "Wait, first give me your UPI so I can verify you are from bank only.",
    ],
    ScammerIntent.MONEY_TRANSFER: [
        "Send money? But beta, I am poor retired person. How much you need?",
        "Transaction is failing. It says 'Insufficient balance'. What to do?",
        "I tried but it's showing error. Give me YOUR account, I'll send through NEFT tomorrow.",
        "Rs.5000? I don't have so much. Only Rs.500 in account.",
        "Wait, let me call my son. He handles all money matters.",
        "Money I can send, but first I need your manager's number for verification.",
        "Transfer? Okay, but tell me YOUR account number. I'll send through bank directly.",
    ],
    ScammerIntent.CLICK_LINK: [
        "Link is not opening. Internet is slow in my area.",
        "It's showing 'Page not found'. Is the link correct?",
        "Beta, I clicked but phone is hanging now. What to do?",
        "This link... my son said not to click random links. Is this safe?",
        "Okay let me try... wait, it's asking for password. Which password?",
        "Link opened but it looks different from my bank website.",
        "Website is not loading. Network problem. Try calling me instead?",
    ],
    ScammerIntent.INSTALL_APP: [
        "Install? My phone storage is full. I don't know how to delete apps.",
        "What is the app name? My grandson will do it tomorrow.",
        "It's saying 'Unknown source'. Phone is not allowing.",
        "Beta, this AnyDesk you are telling... my son said it's dangerous?",
        "App installed but it's asking for some number. What number to give?",
        "Phone is very slow after installing. Something is wrong.",
        "Wait, I need to ask my daughter. She told me not to install anything.",
    ],
    ScammerIntent.FEAR_TACTIC: [
        "Oh god! I am very scared! Please don't arrest me, I am old person!",
        "Police?! What have I done wrong? Please help me sir!",
        "I am having chest pain. Please don't threaten me. I am senior citizen.",
        "Blocked? But I need money for medicines! Please help!",
        "I will do anything, please don't arrest! But first send me official document on WhatsApp.",
        "Oh no! My heart is pounding. Let me drink water first...",
        "Please please, I am innocent! Tell me what document you need. Send me official letter first.",
    ],
    ScammerIntent.URGENCY: [
        "I am trying I am trying! But app is not working!",
        "Don't hurry me beta, I am old. Hands are shaking.",
        "Within 30 minutes? But I need to go to bank. It's far from my house.",
        "Please give me more time. I have to find my documents.",
        "I am doing as fast as I can! Phone is slow.",
        "Wait, doorbell is ringing. Someone is at door. 5 minutes please.",
        "I understand it's urgent. But first confirm your employee ID?",
    ],
    ScammerIntent.PERSONAL_INFO: [
        "Aadhaar? Let me search. Where did I keep the card...",
        "PAN number I don't remember. Let me ask neighbour aunty.",
        "Date of birth? I was born in village. Don't know exact date.",
        "Father's name? Why you need? First tell me YOUR identification.",
        "All documents are in almirah. My son has the key.",
        "Address... same as Aadhaar. But beta, what is YOUR address? For verification?",
        "I will give all details, but first send me official email from your bank ID.",
    ],
    ScammerIntent.CARD_DETAILS: [
        "ATM card? I don't use ATM. Only passbook.",
        "CVV? What is CVV? Where is it written?",
        "Card number is very long. Let me get the card from locker.",
        "Expiry date... the card looks old. Is it still working?",
        "PIN? My son set the PIN. I don't remember.",
        "Wait, you work in bank, you should have my card details already?",
        "Card is there but I don't want to share. Too risky. Give me YOUR card for verification.",
    ],
    ScammerIntent.GREETING: [
        "Haan ji? Who is calling? I can't hear properly.",
        "Hello? Hello? Is this bank?",
        "Namaste beta. Who is this? My phone didn't show name.",
        "Yes yes, I am listening. But speak loudly please.",
        "Hello, I was about to call bank only! Good timing.",
    ],
    ScammerIntent.UNKNOWN: [
        "Sorry beta, I didn't understand. Can you repeat slowly?",
        "What did you say? Network is breaking up.",
        "Acha acha, but what should I do exactly?",
        "I am confused. My son handles all technical things.",
        "Can you explain in simple words? I am not educated much.",
        "Haan ji, I am listening. But speak in Hindi please.",
    ]
}

# Reverse extraction prompts - to get scammer's details
REVERSE_EXTRACTION_PROMPTS = [
    "But beta, first give ME your official account. I need to verify you are genuine.",
    "What is YOUR employee ID? I will note down for complaint if something goes wrong.",
    "Sir, give me your UPI ID. I'll ask my son to verify you first.",
    "Can you share your official bank email? I want to confirm.",
    "Tell me your helpline number. I will call the bank to verify you.",
    "What is YOUR manager's name? I need to file it in my records.",
    "Can you send me official document with your details? On WhatsApp only.",
    "Before I share anything, give me your official ID proof.",
]


def detect_intents(message: str) -> List[ScammerIntent]:
    """
    Detect all intents present in the scammer's message.
    
    Args:
        message: Scammer's message text
        
    Returns:
        List of detected intents, ordered by priority
    """
    message_lower = message.lower()
    detected = []
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                detected.append(intent)
                break  # One match per intent is enough
    
    # If no intent detected, return unknown
    if not detected:
        detected.append(ScammerIntent.UNKNOWN)
    
    return detected


def detect_conversation_phase(
    conversation_history: List[Dict[str, str]],
    current_intents: List[ScammerIntent]
) -> ConversationPhase:
    """
    Determine the current phase of the conversation.
    
    Args:
        conversation_history: List of previous messages
        current_intents: Detected intents in current message
        
    Returns:
        Current conversation phase
    """
    msg_count = len(conversation_history)
    
    # Initial contact
    if msg_count <= 2:
        return ConversationPhase.INITIAL_CONTACT
    
    # Check for extraction attempts
    extraction_intents = {
        ScammerIntent.OTP, ScammerIntent.ACCOUNT_NUMBER,
        ScammerIntent.UPI_ID, ScammerIntent.CARD_DETAILS,
        ScammerIntent.MONEY_TRANSFER
    }
    
    if any(intent in extraction_intents for intent in current_intents):
        if msg_count > 10:
            return ConversationPhase.FINAL_PUSH
        elif msg_count > 6:
            return ConversationPhase.PERSISTENCE
        else:
            return ConversationPhase.EXTRACTION_ATTEMPT
    
    # Fear/urgency based phases
    if ScammerIntent.FEAR_TACTIC in current_intents:
        return ConversationPhase.CREATING_URGENCY
    
    if ScammerIntent.URGENCY in current_intents:
        return ConversationPhase.PERSISTENCE
    
    return ConversationPhase.BUILDING_TRUST


def get_contextual_response(
    intents: List[ScammerIntent],
    phase: ConversationPhase,
    used_responses: List[str]
) -> Tuple[str, bool]:
    """
    Get a contextually appropriate response based on intent and phase.
    
    Args:
        intents: Detected intents in scammer's message
        phase: Current conversation phase
        used_responses: List of previously used responses in this session
        
    Returns:
        Tuple of (response_text, should_attempt_reverse_extraction)
    """
    import random
    
    primary_intent = intents[0] if intents else ScammerIntent.UNKNOWN
    
    # Get candidate responses for primary intent
    candidates = CONTEXTUAL_RESPONSES.get(primary_intent, CONTEXTUAL_RESPONSES[ScammerIntent.UNKNOWN])
    
    # Filter out already used responses
    available = [r for r in candidates if r not in used_responses]
    
    # If all used, reset but still try to avoid immediate repeats
    if not available:
        available = candidates
    
    response = random.choice(available)
    
    # Determine if we should try reverse extraction
    # More likely in extraction/persistence phases
    should_extract = phase in {
        ConversationPhase.EXTRACTION_ATTEMPT,
        ConversationPhase.PERSISTENCE,
        ConversationPhase.FINAL_PUSH
    }
    
    return response, should_extract


def get_reverse_extraction_prompt(used_prompts: List[str]) -> Optional[str]:
    """
    Get a reverse extraction prompt to try to get scammer's details.
    
    Args:
        used_prompts: Previously used extraction prompts
        
    Returns:
        Extraction prompt or None
    """
    import random
    
    available = [p for p in REVERSE_EXTRACTION_PROMPTS if p not in used_prompts]
    if not available:
        available = REVERSE_EXTRACTION_PROMPTS
    
    return random.choice(available)


def analyze_conversation(
    current_message: str,
    conversation_history: List[Dict[str, str]],
    used_responses: List[str]
) -> Dict[str, Any]:
    """
    Complete conversation analysis for smart response generation.
    
    Args:
        current_message: Current scammer message
        conversation_history: Previous messages
        used_responses: Previously used honeypot responses
        
    Returns:
        Analysis dict with intents, phase, suggested response, etc.
    """
    intents = detect_intents(current_message)
    phase = detect_conversation_phase(conversation_history, intents)
    response, should_extract = get_contextual_response(intents, phase, used_responses)
    
    analysis = {
        "detected_intents": [i.value for i in intents],
        "primary_intent": intents[0].value,
        "conversation_phase": phase.value,
        "suggested_fallback": response,
        "should_reverse_extract": should_extract,
        "message_count": len(conversation_history) + 1
    }
    
    if should_extract:
        analysis["reverse_extraction_prompt"] = get_reverse_extraction_prompt(used_responses)
    
    return analysis
