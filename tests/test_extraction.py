"""
Offline Extraction Test Suite
Tests intelligence extraction (regex-only) for all 12 GUVI scam archetypes.
No LLM or server needed - validates regex accuracy directly.
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest
from models.intelligence import (
    extract_all_intelligence, extract_upi_ids, extract_bank_accounts,
    extract_phone_numbers, extract_urls, extract_keywords, extract_emails,
    extract_ifsc_codes, merge_intelligence, has_actionable_intel
)


# All 12 GUVI test archetypes with expected extraction results
TEST_CASES = [
    {
        "name": "1. Bank Fraud / Account Block",
        "message": "Your SBI account is blocked. Send OTP immediately or your account will be permanently closed. Contact +919876543210.",
        "expect_keywords": ["blocked", "otp", "immediately"],
        "expect_phones": ["+919876543210"],
        "expect_scam": True,
    },
    {
        "name": "2. UPI Fraud / Payment",
        "message": "Your payment of Rs.5000 failed. To verify, send money to cashback.scam@fakeupi or call +918765432109.",
        "expect_keywords": ["verify", "send money", "cashback"],
        "expect_upi": ["cashback.scam@fakeupi"],
        "expect_phones": ["+918765432109"],
        "expect_scam": True,
    },
    {
        "name": "3. Digital Arrest Scam",
        "message": "This is CBI. A warrant has been issued in your name. You are under digital arrest. Transfer Rs.50000 immediately to avoid jail.",
        "expect_keywords": ["warrant", "immediately", "transfer"],
        "expect_scam": True,
    },
    {
        "name": "4. KYC Fraud",
        "message": "Dear customer, your KYC is pending. Update now: https://bit.ly/sbi-kyc-update or your account will be blocked within 24 hours.",
        "expect_keywords": ["kyc", "blocked", "update"],
        "expect_urls": ["https://bit.ly/sbi-kyc-update"],
        "expect_scam": True,
    },
    {
        "name": "5. QR Code Scam",
        "message": "Scan this QR code to receive your cashback of Rs.2000. Your UPI: scammer.fraud@fakebank",
        "expect_keywords": ["scan", "cashback"],
        "expect_upi": ["scammer.fraud@fakebank"],
        "expect_scam": True,
    },
    {
        "name": "6. Lottery / Prize Scam",
        "message": "Congratulations! You won Rs.10 Lakhs! Pay Rs.500 processing fee to claim. Contact: lottery@scam.com, UPI: prize123@ybl",
        "expect_keywords": ["won", "pay"],
        "expect_upi": ["prize123@ybl"],
        "expect_scam": True,
    },
    {
        "name": "7. Loan Scam",
        "message": "Pre-approved loan of Rs.5L at 0% interest! Limited time offer. Send Aadhaar + PAN for instant approval. Call 9876543210.",
        "expect_keywords": ["loan", "aadhaar", "pan"],
        "expect_phones": ["+919876543210"],
        "expect_scam": True,
    },
    {
        "name": "8. Investment Scam",
        "message": "Guaranteed 50% returns on crypto! Invest now. Minimum Rs.10000. WhatsApp: +917654321098 for details.",
        "expect_keywords": ["crypto", "invest"],
        "expect_phones": ["+917654321098"],
        "expect_scam": True,
    },
    {
        "name": "9. Courier / Parcel Scam",
        "message": "Your FedEx parcel has been seized by customs. Pay Rs.2000 clearance fee immediately. Transfer to account 12345678901234.",
        "expect_keywords": ["parcel", "customs", "seized", "clearance", "immediately", "fedex"],
        "expect_bank_accounts": ["12345678901234"],
        "expect_scam": True,
    },
    {
        "name": "10. OLX / Marketplace Scam",
        "message": "I am an army officer posted in Kashmir. I'll pay in advance via UPI. Send your account details. My ID: Emp123Captain, phone: 8899776655.",
        "expect_keywords": ["army", "officer"],
        "expect_phones": ["+918899776655"],
        "expect_scam": True,
    },
    {
        "name": "11. Insurance Scam",
        "message": "Your LIC policy maturity amount of Rs.5L is pending. Pay processing fee of Rs.1000. IFSC: SBIN0001234, Account: 1234567890123.",
        "expect_keywords": ["pending", "pay"],
        "expect_ifsc": ["SBIN0001234"],
        "expect_bank_accounts": ["1234567890123"],
        "expect_scam": True,
    },
    {
        "name": "12. Refund Scam",
        "message": "Amazon refund of Rs.2999 pending. Click link to claim: tinyurl.com/amazon-refund-claim. Offer expires today.",
        "expect_keywords": ["refund", "pending", "claim", "expires", "click"],
        "expect_urls": ["tinyurl.com/amazon-refund-claim"],
        "expect_scam": True,
    },
]


class TestExtractionArchetypes:
    """Test all 12 scam archetypes for correct extraction."""

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_keyword_extraction(self, case):
        """Test that expected keywords are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_keywords", [])
        found = intel["suspicious_keywords"]
        for kw in expected:
            assert kw in found, f"Missing keyword '{kw}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_phone_extraction(self, case):
        """Test that expected phone numbers are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_phones", [])
        found = intel["phone_numbers"]
        for phone in expected:
            assert phone in found, f"Missing phone '{phone}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_upi_extraction(self, case):
        """Test that expected UPI IDs are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_upi", [])
        found = intel["upi_ids"]
        for upi in expected:
            assert upi in found, f"Missing UPI '{upi}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_url_extraction(self, case):
        """Test that expected URLs are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_urls", [])
        found = intel["phishing_links"]
        for url in expected:
            assert url in found, f"Missing URL '{url}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_bank_account_extraction(self, case):
        """Test that expected bank accounts are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_bank_accounts", [])
        found = intel["bank_accounts"]
        for acc in expected:
            assert acc in found, f"Missing bank account '{acc}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_ifsc_extraction(self, case):
        """Test that expected IFSC codes are found."""
        intel = extract_all_intelligence(case["message"])
        expected = case.get("expect_ifsc", [])
        found = intel["ifsc_codes"]
        for ifsc in expected:
            assert ifsc in found, f"Missing IFSC '{ifsc}' in {found}"

    @pytest.mark.parametrize("case", TEST_CASES, ids=[c["name"] for c in TEST_CASES])
    def test_scam_detection(self, case):
        """Test that scam is correctly detected via keyword/intel threshold."""
        intel = extract_all_intelligence(case["message"])
        expected_scam = case.get("expect_scam", False)
        if expected_scam:
            # A scam should be detected if: actionable intel OR 2+ keywords
            is_scam = has_actionable_intel(intel) or len(intel["suspicious_keywords"]) >= 2
            assert is_scam, f"Scam not detected! Intel: {intel}"


