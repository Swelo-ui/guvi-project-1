"""
Conversation Analyzer Module - Advanced Version
Provides human-like, varied responses for the honeypot.

Key Features:
- Component-based response building (stalls + tangents + occasional extraction)
- Smart tracking to avoid asking for same info repeatedly
- Response pattern variation (not always [stall + ask])
- Phrase-level duplicate prevention
"""

import re
import random
import hashlib
from typing import Dict, List, Any, Optional, Tuple, Set
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
    INITIAL_CONTACT = "initial"
    BUILDING_TRUST = "trust"
    CREATING_URGENCY = "urgency"
    EXTRACTION_ATTEMPT = "extraction"
    PERSISTENCE = "persistence"
    FINAL_PUSH = "final"


class ResponseType(Enum):
    """Types of responses for varied conversation flow."""
    PURE_STALL = "pure_stall"          # Just delay, no info asking
    FAMILY_TANGENT = "family_tangent"   # Talk about family
    TECHNICAL_ISSUE = "technical_issue" # Phone/app problems
    EMOTIONAL = "emotional"             # Fear, confusion, health
    TOPIC_CONFUSION = "topic_confusion" # Don't understand what they want
    REVERSE_EXTRACT = "reverse_extract" # Ask for their info (use sparingly!)


# Intent detection patterns (unchanged)
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


# ============= COMPONENT-BASED RESPONSES =============

# Pure stall components (no asking for info)
STALL_RESPONSES = {
    ScammerIntent.OTP: [
        "OTP? Let me check my phone...",
        "Wait, message came. Let me read slowly...",
        "Phone was on silent, checking now...",
        "Acha, 6 numbers came. My eyes are weak...",
        "Something came! Wait wait...",
        "Battery is low, screen dim. One minute...",
        "Message opened. Reading it slowly...",
        "Yes yes, I see something. Hold on...",
        "The SMS came. But so many messages here...",
        "Okay, let me find the right message...",
    ],
    ScammerIntent.ACCOUNT_NUMBER: [
        "Account number... let me find passbook...",
        "Which account? I have two banks...",
        "Passbook is in almirah. Wait...",
        "Account? Okay, my son handles this usually...",
        "Let me see... where did I keep it...",
    ],
    ScammerIntent.UPI_ID: [
        "UPI? What is UPI exactly?",
        "My grandson made some app for me...",
        "PhonePe is showing error...",
        "UPI ID... I think it's my phone number?",
        "App is asking for some PIN...",
    ],
    ScammerIntent.FEAR_TACTIC: [
        "Oh god! Please don't arrest me!",
        "My heart is beating fast... wait...",
        "I am very scared! What have I done?",
        "Police?! But I am innocent person!",
        "Please please, I am old person. Don't do this.",
    ],
    ScammerIntent.MONEY_TRANSFER: [
        "Money? But I am retired, not much savings...",
        "Transaction is showing error...",
        "I tried but it's not working...",
        "How much you need? I only have little...",
        "My son handles all money matters...",
    ],
    ScammerIntent.UNKNOWN: [
        "Sorry, I didn't understand properly...",
        "Can you say again? Network was breaking...",
        "What should I do exactly?",
        "I am confused. Say slowly please.",
        "Acha acha, but what you need from me?",
    ]
}

# Family/life tangents (humanizing, no info asking)
FAMILY_TANGENTS = [
    "Actually my grandson was just here. He went to tuition only.",
    "You know, my son always tells me be careful on phone.",
    "These days so many calls come. Yesterday also someone called about lottery.",
    "My daughter in law handles all bank work. She is teacher.",
    "Let me tell you, I am 68 years old. Not good with technology.",
    "Actually I was about to take my BP medicine. Almost forgot.",
    "My neighbour aunty Sharmila also got similar call last week.",
    "You know, in my time we used to go to bank only. No phone phone.",
    "My husband, god bless his soul, he used to handle all this.",
    "I have been customer of this bank for 35 years actually.",
    "My grandson Arjun is very smart with computers. He is 12 only.",
    "Actually doctor said I should not take tension. Heart problem.",
]

