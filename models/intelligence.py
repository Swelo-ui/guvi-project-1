"""
Intelligence Extraction Patterns
Regex-based extraction of bank accounts, UPI IDs, phone numbers, etc.
"""

import re
from typing import Dict, List, Any


# Regex patterns for intelligence extraction
PATTERNS = {
    "upi": r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+',
    "bank_account": r'\b\d{10,18}\b',
    "ifsc": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
    "phone": r'(?<!\d)(?:\+91[\s-]?)?[6-9]\d{9}(?!\d)',
    "url": r'https?://[^\s<>"{}|\\^`\[\]]+|bit\.ly/[^\s]+|tinyurl\.com/[^\s]+',
    "whatsapp": r'wa\.me/\d+',
}

# Suspicious keywords indicating scam
SCAM_KEYWORDS = [
    # Urgency
    "urgent", "immediately", "now", "today only", "expires", "last chance", "limited time",
    # Fear
    "blocked", "suspended", "arrested", "police", "cbi", "fraud", "illegal", "warrant", "cyber crime",
    # Action
    "verify", "confirm", "update", "kyc", "otp", "pin", "password", "verification code", "screen share",
    # Money
    "transfer", "pay", "send money", "refund", "chargeback", "cashback", "prize", "lottery", "won", "fine", "penalty",
    # Authority
    "bank manager", "customer care", "support", "helpline", "toll free", "rbi", "government", "income tax", "gst",
    # Technical
    "link", "click", "download", "install", "app", "apk", "remote access", "anydesk", "teamviewer", "quick support",
    # Channels
    "whatsapp", "telegram", "sms", "email",
    # Identity
    "aadhaar", "pan", "kyc update", "video kyc",
    # Payment tactics
    "qr", "scan", "upi collect", "payment request", "request money",
    # Delivery scams
    "courier", "parcel", "customs", "delivery charge",
    # Investment scams
    "crypto", "bitcoin", "investment", "trading", "profit", "loan", "emi"
]


UPI_HANDLES = {
    "ybl", "oksbi", "okicici", "okhdfcbank", "okaxis", "paytm", "axl", "ibl",
    "upi", "sbi", "icici", "hdfcbank", "axis", "pnb", "kotak", "yesbank",
    "barodampay", "idfcbank"
}


def normalize_upi_ids(items: List[str]) -> List[str]:
    normalized = []
    for item in items:
        if not item:
            continue
        candidate = re.sub(r'[^\w@.-]', '', item.strip().lower())
        if candidate.count("@") != 1:
            continue
        user, handle = candidate.split("@", 1)
        if len(user) < 2:
            continue
        handle = handle.strip(".")
        if handle not in UPI_HANDLES:
            continue
        normalized.append(f"{user}@{handle}")
    return list(set(normalized))


def extract_upi_ids(text: str) -> List[str]:
    matches = re.findall(PATTERNS["upi"], text, re.IGNORECASE)
    return normalize_upi_ids(matches)


def extract_bank_accounts(text: str) -> List[str]:
    """Extract potential bank account numbers."""
    matches = re.findall(PATTERNS["bank_account"], text)
    # Filter: must be 10-18 digits, not look like phone number
    valid = []
    for m in matches:
        # Skip if it looks like a phone number (10 digits starting with 6-9)
        if len(m) == 10 and m[0] in '6789':
            continue
        valid.append(m)
    return list(set(valid))


def extract_ifsc_codes(text: str) -> List[str]:
    """Extract IFSC codes."""
    return list(set(re.findall(PATTERNS["ifsc"], text.upper())))


def normalize_phone_numbers(items: List[str]) -> List[str]:
    normalized = []
    for item in items:
        if not item:
            continue
        clean = re.sub(r'[^\d+]', '', str(item))
        if clean.startswith('+91'):
            clean = clean[3:]
        if len(clean) == 10 and clean[0] in '6789':
            normalized.append(f"+91{clean}")
    return list(set(normalized))


def extract_phone_numbers(text: str) -> List[str]:
    matches = re.findall(PATTERNS["phone"], text)
    return normalize_phone_numbers(matches)


def extract_urls(text: str) -> List[str]:
    """Extract URLs (potential phishing links)."""
    urls = re.findall(PATTERNS["url"], text)
    whatsapp = re.findall(PATTERNS["whatsapp"], text)
    return list(set(urls + whatsapp))


def extract_keywords(text: str) -> List[str]:
    """Extract scam-related keywords."""
    text_lower = text.lower()
    found = []
    for keyword in SCAM_KEYWORDS:
        if keyword in text_lower:
            found.append(keyword)
    return found


def extract_all_intelligence(text: str) -> Dict[str, Any]:
    """
    Extract all intelligence from a message.
    
    Args:
        text: Message text to analyze
    
    Returns:
        Dict with all extracted intelligence
    """
    return {
        "upi_ids": extract_upi_ids(text),
        "bank_accounts": extract_bank_accounts(text),
        "ifsc_codes": extract_ifsc_codes(text),
        "phone_numbers": extract_phone_numbers(text),
        "phishing_links": extract_urls(text),
        "suspicious_keywords": extract_keywords(text)
    }


def merge_intelligence(existing: Dict[str, Any], new: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new intelligence with existing, removing duplicates.
    
    Args:
        existing: Previously extracted intelligence
        new: Newly extracted intelligence
    
    Returns:
        Merged intelligence dict
    """
    merged = {}
    for key in ["upi_ids", "bank_accounts", "ifsc_codes", "phone_numbers", "phishing_links", "suspicious_keywords"]:
        existing_list = existing.get(key, [])
        new_list = new.get(key, [])
        merged[key] = list(set(existing_list + new_list))
    merged["upi_ids"] = normalize_upi_ids(merged.get("upi_ids", []))
    merged["phone_numbers"] = normalize_phone_numbers(merged.get("phone_numbers", []))
    return merged


def has_actionable_intel(intelligence: Dict[str, Any]) -> bool:
    """
    Check if intelligence contains actionable data.
    
    Args:
        intelligence: Intelligence dict
    
    Returns:
        True if contains bank/UPI/links
    """
    return bool(
        intelligence.get("upi_ids") or
        intelligence.get("bank_accounts") or
        intelligence.get("phishing_links") or
        intelligence.get("ifsc_codes")
    )