class TestEdgeCases:
    """Test edge cases and disambiguation."""

    def test_upi_with_unknown_handle(self):
        """UPI IDs with non-standard handles should be extracted."""
        text = "Send money to cashback.scam@fakeupi"
        upis = extract_upi_ids(text)
        assert "cashback.scam@fakeupi" in upis

    def test_upi_with_known_handle(self):
        """UPI IDs with standard handles should always be extracted."""
        text = "My UPI: rajesh42@ybl"
        upis = extract_upi_ids(text)
        assert "rajesh42@ybl" in upis

    def test_email_not_confused_as_upi(self):
        """Real emails should not be extracted as UPI IDs."""
        text = "Contact support@gmail.com"
        upis = extract_upi_ids(text)
        emails = extract_emails(text)
        assert "support@gmail.com" not in upis
        assert "support@gmail.com" in emails

    def test_url_without_protocol(self):
        """tinyurl.com links without http:// should be captured."""
        text = "Click: tinyurl.com/amazon-refund-claim"
        urls = extract_urls(text)
        assert any("tinyurl.com/amazon-refund-claim" in u for u in urls)

    def test_url_with_protocol(self):
        """Normal URLs with http:// should be captured."""
        text = "Visit https://bit.ly/sbi-kyc-update"
        urls = extract_urls(text)
        assert any("bit.ly/sbi-kyc-update" in u for u in urls)

    def test_bitly_without_protocol(self):
        """bit.ly links without http:// should be captured."""
        text = "Click bit.ly/fake-offer now"
        urls = extract_urls(text)
        assert any("bit.ly/fake-offer" in u for u in urls)

    def test_bank_account_context_disambiguation(self):
        """10-digit number near 'account' should be treated as bank account."""
        text = "Your bank account number is 9876543210. Transfer immediately."
        accounts = extract_bank_accounts(text)
        assert "9876543210" in accounts

    def test_phone_context_disambiguation(self):
        """10-digit number near 'call' should be treated as phone, not account."""
        text = "Call 9876543210 for support"
        phones = extract_phone_numbers(text)
        accounts = extract_bank_accounts(text)
        assert "+919876543210" in phones
        assert "9876543210" not in accounts

    def test_long_number_is_bank_account(self):
        """Numbers longer than 10 digits should always be bank accounts."""
        text = "Account: 12345678901234"
        accounts = extract_bank_accounts(text)
        assert "12345678901234" in accounts

    def test_army_keyword(self):
        """'army' should be detected as scam keyword."""
        keywords = extract_keywords("I am in the army, posted in Leh")
        assert "army" in keywords

    def test_officer_keyword(self):
        """'officer' should be detected as scam keyword."""
        keywords = extract_keywords("I am an officer in the Indian Army")
        assert "officer" in keywords

    def test_word_boundary_keywords(self):
        """Keywords should match on word boundaries, not partial words."""
        # 'now' should not match in 'knowledge' or 'snow'
        keywords = extract_keywords("I have knowledge about snow patterns")
        assert "now" not in keywords

    def test_non_scam_message(self):
        """A normal, benign message should not flag as scam."""
        intel = extract_all_intelligence("Hello, how are you today? The weather is nice.")
        is_scam = has_actionable_intel(intel) or len(intel["suspicious_keywords"]) >= 2
        assert not is_scam, f"False positive! Keywords: {intel['suspicious_keywords']}"

    def test_merge_intelligence_deduplication(self):
        """Merging should deduplicate results."""
        intel1 = {"upi_ids": ["abc@ybl"], "bank_accounts": [], "emails": [],
                  "ifsc_codes": [], "phone_numbers": ["+919876543210"],
                  "phishing_links": [], "suspicious_keywords": ["otp"]}
        intel2 = {"upi_ids": ["abc@ybl", "def@paytm"], "bank_accounts": [],
                  "emails": [], "ifsc_codes": [], "phone_numbers": ["+919876543210"],
                  "phishing_links": [], "suspicious_keywords": ["otp", "verify"]}
        merged = merge_intelligence(intel1, intel2)
        assert len(merged["upi_ids"]) == 2

    def test_guvi_bug_ifsc_extraction(self):
        """Regression test: FBIN0001234 should be extracted."""
        text = "IFSC code FBIN0001234 hai"
        ifsc = extract_ifsc_codes(text)
        assert "FBIN0001234" in ifsc

    def test_guvi_bug_phone_formatting(self):
        """Regression test: +91-9876543210 should be Phone, NOT Bank Account."""
        text = "Our official email is support@fakebank.com; please send the OTP to +91-9876543210 right away so we can secure your account before it gets blocked."
        phones = extract_phone_numbers(text)
        accounts = extract_bank_accounts(text)
        assert "+919876543210" in phones
        assert "9876543210" not in accounts

    def test_guvi_bug_email_as_upi(self):
        """Regression test: support@fakebank.com is Email, NOT UPI."""
        text = "Contact support@fakebank.com for help."
        emails = extract_emails(text)
        upis = extract_upi_ids(text)
        assert "support@fakebank.com" in emails
        assert "support@fakebank.com" not in upis

    def test_guvi_bug_bank_account_fragment_rejected(self):
        """Regression: '3456' (last 4 digits) should NOT be a valid bank account after normalization."""
        from models.intelligence import normalize_bank_accounts
        # LLM might extract "3456" from "account ending with 3456"
        result = normalize_bank_accounts(["3456", "1234", "98765"])
        assert len(result) == 0, f"Short fragments should be rejected, got: {result}"

    def test_guvi_bug_valid_bank_account_kept(self):
        """Regression: Full 16-digit account should be kept after normalization."""
        from models.intelligence import normalize_bank_accounts
        result = normalize_bank_accounts(["1234567890123456", "3456"])
        assert "1234567890123456" in result
        assert "3456" not in result
        assert len(result) == 1

    def test_guvi_bug_merge_filters_short_accounts(self):
        """Regression: merge_intelligence should filter out short bank account fragments."""
        intel1 = {"upi_ids": [], "bank_accounts": [], "emails": [],
                  "ifsc_codes": [], "phone_numbers": [],
                  "phishing_links": [], "suspicious_keywords": []}
        # Simulate LLM returning "3456" as bank account
        intel2 = {"upi_ids": [], "bank_accounts": ["3456"], "emails": [],
                  "ifsc_codes": [], "phone_numbers": [],
                  "phishing_links": [], "suspicious_keywords": []}
        merged = merge_intelligence(intel1, intel2)
        assert "3456" not in merged["bank_accounts"], f"Short fragment '3456' should be filtered out"

    def test_guvi_bug_email_no_tld_with_email_context(self):
        """Regression: scammer.fraud@fakebank should be captured as email when 'email' keyword is nearby."""
        text = "Our official email is scammer.fraud@fakebank; please send the OTP."
        emails = extract_emails(text)
        assert "scammer.fraud@fakebank" in emails, f"Got emails: {emails}"

    def test_guvi_bug_email_no_tld_without_context(self):
        """Without 'email' keyword, scammer.fraud@fakebank should NOT be in emails (it's a UPI)."""
        text = "Send money to scammer.fraud@fakebank for payment."
        emails = extract_emails(text)
        assert "scammer.fraud@fakebank" not in emails

    def test_guvi_bug_ifsc_fkbk(self):
        """Regression: FKBK0001234 should be extracted as IFSC code."""
        text = "Use IFSC code FKBK0001234 for the transfer."
        ifsc = extract_ifsc_codes(text)
        assert "FKBK0001234" in ifsc

    # ===== Round 2 Regression Tests =====

    def test_round2_phone_not_confused_as_bank_account(self):
        """Bug 3 regression: 10-digit number near 'account' should NOT be phone."""
        text = "Transfer to account 9876543210 immediately"
        phones = extract_phone_numbers(text)
        accounts = extract_bank_accounts(text)
        # It's in bank-account context, phone should NOT include it
        assert "+919876543210" not in phones, f"Account-context number wrongly in phones: {phones}"
        assert "9876543210" in accounts

    def test_round2_merge_preserves_fake_credentials(self):
        """Bug 4 regression: fake_credentials survives merge_intelligence."""
        intel1 = {"upi_ids": [], "bank_accounts": [], "emails": [],
                  "ifsc_codes": [], "phone_numbers": [],
                  "phishing_links": [], "suspicious_keywords": [],
                  "fake_credentials": ["EmpID-1234"]}
        intel2 = {"upi_ids": [], "bank_accounts": [], "emails": [],
                  "ifsc_codes": [], "phone_numbers": [],
                  "phishing_links": [], "suspicious_keywords": [],
                  "fake_credentials": ["Captain-Rank"]}
        merged = merge_intelligence(intel1, intel2)
        assert "EmpID-1234" in merged.get("fake_credentials", []), f"Lost fake_credentials: {merged}"
        assert "Captain-Rank" in merged.get("fake_credentials", [])

    def test_round2_clean_json_preserves_true_in_strings(self):
        """Bug 5 regression: True inside a JSON string value should NOT be lowercased."""
        from core.llm_client import clean_json_string
        raw = '{"response": "You said True? That is False", "scam_detected": True}'
        cleaned = clean_json_string(raw)
        import json
        parsed = json.loads(cleaned)
        # The string content should be preserved as-is
        assert "True" in parsed["response"], f"String value corrupted: {parsed['response']}"
        assert parsed.get("scam_detected") == True  # noqa: E712  (JSON true → Python True)

    def test_round2_phone_standalone_still_extracted(self):
        """Bug 3 sanity: 10-digit phone w/o account context SHOULD still be a phone."""
        text = "Call me on 9876543210 for details"
        phones = extract_phone_numbers(text)
        assert "+919876543210" in phones