# Technical issue tangents
TECHNICAL_TANGENTS = [
    "This phone is so slow. My old Nokia was better.",
    "Internet is very bad in my area. Jio network problem.",
    "Screen is cracked, can't see properly.",
    "App keeps closing. What to do?",
    "Phone heating up. Is this normal?",
    "Battery showing 5% only. Charger is in other room.",
    "Font is too small. Where is setting?",
    "Hello? Hello? I think network is breaking.",
    "Arre, phone screen went black suddenly.",
    "This touch screen doesn't work properly. My finger too dry.",
]

# Confusion responses (topic confusion)
CONFUSION_RESPONSES = [
    "Wait, which bank you said? I have SBI and HDFC both.",
    "Sorry, I'm confused. What exactly happened to my account?",
    "You said blocked? But I withdrew money yesterday only.",
    "I don't understand all this. Can you call my son?",
    "Beta, speak in Hindi please. English not good.",
    "What fraud? I haven't done any transaction today.",
    "Are you from bank or police? I'm confused now.",
    "This OTP thing... my grandson explained but I forgot.",
    "Sir, which department you are calling from exactly?",
    "I thought this was about my pension. Wrong call?",
]

# Emotional responses (fear, health, overwhelm)
EMOTIONAL_RESPONSES = [
    "I am getting very tensed. Please wait...",
    "My hands are shaking now. Give me one minute.",
    "This is too much for me. I am old person.",
    "I feel dizzy. Let me sit down first.",
    "Please don't shout. My hearing is weak.",
    "I am alone at home. Very scared now.",
    "You are making me very nervous beta.",
    "Let me drink water. Throat is dry from tension.",
    "I have sugar also. This stress is not good.",
    "Oh god, what will happen to my money?",
]

# Reverse extraction prompts (categories to track)
REVERSE_EXTRACT_BY_CATEGORY = {
    "employee_id": [
        "But what is YOUR employee ID? I should note down.",
        "Tell me your ID number. For my safety.",
        "What is your staff ID? I will verify with bank.",
    ],
    "designation": [
        "What is your designation? I need to note properly.",
        "Which post are you? Manager or officer?",
        "Tell me your designation, beta."
    ],
    "upi_id": [
        "Give me YOUR UPI ID. My son will verify.",
        "What is your official UPI? I'll cross check.",
        "Sir, share your UPI, I need to confirm.",
    ],
    "ifsc": [
        "What is your bank IFSC code? I will check.",
        "IFSC code bata dijiye, beta.",
        "Please share your IFSC. I will verify."
    ],
    "phone_number": [
        "What is your direct number? I'll call you back.",
        "Give me official helpline. I will verify.",
        "Share your phone number, I want to save.",
    ],
    "email": [
        "What is your official bank email?",
        "Please send your bank email ID.",
        "Your official email? I will verify with my son."
    ],
    "branch": [
        "Which branch are you calling from?",
        "Branch ka naam bata dijiye.",
        "What is your branch? I will note down."
    ],
    "account_number": [
        "First give me YOUR account for verification.",
        "What is your official bank account?",
        "Share your account details for my records.",
    ],
    "name": [
        "What is your full name? I'm writing down.",
        "Tell me your name again. I forgot.",
        "What should I call you? I need your name.",
    ],
    "document": [
        "Can you send official document on WhatsApp?",
        "Send me proof from your bank email.",
        "Share your ID proof. Then I trust you.",
    ],
    "aadhaar": [
        "Aapka Aadhaar number bata dijiye, verification ke liye.",
        "For my records, your Aadhaar ID please?",
        "Beta, apna Aadhaar number do na. Main note karungi.",
        "I need your Aadhaar for verification. What is it?",
    ],
    "pan": [
        "Aapka PAN card number kya hai? Main note kar rahi hoon.",
        "PAN card number dijiye beta, I need for tax purposes.",
        "Share your PAN number. My son says always ask PAN.",
        "What is your PAN? I will verify with income tax.",
    ],
}


# ============= SESSION TRACKING =============
# Track per session what we've used AND what scammer has revealed
_session_data: Dict[str, Dict] = {}

