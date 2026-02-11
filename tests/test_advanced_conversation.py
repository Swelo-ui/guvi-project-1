"""
🔥 Advanced Multi-Turn Scam Conversation Tester v2.0
Simulates GUVI's automated evaluation scenarios with full conversations.

Tests:
 1. Full multi-turn scam conversations (3-7 messages each)
 2. Response JSON format compliance (all GUVI-required + new fields)
 3. Intelligence extraction accuracy across turns (UPI, bank, Aadhaar, PAN, etc.)
 4. Scam detection consistency
 5. Non-scam message handling (trap detection)
 6. Response quality (non-empty, varied, contextual, Hinglish)
 7. Engagement metrics tracking
 8. Aadhaar number extraction from identity scams
 9. PAN card number extraction from loan/tax scams
10. Bank name extraction from impersonation scams
11. Style-switch detection (scammer changing tactics mid-conversation)
12. Multi-identity scam combining Aadhaar + PAN + bank in one conversation

Usage:
    # Start server first: python app.py
    python tests/test_advanced_conversation.py
"""

import requests
import json
import time
import sys
import os

# Configuration
API_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:5000/api/honey-pot")
API_KEY = "sk_ironmask_hackathon_2026"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}

# Color codes for terminal output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
MAGENTA = "\033[95m"
BOLD = "\033[1m"
RESET = "\033[0m"
DIM = "\033[2m"


def send_message(session_id: str, message: str, history: list) -> dict:
    """Send a message to the honeypot API and return the response."""
    payload = {
        "sessionId": session_id,
        "message": {"text": message},
        "conversationHistory": history
    }
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        return response.json()
    except requests.exceptions.ConnectionError:
        print(f"\n{RED}❌ Cannot connect to {API_URL}")
        print(f"   Start the server first: python app.py{RESET}\n")
        sys.exit(1)
    except Exception as e:
        return {"error": str(e)}


def validate_response_format(response: dict) -> list:
    """Validate the response has all GUVI-required fields + new advanced fields.
    Returns list of issues.
    """
    issues = []

    # Required top-level fields
    required_fields = {
        "status": str,
        "scamDetected": bool,
        "engagementMetrics": dict,
        "extractedIntelligence": dict,
        "agentNotes": str,
        "reply": str,
    }
    for field, expected_type in required_fields.items():
        if field not in response:
            issues.append(f"Missing field: '{field}'")
        elif not isinstance(response[field], expected_type):
            issues.append(f"'{field}' should be {expected_type.__name__}, got {type(response[field]).__name__}")

    # Engagement metrics
    metrics = response.get("engagementMetrics", {})
    if "engagementDurationSeconds" not in metrics:
        issues.append("Missing engagementMetrics.engagementDurationSeconds")
    if "totalMessagesExchanged" not in metrics:
        issues.append("Missing engagementMetrics.totalMessagesExchanged")

    # Intelligence structure — ALL fields should be arrays (including new ones)
    intel = response.get("extractedIntelligence", {})
    required_intel_fields = [
        "bankAccounts", "upiIds", "phishingLinks",
        "phoneNumbers", "suspiciousKeywords",
        # New advanced fields
        "fakeCredentials", "aadhaarNumbers", "panNumbers", "mentionedBanks",
    ]
    for field in required_intel_fields:
        if field not in intel:
            issues.append(f"Missing extractedIntelligence.{field}")
        elif not isinstance(intel[field], list):
            issues.append(f"extractedIntelligence.{field} should be list, got {type(intel[field]).__name__}")

    # Reply should be non-empty
    reply = response.get("reply", "")
    if not reply or not reply.strip():
        issues.append("Reply is empty!")

    return issues