class TestAdvancedExtraction:
    """Tests for Phase 2 advanced extraction: Aadhaar, PAN, bank names."""

    def test_aadhaar_extraction_spaced(self):
        """Aadhaar number in spaced format should be extracted."""
        from models.intelligence import extract_aadhaar_numbers
        text = "Your Aadhaar number 4321 8765 2109 needs verification"
        result = extract_aadhaar_numbers(text)
        assert "432187652109" in result

    def test_aadhaar_extraction_continuous(self):
        """Aadhaar number as continuous digits with context should be extracted."""
        from models.intelligence import extract_aadhaar_numbers
        text = "For Aadhaar verification, send 432187652109 to us"
        result = extract_aadhaar_numbers(text)
        assert "432187652109" in result

    def test_aadhaar_rejects_starting_with_01(self):
        """Aadhaar cannot start with 0 or 1."""
        from models.intelligence import extract_aadhaar_numbers
        text = "Your aadhaar is 0123 4567 8901"
        result = extract_aadhaar_numbers(text)
        assert len(result) == 0, f"Should reject Aadhaar starting with 0, got: {result}"

    def test_pan_extraction(self):
        """PAN card number should be extracted."""
        from models.intelligence import extract_pan_numbers
        text = "Send your PAN ABCDE1234F for loan verification"
        result = extract_pan_numbers(text)
        assert "ABCDE1234F" in result

    def test_pan_not_random_text(self):
        """Random text should not be extracted as PAN."""
        from models.intelligence import extract_pan_numbers
        text = "Hello, how are you today?"
        result = extract_pan_numbers(text)
        assert len(result) == 0

    def test_bank_name_extraction_single(self):
        """Single-word bank names should be extracted."""
        from models.intelligence import extract_mentioned_banks
        text = "I am calling from HDFC Bank headquarters"
        result = extract_mentioned_banks(text)
        assert "hdfc" in result

    def test_bank_name_extraction_multi_word(self):
        """Multi-word bank names like 'yes bank' should be extracted."""
        from models.intelligence import extract_mentioned_banks
        text = "This is Yes Bank customer care calling"
        result = extract_mentioned_banks(text)
        assert "yes bank" in result

    def test_extract_all_includes_new_fields(self):
        """extract_all_intelligence should return all new fields."""
        intel = extract_all_intelligence("Send Aadhaar 4321 8765 2109 and PAN ABCDE1234F to SBI branch")
        assert "aadhaar_numbers" in intel
        assert "pan_numbers" in intel
        assert "mentioned_banks" in intel
        assert "432187652109" in intel["aadhaar_numbers"]