def get_session_data(session_id: str) -> Dict:
    """Get or create session tracking data with conversation memory."""
    if session_id not in _session_data:
        _session_data[session_id] = {
            # Response tracking
            "used_stalls": [],           # Exact stall responses used
            "used_tangents": [],         # Tangent phrases used
            "used_extractions": [],      # Extraction phrases used
            "asked_categories": [],      # Categories of info we've asked for
            "last_response_type": None,  # To avoid same type twice
            "response_count": 0,         # Total responses in session
            "phrase_hashes": set(),      # Hash of first few words to detect similar starts
            
            # CONVERSATION MEMORY - what scammer has revealed
            "scammer_memory": {
                "claimed_name": None,        # "My name is Rajesh"
                "claimed_employee_id": None, # "My ID is SBI12345"
                "claimed_bank": None,        # "I am from SBI"
                "claimed_upi": None,         # "My UPI is xyz@bank"
                "claimed_phone": None,       # "Call me at 98765..."
                "claimed_account": None,     # "My account is 1234..."
                "claimed_designation": None, # "I am manager"
                "claimed_branch": None,
                "claimed_email": None,
                "claimed_ifsc": None,
                "threat_type": None,         # "digital arrest", "account blocked"
                "urgency_level": 0,          # How urgent they're being (0-3)
                "times_asked_otp": 0,        # How many times they asked for OTP
                "times_asked_account": 0,    # How many times they asked for account
                "links_shared": [],          # Any URLs they shared
                "apps_mentioned": [],        # Apps they want us to install
            },
            
            # Strategic context
            "scam_type_detected": None,  # bank_fraud, digital_arrest, etc.
            "previous_scam_type": None,  # For style-switch detection
            "style_switch_count": 0,     # How many times scammer changed tactics
            "scammer_getting_frustrated": False,  # Are they pushing harder?
        }
    return _session_data[session_id]


