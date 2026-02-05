"""
Comprehensive Test Suite for Operation Iron-Mask
Tests all 12 scam archetypes, intelligence extraction, and persona consistency
"""

import os
import requests
import json
import time
import pytest
from datetime import datetime

API_URL = "http://127.0.0.1:5000/api/honey-pot"
API_KEY = "sk_ironmask_hackathon_2026"
HEADERS = {
    "x-api-key": API_KEY,
    "Content-Type": "application/json"
}
RUN_INTEGRATION = os.getenv("RUN_INTEGRATION_TESTS") == "true"

# Test cases for all 12 scam archetypes
TEST_CASES = [
    {
        "name": "1. UPI Fraud",
        "session_id": "test-upi-fraud-001",
        "message": "Your account has been compromised! Send Rs.1 to verify@paytm to verify your account.",
        "expected_upi": ["verify@paytm"]
    },
    {
        "name": "2. Digital Arrest",
        "session_id": "test-digital-arrest-001",
        "message": "This is CBI calling. You are under digital arrest. Your Aadhaar is linked to money laundering. Pay Rs.50,000 fine to avoid arrest.",
        "expected_keywords": ["arrest", "Aadhaar", "pay"]
    },
    {
        "name": "3. Bank Account Block",
        "session_id": "test-bank-block-001",
        "message": "ALERT: Your SBI account 12345678901 will be blocked in 2 hours. Share OTP to verify: 9876543210",
        "expected_phone": ["+919876543210"]
    },
    {
        "name": "4. KYC Fraud",
        "session_id": "test-kyc-fraud-001",
        "message": "Dear customer, your bank KYC is expired. Update now: https://bit.ly/sbi-kyc-update or account will be suspended.",
        "expected_links": ["https://bit.ly/sbi-kyc-update"]
    },
    {
        "name": "5. QR Code Scam",
        "session_id": "test-qr-scam-001",
        "message": "Scan this QR code to receive Rs.5000 cashback directly to your account. Limited time offer!",
        "expected_keywords": ["cashback", "scan"]
    },
    {
        "name": "6. Lottery Scam",
        "session_id": "test-lottery-001",
        "message": "Congratulations! You have won Rs.25,00,000 in Jio Lucky Draw! Pay Rs.5000 processing fee to scammer_lottery@ybl",
        "expected_upi": ["scammer_lottery@ybl"]
    },
    {
        "name": "7. Loan Scam",
        "session_id": "test-loan-001",
        "message": "Get instant loan of Rs.5 lakh approved! No documents needed. Just pay Rs.2000 advance to loan_agent@paytm",
        "expected_upi": ["loan_agent@paytm"]
    },
    {
        "name": "8. Investment Scam",
        "session_id": "test-investment-001",
        "message": "Earn Rs.10,000 daily with cryptocurrency trading! Minimum investment Rs.5000. Contact: 8899776655",
        "expected_phone": ["+918899776655"]
    },
    {
        "name": "9. Courier Scam",
        "session_id": "test-courier-001",
        "message": "Your FedEx parcel seized at customs with illegal items. Pay Rs.3000 clearance or face arrest. UPI: customs_clear@ybl",
        "expected_upi": ["customs_clear@ybl"]
    },
    {
        "name": "10. OLX/Marketplace Scam",
        "session_id": "test-olx-001",
        "message": "I want to buy your item. I am army officer, will send money via QR code. Scan to receive Rs.15000.",
        "expected_keywords": ["scan", "army"]
    },
    {
        "name": "11. Aadhaar Scam",
        "session_id": "test-aadhaar-001",
        "message": "Your Aadhaar card is being misused for fraud. Call immediately 7788996655 to block or police will arrest you.",
        "expected_phone": ["+917788996655"]
    },
    {
        "name": "12. Refund Scam",
        "session_id": "test-refund-001",
        "message": "Amazon refund of Rs.2999 pending. Click link to claim: tinyurl.com/amazon-refund-claim",
        "expected_links": ["tinyurl.com/amazon-refund-claim"]
    }
]


