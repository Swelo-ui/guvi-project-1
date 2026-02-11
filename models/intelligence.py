"""
Intelligence Extraction Patterns
Regex-based extraction of bank accounts, UPI IDs, phone numbers, etc.
"""

import re
from typing import Dict, List, Any


# Regex patterns for intelligence extraction
PATTERNS = {
    "upi": r'[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+',
    "email": r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}',
    "bank_account": r'\b\d{10,18}\b',
    "ifsc": r'\b[A-Z]{4}0[A-Z0-9]{6}\b',
    # Enhanced phone: captures +91, international, and 10-digit numbers
    "phone": r'(?<!\d)(?:\+?\d{1,3}[\s-]?)?[6-9]\d{9}(?!\d)',
    # URL: with protocol OR known shortener domains without protocol
    "url": r'https?://[^\s<>"{}|\\^`\[\]]+',
    "url_shortener": r'(?:bit\.ly|tinyurl\.com|goo\.gl|t\.co|is\.gd|rb\.gy|cutt\.ly|short\.io|ow\.ly)/[^\s<>"{}|\\^`\[\]]+',
    "whatsapp": r'wa\.me/\d+',
    # Fake credentials: employee IDs, fake refs
    "fake_credential": r'(?:emp(?:loyee)?|staff|officer)[\s_-]?(?:id)?[\s:_-]*([a-zA-Z0-9]+)',
}

# Suspicious keywords indicating scam
SCAM_KEYWORDS = [
    # Urgency
    "urgent", "immediately", "now", "today only", "expires", "last chance", "limited time", "hurry",
    # Fear
    "blocked", "suspended", "arrested", "police", "cbi", "fraud", "illegal", "warrant", "cyber crime",
    "seized", "confiscated", "compromised",
    # Action
    "verify", "confirm", "update", "kyc", "otp", "pin", "password", "verification code", "screen share",
    # Money
    "transfer", "pay", "send money", "refund", "chargeback", "cashback", "prize", "lottery", "won",
    "fine", "penalty", "processing fee", "clearance",
    # Authority / Impersonation
    "bank manager", "customer care", "support", "helpline", "toll free", "rbi", "government",
    "income tax", "gst", "army", "officer", "captain", "colonel", "military",
    # Technical
    "link", "click", "download", "install", "app", "apk", "remote access", "anydesk", "teamviewer",
    "quick support",
    # Channels
    "whatsapp", "telegram", "sms", "email",
    # Identity
    "aadhaar", "pan", "kyc update", "video kyc",
    # Payment tactics
    "qr", "scan", "upi collect", "payment request", "request money",
    # Delivery / Courier scams
    "courier", "parcel", "customs", "delivery charge", "fedex", "dhl",
    # Investment scams
    "crypto", "bitcoin", "investment", "invest", "trading", "profit", "loan", "emi",
    # Marketplace / Deal scams
    "deal", "offer", "coupon", "free", "buy", "sell", "marketplace", "olx",
    # Refund scams
    "claim", "pending", "approved", "eligible",
]


UPI_HANDLES = {
    "ybl", "oksbi", "okicici", "okhdfcbank", "okaxis", "paytm", "axl", "ibl",
    "upi", "sbi", "icici", "hdfcbank", "axis", "pnb", "kotak", "yesbank",
    "barodampay", "idfcbank", "apl", "boi", "cbin", "cnrb", "fbl", "idbi",
    "indus", "kbl", "lvb", "rbl", "uco", "unionbankofindia", "citi",
}

# Context keywords that indicate surrounding text is about accounts, not phones
ACCOUNT_CONTEXT_KEYWORDS = [
    "account", "a/c", "acc", "bank", "deposit", "balance", "savings",
    "current", "credit", "debit", "transfer", "neft", "rtgs", "imps",
    "ifsc", "branch", "passbook", "cheque",
]

# Context keywords that indicate surrounding text is about phone numbers
PHONE_CONTEXT_KEYWORDS = [
    "call", "phone", "mobile", "contact", "whatsapp", "sms", "helpline",
    "dial", "ring", "cell",
]