def extract_scammer_intel(message: str, session: Dict) -> None:
    """
    Extract and remember what the scammer reveals in their message.
    Updates the session's scammer_memory in place.
    """
    memory = session["scammer_memory"]
    message_lower = message.lower()
    
    # Extract claimed name
    name_patterns = [
        r'my name is ([a-zA-Z ]{3,})',
        r'i am ([a-zA-Z ]{3,}) from',
        r'this is ([a-zA-Z ]{3,}) calling',
        r'([a-zA-Z ]{3,}) speaking',
        r'mera poora naam ([a-zA-Z ]{3,}) hai',
        r'mera naam ([a-zA-Z ]{3,}) hai',
        r'poora naam ([a-zA-Z ]{3,}) hai',
        r'my full name is ([a-zA-Z ]{3,})',
    ]
    for pattern in name_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            raw_name = re.sub(r'\s+', ' ', match.group(1)).strip()
            memory["claimed_name"] = raw_name.title()
            break
    
    # Extract employee ID
    id_patterns = [
        r'employee id[:\s]+(\w+)',
        r'staff id[:\s]+(\w+)',
        r'id[:\s]+([A-Z0-9]+)',
        r'my id is (\w+)',
    ]
    for pattern in id_patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            memory["claimed_employee_id"] = match.group(1)
            break
    
    # Extract bank name
    bank_patterns = [
        r'from (sbi|hdfc|icici|axis|pnb|bob|kotak|yes bank|rbi)',
        r'(sbi|hdfc|icici|axis|pnb|bob|kotak) (bank|headquarters|office)',
    ]
    for pattern in bank_patterns:
        match = re.search(pattern, message_lower)
        if match:
            memory["claimed_bank"] = match.group(1).upper()
            break
    
    # Extract UPI ID and Email — disambiguate by checking for email TLD domains
    at_match = re.search(r'([a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+)', message)
    if at_match:
        match_val = at_match.group(1)
        domain_part = match_val.split('@')[1].lower() if '@' in match_val else ''
        email_tlds = ('.com', '.in', '.net', '.org', '.co', '.edu', '.gov', '.io')
        is_email = any(domain_part.endswith(tld) for tld in email_tlds)
        
        if is_email or re.search(r'\bemail\b', message_lower):
            # It's an email address
            memory["claimed_email"] = match_val
        else:
            # It's a UPI ID (no email-like TLD)
            memory["claimed_upi"] = match_val
    
    # Extract phone number
    phone_match = re.search(r'\+?91[\s-]?(\d{10})', message)
    if phone_match:
        memory["claimed_phone"] = phone_match.group(0)
    elif re.search(r'(\d{10})', message):
        phone_match = re.search(r'(\d{10})', message)
        memory["claimed_phone"] = phone_match.group(1)
    
    # Extract account number (long number)
    account_match = re.search(r'(\d{12,16})', message)
    if account_match:
        memory["claimed_account"] = account_match.group(1)

    ifsc_match = re.search(r'\b[A-Z]{4}0[A-Z0-9]{6}\b', message.upper())
    if ifsc_match:
        memory["claimed_ifsc"] = ifsc_match.group(0)

    branch_match = re.search(r'\b([a-zA-Z ]+)\s+branch\b', message, re.IGNORECASE)
    if branch_match:
        memory["claimed_branch"] = branch_match.group(1).strip().title()

    designation_match = re.search(r'\b(manager|officer|agent|executive|fraud prevention|customer care|support)\b', message_lower)
    if designation_match:
        memory["claimed_designation"] = designation_match.group(1).title()
    
    # Detect threat type with style-switch detection
    new_scam_type = None
    if re.search(r'digital arrest|cyber crime|cbi|police|warrant', message_lower):
        memory["threat_type"] = "digital_arrest"
        new_scam_type = "digital_arrest"
    elif re.search(r'blocked|suspended|frozen|compromised', message_lower):
        memory["threat_type"] = "account_blocked"
        new_scam_type = "bank_fraud"
    elif re.search(r'lottery|won|prize|reward', message_lower):
        new_scam_type = "lottery_scam"
    elif re.search(r'aadhaar|aadhar|uid|pan card|pan number|biometric', message_lower):
        new_scam_type = "aadhaar_scam"
    elif re.search(r'sim swap|sim card|deactivate|reactivate', message_lower):
        new_scam_type = "sim_swap_scam"
    elif re.search(r'courier|parcel|customs|fedex|dhl', message_lower):
        new_scam_type = "courier_scam"
    elif re.search(r'invest|trading|crypto|bitcoin|profit', message_lower):
        new_scam_type = "investment_scam"
    elif re.search(r'loan|emi|pre.?approved|interest rate', message_lower):
        new_scam_type = "loan_scam"
    elif re.search(r'refund|claim|cashback', message_lower):
        new_scam_type = "refund_scam"
    elif re.search(r'kyc|update.*account|verify.*identity', message_lower):
        new_scam_type = "kyc_fraud"
    
    # Style-switch detection: if scammer changes tactics mid-conversation
    if new_scam_type:
        old_scam_type = session.get("scam_type_detected")
        if old_scam_type and old_scam_type != new_scam_type:
            session["previous_scam_type"] = old_scam_type
            session["style_switch_count"] = session.get("style_switch_count", 0) + 1
        session["scam_type_detected"] = new_scam_type
    
    # Track urgency escalation
    if re.search(r'immediately|urgent|now|quickly|hurry', message_lower):
        memory["urgency_level"] = min(memory["urgency_level"] + 1, 3)
    
    # Track OTP requests
    if re.search(r'\botp\b', message_lower):
        memory["times_asked_otp"] += 1
    
    # Track account requests  
    if re.search(r'account\s*(number|detail|no)', message_lower):
        memory["times_asked_account"] += 1
    
    # Check if scammer is getting frustrated
    if memory["times_asked_otp"] >= 3 or memory["urgency_level"] >= 2:
        session["scammer_getting_frustrated"] = True
    
    # Extract any links
    links = re.findall(r'https?://\S+', message)
    if links:
        memory["links_shared"].extend(links)
    
    # Extract mentioned apps
    app_match = re.search(r'(anydesk|teamviewer|quickshare|zoom|remote)', message_lower)
    if app_match:
        memory["apps_mentioned"].append(app_match.group(1))

def get_phrase_hash(text: str) -> str:
    """Get hash of first 8 words to detect similar phrases (increased from 5)."""
    words = text.lower().split()[:8]
    return hashlib.md5(" ".join(words).encode()).hexdigest()[:8]

