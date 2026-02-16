"""Validate fixes with GUVI's EXACT substring matching logic."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from models.intelligence import (
    extract_upi_ids, extract_bank_accounts, extract_phone_numbers,
    extract_urls, extract_emails, extract_keywords, extract_mentioned_banks
)

print("=" * 60)
print(" GUVI Substring Matching Simulation")
print(" Tests: fake_value in str(extracted_value)")
print("=" * 60)

# Simulates GUVI's exact scoring logic:
# any(fake_value in str(v) for v in extracted_values)
def guvi_check(fake_value, extracted_values):
    return any(fake_value in str(v) for v in extracted_values)

tests = [
    # (scenario, fake_key, fake_value, extraction_func, test_text)
    ("bank_fraud", "bankAccount", "1234567890123456",
     extract_bank_accounts, "transfer from account 1234567890123456"),
    ("bank_fraud", "upiId", "scammer.fraud@fakebank",
     extract_upi_ids, "send to scammer.fraud@fakebank"),
    ("bank_fraud", "phoneNumber", "+91-9876543210",
     extract_phone_numbers, "call me at +91-9876543210"),
    ("upi_fraud", "upiId", "cashback.scam@fakeupi",
     extract_upi_ids, "pay to cashback.scam@fakeupi"),
    ("upi_fraud", "phoneNumber", "+91-8765432109",
     extract_phone_numbers, "contact at +91-8765432109"),
    ("phishing", "phishingLink", "http://amaz0n-deals.fake-site.com/claim?id=12345",
     extract_urls, "click http://amaz0n-deals.fake-site.com/claim?id=12345"),
    ("phishing", "emailAddress", "offers@fake-amazon-deals.com",
     extract_emails, "email us at offers@fake-amazon-deals.com"),
]

passed = 0
total_pts = 0
for scenario, fake_key, fake_value, func, text in tests:
    result = func(text)
    match = guvi_check(fake_value, result)
    pts = 10 if match else 0
    total_pts += pts
    icon = "PASS" if match else "FAIL"
    print(f"\n  [{icon}] {scenario}/{fake_key} ({pts} pts)")
    print(f"    fakeData:  {fake_value}")
    print(f"    extracted: {result}")
    print(f"    check:     '{fake_value}' in {[str(v) for v in result]} = {match}")
    if match:
        passed += 1

print(f"\n{'=' * 60}")
print(f"  Results: {passed}/{len(tests)} checks passed")
print(f"  Intelligence Score: {total_pts}/70 pts (max for 7 fakeData items)")
print(f"{'=' * 60}")