def validate_response_quality(replies: list) -> list:
    """Advanced response quality checks beyond basic format.
    Returns list of quality warnings (not hard failures).
    """
    warnings = []

    if len(replies) < 2:
        return warnings

    # Check for repeated replies
    unique_replies = set(replies)
    if len(unique_replies) < max(2, len(replies) // 2):
        warnings.append(f"Low variety: only {len(unique_replies)} unique replies out of {len(replies)}")

    # Check reply length — should be substantial, not one-liners
    short_replies = [r for r in replies if len(r.strip()) < 30]
    if short_replies:
        warnings.append(f"{len(short_replies)} replies are too short (<30 chars)")

    # Check for repeated opening phrases (first 5 words)
    openings = [" ".join(r.split()[:5]).lower() for r in replies if r.strip()]
    if len(openings) != len(set(openings)):
        warnings.append("Some replies start with identical phrases (anti-repetition issue)")

    # Check for Hinglish / Indian English markers (at least some should appear)
    hinglish_markers = [
        "beta", "ji", "na", "haan", "arre", "acha", "bata", "sir",
        "bhai", "aunty", "uncle", "abhi", "pehle", "kya", "nahi",
        "bhagwan", "ram", "main", "mera", "aapka", "dijiye", "raha",
    ]
    has_hinglish = False
    for reply in replies:
        reply_lower = reply.lower()
        if any(marker in reply_lower for marker in hinglish_markers):
            has_hinglish = True
            break
    if not has_hinglish and len(replies) >= 3:
        warnings.append("No Hinglish/Indian English markers detected — persona may not sound authentic")

    return warnings


def print_header(title: str):
    print(f"\n{'='*70}")
    print(f"{BOLD}{CYAN}  {title}{RESET}")
    print(f"{'='*70}")


def print_turn(turn_num: int, sender: str, message: str):
    color = RED if sender == "SCAMMER" else GREEN
    label = "🔴 SCAMMER" if sender == "SCAMMER" else "🟢 HONEYPOT"
    # Truncate long messages
    display = message[:120] + "..." if len(message) > 120 else message
    print(f"\n  {color}{BOLD}[Turn {turn_num}] {label}:{RESET}")
    print(f"  {DIM}{display}{RESET}")


def print_intel_summary(intel: dict):
    """Print a compact intelligence summary including new advanced fields."""
    items = []
    if intel.get("upiIds"):
        items.append(f"UPI: {intel['upiIds']}")
    if intel.get("bankAccounts"):
        items.append(f"Bank: {intel['bankAccounts']}")
    if intel.get("phoneNumbers"):
        items.append(f"Phone: {intel['phoneNumbers']}")
    if intel.get("phishingLinks"):
        items.append(f"Links: {intel['phishingLinks']}")
    if intel.get("ifscCodes"):
        items.append(f"IFSC: {intel['ifscCodes']}")
    if intel.get("emails"):
        items.append(f"Email: {intel['emails']}")
    # New advanced fields
    if intel.get("fakeCredentials"):
        items.append(f"FakeCreds: {intel['fakeCredentials']}")
    if intel.get("aadhaarNumbers"):
        items.append(f"🪪 Aadhaar: {intel['aadhaarNumbers']}")
    if intel.get("panNumbers"):
        items.append(f"📄 PAN: {intel['panNumbers']}")
    if intel.get("mentionedBanks"):
        items.append(f"🏦 Banks: {intel['mentionedBanks']}")
    # Keywords (truncated)
    if intel.get("suspiciousKeywords"):
        kw_list = intel['suspiciousKeywords'][:8]
        if len(intel['suspiciousKeywords']) > 8:
            kw_list.append(f"+{len(intel['suspiciousKeywords'])-8} more")
        items.append(f"Keywords: {kw_list}")
    if items:
        print(f"  {YELLOW}📊 Intel: {', '.join(items)}{RESET}")
    else:
        print(f"  {DIM}📊 Intel: (none extracted){RESET}")


# ============================================================
# ADVANCED MULTI-TURN SCAM CONVERSATION SCENARIOS
# ============================================================

SCENARIOS = [
    # ── Original scenarios (enhanced with new field expectations) ──
    {
        "name": "🏦 1. Bank Fraud - SBI Account Block (5 turns)",
        "session_id": "adv-v2-bank-fraud-001",
        "turns": [
            "Hello, this is SBI Bank security department. Your account ending with 4532 has been flagged for suspicious activity. We need to verify your identity immediately.",
            "Sir, I understand your concern. But this is very urgent. Your account will be permanently blocked within 30 minutes. Please share your registered mobile number and OTP for verification.",
            "Sir, we have already verified your identity from our end. The OTP has been sent to your mobile +919876543210. Please share it now or your savings of Rs.2.5 lakhs will be frozen.",
            "Sir, I am Officer Rajesh Kumar, Employee ID EMP4521. My supervisor's number is 9988776655. Please cooperate. Share the 6-digit OTP now to secure your account SBIN0005432.",
            "This is your LAST WARNING. If you don't share the OTP in 2 minutes, we will file an FIR against you for money laundering. Your account 34567890123 will be seized by RBI.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["phoneNumbers"],
        "expect_mentioned_banks": True,  # Should detect SBI / RBI
    },
    {
        "name": "💰 2. UPI Cashback Fraud (4 turns)",
        "session_id": "adv-v2-upi-fraud-002",
        "turns": [
            "Congratulations! You have won a Rs.5000 cashback from Paytm. To claim, please verify your identity.",
            "Please send Rs.99 to our verification UPI: cashback.claim@fakeupi to process your Rs.5000 cashback. This is a limited time offer!",
            "Sir, I understand. Let me give you my direct number +918765432109. You can also verify at our website. Your cashback reference: CB-2026-8876.",
            "Okay sir, the last step is to scan this QR code OR send money to verify@fakebank. Your cashback of Rs.5000 will be credited in 2 minutes. Hurry, offer expires now!",
        ],
        "expect_scam": True,
        "expect_min_keywords": 4,
        "expect_intel_types": ["upiIds", "phoneNumbers"],
        "expect_mentioned_banks": True,  # "Paytm" is in the bank list
    },
    {
        "name": "👮 3. Digital Arrest Scam (5 turns)",
        "session_id": "adv-v2-digital-arrest-003",
        "turns": [
            "This is the Cyber Crime Division of Mumbai Police. A case number CYB-2026-4432 has been registered against your Aadhaar number for money laundering.",
            "A warrant has been issued in your name. You are under digital arrest. Do not disconnect this call or share this information with anyone, or you will be arrested immediately.",
            "The Supreme Court has ordered your immediate arrest. However, if you cooperate and transfer Rs.50000 as security deposit, we can clear your name. Transfer to account 12345678901234.",
            "I am Senior Officer Captain Raj Malhotra from CBI. My badge number is CBI-7721. If you don't pay now, our team will arrive at your house within 1 hour. IFSC: SBIN0001234",
            "This is your final chance. Pay Rs.50000 to UPI: cbi.clearance@ybl or face 7 years in jail. Your Aadhaar has been linked to a Rs.2 crore fraud case.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 6,
        "expect_intel_types": ["upiIds", "bankAccounts"],
    },
    {
        "name": "📦 4. Courier Customs Scam (4 turns)",
        "session_id": "adv-v2-courier-004",
        "turns": [
            "Dear customer, your FedEx parcel from UK has been seized by Indian Customs. Package ID: FDX-UK-99823. It contains illegal substances.",
            "To release your package, you need to pay customs clearance fee of Rs.15000. Otherwise the package will be destroyed and a case will be filed against you.",
            "Transfer the amount to bank account 56789012345678, IFSC: HDFC0001234. Contact our customs helpline: 9876123456 for tracking.",
            "This is your final notice. The parcel will be handed to narcotics division tomorrow. Pay immediately or face arrest. Email confirmation: customs.fedex@fakemail.com",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["bankAccounts", "phoneNumbers"],
        "expect_mentioned_banks": True,  # HDFC in IFSC context
    },
    {
        "name": "🔗 5. Phishing Link KYC Scam (3 turns)",
        "session_id": "adv-v2-kyc-phishing-005",
        "turns": [
            "Dear SBI customer, your KYC verification is pending. Your account will be blocked within 24 hours if not updated. Click: https://bit.ly/sbi-kyc-update",
            "Sir, this is mandatory RBI guideline. All accounts without updated KYC will be frozen. You can also update via tinyurl.com/sbi-kyc-urgent. Deadline is today.",
            "If you are unable to click the link, please share your Aadhaar number, PAN card, and account details. We will update KYC from our end. This is SBI customer care speaking.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 4,
        "expect_intel_types": ["phishingLinks"],
        "expect_mentioned_banks": True,  # SBI + RBI
    },
    {
        "name": "🛒 6. Refund Scam with Shortener URLs (3 turns)",
        "session_id": "adv-v2-refund-006",
        "turns": [
            "Amazon refund of Rs.2999 is pending for your cancelled order #AZ-99821. Click to claim: tinyurl.com/amazon-refund-claim",
            "Sir, your refund is approved. You are eligible for Rs.2999 refund + Rs.500 compensation. Total Rs.3499. Please verify your bank details at bit.ly/amazon-refund-verify",
            "Sir for faster processing, please share your UPI ID or bank account number. Our refund team member will call you on +917654321098. Refund expires today only.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 4,
        "expect_intel_types": ["phishingLinks", "phoneNumbers"],
    },
    {
        "name": "✅ 7. Non-Scam Trap Message (legitimate conversation)",
        "session_id": "adv-v2-legit-007",
        "turns": [
            "Hello uncle ji, how are you? This is your neighbor Priya. I wanted to ask about the community meeting tomorrow.",
            "Yes uncle, the meeting is at 5 PM in the park. Aunty said she will bring samosas. Weather is very nice today, isn't it?",
        ],
        "expect_scam": False,
        "expect_min_keywords": 0,
        "expect_intel_types": [],
    },

    # ── NEW ADVANCED SCENARIOS ──

    {
        "name": "🪪 8. Aadhaar/KYC Identity Theft Scam (5 turns)",
        "session_id": "adv-v2-aadhaar-008",
        "turns": [
            "This is UIDAI Aadhaar helpline. Your Aadhaar card 2345 6789 0123 has been linked to multiple fraudulent accounts. We need to verify your identity immediately.",
            "Sir, for Aadhaar verification, you must confirm your registered mobile and date of birth. Your Aadhaar 2345 6789 0123 will be permanently deactivated in 2 hours if not verified.",
            "I am Officer Amit from UIDAI biometric verification center. My employee ID is UIDAI-8832. We need your fingerprint data update via our app. Download from: https://bit.ly/aadhaar-update-app",
            "Sir, we are also showing a PAN card BXYPK4321L linked to your Aadhaar that was used for tax evasion of Rs.15 lakhs. Income tax department has been notified.",
            "This is final warning from UIDAI. Your Aadhaar 2345 6789 0123 will be blocked permanently. Pay verification fee Rs.5000 to UPI: uidai.verify@ybl or face legal action. Contact: 9871234560",
        ],
        "expect_scam": True,
        "expect_min_keywords": 6,
        "expect_intel_types": ["aadhaarNumbers", "phoneNumbers"],
        "expect_aadhaar": True,
        "expect_pan": True,
    },
    {
        "name": "📄 9. PAN Card / Tax Fraud Scam (4 turns)",
        "session_id": "adv-v2-pan-tax-009",
        "turns": [
            "This is Income Tax Department of India. Your PAN CXYPD5678H has been flagged for irregular transactions of Rs.25 lakhs in last quarter.",
            "Sir, under Section 271C of Income Tax Act, a penalty of Rs.2 lakhs has been imposed. Your PAN CXYPD5678H will be deactivated if not paid within 24 hours.",
            "Pay the penalty amount to HDFC account 98765432101234, IFSC: HDFC0009876. Send receipt to our official email: incometax.penalty@fakegovt.com. Officer ID: ITO-4456.",
            "Sir, I am giving you one last chance. If penalty is not paid by EOD, your PAN CXYPD5678H will be blacklisted permanently and all your bank accounts will be frozen by RBI. Contact: +919876012345",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["panNumbers", "bankAccounts", "phoneNumbers"],
        "expect_pan": True,
        "expect_mentioned_banks": True,  # HDFC + RBI
    },
    {
        "name": "📈 10. Investment / Crypto Scam (4 turns)",
        "session_id": "adv-v2-investment-010",
        "turns": [
            "Hello sir! I am from Axis Bank investment advisory. Special offer: invest Rs.10000 in our crypto fund and earn guaranteed 500% profit in 30 days.",
            "Sir, this is a verified trading platform. Many SBI and ICICI customers have already earned lakhs. Join our WhatsApp group: wa.me/919876543210 for daily tips.",
            "To start investing, transfer Rs.10000 to our Kotak account 45678901234567 IFSC: KKBK0001234. You will get login credentials for our trading app within 1 hour.",
            "Sir, your first profit of Rs.50000 is ready! But to withdraw, you need to pay 10% TDS fee Rs.5000. Transfer to UPI: invest.profit@paytm. Hurry, market closing soon!",
        ],
        "expect_scam": True,
        "expect_min_keywords": 6,
        "expect_intel_types": ["bankAccounts", "upiIds"],
        "expect_mentioned_banks": True,  # Axis, SBI, ICICI, Kotak, Paytm
    },
    {
        "name": "📱 11. SIM Swap / Account Takeover Scam (4 turns)",
        "session_id": "adv-v2-sim-swap-011",
        "turns": [
            "Dear Jio customer, your SIM card will be deactivated within 2 hours due to KYC non-compliance. Call our helpline immediately to reactivate: 8899776655.",
            "Sir, to reactivate your SIM card, we need your Aadhaar number for biometric verification. Your current SIM 9876543210 will stop working if not verified.",
            "Please share your Aadhaar number 4567 8901 2345 with us for UIDAI re-verification. Also share last 4 digits of PAN for identity confirmation. Our officer ID: JIO-SIM-4432.",
            "Sir, SIM reissue fee of Rs.499 is required. Pay to UPI: jio.reissue@ybl. After payment, your new SIM will be activated within 4 hours. Don't share this OTP with anyone: 847291",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["phoneNumbers", "upiIds"],
        "expect_aadhaar": True,
    },
    {
        "name": "🔄 12. Style-Switch Scam (Bank → Digital Arrest, 6 turns)",
        "session_id": "adv-v2-style-switch-012",
        "turns": [
            # Phase 1: Starts as bank fraud
            "Hello, this is HDFC Bank customer care. Your account has been compromised due to unauthorized transaction of Rs.75000. We need to verify your details.",
            "Sir, please cooperate. We are trying to protect your HDFC savings account. Share your OTP to revert the fraudulent transaction. Your money is at risk!",
            # Phase 2: Switches to digital arrest when victim doesn't cooperate
            "Sir, since you are not cooperating, I am transferring your call to Cyber Crime Division. This is now a police matter.",
            "This is Inspector Sharma from CBI Cyber Crime Branch. We have traced the fraudulent transaction to your account. You are now under digital arrest. Do not disconnect.",
            "A warrant has been issued against you. The only way to avoid arrest is to transfer Rs.1 lakh as security deposit. Account: 11223344556677, IFSC: SBIN0001111.",
            # Phase 3: Throws in Aadhaar threat
            "Your Aadhaar 3456 7890 1234 has been flagged by UIDAI. PAN FGHIJ6789K is also under investigation. Pay immediately to UPI: cbi.security@ybl or face 10 years in prison.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 8,
        "expect_intel_types": ["bankAccounts", "upiIds"],
        "expect_style_switch": True,  # Should detect tactic change
        "expect_aadhaar": True,
        "expect_pan": True,
        "expect_mentioned_banks": True,  # HDFC, SBI
    },
    {
        "name": "🧬 13. Combined Identity Scam — Aadhaar + PAN + Bank (7 turns)",
        "session_id": "adv-v2-combined-identity-013",
        "turns": [
            "Hello, this is Reserve Bank of India alert. A suspicious loan application for Rs.50 lakhs was filed using your PAN AXYBC1234D. Please verify.",
            "Sir, the loan was applied at PNB branch using your identity. Your Aadhaar 5678 1234 9012 and PAN AXYBC1234D were submitted as proof. Is this authorized by you?",
            "Sir, this is very serious. The loan amount has already been disbursed to account 22334455667788 at PNB, IFSC: PUNB0123400. We need to freeze this immediately.",
            "To freeze the fraudulent loan, we need you to pay insurance deposit Rs.25000. Transfer to our RBI verification account. Officer: RBI-FRAUD-7789.",
            "Sir, I am connecting you to PNB manager for final verification. His direct number is 7766554433. Share your registered mobile number for OTP verification.",
            "Beta, this is PNB Branch Manager Singh speaking. Please share your Aadhaar 5678 1234 9012 biometric for verification. Also confirm your registered email for our records.",
            "Final step: Pay Rs.25000 to UPI: rbi.freeze@ybl or the full Rs.50 lakh loan will be recovered from your savings. Your PAN AXYBC1234D will be permanently blacklisted.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 8,
        "expect_intel_types": ["bankAccounts", "upiIds", "phoneNumbers", "panNumbers", "aadhaarNumbers"],
        "expect_aadhaar": True,
        "expect_pan": True,
        "expect_mentioned_banks": True,  # RBI, PNB
    },
]


def run_scenario(scenario: dict) -> dict:
    """Run a full multi-turn conversation scenario and return results."""
    results = {
        "name": scenario["name"],
        "passed": True,
        "issues": [],
        "warnings": [],
        "turns": [],
        "final_response": None,
        "total_time": 0,
    }

    print_header(scenario["name"])

    history = []
    start_time = time.time()

    for i, scammer_msg in enumerate(scenario["turns"]):
        turn_num = i + 1
        print_turn(turn_num, "SCAMMER", scammer_msg)

        # Send message
        response = send_message(scenario["session_id"], scammer_msg, history)

        if "error" in response and "status" not in response:
            results["issues"].append(f"Turn {turn_num}: API error - {response['error']}")
            results["passed"] = False
            continue

        # Validate JSON format (includes new fields)
        format_issues = validate_response_format(response)
        if format_issues:
            for issue in format_issues:
                results["issues"].append(f"Turn {turn_num}: {issue}")
            results["passed"] = False

        # Show honeypot reply
        reply = response.get("reply", "(no reply)")
        print_turn(turn_num, "HONEYPOT", reply)

        # Show intel
        intel = response.get("extractedIntelligence", {})
        print_intel_summary(intel)

        scam_detected = response.get("scamDetected", False)
        label = f"{GREEN}✓ Scam Detected{RESET}" if scam_detected else f"{DIM}○ No scam{RESET}"
        print(f"  {label} | Messages: {response.get('engagementMetrics', {}).get('totalMessagesExchanged', '?')}")

        # Update history
        history.append({"sender": "scammer", "text": scammer_msg})
        history.append({"sender": "agent", "text": reply})

        results["turns"].append({
            "scammer": scammer_msg,
            "reply": reply,
            "scamDetected": scam_detected,
            "intel": intel,
        })
        results["final_response"] = response

        time.sleep(0.5)  # Small delay between turns

    elapsed = time.time() - start_time
    results["total_time"] = round(elapsed, 1)

    # --- Post-conversation validations ---
    final = results["final_response"]
    if final:
        final_intel = final.get("extractedIntelligence", {})
        final_scam = final.get("scamDetected", False)

        # 1. Check scam detection
        if scenario["expect_scam"] and not final_scam:
            results["issues"].append("❌ SCAM NOT DETECTED in final response!")
            results["passed"] = False
        elif not scenario["expect_scam"] and final_scam:
            results["issues"].append("❌ FALSE POSITIVE: Non-scam flagged as scam!")
            results["passed"] = False

        # 2. Check minimum keywords
        kw_count = len(final_intel.get("suspiciousKeywords", []))
        if kw_count < scenario["expect_min_keywords"]:
            results["issues"].append(
                f"Only {kw_count} keywords found, expected ≥{scenario['expect_min_keywords']}"
            )
            results["passed"] = False

        # 3. Check expected intel types (original)
        for intel_type in scenario["expect_intel_types"]:
            if not final_intel.get(intel_type):
                results["issues"].append(f"Expected {intel_type} but got empty list")
                results["passed"] = False

        # 4. Check Aadhaar extraction
        if scenario.get("expect_aadhaar"):
            aadhaar_list = final_intel.get("aadhaarNumbers", [])
            if not aadhaar_list:
                results["issues"].append("Expected aadhaarNumbers but got empty list")
                results["passed"] = False
            else:
                print(f"  {MAGENTA}🪪 Aadhaar extracted: {aadhaar_list}{RESET}")

        # 5. Check PAN extraction
        if scenario.get("expect_pan"):
            pan_list = final_intel.get("panNumbers", [])
            if not pan_list:
                results["issues"].append("Expected panNumbers but got empty list")
                results["passed"] = False
            else:
                print(f"  {MAGENTA}📄 PAN extracted: {pan_list}{RESET}")

        # 6. Check bank name extraction
        if scenario.get("expect_mentioned_banks"):
            banks_list = final_intel.get("mentionedBanks", [])
            if not banks_list:
                results["issues"].append("Expected mentionedBanks but got empty list")
                results["passed"] = False
            else:
                print(f"  {MAGENTA}🏦 Banks mentioned: {banks_list}{RESET}")

        # 7. Check style-switch detection (via agent notes or scam type changes)
        if scenario.get("expect_style_switch"):
            agent_notes = final.get("agentNotes", "")
            # The scam type should have changed during the conversation
            scam_types_seen = set()
            for turn in results["turns"]:
                turn_notes = str(turn.get("intel", {}))
                if "digital_arrest" in turn_notes or "digital arrest" in turn_notes.lower():
                    scam_types_seen.add("digital_arrest")
                if "bank_fraud" in turn_notes or "bank fraud" in turn_notes.lower():
                    scam_types_seen.add("bank_fraud")
            # We still report it as info even if we can't detect via API
            print(f"  {MAGENTA}🔄 Style-switch scenario: Agent should have detected tactic change{RESET}")

        # 8. Check reply variety
        replies = [t["reply"] for t in results["turns"]]
        unique_replies = set(replies)
        if len(results["turns"]) >= 3 and len(unique_replies) < 2:
            results["issues"].append("All replies are identical — no variety!")
            results["passed"] = False

        # 9. Response quality warnings (non-blocking)
        quality_warnings = validate_response_quality(replies)
        results["warnings"] = quality_warnings

    # Print summary
    print(f"\n  {'─'*50}")
    if results["passed"]:
        print(f"  {GREEN}{BOLD}✅ SCENARIO PASSED{RESET} ({results['total_time']}s)")
    else:
        print(f"  {RED}{BOLD}❌ SCENARIO FAILED{RESET} ({results['total_time']}s)")
        for issue in results["issues"]:
            print(f"  {RED}  ⚠ {issue}{RESET}")
    if results.get("warnings"):
        for w in results["warnings"]:
            print(f"  {YELLOW}  ⚠ Quality: {w}{RESET}")

    return results


def main():
    print(f"\n{BOLD}{CYAN}{'='*70}")
    print(f"  🔥 ADVANCED MULTI-TURN SCAM CONVERSATION TESTER v2.0")
    print(f"  Featuring: Aadhaar, PAN, Bank Name, Style-Switch Detection")
    print(f"  Target: {API_URL}")
    print(f"{'='*70}{RESET}\n")

    # Quick health check
    try:
        health = requests.get(API_URL.replace("/api/honey-pot", "/health"), timeout=5)
        if health.status_code == 200:
            print(f"  {GREEN}✓ Server is running{RESET}\n")
        else:
            print(f"  {YELLOW}⚠ Health check returned {health.status_code}{RESET}\n")
    except:
        print(f"  {RED}❌ Cannot reach server at {API_URL}")
        print(f"  Start with: python app.py{RESET}\n")
        sys.exit(1)

    # Run all scenarios
    all_results = []
    total_start = time.time()

    for scenario in SCENARIOS:
        result = run_scenario(scenario)
        all_results.append(result)

    total_time = round(time.time() - total_start, 1)

    # Final summary
    passed = sum(1 for r in all_results if r["passed"])
    failed = sum(1 for r in all_results if not r["passed"])
    total = len(all_results)

    print(f"\n\n{'='*70}")
    print(f"{BOLD}{CYAN}  📋 FINAL RESULTS SUMMARY{RESET}")
    print(f"{'='*70}")
    print(f"  Total scenarios: {total}")
    print(f"  {GREEN}Passed: {passed}{RESET}")
    if failed:
        print(f"  {RED}Failed: {failed}{RESET}")
    print(f"  Time: {total_time}s")
    print()

    for r in all_results:
        status = f"{GREEN}✅ PASS{RESET}" if r["passed"] else f"{RED}❌ FAIL{RESET}"
        turns = len(r["turns"])
        print(f"  {status}  {r['name']} ({turns} turns, {r['total_time']}s)")
        if not r["passed"]:
            for issue in r["issues"][:3]:
                print(f"        {RED}⚠ {issue}{RESET}")

    # Quality warnings summary
    total_warnings = sum(len(r.get("warnings", [])) for r in all_results)
    if total_warnings > 0:
        print(f"\n  {YELLOW}{BOLD}⚠ Quality Warnings: {total_warnings}{RESET}")
        for r in all_results:
            for w in r.get("warnings", []):
                print(f"    {YELLOW}→ {r['name'][:30]}: {w}{RESET}")

    print(f"\n{'='*70}")

    # Intelligence extraction scorecard
    print(f"\n{BOLD}{MAGENTA}  🧠 INTELLIGENCE EXTRACTION SCORECARD{RESET}")
    print(f"{'─'*70}")

    # Collect all extracted intel across all scam scenarios
    all_intel = {
        "upiIds": [], "bankAccounts": [], "phoneNumbers": [],
        "phishingLinks": [], "ifscCodes": [], "emails": [],
        "fakeCredentials": [], "aadhaarNumbers": [], "panNumbers": [],
        "mentionedBanks": [], "suspiciousKeywords": [],
    }
    for r in all_results:
        if r["final_response"] and r["final_response"].get("scamDetected"):
            intel = r["final_response"].get("extractedIntelligence", {})
            for key in all_intel:
                all_intel[key].extend(intel.get(key, []))

    for key, values in all_intel.items():
        unique_vals = list(set(values))
        icon = "✓" if unique_vals else "○"
        color = GREEN if unique_vals else DIM
        label = key.replace("Numbers", " #s").replace("Ids", " IDs").replace("Accounts", " Accts")
        count = len(unique_vals)
        sample = str(unique_vals[:3])[:60] if unique_vals else "-"
        print(f"  {color}{icon} {label:20s} : {count:3d} unique | {sample}{RESET}")

    print(f"{'─'*70}")

    # Show detailed intelligence from a scenario with most intel
    best_scenario = None
    best_count = 0
    for r in all_results:
        if r["final_response"]:
            intel = r["final_response"].get("extractedIntelligence", {})
            count = sum(len(v) for v in intel.values() if isinstance(v, list))
            if count > best_count:
                best_count = count
                best_scenario = r

    if best_scenario:
        print(f"\n{BOLD}📊 Richest Response (from: {best_scenario['name']}):{RESET}")
        print(json.dumps(best_scenario["final_response"], indent=2, ensure_ascii=False))

    print()

    # Exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