def is_similar_used(session: Dict, response: str) -> bool:
    """Check if this exact response or similar phrase has been used."""
    # Check EXACT match first
    if response in session.get("used_exact_responses", []):
        return True
    
    # Then check phrase hash (for similar starts)
    phrase_hash = get_phrase_hash(response)
    return phrase_hash in session["phrase_hashes"]

def mark_response_used(session: Dict, response: str, response_type: ResponseType):
    """Mark a response as used in session (both exact and phrase hash)."""
    # Track exact response
    if "used_exact_responses" not in session:
        session["used_exact_responses"] = []
    session["used_exact_responses"].append(response)
    
    # Track phrase hash
    session["phrase_hashes"].add(get_phrase_hash(response))
    session["last_response_type"] = response_type
    session["response_count"] += 1
    
    if response_type == ResponseType.PURE_STALL:
        session["used_stalls"].append(response)
    elif response_type in (ResponseType.FAMILY_TANGENT, ResponseType.EMOTIONAL):
        session["used_tangents"].append(response)


# ============= RESPONSE BUILDING =============

def detect_intents(message: str) -> List[ScammerIntent]:
    """Detect all intents present in the scammer's message."""
    message_lower = message.lower()
    detected = []
    
    for intent, patterns in INTENT_PATTERNS.items():
        for pattern in patterns:
            if re.search(pattern, message_lower, re.IGNORECASE):
                detected.append(intent)
                break
    
    if not detected:
        detected.append(ScammerIntent.UNKNOWN)
    
    return detected


def detect_conversation_phase(
    conversation_history: List[Dict[str, str]],
    current_intents: List[ScammerIntent]
) -> ConversationPhase:
    """Determine the current phase of the conversation."""
    msg_count = len(conversation_history)
    
    if msg_count <= 2:
        return ConversationPhase.INITIAL_CONTACT
    
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
    
    if ScammerIntent.FEAR_TACTIC in current_intents:
        return ConversationPhase.CREATING_URGENCY
    
    if ScammerIntent.URGENCY in current_intents:
        return ConversationPhase.PERSISTENCE
    
    return ConversationPhase.BUILDING_TRUST


def choose_response_type(session: Dict, phase: ConversationPhase) -> ResponseType:
    """Choose what TYPE of response to give (varied, not always same)."""
    response_count = session["response_count"]
    last_type = session["last_response_type"]
    
    # First response: pure stall or greeting
    if response_count == 0:
        return ResponseType.PURE_STALL
    
    # Don't repeat same type twice in a row
    available_types = list(ResponseType)
    if last_type:
        available_types = [t for t in available_types if t != last_type]
    
    # Weighted selection based on phase
    if phase in (ConversationPhase.INITIAL_CONTACT, ConversationPhase.BUILDING_TRUST):
        # Early: more stalls and tangents, less extraction
        weights = {
            ResponseType.PURE_STALL: 35,
            ResponseType.FAMILY_TANGENT: 25,
            ResponseType.TECHNICAL_ISSUE: 20,
            ResponseType.TOPIC_CONFUSION: 15,
            ResponseType.EMOTIONAL: 5,
            ResponseType.REVERSE_EXTRACT: 0,  # Don't extract early
        }
    elif phase == ConversationPhase.CREATING_URGENCY:
        # Fear tactics: more emotional, some confusion
        weights = {
            ResponseType.PURE_STALL: 15,
            ResponseType.FAMILY_TANGENT: 10,
            ResponseType.TECHNICAL_ISSUE: 15,
            ResponseType.TOPIC_CONFUSION: 15,
            ResponseType.EMOTIONAL: 35,
            ResponseType.REVERSE_EXTRACT: 10,
        }
    elif phase in (ConversationPhase.EXTRACTION_ATTEMPT, ConversationPhase.PERSISTENCE):
        # Active extraction: mix of stalling and occasional reverse extract
        weights = {
            ResponseType.PURE_STALL: 30,
            ResponseType.FAMILY_TANGENT: 15,
            ResponseType.TECHNICAL_ISSUE: 20,
            ResponseType.TOPIC_CONFUSION: 10,
            ResponseType.EMOTIONAL: 10,
            ResponseType.REVERSE_EXTRACT: 15,
        }
    else:  # FINAL_PUSH
        # Late: more reverse extraction attempts
        weights = {
            ResponseType.PURE_STALL: 25,
            ResponseType.FAMILY_TANGENT: 10,
            ResponseType.TECHNICAL_ISSUE: 15,
            ResponseType.TOPIC_CONFUSION: 15,
            ResponseType.EMOTIONAL: 15,
            ResponseType.REVERSE_EXTRACT: 20,
        }
    
    # Filter by available types and normalize weights
    choices = []
    probs = []
    for t in available_types:
        if t in weights:
            choices.append(t)
            probs.append(weights[t])
    
    total = sum(probs)
    probs = [p / total for p in probs]
    
    return random.choices(choices, probs)[0]