def normalize_upi_ids(items: List[str], allow_unknown: bool = False) -> List[str]:
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
        # Known UPI handle - always accept
        if handle in UPI_HANDLES:
            normalized.append(f"{user}@{handle}")
            continue
        # Unknown handle with a dot (looks like email domain) - skip unless allowed
        if "." in handle and not allow_unknown:
            continue
        # Unknown handle without dot - accept if context allows OR always allow
        # (GUVI tests use handles like @fakeupi, @fakebank)
        if allow_unknown or (not "." in handle and len(handle) >= 2):
            normalized.append(f"{user}@{handle}")
    return _deduplicate(normalized)


def _deduplicate(items: List[str]) -> List[str]:
    """Deduplicate list while preserving order."""
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            result.append(item)
            seen.add(item)
    return result


def extract_upi_ids(text: str) -> List[str]:
    """Extract UPI IDs like name@handle or phone@handle."""
    matches = re.findall(PATTERNS["upi"], text, re.IGNORECASE)
    
    # Filter out obvious emails before UPI processing
    email_matches = set(re.findall(PATTERNS["email"], text, re.IGNORECASE))
    
    normalized = []
    for candidate in matches:
        if "@" not in candidate:
            continue
            
        # If this exact match is also found as an email, check if it's a known UPI handle
        if candidate.lower() in {e.lower() for e in email_matches}:
            _, handle = candidate.lower().split("@", 1)
            # Only accept as UPI if it uses a known UPI handle (like @ybl, @oksbi)
            # If it's a generic domain (sbi.co.in) and matches email pattern, it's likely just an email
            if handle.strip(".") not in UPI_HANDLES:
                continue
                
        user, handle = candidate.split("@", 1)
        if len(user) < 2:
            continue
        
        handle = handle.lower()
        # Basic validation: handle shouldn't contain spaces or unusual characters
        if not re.match(r'^[a-z0-9.-]+$', handle):
            continue
            
        normalized.append(f"{user}@{handle}")
    
    return _deduplicate(normalized)


def _has_context(text: str, position: int, keywords: List[str], window: int = 80) -> bool:
    """Check if any keyword appears near a given position in the text."""
    start = max(0, position - window)
    end = min(len(text), position + window)
    surrounding = text[start:end].lower()
    return any(kw in surrounding for kw in keywords)


def extract_bank_accounts(text: str) -> List[str]:
    """Extract bank account numbers (10-16 digits) with context validation."""
    valid = []
    for m in re.finditer(PATTERNS["bank_account"], text):
        acc = m.group(0)
        # Context check to avoid phone numbers (most Indian accounts are > 10 digits)
        # or if 10 digits, they usually don't start with 6-9 unless it's a phone-linked account
        if len(acc) == 10 and acc[0] in '6789':
            # Only accept if "account" or "number" keywords are nearby
            context = text[max(0, m.start()-30):min(len(text), m.end()+30)].lower()
            if any(kw in context for kw in ['account', 'acc', 'no', 'a/c', 'number']):
                valid.append(acc)
        else:
            valid.append(acc)
            
    return _deduplicate(valid)


def extract_ifsc_codes(text: str) -> List[str]:
    """Extract IFSC codes."""
    return _deduplicate(re.findall(PATTERNS["ifsc"], text.upper()))


def normalize_phone_numbers(items: List[str]) -> List[str]:
    """Normalize phone numbers to +91 format for Indian numbers, keep others."""
    normalized = []
    for item in items:
        if not item:
            continue
        clean = re.sub(r'[^\d+]', '', str(item))
        # Handle +91 prefix
        if clean.startswith('+91'):
            clean = clean[3:]
        elif clean.startswith('91') and len(clean) == 12:
            clean = clean[2:]
        # Valid 10-digit Indian mobile number
        if len(clean) == 10 and clean[0] in '6789':
            normalized.append(f"+91{clean}")
        # Accept any 10-digit number
        elif len(clean) == 10:
            normalized.append(clean)
    return _deduplicate(normalized)


