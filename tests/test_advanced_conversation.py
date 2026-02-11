"""
🔥 Advanced Multi-Turn Scam Conversation Tester
Simulates GUVI's automated evaluation scenarios with full conversations.

Tests:
1. Full multi-turn scam conversations (5+ messages each)
2. Response JSON format compliance
3. Intelligence extraction accuracy across turns
4. Scam detection consistency
5. Non-scam message handling (trap detection)
6. Response quality (non-empty, varied, contextual)
7. Engagement metrics tracking

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
    """Validate the response has all GUVI-required fields. Returns list of issues."""
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
    
    # Intelligence structure - all should be arrays
    intel = response.get("extractedIntelligence", {})
    required_intel_fields = [
        "bankAccounts", "upiIds", "phishingLinks",
        "phoneNumbers", "suspiciousKeywords"
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
    """Print a compact intelligence summary."""
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
    {
        "name": "🏦 Bank Fraud - SBI Account Block (5 turns)",
        "session_id": "adv-test-bank-fraud-001",
        "turns": [
            "Hello, this is SBI Bank security department. Your account ending with 4532 has been flagged for suspicious activity. We need to verify your identity immediately.",
            "Sir, I understand your concern. But this is very urgent. Your account will be permanently blocked within 30 minutes. Please share your registered mobile number and OTP for verification.",
            "Sir, we have already verified your identity from our end. The OTP has been sent to your mobile +919876543210. Please share it now or your savings of Rs.2.5 lakhs will be frozen.",
            "Sir, I am Officer Rajesh Kumar, Employee ID EMP4521. My supervisor's number is 9988776655. Please cooperate. Share the 6-digit OTP now to secure your account SBIN0005432.",
            "This is your LAST WARNING. If you don't share the OTP in 2 minutes, we will file an FIR against you for money laundering. Your account 34567890123 will be seized by RBI.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["phoneNumbers"],  # Should extract phones at minimum
    },
    {
        "name": "💰 UPI Cashback Fraud (4 turns)",
        "session_id": "adv-test-upi-fraud-002",
        "turns": [
            "Congratulations! You have won a Rs.5000 cashback from Paytm. To claim, please verify your identity.",
            "Please send Rs.99 to our verification UPI: cashback.claim@fakeupi to process your Rs.5000 cashback. This is a limited time offer!",
            "Sir, I understand. Let me give you my direct number +918765432109. You can also verify at our website. Your cashback reference: CB-2026-8876.",
            "Okay sir, the last step is to scan this QR code OR send money to verify@fakebank. Your cashback of Rs.5000 will be credited in 2 minutes. Hurry, offer expires now!",
        ],
        "expect_scam": True,
        "expect_min_keywords": 4,
        "expect_intel_types": ["upiIds", "phoneNumbers"],
    },
    {
        "name": "👮 Digital Arrest Scam (5 turns)",
        "session_id": "adv-test-digital-arrest-003",
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
        "name": "📦 Courier Customs Scam (4 turns)",
        "session_id": "adv-test-courier-004",
        "turns": [
            "Dear customer, your FedEx parcel from UK has been seized by Indian Customs. Package ID: FDX-UK-99823. It contains illegal substances.",
            "To release your package, you need to pay customs clearance fee of Rs.15000. Otherwise the package will be destroyed and a case will be filed against you.",
            "Transfer the amount to bank account 56789012345678, IFSC: HDFC0001234. Contact our customs helpline: 9876123456 for tracking.",
            "This is your final notice. The parcel will be handed to narcotics division tomorrow. Pay immediately or face arrest. Email confirmation: customs.fedex@fakemail.com",
        ],
        "expect_scam": True,
        "expect_min_keywords": 5,
        "expect_intel_types": ["bankAccounts", "phoneNumbers"],
    },
    {
        "name": "🔗 Phishing Link KYC Scam (3 turns)",
        "session_id": "adv-test-kyc-phishing-005",
        "turns": [
            "Dear SBI customer, your KYC verification is pending. Your account will be blocked within 24 hours if not updated. Click: https://bit.ly/sbi-kyc-update",
            "Sir, this is mandatory RBI guideline. All accounts without updated KYC will be frozen. You can also update via tinyurl.com/sbi-kyc-urgent. Deadline is today.",
            "If you are unable to click the link, please share your Aadhaar number, PAN card, and account details. We will update KYC from our end. This is SBI customer care speaking.",
        ],
        "expect_scam": True,
        "expect_min_keywords": 4,
        "expect_intel_types": ["phishingLinks"],
    },
    {
        "name": "🛒 Refund Scam with Shortener URLs (3 turns)",  
        "session_id": "adv-test-refund-006",
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
        "name": "✅ Non-Scam Trap Message (legitimate conversation)",
        "session_id": "adv-test-legit-007",
        "turns": [
            "Hello uncle ji, how are you? This is your neighbor Priya. I wanted to ask about the community meeting tomorrow.",
            "Yes uncle, the meeting is at 5 PM in the park. Aunty said she will bring samosas. Weather is very nice today, isn't it?",
        ],
        "expect_scam": False,
        "expect_min_keywords": 0,
        "expect_intel_types": [],
    },
]


def run_scenario(scenario: dict) -> dict:
    """Run a full multi-turn conversation scenario and return results."""
    results = {
        "name": scenario["name"],
        "passed": True,
        "issues": [],
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
        
        # Validate JSON format
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
        
        # Check scam detection
        if scenario["expect_scam"] and not final_scam:
            results["issues"].append("SCAM NOT DETECTED in final response!")
            results["passed"] = False
        elif not scenario["expect_scam"] and final_scam:
            results["issues"].append("FALSE POSITIVE: Non-scam flagged as scam!")
            results["passed"] = False
        
        # Check minimum keywords
        kw_count = len(final_intel.get("suspiciousKeywords", []))
        if kw_count < scenario["expect_min_keywords"]:
            results["issues"].append(
                f"Only {kw_count} keywords found, expected ≥{scenario['expect_min_keywords']}"
            )
            results["passed"] = False
        
        # Check expected intel types
        for intel_type in scenario["expect_intel_types"]:
            if not final_intel.get(intel_type):
                results["issues"].append(f"Expected {intel_type} but got empty list")
                results["passed"] = False
        
        # Check reply variety (not all same reply)
        replies = [t["reply"] for t in results["turns"]]
        unique_replies = set(replies)
        if len(results["turns"]) >= 3 and len(unique_replies) < 2:
            results["issues"].append("All replies are identical — no variety!")
            results["passed"] = False
    
    # Print summary
    print(f"\n  {'─'*50}")
    if results["passed"]:
        print(f"  {GREEN}{BOLD}✅ SCENARIO PASSED{RESET} ({results['total_time']}s)")
    else:
        print(f"  {RED}{BOLD}❌ SCENARIO FAILED{RESET} ({results['total_time']}s)")
        for issue in results["issues"]:
            print(f"  {RED}  ⚠ {issue}{RESET}")
    
    return results


def main():
    print(f"\n{BOLD}{CYAN}{'='*70}")
    print(f"  🔥 ADVANCED MULTI-TURN SCAM CONVERSATION TESTER")
    print(f"  Simulating GUVI Automated Evaluation Scenarios")
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
    
    print(f"\n{'='*70}")
    
    # Show detailed intelligence from last scam scenario
    last_scam = None
    for r in all_results:
        if r["final_response"] and r["final_response"].get("scamDetected"):
            last_scam = r
    
    if last_scam:
        print(f"\n{BOLD}📊 Sample Full Response (from: {last_scam['name']}):{RESET}")
        print(json.dumps(last_scam["final_response"], indent=2, ensure_ascii=False))
    
    print()
    
    # Exit code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