def get_available_extraction_category(session: Dict, phase: ConversationPhase) -> Optional[str]:
    asked = session["asked_categories"]
    recent = asked[-3:] if len(asked) >= 3 else asked
    memory = session["scammer_memory"]

    category_to_memory = {
        "name": "claimed_name",
        "employee_id": "claimed_employee_id",
        "designation": "claimed_designation",
        "phone_number": "claimed_phone",
        "upi_id": "claimed_upi",
        "ifsc": "claimed_ifsc",
        "email": "claimed_email",
        "branch": "claimed_branch",
        "account_number": "claimed_account",
        "document": "claimed_employee_id"
    }

    if phase in (ConversationPhase.INITIAL_CONTACT, ConversationPhase.BUILDING_TRUST):
        priority = ["name", "employee_id", "designation", "document"]
    elif phase in (ConversationPhase.CREATING_URGENCY, ConversationPhase.EXTRACTION_ATTEMPT):
        priority = ["phone_number", "email", "branch", "employee_id", "name"]
    else:
        priority = ["upi_id", "ifsc", "account_number", "phone_number", "email", "branch", "employee_id"]

    for category in priority:
        memory_key = category_to_memory.get(category)
        if memory_key and not memory.get(memory_key) and category not in recent:
            return category

    for category, memory_key in category_to_memory.items():
        if not memory.get(memory_key) and category not in recent:
            return category

    categories = list(REVERSE_EXTRACT_BY_CATEGORY.keys())
    available = [c for c in categories if c not in recent]
    if not available:
        available = categories
    chosen = random.choice(available)
    session["used_extractions"].append(chosen)
    return chosen


def build_response(
    session: Dict,
    primary_intent: ScammerIntent,
    response_type: ResponseType,
    phase: ConversationPhase
) -> str:
    """Build a response based on type and intent."""
    
    # Get stall pool for this intent
    stall_pool = STALL_RESPONSES.get(primary_intent, STALL_RESPONSES[ScammerIntent.UNKNOWN])
    
    # Filter out used stalls
    available_stalls = [s for s in stall_pool if not is_similar_used(session, s)]
    if not available_stalls:
        available_stalls = stall_pool
    
    base_stall = random.choice(available_stalls)
    
    if response_type == ResponseType.PURE_STALL:
        return base_stall
    
    elif response_type == ResponseType.FAMILY_TANGENT:
        available = [t for t in FAMILY_TANGENTS if not is_similar_used(session, t)]
        tangent = random.choice(available) if available else random.choice(FAMILY_TANGENTS)
        return tangent
    
    elif response_type == ResponseType.TECHNICAL_ISSUE:
        available = [t for t in TECHNICAL_TANGENTS if not is_similar_used(session, t)]
        tangent = random.choice(available) if available else random.choice(TECHNICAL_TANGENTS)
        return tangent
    
    elif response_type == ResponseType.EMOTIONAL:
        available = [e for e in EMOTIONAL_RESPONSES if not is_similar_used(session, e)]
        emotional = random.choice(available) if available else random.choice(EMOTIONAL_RESPONSES)
        return emotional
    
    elif response_type == ResponseType.TOPIC_CONFUSION:
        available = [c for c in CONFUSION_RESPONSES if not is_similar_used(session, c)]
        confusion = random.choice(available) if available else random.choice(CONFUSION_RESPONSES)
        return confusion
    
    elif response_type == ResponseType.REVERSE_EXTRACT:
        # Get a category we haven't asked about recently
        category = get_available_extraction_category(session, phase)
        session["asked_categories"].append(category)
        
        prompts = REVERSE_EXTRACT_BY_CATEGORY[category]
        available = [
            p for p in prompts
            if p not in session["used_extractions"] and not is_similar_used(session, p)
        ]
        extraction = random.choice(available) if available else random.choice(prompts)
        session["used_extractions"].append(extraction)
        
        # Combine stall + extraction
        return f"{base_stall} {extraction}"
    
    return base_stall  # Fallback