BULK_UPI_USERS = [
    "rajesh", "sunita", "amit", "priya", "vikas", "neha", "anil", "kiran"
]
BULK_UPI_HANDLES = [
    "ybl", "paytm", "oksbi", "okicici", "okhdfcbank", "okaxis", "upi", "fakeupi", "fakebank", "okpnb"
]
BULK_UPI_CASES = [(user, handle) for user in BULK_UPI_USERS for handle in BULK_UPI_HANDLES]

BULK_PHONE_NUMBERS = [f"9{str(i).zfill(9)}" for i in range(800000000, 800000040)]

BULK_IFSC_PREFIXES = [
    "SBIN", "HDFC", "ICIC", "UTIB", "PUNB", "BARB", "KKBK", "YESB", "CNRB", "UBIN",
    "IBKL", "INDB", "BDBL", "FDRL", "IDFB", "RATN", "UCBA", "IDIB", "BKID", "CBIN",
    "FINO", "ESAF", "SIBL", "PSIB", "KARB", "IOBA", "MAHB", "VIJB", "DLXB", "CSBK"
]
BULK_IFSC_CODES = [
    f"{prefix}0{str(100000 + idx).zfill(6)}"
    for idx, prefix in enumerate(BULK_IFSC_PREFIXES)
]

BULK_URLS = [f"https://example{i}.com/path" for i in range(20)]