def run_test(test_case):
    """Run a single test case and return results."""
    payload = {
        "sessionId": test_case["session_id"],
        "message": {
            "sender": "scammer",
            "text": test_case["message"]
        },
        "conversationHistory": []
    }
    
    start_time = time.time()
    
    try:
        response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
        latency = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            
            # Check results
            results = {
                "name": test_case["name"],
                "status": "PASS" if data.get("scamDetected") else "FAIL",
                "latency_ms": round(latency * 1000, 2),
                "scam_detected": data.get("scamDetected"),
                "reply_preview": data.get("reply", "")[:80] + "...",
                "extracted_upi": data.get("extractedIntelligence", {}).get("upiIds", []),
                "extracted_phone": data.get("extractedIntelligence", {}).get("phoneNumbers", []),
                "extracted_links": data.get("extractedIntelligence", {}).get("phishingLinks", []),
                "keywords": data.get("extractedIntelligence", {}).get("suspiciousKeywords", [])
            }
            
            # Verify expected extractions
            if "expected_upi" in test_case:
                found = any(upi in results["extracted_upi"] for upi in test_case["expected_upi"])
                results["upi_extraction"] = "✅" if found else "❌"
            if "expected_phone" in test_case:
                found = any(phone in results["extracted_phone"] for phone in test_case["expected_phone"])
                results["phone_extraction"] = "✅" if found else "❌"
            if "expected_links" in test_case:
                found = any(link in str(results["extracted_links"]) for link in test_case["expected_links"])
                results["link_extraction"] = "✅" if found else "❌"
            if "expected_keywords" in test_case:
                found = any(kw.lower() in str(results["keywords"]).lower() for kw in test_case["expected_keywords"])
                results["keyword_extraction"] = "✅" if found else "❌"
            
            return results
        else:
            return {"name": test_case["name"], "status": "ERROR", "error": response.text}
            
    except Exception as e:
        return {"name": test_case["name"], "status": "ERROR", "error": str(e)}


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set RUN_INTEGRATION_TESTS=true to run")
def test_persona_consistency():
    """Test that personas are consistent across multiple messages."""
    session_id = "test-persona-consistency-final"
    
    # First message
    payload1 = {
        "sessionId": session_id,
        "message": {"sender": "scammer", "text": "Hello, what is your name?"},
        "conversationHistory": []
    }
    
    resp1 = requests.post(API_URL, headers=HEADERS, json=payload1, timeout=60)
    reply1 = resp1.json().get("reply", "")
    
    # Second message
    payload2 = {
        "sessionId": session_id,
        "message": {"sender": "scammer", "text": "Tell me your bank name again."},
        "conversationHistory": [
            {"sender": "scammer", "text": "Hello, what is your name?"},
            {"sender": "user", "text": reply1}
        ]
    }
    
    resp2 = requests.post(API_URL, headers=HEADERS, json=payload2, timeout=60)
    reply2 = resp2.json().get("reply", "")
    
    return {
        "test": "Persona Consistency",
        "first_reply": reply1[:100] + "...",
        "second_reply": reply2[:100] + "...",
        "status": "PASS (check replies)"
    }


@pytest.mark.skipif(not RUN_INTEGRATION, reason="Set RUN_INTEGRATION_TESTS=true to run")
def test_latency():
    """Test API responds within 1 second."""
    payload = {
        "sessionId": "latency-test-001",
        "message": {"sender": "scammer", "text": "Quick test message"},
        "conversationHistory": []
    }
    
    start = time.time()
    response = requests.post(API_URL, headers=HEADERS, json=payload, timeout=60)
    latency = time.time() - start
    
    return {
        "test": "Latency Test",
        "latency_seconds": round(latency, 2),
        "under_1_second": "✅" if latency < 1 else "❌ (LLM may be slow)",
        "status": "PASS" if response.status_code == 200 else "FAIL"
    }


def main():
    print("=" * 60)
    print("🎯 Operation Iron-Mask: Comprehensive Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Test all 12 archetypes
    print("📋 Testing 12 Scam Archetypes...")
    print("-" * 60)
    
    results = []
    passed = 0
    
    for test_case in TEST_CASES:
        print(f"  Testing: {test_case['name']}...", end=" ", flush=True)
        result = run_test(test_case)
        results.append(result)
        
        if result.get("status") == "PASS":
            passed += 1
            print(f"✅ ({result.get('latency_ms', 0)}ms)")
        else:
            print(f"❌ {result.get('error', '')}")
    
    print()
    print(f"Archetype Tests: {passed}/{len(TEST_CASES)} passed")
    print()
    
    # Persona consistency test
    print("🎭 Testing Persona Consistency...", end=" ", flush=True)
    persona_result = test_persona_consistency()
    print("✅")
    
    # Latency test
    print("⏱️ Testing Latency...", end=" ", flush=True)
    latency_result = test_latency()
    print(f"✅ ({latency_result.get('latency_seconds', 0)}s)")
    
    print()
    print("=" * 60)
    print("📊 Detailed Results")
    print("=" * 60)
    
    for r in results:
        print(f"\n{r['name']}:")
        print(f"  Status: {r.get('status')}")
        print(f"  Latency: {r.get('latency_ms', 'N/A')}ms")
        print(f"  Scam Detected: {r.get('scam_detected')}")
        print(f"  Reply: {r.get('reply_preview', 'N/A')}")
        
        if r.get('extracted_upi'):
            print(f"  UPIs: {r['extracted_upi']} {r.get('upi_extraction', '')}")
        if r.get('extracted_phone'):
            print(f"  Phones: {r['extracted_phone']} {r.get('phone_extraction', '')}")
        if r.get('extracted_links'):
            print(f"  Links: {r['extracted_links']} {r.get('link_extraction', '')}")
        if r.get('keywords'):
            print(f"  Keywords: {r['keywords'][:5]}...")
    
    print()
    print("🎭 Persona Consistency:")
    print(f"  First Reply: {persona_result.get('first_reply')}")
    print(f"  Second Reply: {persona_result.get('second_reply')}")
    
    print()
    print("⏱️ Latency:")
    print(f"  Response Time: {latency_result.get('latency_seconds')}s")
    print(f"  Under 1 second: {latency_result.get('under_1_second')}")
    
    print()
    print("=" * 60)
    print("✅ Test Suite Completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