def normalize_bank_accounts(items: list) -> list:
    """Validate and normalize bank account numbers.
    Filters out short fragments (< 10 digits) that LLM may incorrectly extract.
    E.g., 'account ending with 3456' → '3456' is NOT a valid bank account.
    """
    valid = []
    for item in items:
        if not item:
            continue
        clean = re.sub(r'[^\d]', '', str(item))
        # Bank accounts must be at least 10 digits
        if len(clean) >= 10:
            valid.append(clean)
    return _deduplicate(valid)


def extract_phone_numbers(text: str) -> List[str]:
    """Extract phone numbers - enhanced to catch more formats.
    Skips 10-digit numbers in bank-account context to avoid cross-contamination.
    """
    matches = []
    
    # Positive indicators that strongly suggest a number is a phone number
    # If these are present, they override the "account" context exclusion
    phone_indicators = ["phone", "call", "mob", "mobile", "whatsapp", "contact", "sms", "text"]
    
    # Primary phone pattern (captures +91 prefixed and 6-9 starting numbers)
    for m in re.finditer(PATTERNS["phone"], text):
        raw = m.group()
        # If it has explicit phone formatting (+ prefix), accept it immediately
        # phone numbers with + are never bank accounts
        if raw.strip().startswith('+'):
            matches.append(raw)
            continue
            
        # Strip country-code prefix to get the core 10-digit number
        core = re.sub(r'[^\d]', '', raw)
        if core.startswith('91') and len(core) == 12:
            core = core[2:]
            
        # If it's a bare 10-digit number, check for bank-account context
        # (Only filter if it DOESN'T look like a formatted phone number)
        if len(core) == 10:
            # Check if it has phone-like separators (dashes/spaces) - if so, it's likely a phone
            has_separators = '-' in raw or ' ' in raw
            
            # Check for positive phone indicators immediately preceding the number
            has_phone_indicator = _has_context(text, m.start(), phone_indicators, window=25)
            
            # If it's a bare block of digits closely associated with account keywords, skip it
            # UNLESS it has a strong phone indicator
            if not has_separators and not has_phone_indicator:
                if _has_context(text, m.start(), ACCOUNT_CONTEXT_KEYWORDS, window=50):
                    continue  # Skip — likely a bank account
        
        matches.append(raw)
    
    # Secondary: catch standalone 10-digit sequences not already found
    for m in re.finditer(r'\b(\d{10})\b', text):
        num = m.group(1)
        # Avoid duplicates (raw or core)
        if num not in matches and num not in [re.sub(r'[^\d]', '', m) for m in matches]:
            
            # Check for positive phone indicators
            has_phone_indicator = _has_context(text, m.start(), phone_indicators, window=25)
            
            # Standalone 10-digit number: strict context check
            # If explicit phone context, keep it. If account context (and no phone context), skip it.
            if not has_phone_indicator and _has_context(text, m.start(), ACCOUNT_CONTEXT_KEYWORDS, window=50):
                continue
                
            matches.append(num)
    
    return normalize_phone_numbers(_deduplicate(matches))


def extract_fake_credentials(text: str) -> List[str]:
    """Extract fake employee IDs, staff IDs, and similar credentials."""
    matches = re.findall(PATTERNS["fake_credential"], text, re.IGNORECASE)
    # Also look for patterns like "Emp123sumit"
    additional = re.findall(r'\b[Ee]mp\d*[a-zA-Z]*\d*\b', text)
    return _deduplicate([m.strip() for m in matches + additional if m.strip()])


def extract_urls(text: str) -> List[str]:
    """Extract URLs (potential phishing links), including protocol-less shortener URLs."""
    urls = re.findall(PATTERNS["url"], text)
    # Capture shortener URLs without http:// prefix
    shortener_urls = re.findall(PATTERNS["url_shortener"], text, re.IGNORECASE)
    # Reconstruct full shortener match from capture
    for match in re.finditer(PATTERNS["url_shortener"], text, re.IGNORECASE):
        full_match = match.group(0)
        if full_match not in urls:
            urls.append(full_match)
    whatsapp = re.findall(PATTERNS["whatsapp"], text)
    # Clean trailing punctuation from URLs
    cleaned = []
    for url in _deduplicate(urls + whatsapp):
        url = url.rstrip('.,;:!?)')
        if url:
            cleaned.append(url)
    return _deduplicate(cleaned)