BULK_KEYWORDS = [
    "blocked", "suspended", "arrested", "police", "cbi", "fraud", "illegal", "warrant",
    "seized", "compromised", "verify", "confirm", "update", "kyc", "otp", "pin",
    "password", "verification code", "screen share", "transfer", "pay", "send money",
    "refund", "chargeback", "cashback", "prize", "lottery", "won", "fine", "processing fee",
    "bank manager", "customer care", "support", "helpline", "toll free", "rbi", "government",
    "income tax", "gst", "army", "officer", "captain", "colonel", "military", "link",
    "click", "download", "install", "app", "apk", "remote access", "anydesk", "teamviewer",
    "quick support", "whatsapp", "telegram", "sms", "email", "aadhaar", "pan", "kyc update",
    "video kyc", "aadhaar number", "pan card", "pan number", "aeps", "biometric",
    "fingerprint", "uidai", "sim swap", "sim card", "deactivate", "reactivate", "reissue",
    "qr", "scan", "upi collect", "payment request", "request money", "courier", "parcel",
    "customs", "delivery charge", "fedex", "dhl", "crypto", "bitcoin", "investment",
    "invest", "trading", "profit", "loan", "emi", "deal", "offer", "coupon", "free",
    "buy", "sell", "marketplace", "olx", "claim", "pending", "approved", "eligible"
]

