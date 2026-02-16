"""
🎯 GUVI Evaluation Scenario Test Suite
Tests the honeypot against the EXACT 3 scenarios GUVI uses for automated evaluation.

Scenarios:
  1. bank_fraud  - Bank account fraud with urgency tactics (SMS)
  2. upi_fraud   - UPI cashback scam (WhatsApp)
  3. phishing    - Phishing link with fake offer (Email)

Each scenario simulates multi-turn conversations where the scammer gradually
reveals fakeData items, mirroring GUVI's automated evaluator behavior.

Usage:
    # Local server (default):
    python tests/test_guvi_scenarios.py

    # Remote Render deployment:
    set TEST_API_URL=https://guvi-project-1-wefr.onrender.com/api/honey-pot
    python tests/test_guvi_scenarios.py
"""

import requests
import json
import time
import sys
import os

# ─── Configuration ──────────────────────────────────────────────────
API_URL = os.getenv("TEST_API_URL", "http://127.0.0.1:5000/api/honey-pot")
API_KEY = "sk_ironmask_hackathon_2026"
HEADERS = {"x-api-key": API_KEY, "Content-Type": "application/json"}

# Colors
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
M = "\033[95m"; B = "\033[1m"; D = "\033[2m"; X = "\033[0m"

# ─── GUVI Evaluation Scenarios (exact spec) ─────────────────────────

GUVI_SCENARIOS = [
    {
        "scenarioId": "bank_fraud",
        "name": "Bank Fraud Detection",
        "description": "Bank account fraud with urgency tactics",
        "scamType": "bank_fraud",
        "initialMessage": "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210"
        },
        # Multi-turn scammer messages that gradually reveal fakeData
        "scammerTurns": [
            # Turn 1: Initial message (from spec)
            "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
            # Turn 2: Pressure + reveals phone number
            "Sir, this is very urgent. I am calling from SBI fraud department. Call me back at +91-9876543210 to verify your account details.",
            # Turn 3: Reveals bank account number
            "Sir, we have detected suspicious transfer of Rs.50000 from your account 1234567890123456. Please share OTP to reverse this transaction immediately.",
            # Turn 4: Reveals UPI ID
            "If you cannot share OTP, please transfer Rs.1 as verification to our secure UPI: scammer.fraud@fakebank. This is mandatory for account recovery.",
            # Turn 5: Final pressure
            "This is your LAST WARNING. Your SBI account 1234567890123456 will be permanently blocked. Share OTP or pay via UPI scammer.fraud@fakebank NOW.",
        ],
        "expectedExtraction": {
            "phoneNumbers": ["+91-9876543210"],
            "bankAccounts": ["1234567890123456"],
            "upiIds": ["scammer.fraud@fakebank"],
            "mentionedBanks": ["sbi"],
            "minKeywords": 5,
        }
    },
    {
        "scenarioId": "upi_fraud",
        "name": "UPI Fraud Multi-turn",
        "description": "UPI fraud with cashback scam",
        "scamType": "upi_fraud",
        "initialMessage": "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109"
        },
        "scammerTurns": [
            # Turn 1: Initial cashback lure
            "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
            # Turn 2: Reveals phone number
            "Sir, this is Paytm official support. You can also contact us at +91-8765432109 for cashback verification. Offer expires in 30 minutes!",
            # Turn 3: Reveals UPI ID
            "To claim your Rs.5000 cashback, please send Rs.10 verification fee to our official UPI: cashback.scam@fakeupi. Amount will be refunded with cashback.",
            # Turn 4: Urgency push
            "Sir, only 5 minutes left! Send Rs.10 to cashback.scam@fakeupi or call +91-8765432109. Your Paytm cashback of Rs.5000 will expire!",
        ],
        "expectedExtraction": {
            "phoneNumbers": ["+91-8765432109"],
            "upiIds": ["cashback.scam@fakeupi"],
            "mentionedBanks": ["paytm"],
            "minKeywords": 4,
        }
    },
    {
        "scenarioId": "phishing_link",
        "name": "Phishing Link Detection",
        "description": "Phishing link with fake offer",
        "scamType": "phishing",
        "initialMessage": "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
        "metadata": {"channel": "Email", "language": "English", "locale": "IN"},
        "weight": 10,
        "maxTurns": 10,
        "fakeData": {
            "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
            "emailAddress": "offers@fake-amazon-deals.com"
        },
        "scammerTurns": [
            # Turn 1: Initial phishing
            "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
            # Turn 2: Reveals email
            "Sir, this is a verified offer from Amazon. For details, email us at offers@fake-amazon-deals.com or click http://amaz0n-deals.fake-site.com/claim?id=12345",
            # Turn 3: Additional pressure
            "HURRY! Only 3 iPhones left at Rs.999. Click http://amaz0n-deals.fake-site.com/claim?id=12345 NOW. Contact: offers@fake-amazon-deals.com for support.",
        ],
        "expectedExtraction": {
            "phishingLinks": ["http://amaz0n-deals.fake-site.com/claim?id=12345"],
            "emails": ["offers@fake-amazon-deals.com"],
            "minKeywords": 3,
        }
    }
]