def get_contextual_response(
    intents: List[ScammerIntent],
    phase: ConversationPhase,
    used_responses: List[str],
    session_id: str = "default"
) -> Tuple[str, bool]:
    """
    Get a contextually appropriate, human-like response.
    
    Returns:
        Tuple of (response_text, should_attempt_reverse_extraction)
    """
    session = get_session_data(session_id)
    primary_intent = intents[0] if intents else ScammerIntent.UNKNOWN
    
    # Choose response type (varied)
    response_type = choose_response_type(session, phase)
    
    # Build the response
    response = build_response(session, primary_intent, response_type, phase)
    
    # Safety check: deduplicate
    attempts = 0
    while is_similar_used(session, response) and attempts < 5:
        response_type = choose_response_type(session, phase)
        response = build_response(session, primary_intent, response_type, phase)
        attempts += 1
    
    appended_extraction = False
    if response_type != ResponseType.REVERSE_EXTRACT and phase in (
        ConversationPhase.EXTRACTION_ATTEMPT,
        ConversationPhase.PERSISTENCE,
        ConversationPhase.FINAL_PUSH
    ):
        if random.random() > 0.6:
            prompt = get_reverse_extraction_prompt([], session_id=session_id, phase=phase)
            if prompt and not is_similar_used(session, prompt):
                response = f"{response} {prompt}"
                appended_extraction = True
    
    track_type = ResponseType.REVERSE_EXTRACT if appended_extraction else response_type
    mark_response_used(session, response, track_type)
    
    should_extract = (response_type == ResponseType.REVERSE_EXTRACT) or appended_extraction
    return response, should_extract


def get_reverse_extraction_prompt(
    used_prompts: List[str],
    session_id: str = "default",
    phase: ConversationPhase = ConversationPhase.EXTRACTION_ATTEMPT
) -> Optional[str]:
    session = get_session_data(session_id)
    category = get_available_extraction_category(session, phase)
    session["asked_categories"].append(category)
    
    prompts = REVERSE_EXTRACT_BY_CATEGORY[category]
    available = [
        p for p in prompts
        if p not in used_prompts and p not in session["used_extractions"] and not is_similar_used(session, p)
    ]
    
    if not available:
        available = prompts
    
    return random.choice(available)