AUTHORITY_KEYWORDS = {
    "bank manager", "customer care", "support", "helpline", "toll free", "rbi", "government",
    "income tax", "gst", "army", "officer", "captain", "colonel", "military",
}

TECH_KEYWORDS = {
    "link", "click", "download", "install", "app", "apk", "remote access", "anydesk", "teamviewer",
    "quick support",
}

PAYMENT_KEYWORDS = {
    "transfer", "pay", "send money", "refund", "chargeback", "cashback", "prize", "lottery", "won",
    "fine", "processing fee", "qr", "scan", "upi collect", "payment request", "request money",
}

IDENTITY_KEYWORDS = {
    "aadhaar", "pan", "kyc update", "video kyc", "aadhaar number", "pan card", "pan number", "aeps",
    "biometric", "fingerprint", "uidai",
}

SIM_KEYWORDS = {
    "sim swap", "sim card", "deactivate", "reactivate", "reissue",
}

DELIVERY_KEYWORDS = {
    "courier", "parcel", "customs", "delivery charge", "fedex", "dhl",
}

INVESTMENT_KEYWORDS = {
    "crypto", "bitcoin", "investment", "invest", "trading", "profit", "loan", "emi",
}

MARKETPLACE_KEYWORDS = {
    "deal", "offer", "coupon", "free", "buy", "sell", "marketplace", "olx",
}

CHANNEL_KEYWORDS = {
    "whatsapp", "telegram", "sms", "email",
}

STATUS_KEYWORDS = {
    "blocked", "suspended", "arrested", "police", "cbi", "fraud", "illegal", "warrant",
    "seized", "compromised", "verify", "confirm", "update", "kyc", "otp", "pin", "password",
    "verification code", "screen share", "bank manager", "customer care", "support", "helpline",
    "toll free", "rbi", "government", "income tax", "gst", "claim", "pending", "approved", "eligible",
}


def build_keyword_message(keyword: str) -> str:
    if keyword in AUTHORITY_KEYWORDS:
        return f"Caller claims to be {keyword} and asked for verification."
    if keyword in TECH_KEYWORDS:
        return f"Install {keyword} now to complete verification."
    if keyword in PAYMENT_KEYWORDS:
        return f"{keyword} required to complete refund, reply urgently."
    if keyword in IDENTITY_KEYWORDS:
        return f"Share {keyword} for kyc update to avoid disruption."
    if keyword in SIM_KEYWORDS:
        return f"Your {keyword} request is pending, confirm to proceed."
    if keyword in DELIVERY_KEYWORDS:
        return f"Parcel on hold, {keyword} required for release."
    if keyword in INVESTMENT_KEYWORDS:
        return f"{keyword} scheme promises profit, act today."
    if keyword in MARKETPLACE_KEYWORDS:
        return f"Limited {keyword} today, respond to proceed."
    if keyword in CHANNEL_KEYWORDS:
        return f"Reply on {keyword} to complete verification."
    if keyword in STATUS_KEYWORDS:
        return f"Notice: {keyword} detected, respond to verify."
    return f"{keyword} required to continue."