# ─── Helpers ────────────────────────────────────────────────────────

def send_message(session_id, message, history, metadata=None):
    """Send a message to the honeypot API."""
    payload = {
        "sessionId": session_id,
        "message": {"text": message},
        "conversationHistory": history
    }
    if metadata:
        payload["metadata"] = metadata
    try:
        resp = requests.post(API_URL, headers=HEADERS, json=payload, timeout=30)
        return resp.json()
    except requests.exceptions.ConnectionError:
        print(f"\n{R}❌ Cannot connect to {API_URL}")
        print(f"   Start the server first: python app.py{X}\n")
        sys.exit(1)
    except Exception as e:
        return {"error": str(e)}


def validate_format(response):
    """Validate GUVI-required response format."""
    issues = []
    for field, typ in {"status": str, "scamDetected": bool, "engagementMetrics": dict,
                       "extractedIntelligence": dict, "agentNotes": str, "reply": str}.items():
        if field not in response:
            issues.append(f"Missing '{field}'")
        elif not isinstance(response[field], typ):
            issues.append(f"'{field}' wrong type: {type(response[field]).__name__}")

    metrics = response.get("engagementMetrics", {})
    for mf in ["engagementDurationSeconds", "totalMessagesExchanged"]:
        if mf not in metrics:
            issues.append(f"Missing engagementMetrics.{mf}")

    intel = response.get("extractedIntelligence", {})
    for field in ["bankAccounts", "upiIds", "phishingLinks", "phoneNumbers",
                   "suspiciousKeywords", "emails", "ifscCodes"]:
        if field not in intel:
            issues.append(f"Missing extractedIntelligence.{field}")
        elif not isinstance(intel[field], list):
            issues.append(f"extractedIntelligence.{field} not a list")

    if not response.get("reply", "").strip():
        issues.append("Reply is empty")
    return issues


def check_extraction(final_intel, expected, scenario_name):
    """Check if expected intelligence items were extracted."""
    issues = []

    for key in ["phoneNumbers", "bankAccounts", "upiIds", "phishingLinks", "emails", "emailAddresses"]:
        expected_items = expected.get(key, [])
        actual_items = [x.lower() for x in final_intel.get(key, [])]

        for item in expected_items:
            item_lower = item.lower()
            # Normalize phone for comparison
            if key == "phoneNumbers":
                item_clean = item_lower.replace("-", "").replace(" ", "")
                actual_clean = [a.replace("-", "").replace(" ", "") for a in actual_items]
                if item_clean not in actual_clean:
                    issues.append(f"Missing {key}: {item} (got: {final_intel.get(key, [])})")
            elif item_lower not in actual_items:
                issues.append(f"Missing {key}: {item} (got: {final_intel.get(key, [])})")

    # Check mentioned banks
    if "mentionedBanks" in expected:
        actual_banks = [b.lower() for b in final_intel.get("mentionedBanks", [])]
        for bank in expected["mentionedBanks"]:
            if bank.lower() not in actual_banks:
                issues.append(f"Missing mentionedBank: {bank} (got: {actual_banks})")

    # Check minimum keywords
    min_kw = expected.get("minKeywords", 0)
    actual_kw = len(final_intel.get("suspiciousKeywords", []))
    if actual_kw < min_kw:
        issues.append(f"Only {actual_kw} keywords, expected ≥{min_kw}")

    return issues