def analyze_conversation(
    current_message: str,
    conversation_history: List[Dict[str, str]],
    used_responses: List[str],
    session_id: str = "default"
) -> Dict[str, Any]:
    """
    Complete conversation analysis for smart response generation.
    Analyzes the ENTIRE conversation history to strategically respond.
    
    Returns:
        Analysis dict with intents, phase, suggested response, scammer memory, etc.
    """
    session = get_session_data(session_id)
    
    # STEP 1: Reset mutable counters before full re-scan to prevent inflation.
    # Without this, re-processing history on every call would keep incrementing
    # times_asked_otp / times_asked_account and duplicating links_shared / apps_mentioned.
    memory = session["scammer_memory"]
    memory["times_asked_otp"] = 0
    memory["times_asked_account"] = 0
    memory["urgency_level"] = 0
    memory["links_shared"] = []
    memory["apps_mentioned"] = []
    session["scammer_getting_frustrated"] = False
    
    # Now re-scan ALL scammer messages (build full memory from scratch)
    for msg in conversation_history:
        if msg.get("sender") == "scammer":
            extract_scammer_intel(msg.get("text", ""), session)
    
    # Extract from current message too
    extract_scammer_intel(current_message, session)
    
    # STEP 2: Detect intents and phase
    intents = detect_intents(current_message)
    phase = detect_conversation_phase(conversation_history, intents)
    
    # STEP 3: Generate base response
    response, should_extract = get_contextual_response(intents, phase, used_responses, session_id)
    
    # STEP 4: PERSONALIZE response using scammer memory
    response = personalize_response(response, session)
    
    # STEP 5: Build analysis
    memory = session["scammer_memory"]
    analysis = {
        "detected_intents": [i.value for i in intents],
        "primary_intent": intents[0].value,
        "conversation_phase": phase.value,
        "suggested_fallback": response,
        "should_reverse_extract": should_extract,
        "message_count": len(conversation_history) + 1,
        
        # Memory context for debugging/logging
        "scammer_memory": {
            "name": memory["claimed_name"],
            "bank": memory["claimed_bank"],
            "employee_id": memory["claimed_employee_id"],
            "phone": memory["claimed_phone"],
            "upi_id": memory["claimed_upi"],
            "account_number": memory["claimed_account"],
            "designation": memory["claimed_designation"],
            "branch": memory["claimed_branch"],
            "email": memory["claimed_email"],
            "ifsc": memory["claimed_ifsc"],
            "times_asked_otp": memory["times_asked_otp"],
            "urgency_level": memory["urgency_level"],
        },
        "scam_type": session.get("scam_type_detected"),
        "scammer_frustrated": session.get("scammer_getting_frustrated", False),
    }
    
    if should_extract:
        analysis["reverse_extraction_prompt"] = None  # Already included in response
    
    return analysis


def personalize_response(response: str, session: Dict) -> str:
    """
    Personalize a response using what we know about the scammer.
    Makes the honeypot seem like it remembers the conversation.
    """
    memory = session["scammer_memory"]
    
    # Sometimes add personalized reference (30% chance)
    if random.random() > 0.7:
        personalizations = []
        
        # Reference their claimed name
        if memory["claimed_name"]:
            personalizations.append(f"Haan {memory['claimed_name']} ji, ")
            personalizations.append(f"Acha {memory['claimed_name']} beta, ")
        
        # Reference their claimed bank
        if memory["claimed_bank"]:
            personalizations.append(f"This is {memory['claimed_bank']} na? ")
            personalizations.append(f"Aap {memory['claimed_bank']} se ho na? ")
        
        # Reference their employee ID
        if memory["claimed_employee_id"]:
            personalizations.append(f"Your ID was {memory['claimed_employee_id']} only right? ")
        
        # Reference if they've asked for OTP before
        if memory["times_asked_otp"] >= 2:
            personalizations.append("You keep asking for OTP only... ")
            personalizations.append("Arre you already asked for OTP before also... ")
        
        # Reference their UPI if they mentioned
        if memory["claimed_upi"]:
            personalizations.append(f"I noted your UPI {memory['claimed_upi']}... ")
        
        if personalizations:
            prefix = random.choice(personalizations)
            response = prefix + response
    
    # Strategic notes based on frustration
    if session.get("scammer_getting_frustrated") and random.random() > 0.8:
        suffix_options = [
            " Why you are getting angry?",
            " Don't shout at me please.",
            " I am trying only, be patient.",
            " You are talking very fast...",
        ]
        response = response + random.choice(suffix_options)
    
    return response


def get_conversation_intel(session_id: str) -> Dict[str, Any]:
    """
    Get all extracted intelligence about the scammer for this session.
    Useful for debugging and final report.
    """
    session = get_session_data(session_id)
    return {
        "scammer_memory": session["scammer_memory"],
        "scam_type": session.get("scam_type_detected"),
        "scammer_frustrated": session.get("scammer_getting_frustrated", False),
        "response_count": session.get("response_count", 0),
        "asked_categories": session.get("asked_categories", []),
    }


# Legacy export for compatibility
CONTEXTUAL_RESPONSES = STALL_RESPONSES
REVERSE_EXTRACTION_PROMPTS = []
for cat_prompts in REVERSE_EXTRACT_BY_CATEGORY.values():
    REVERSE_EXTRACTION_PROMPTS.extend(cat_prompts)