class TestBulkExtraction:
    """High-volume regression coverage for extraction helpers."""

    @pytest.mark.parametrize("user,handle", BULK_UPI_CASES)
    def test_bulk_upi_ids(self, user, handle):
        text = f"Please send to {user}@{handle} for verification"
        upis = extract_upi_ids(text)
        assert f"{user}@{handle}" in upis

    @pytest.mark.parametrize("phone", BULK_PHONE_NUMBERS)
    def test_bulk_phone_numbers(self, phone):
        text = f"Call {phone} immediately"
        phones = extract_phone_numbers(text)
        assert f"+91{phone}" in phones

    @pytest.mark.parametrize("ifsc", BULK_IFSC_CODES)
    def test_bulk_ifsc_codes(self, ifsc):
        text = f"Use IFSC code {ifsc} for transfer"
        codes = extract_ifsc_codes(text)
        assert ifsc in codes

    @pytest.mark.parametrize("url", BULK_URLS)
    def test_bulk_urls(self, url):
        text = f"Click here {url} to update"
        urls = extract_urls(text)
        assert url in urls

    @pytest.mark.parametrize("keyword", BULK_KEYWORDS)
    def test_bulk_keywords(self, keyword):
        text = build_keyword_message(keyword)
        keywords = extract_keywords(text)
        assert keyword in keywords

    def test_has_actionable_intel_with_phone(self):
        """Phone numbers alone should now trigger actionable intel."""
        assert has_actionable_intel({"phone_numbers": ["+919876543210"], "upi_ids": [],
                                     "bank_accounts": [], "phishing_links": [], "ifsc_codes": [],
                                     "aadhaar_numbers": [], "pan_numbers": []})

    def test_merge_preserves_new_fields(self):
        """merge_intelligence should preserve aadhaar, pan, mentioned_banks."""
        from models.intelligence import merge_intelligence
        intel1 = {"upi_ids": [], "bank_accounts": [], "emails": [], "ifsc_codes": [],
                  "phone_numbers": [], "phishing_links": [], "suspicious_keywords": [],
                  "fake_credentials": [], "aadhaar_numbers": ["432187652109"],
                  "pan_numbers": [], "mentioned_banks": ["sbi"]}
        intel2 = {"upi_ids": [], "bank_accounts": [], "emails": [], "ifsc_codes": [],
                  "phone_numbers": [], "phishing_links": [], "suspicious_keywords": [],
                  "fake_credentials": [], "aadhaar_numbers": [],
                  "pan_numbers": ["ABCDE1234F"], "mentioned_banks": ["hdfc"]}
        merged = merge_intelligence(intel1, intel2)
        assert "432187652109" in merged["aadhaar_numbers"]
        assert "ABCDE1234F" in merged["pan_numbers"]
        assert "sbi" in merged["mentioned_banks"]
        assert "hdfc" in merged["mentioned_banks"]

    def test_new_scam_keywords_detected(self):
        """New keywords like sim swap, biometric, aadhaar number should be detected."""
        from models.intelligence import extract_keywords
        kw1 = extract_keywords("Your SIM card will be deactivate unless you verify biometric")
        assert "sim card" in kw1
        assert "deactivate" in kw1
        assert "biometric" in kw1

    def test_style_switch_detection(self):
        """Conversation analyzer should detect when scammer changes tactics."""
        from core.conversation_analyzer import get_session_data, extract_scammer_intel
        session = get_session_data("test_style_switch_session_99")
        # First message: bank fraud
        extract_scammer_intel("Your SBI account is blocked. Share OTP now.", session)
        assert session["scam_type_detected"] == "bank_fraud"
        # Second message: switches to digital arrest
        extract_scammer_intel("This is CBI. You are under digital arrest.", session)
        assert session["scam_type_detected"] == "digital_arrest"
        assert session["previous_scam_type"] == "bank_fraud"
        assert session["style_switch_count"] == 1

    def test_bank_name_from_ifsc_prefix(self):
        """Bank names should be extracted from IFSC code prefixes."""
        from models.intelligence import extract_mentioned_banks
        # HDFC appears only in IFSC code, not as standalone text
        result = extract_mentioned_banks("Transfer to account 56789012345678, IFSC: HDFC0001234")
        assert "hdfc" in result
        # SBI from IFSC
        result2 = extract_mentioned_banks("IFSC: SBIN0005432")
        assert "sbi" in result2
        # PNB from IFSC
        result3 = extract_mentioned_banks("IFSC: PUNB0123400")
        assert "pnb" in result3
        # Multiple banks: one in text, one in IFSC
        result4 = extract_mentioned_banks("SBI said transfer to IFSC: HDFC0001234")
        assert "sbi" in result4
        assert "hdfc" in result4


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])