def print_turn(n, sender, msg):
    color = R if sender == "SCAMMER" else G
    icon = "🔴" if sender == "SCAMMER" else "🟢"
    display = msg[:130] + "..." if len(msg) > 130 else msg
    print(f"\n  {color}{B}[Turn {n}] {icon} {sender}:{X}")
    print(f"  {D}{display}{X}")


def print_intel(intel):
    """Compact intel summary."""
    items = []
    for key, label in [("upiIds", "UPI"), ("bankAccounts", "Bank"), ("phoneNumbers", "Phone"),
                        ("phishingLinks", "Links"), ("emails", "Email"), ("ifscCodes", "IFSC"),
                        ("mentionedBanks", "🏦Banks")]:
        vals = intel.get(key, [])
        if vals:
            items.append(f"{label}: {vals}")
    kws = intel.get("suspiciousKeywords", [])
    if kws:
        items.append(f"Keywords({len(kws)}): {kws[:6]}")
    if items:
        print(f"  {Y}📊 {', '.join(items)}{X}")
    else:
        print(f"  {D}📊 Intel: (none){X}")


# ─── Pre-flight: Regex Unit Validation ──────────────────────────────

def run_regex_preflight():
    """Test extraction functions directly against fakeData items."""
    print(f"\n{B}{M}{'='*70}")
    print(f"  🔬 PRE-FLIGHT: Regex Extraction Validation")
    print(f"{'='*70}{X}\n")

    try:
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
        from models.intelligence import (
            extract_upi_ids, extract_bank_accounts, extract_phone_numbers,
            extract_urls, extract_emails, extract_keywords, extract_mentioned_banks
        )
    except ImportError:
        print(f"  {Y}⚠ Cannot import intelligence module — skipping preflight{X}")
        return True

    tests = [
        ("bank_fraud: bank account", extract_bank_accounts,
         "transfer from account 1234567890123456", "1234567890123456"),
        ("bank_fraud: UPI ID", extract_upi_ids,
         "send to scammer.fraud@fakebank", "scammer.fraud@fakebank"),
        ("bank_fraud: phone", extract_phone_numbers,
         "call me at +91-9876543210", "+919876543210"),
        ("bank_fraud: mentioned bank", extract_mentioned_banks,
         "Your SBI account has been compromised", "sbi"),
        ("upi_fraud: UPI ID", extract_upi_ids,
         "pay to cashback.scam@fakeupi", "cashback.scam@fakeupi"),
        ("upi_fraud: phone", extract_phone_numbers,
         "contact at +91-8765432109", "+918765432109"),
        ("upi_fraud: mentioned bank", extract_mentioned_banks,
         "cashback from Paytm", "paytm"),
        ("phishing: URL", extract_urls,
         "click http://amaz0n-deals.fake-site.com/claim?id=12345", "http://amaz0n-deals.fake-site.com/claim?id=12345"),
        ("phishing: email", extract_emails,
         "email us at offers@fake-amazon-deals.com", "offers@fake-amazon-deals.com"),
        ("keywords: urgent", extract_keywords,
         "URGENT: Your account has been compromised", "urgent"),
        ("keywords: cashback", extract_keywords,
         "You have won a cashback of Rs. 5000", "cashback"),
    ]

    all_passed = True
    for label, func, text, expected in tests:
        result = func(text)
        # Normalize for comparison
        result_lower = [r.lower() for r in result]
        passed = expected.lower() in result_lower
        icon = f"{G}✓{X}" if passed else f"{R}✗{X}"
        if not passed:
            all_passed = False
            print(f"  {icon} {label}")
            print(f"    {R}Expected: {expected}, Got: {result}{X}")
        else:
            print(f"  {icon} {label}: {expected}")

    print()
    if all_passed:
        print(f"  {G}{B}✅ All regex tests passed!{X}")
    else:
        print(f"  {R}{B}⚠ Some regex tests failed — check extraction patterns{X}")
    print()
    return all_passed