def extract_emails(text: str) -> List[str]:
    """Extract emails, filtering out UPI IDs.
    Also captures addresses with non-TLD domains (like 'fakebank')
    when the word 'email' appears nearby in the text.
    """
    matches = re.findall(PATTERNS["email"], text, re.IGNORECASE)
    # Also check for @-patterns that the email regex misses (no TLD domains)
    at_patterns = re.findall(PATTERNS["upi"], text, re.IGNORECASE)
    
    # Check if 'email' keyword appears in text
    has_email_context = bool(re.search(r'\bemail\b', text.lower()))
    
    emails = []
    # Process standard email matches (these have TLDs, so we trust them more)
    for m in matches:
        _, domain = m.lower().split("@", 1) if "@" in m else ("", "")
        # Remove the aggressive UPI handle check for standard emails
        # A valid email like support@sbi.co.in shouldn't be filtered just because 'sbi' is a UPI handle
        
        # If domain has no dot (like fakeupi, fakebank), it's likely a UPI ID
        # (Though the regex requires a dot, so this is just a safety check)
        if "." not in domain:
            continue
        emails.append(m.lower())
    
    # If 'email' keyword is in text, also capture @-patterns with non-TLD domains
    # This is where we need to be careful not to capture UPI IDs as emails
    if has_email_context:
        for m in at_patterns:
            lower_m = m.lower()
            if lower_m in emails:
                continue
            _, domain = lower_m.split("@", 1) if "@" in lower_m else ("", "")
            domain_base = domain.split(".")[0] if "." in domain else domain
            
            # Here we MUST filter out known UPI handles because the regex is permissive
            if domain_base in UPI_HANDLES:
                continue
                
            # Accept non-TLD domains when 'email' context is present
            if "." not in domain and len(domain) >= 2:
                emails.append(lower_m)
    
    return _deduplicate(emails)


def extract_keywords(text: str) -> List[str]:
    """Extract scam-related keywords using word-boundary matching."""
    text_lower = text.lower()
    found = []
    for keyword in SCAM_KEYWORDS:
        # Use word boundary for single words, substring for multi-word phrases
        if " " in keyword:
            if keyword in text_lower:
                found.append(keyword)
        else:
            # Check with word boundary to avoid partial matches like "snow" matching "now"
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, text_lower):
                found.append(keyword)
    return found


def normalize_keywords(items: List[str]) -> List[str]:
    normalized = []
    keyword_set = set(SCAM_KEYWORDS)
    for item in items:
        if not item:
            continue
        candidate = re.sub(r'\s+', ' ', str(item).strip().lower())
        if candidate in keyword_set:
            normalized.append(candidate)
    return _deduplicate(normalized)


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
        "emails": extract_emails(text),
        "ifsc_codes": extract_ifsc_codes(text),
        "phone_numbers": extract_phone_numbers(text),
        "phishing_links": extract_urls(text),
        "suspicious_keywords": extract_keywords(text),
        # Internal field for tracking
        "fake_credentials": extract_fake_credentials(text),
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
    for key in ["upi_ids", "bank_accounts", "emails", "ifsc_codes", "phone_numbers", "phishing_links", "suspicious_keywords", "fake_credentials"]:
        existing_list = existing.get(key, [])
        new_list = new.get(key, [])
        merged[key] = _deduplicate(existing_list + new_list)
    merged["upi_ids"] = normalize_upi_ids(merged.get("upi_ids", []), allow_unknown=True)
    merged["bank_accounts"] = normalize_bank_accounts(merged.get("bank_accounts", []))
    merged["phone_numbers"] = normalize_phone_numbers(merged.get("phone_numbers", []))
    merged["suspicious_keywords"] = normalize_keywords(merged.get("suspicious_keywords", []))
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