# ─── Main Scenario Runner ──────────────────────────────────────────

def run_scenario(scenario):
    """Run a GUVI evaluation scenario with multi-turn conversation."""
    sid = f"guvi_eval_{scenario['scenarioId']}_{int(time.time())}"
    name = scenario["name"]
    scam_type = scenario["scamType"]
    expected = scenario["expectedExtraction"]

    print(f"\n{'='*70}")
    print(f"{B}{C}  🎯 [{scam_type.upper()}] {name}{X}")
    print(f"  {D}Channel: {scenario['metadata']['channel']} | Max Turns: {scenario['maxTurns']} | Weight: {scenario['weight']}{X}")
    print(f"{'='*70}")

    result = {
        "name": name,
        "scenarioId": scenario["scenarioId"],
        "passed": True,
        "issues": [],
        "warnings": [],
        "turns": [],
        "total_time": 0,
    }

    history = []
    start = time.time()

    for i, msg in enumerate(scenario["scammerTurns"]):
        turn_num = i + 1
        print_turn(turn_num, "SCAMMER", msg)

        resp = send_message(sid, msg, history, scenario.get("metadata"))
        if "error" in resp and "status" not in resp:
            result["issues"].append(f"Turn {turn_num}: API error - {resp['error']}")
            result["passed"] = False
            continue

        # Validate format
        fmt_issues = validate_format(resp)
        if fmt_issues:
            for issue in fmt_issues:
                result["issues"].append(f"Turn {turn_num}: {issue}")
            result["passed"] = False

        reply = resp.get("reply", "(no reply)")
        print_turn(turn_num, "HONEYPOT", reply)

        intel = resp.get("extractedIntelligence", {})
        print_intel(intel)

        scam = resp.get("scamDetected", False)
        label = f"{G}✓ Scam Detected{X}" if scam else f"{D}○ No scam{X}"
        msgs = resp.get("engagementMetrics", {}).get("totalMessagesExchanged", "?")
        print(f"  {label} | Messages: {msgs}")

        history.append({"sender": "scammer", "text": msg})
        history.append({"sender": "agent", "text": reply})

        result["turns"].append({
            "scammer": msg, "reply": reply,
            "scamDetected": scam, "intel": intel,
        })

        time.sleep(0.5)

    elapsed = time.time() - start
    result["total_time"] = round(elapsed, 1)

    # Post-conversation validation
    if result["turns"]:
        final = result["turns"][-1]
        final_intel = final["intel"]

        # 1. Scam must be detected
        if not final["scamDetected"]:
            result["issues"].append("❌ SCAM NOT DETECTED in final response!")
            result["passed"] = False

        # 2. Check intelligence extraction
        extraction_issues = check_extraction(final_intel, expected, name)
        for issue in extraction_issues:
            result["issues"].append(issue)
            result["passed"] = False

        # 3. Reply variety
        replies = [t["reply"] for t in result["turns"]]
        if len(replies) >= 3 and len(set(replies)) < 2:
            result["issues"].append("All replies identical — no variety")
            result["passed"] = False

        # 4. Reply quality
        short = [r for r in replies if len(r.strip()) < 20]
        if short:
            result["warnings"].append(f"{len(short)} replies too short (<20 chars)")

    # Summary
    print(f"\n  {'─'*50}")
    if result["passed"]:
        print(f"  {G}{B}✅ SCENARIO PASSED{X} ({result['total_time']}s)")
    else:
        print(f"  {R}{B}❌ SCENARIO FAILED{X} ({result['total_time']}s)")
        for issue in result["issues"]:
            print(f"  {R}  ⚠ {issue}{X}")
    for w in result.get("warnings", []):
        print(f"  {Y}  ⚠ {w}{X}")

    return result


def main():
    print(f"\n{B}{C}{'='*70}")
    print(f"  🎯 GUVI EVALUATION SCENARIO TEST SUITE")
    print(f"  Exact scenarios from GUVI automated evaluation")
    print(f"  Target: {API_URL}")
    print(f"{'='*70}{X}")

    # Phase 1: Regex pre-flight
    regex_ok = run_regex_preflight()
    if not regex_ok:
        print(f"{Y}⚠ Regex issues detected — API tests may also fail{X}")

    # Phase 2: Health check
    print(f"\n{B}🏥 Health Check...{X}")
    try:
        health_url = API_URL.replace("/api/honey-pot", "/health")
        health = requests.get(health_url, timeout=10)
        if health.status_code == 200:
            print(f"  {G}✓ Server is healthy{X}\n")
        else:
            print(f"  {Y}⚠ Health returned {health.status_code}{X}\n")
    except Exception:
        print(f"  {R}❌ Cannot reach server at {API_URL}")
        print(f"  Start with: python app.py{X}\n")
        sys.exit(1)

    # Phase 3: Run all 3 GUVI scenarios
    all_results = []
    total_start = time.time()

    for scenario in GUVI_SCENARIOS:
        result = run_scenario(scenario)
        all_results.append(result)

    total_time = round(time.time() - total_start, 1)

    # ─── Final Summary ──────────────────────────────────────────────
    passed = sum(1 for r in all_results if r["passed"])
    failed = sum(1 for r in all_results if not r["passed"])
    total = len(all_results)

    print(f"\n\n{'='*70}")
    print(f"{B}{C}  📋 GUVI EVALUATION RESULTS{X}")
    print(f"{'='*70}")
    print(f"  Total scenarios: {total}")
    print(f"  {G}Passed: {passed}{X}")
    if failed:
        print(f"  {R}Failed: {failed}{X}")
    print(f"  Total time: {total_time}s")
    print()

    for r in all_results:
        status = f"{G}✅ PASS{X}" if r["passed"] else f"{R}❌ FAIL{X}"
        turns = len(r["turns"])
        print(f"  {status}  [{r['scenarioId']}] {r['name']} ({turns} turns, {r['total_time']}s)")
        if not r["passed"]:
            for issue in r["issues"][:5]:
                print(f"        {R}⚠ {issue}{X}")

    # Weighted score
    total_weight = sum(s["weight"] for s in GUVI_SCENARIOS)
    earned_weight = sum(
        s["weight"] for s, r in zip(GUVI_SCENARIOS, all_results) if r["passed"]
    )
    print(f"\n  {B}Weighted Score: {earned_weight}/{total_weight} ({earned_weight/total_weight*100:.0f}%){X}")

    # Intelligence extraction summary
    print(f"\n{B}{M}  🧠 INTELLIGENCE EXTRACTION SUMMARY{X}")
    print(f"{'─'*70}")
    all_intel = {}
    for key in ["upiIds", "bankAccounts", "phoneNumbers", "phishingLinks",
                 "emails", "ifscCodes", "mentionedBanks", "suspiciousKeywords"]:
        all_intel[key] = []
    for r in all_results:
        if r["turns"]:
            intel = r["turns"][-1].get("intel", {})
            for key in all_intel:
                all_intel[key].extend(intel.get(key, []))

    for key, vals in all_intel.items():
        unique = list(set(vals))
        icon = f"{G}✓{X}" if unique else f"{D}○{X}"
        sample = str(unique[:3])[:60] if unique else "-"
        print(f"  {icon} {key:22s}: {len(unique):3d} unique | {sample}")

    print(f"{'─'*70}\n")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
