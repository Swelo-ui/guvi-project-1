"""
🎯 GUVI EVALUATION SIMULATOR (Full 15 Scenarios)
Replicates GUVI's EXACT scoring algorithm (100 pts per scenario):
  - Scam Detection:         20 pts
  - Intelligence Extraction: 40 pts (proportional per fakeData item)
  - Engagement Quality:     20 pts
  - Response Structure:     20 pts

Runs multi-turn conversations against your API endpoint,
then scores using the same logic GUVI uses.

Usage:
    python tests/guvi_evaluator.py                    # Local
    python tests/guvi_evaluator.py --remote           # Render deployment
    python tests/guvi_evaluator.py --url <URL>        # Custom URL
    python tests/guvi_evaluator.py --remote --fast    # Quick 5-scenario run
"""

import requests
import json
import time
import sys
import os
import uuid
from datetime import datetime, timezone

# ─── Configuration ──────────────────────────────────────────────────
DEFAULT_LOCAL = "http://127.0.0.1:5000/api/honey-pot"
DEFAULT_REMOTE = "https://guvi-project-1-wefr.onrender.com/api/honey-pot"
API_KEY = "sk_ironmask_hackathon_2026"

# Parse args
API_URL = DEFAULT_LOCAL
FAST_MODE = False
for i, arg in enumerate(sys.argv[1:], 1):
    if arg == "--remote":
        API_URL = DEFAULT_REMOTE
    elif arg == "--fast":
        FAST_MODE = True
    elif arg == "--url" and i < len(sys.argv) - 1:
        API_URL = sys.argv[i + 1]
    elif not arg.startswith("--"):
        API_URL = arg

HEADERS = {"Content-Type": "application/json", "x-api-key": API_KEY}

# Colors
G = "\033[92m"; R = "\033[91m"; Y = "\033[93m"; C = "\033[96m"
M = "\033[95m"; B = "\033[1m"; D = "\033[2m"; X = "\033[0m"

# ─── ALL 15 GUVI Evaluation Scenarios ──────────────────────────────
# Each scenario has multi-turn scammer messages with embedded fakeData.
# The scoring evaluates whether fakeData items appear in extractedIntelligence.

SCENARIOS = [
    {
        "scenarioId": "bank_fraud",
        "name": "Bank Fraud Detection",
        "scamType": "bank_fraud",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "bankAccount": "1234567890123456",
            "upiId": "scammer.fraud@fakebank",
            "phoneNumber": "+91-9876543210"
        },
        "scammerTurns": [
            "URGENT: Your SBI account has been compromised. Your account will be blocked in 2 hours. Share your account number and OTP immediately to verify your identity.",
            "Sir, this is very urgent matter. I am Senior Manager from SBI fraud department. Please call me back immediately at +91-9876543210 to verify your account details before it gets blocked.",
            "Sir, we have detected suspicious transfer of Rs.50000 from your account number 1234567890123456. If you did not authorize this, please share the OTP sent to your registered mobile to reverse the transaction immediately.",
            "If you cannot share OTP sir, then for emergency verification please transfer Rs.1 to our secure fraud recovery UPI: scammer.fraud@fakebank. This is mandatory RBI procedure for account recovery.",
            "This is your FINAL WARNING sir. Your SBI account 1234567890123456 will be PERMANENTLY BLOCKED and all funds will be frozen. Either share OTP or verify via UPI scammer.fraud@fakebank or call +91-9876543210 RIGHT NOW.",
        ],
    },
    {
        "scenarioId": "upi_fraud",
        "name": "UPI Fraud Multi-turn",
        "scamType": "upi_fraud",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "upiId": "cashback.scam@fakeupi",
            "phoneNumber": "+91-8765432109"
        },
        "scammerTurns": [
            "Congratulations! You have won a cashback of Rs. 5000 from Paytm. To claim your reward, please verify your UPI details. This is from official customer support.",
            "Sir, I am from Paytm official customer support team. Your cashback of Rs.5000 has been approved. You can also contact us at +91-8765432109 for verification. This offer expires in 30 minutes only!",
            "To claim your Rs.5000 cashback immediately, just send Rs.10 as verification fee to our official UPI ID: cashback.scam@fakeupi. The Rs.10 will be refunded along with your Rs.5000 cashback within minutes.",
            "Sir, time is running out! Only 5 minutes left for your offer! Please send Rs.10 to cashback.scam@fakeupi immediately or call +91-8765432109. After that your Paytm cashback of Rs.5000 will expire permanently!",
            "Sir this is last reminder. Rs.5000 cashback waiting. Send just Rs.10 to cashback.scam@fakeupi now. Contact +91-8765432109 for help. Don't miss this opportunity!",
        ],
    },
    {
        "scenarioId": "phishing_link",
        "name": "Phishing Link Detection",
        "scamType": "phishing",
        "metadata": {"channel": "Email", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phishingLink": "http://amaz0n-deals.fake-site.com/claim?id=12345",
            "emailAddress": "offers@fake-amazon-deals.com"
        },
        "scammerTurns": [
            "You have been selected for iPhone 15 Pro at just Rs. 999! Click here to claim: http://amaz0n-deals.fake-site.com/claim?id=12345. Offer expires in 10 minutes!",
            "Sir, this is a verified offer from Amazon India. For more details or if you have questions, email us at offers@fake-amazon-deals.com or click http://amaz0n-deals.fake-site.com/claim?id=12345 to claim your iPhone now.",
            "HURRY sir! Only 3 iPhones left at Rs.999! This is exclusive deal. Click http://amaz0n-deals.fake-site.com/claim?id=12345 NOW before stock runs out. Contact: offers@fake-amazon-deals.com for customer support.",
            "Sir are you still interested? I can hold one iPhone 15 Pro for you at Rs.999. Just click http://amaz0n-deals.fake-site.com/claim?id=12345 or email offers@fake-amazon-deals.com. Last chance!",
        ],
    },
    {
        "scenarioId": "kyc_fraud",
        "name": "KYC Fraud",
        "scamType": "kyc_fraud",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-9988776655",
            "upiId": "kyc.update@fakebank",
            "phishingLink": "http://sbi-kyc-update.fake.in/verify"
        },
        "scammerTurns": [
            "ALERT: Your SBI account KYC is expired. Update your KYC immediately or your account will be suspended within 24 hours. This is mandatory RBI compliance.",
            "Dear Customer, I am calling from SBI KYC department. Your KYC must be updated today. Please call our helpline at +91-9988776655 for immediate assistance. Failure will result in account freeze.",
            "For quick KYC update, please click this secure link: http://sbi-kyc-update.fake.in/verify and enter your details. This is official SBI portal for video KYC verification.",
            "Sir if link is not working, you can complete KYC by sending Rs.1 verification to our official UPI: kyc.update@fakebank. This confirms your identity as per RBI guidelines. Call +91-9988776655 for help.",
            "FINAL NOTICE: Your account will be BLOCKED today if KYC not updated. Use link http://sbi-kyc-update.fake.in/verify or UPI kyc.update@fakebank or call +91-9988776655. Aadhar and PAN required.",
        ],
    },
    {
        "scenarioId": "job_scam",
        "name": "Job Scam",
        "scamType": "job_scam",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-7766554433",
            "bankAccount": "9876543210987654",
            "upiId": "hr.recruiter@fakeupi"
        },
        "scammerTurns": [
            "Congratulations! You have been selected for a Work From Home job at TCS. Salary Rs.50000/month. No experience needed. Contact HR immediately for joining details.",
            "Dear Candidate, I am HR Manager at TCS Recruitment. Your profile has been shortlisted. Please call me at +91-7766554433 for interview scheduling. Registration fee of Rs.500 is required.",
            "To confirm your joining, please transfer the registration fee of Rs.500 to company account number 9876543210987654. This is refundable after first month salary. Contact +91-7766554433 for any queries.",
            "Sir, many candidates are waiting. If you want this position, pay Rs.500 registration to UPI: hr.recruiter@fakeupi or bank account 9876543210987654. Last date today only. Call +91-7766554433.",
            "Final opportunity! TCS WFH position closing today. Pay Rs.500 to hr.recruiter@fakeupi or account 9876543210987654. Call HR at +91-7766554433 immediately!",
        ],
    },
    {
        "scenarioId": "lottery_scam",
        "name": "Lottery Scam",
        "scamType": "lottery_scam",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-9900112233",
            "upiId": "lottery.claim@fakepay",
            "bankAccount": "5566778899001122"
        },
        "scammerTurns": [
            "CONGRATULATIONS! Your mobile number has won Rs.25,00,000 in the International Lucky Draw 2026! Claim your prize now. This is not a joke, verified by RBI.",
            "Dear Winner, I am Prize Distribution Manager. Your lottery ticket number LT-78234 has won Rs.25 lakhs. To process your claim, contact our office at +91-9900112233 immediately.",
            "Sir, to release your prize money of Rs.25 lakhs, a processing fee of Rs.5000 is required. Please transfer to our official account 5566778899001122 at HDFC Bank. Call +91-9900112233 for confirmation.",
            "Alternative payment: Send Rs.5000 to lottery.claim@fakepay UPI for faster processing. Your Rs.25 lakh prize will be credited within 2 hours. Contact +91-9900112233. Offer valid today only!",
            "URGENT: If fee not received by 6 PM, your Rs.25 lakh prize will be cancelled. Pay to lottery.claim@fakepay or account 5566778899001122. Call +91-9900112233 NOW!",
        ],
    },
    {
        "scenarioId": "electricity_bill",
        "name": "Electricity Bill Scam",
        "scamType": "electricity_bill",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-8877665544",
            "phishingLink": "http://electricity-bill-pay.fake.co/pay",
            "upiId": "ebill.payment@fakeupi"
        },
        "scammerTurns": [
            "ALERT: Your electricity connection will be DISCONNECTED tonight at 10 PM due to unpaid bill of Rs.3,450. Pay immediately to avoid disconnection.",
            "Dear Consumer, this is from State Electricity Board. Your bill of Rs.3450 is overdue. To avoid disconnection, contact our customer care at +91-8877665544 immediately.",
            "Pay your overdue electricity bill online: http://electricity-bill-pay.fake.co/pay. Enter your consumer number and pay Rs.3450. Call +91-8877665544 if you face any issues.",
            "If online payment is not working, pay directly via UPI to ebill.payment@fakeupi. Amount: Rs.3450. Your electricity will be restored within 1 hour. Contact +91-8877665544.",
            "FINAL WARNING: Disconnection in 30 minutes! Pay Rs.3450 to ebill.payment@fakeupi or via http://electricity-bill-pay.fake.co/pay. Call +91-8877665544 for emergency!",
        ],
    },
    {
        "scenarioId": "govt_scheme",
        "name": "Government Scheme Scam",
        "scamType": "govt_scheme",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-9191828273",
            "upiId": "pmkisan.benefit@fakegov",
            "phishingLink": "http://pmkisan-yojana.fake.gov.in/apply"
        },
        "scammerTurns": [
            "Dear Citizen, you are eligible for PM Kisan Yojana benefit of Rs.6000. Register now to receive direct bank transfer from Government of India.",
            "I am from PM Kisan Samman Nidhi office. Your Aadhaar-linked account is eligible for Rs.6000 annual benefit. Call our helpline +91-9191828273 to register. Limited slots available.",
            "Register for PM Kisan benefit at: http://pmkisan-yojana.fake.gov.in/apply. Enter your Aadhaar and bank details. Contact +91-9191828273 for assistance. Government approved scheme.",
            "To activate your PM Kisan benefit immediately, pay one-time registration charge of Rs.250 to pmkisan.benefit@fakegov UPI. Amount will be adjusted from your first installment. Call +91-9191828273.",
            "Last date extended! Register now at http://pmkisan-yojana.fake.gov.in/apply or pay Rs.250 to pmkisan.benefit@fakegov. Contact +91-9191828273. Don't miss Rs.6000 government benefit!",
        ],
    },
    {
        "scenarioId": "crypto_investment",
        "name": "Crypto Investment Scam",
        "scamType": "crypto_investment",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-7788990011",
            "upiId": "crypto.invest@fakepay",
            "phishingLink": "http://bitcoin-profit-india.fake.com/invest"
        },
        "scammerTurns": [
            "Exclusive Investment Opportunity! Earn 300% returns in just 30 days with Bitcoin trading. Minimum investment Rs.10000. Guaranteed profits by expert traders.",
            "Hello, I am Senior Crypto Analyst. Our AI-powered trading bot guarantees minimum 10% daily returns. Invest Rs.10000 today and withdraw Rs.40000 after 30 days. Contact me at +91-7788990011.",
            "Start your crypto journey now! Visit our platform: http://bitcoin-profit-india.fake.com/invest. Create account and deposit minimum Rs.10000. Call +91-7788990011 for guided investment.",
            "For instant investment, transfer Rs.10000 to crypto.invest@fakepay UPI. Your trading account will be activated immediately with 3x bonus. Contact +91-7788990011 for portfolio details.",
            "Last chance! Bitcoin reaching all-time high! Invest via crypto.invest@fakepay or http://bitcoin-profit-india.fake.com/invest. Call +91-7788990011. Don't miss guaranteed 300% returns!",
        ],
    },
    {
        "scenarioId": "customs_parcel",
        "name": "Customs Parcel Scam",
        "scamType": "customs_parcel",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-6655443322",
            "bankAccount": "1122334455667788",
            "upiId": "customs.clearance@fakepay"
        },
        "scammerTurns": [
            "CUSTOMS ALERT: Your international parcel #IND-29384 from DHL has been held at Mumbai Customs. Pay customs duty of Rs.8500 within 24 hours or parcel will be returned.",
            "I am Officer Sharma from Indian Customs Department. Your parcel contains items worth Rs.85000. Customs duty of Rs.8500 must be paid immediately. Contact +91-6655443322 for clearance process.",
            "To clear your parcel, transfer customs duty Rs.8500 to official account 1122334455667788 at Union Bank. Contact clearance desk at +91-6655443322. Parcel ID: IND-29384.",
            "For faster clearance, pay Rs.8500 via UPI to customs.clearance@fakepay. Your parcel will be dispatched same day. Direct any queries to +91-6655443322. Officer Sharma, Badge #CUS-4521.",
            "FINAL NOTICE: Parcel #IND-29384 will be DESTROYED if duty not paid. Transfer Rs.8500 to customs.clearance@fakepay or account 1122334455667788. Call +91-6655443322 IMMEDIATELY!",
        ],
    },
    {
        "scenarioId": "tech_support",
        "name": "Tech Support Scam",
        "scamType": "tech_support",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-9123456780",
            "emailAddress": "support@fake-microsoft-help.com",
            "phishingLink": "http://windows-security-fix.fake.com/download"
        },
        "scammerTurns": [
            "SECURITY ALERT: Your Windows computer has been infected with Trojan virus! Your banking data is at risk. Contact Microsoft Technical Support immediately to fix this issue.",
            "I am from Microsoft Security Team. We have detected malware on your device that is stealing your passwords. Please call our toll-free helpline at +91-9123456780 for remote assistance.",
            "To protect your computer, download our security tool from: http://windows-security-fix.fake.com/download. Or email us at support@fake-microsoft-help.com for manual fix instructions. Call +91-9123456780.",
            "Sir, your computer is ACTIVELY being hacked right now! Please install our security software from http://windows-security-fix.fake.com/download immediately. Email support@fake-microsoft-help.com or call +91-9123456780.",
            "CRITICAL: We will need to install AnyDesk for remote fix. Download from http://windows-security-fix.fake.com/download. Contact support@fake-microsoft-help.com or call +91-9123456780. Don't turn off your computer!",
        ],
    },
    {
        "scenarioId": "loan_approval",
        "name": "Loan Approval Scam",
        "scamType": "loan_approval",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-8800990077",
            "upiId": "loan.process@fakebank",
            "bankAccount": "4455667788990011"
        },
        "scammerTurns": [
            "Dear Customer, your Pre-Approved Personal Loan of Rs.5,00,000 at just 2% interest is ready for disbursal! No documents required. Apply now before offer expires.",
            "I am Loan Manager from HDFC Bank. Your CIBIL score qualifies you for instant Rs.5 lakh loan at lowest interest. Call me at +91-8800990077 to complete the process in 15 minutes.",
            "Sir, loan approved! To process disbursement, pay one-time processing fee of Rs.2000 to our account 4455667788990011. Call +91-8800990077 after payment. Loan amount will be credited in 1 hour.",
            "Faster option: Pay Rs.2000 processing fee via UPI to loan.process@fakebank. Your Rs.5 lakh loan will be in your account within 30 minutes. Contact +91-8800990077 for status.",
            "FINAL: Pre-approved loan offer expiring! Pay Rs.2000 to loan.process@fakebank or account 4455667788990011. Call +91-8800990077. Don't lose Rs.5 lakh at 2% interest!",
        ],
    },
    {
        "scenarioId": "income_tax",
        "name": "Income Tax Scam",
        "scamType": "income_tax",
        "metadata": {"channel": "Email", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-7700880099",
            "bankAccount": "3344556677889900",
            "emailAddress": "refund@fake-incometax.gov.in"
        },
        "scammerTurns": [
            "NOTICE: Income Tax Department has detected discrepancy in your ITR filing for AY 2025-26. Penalty of Rs.15000 will be charged if not resolved within 48 hours.",
            "Dear Taxpayer, this is from Income Tax Department. Your PAN is linked to suspicious transactions. Contact our investigation officer at +91-7700880099 to resolve immediately or face legal action.",
            "To settle your income tax dues of Rs.15000 and avoid prosecution, transfer to IT Department account 3344556677889900. For clarification, email refund@fake-incometax.gov.in or call +91-7700880099.",
            "Alternatively, if you have a refund pending, email your bank details to refund@fake-incometax.gov.in for processing. Contact +91-7700880099. Pay penalty to account 3344556677889900 to avoid FIR.",
            "FINAL WARNING from Income Tax Department. Pay Rs.15000 to 3344556677889900 or email refund@fake-incometax.gov.in. FIR will be filed if not paid today. Call +91-7700880099 for officer verification.",
        ],
    },
    {
        "scenarioId": "refund_scam",
        "name": "Refund Scam",
        "scamType": "refund_scam",
        "metadata": {"channel": "SMS", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-9090808070",
            "upiId": "refund.process@fakeupi"
        },
        "scammerTurns": [
            "Your refund of Rs.3500 from Flipkart is pending. Your bank verification is required to process the refund. Click to verify your account details.",
            "I am from Flipkart Customer Support. Your order #FK-8823 return has been approved and refund of Rs.3500 is ready. To process, call us at +91-9090808070 and share your UPI ID.",
            "Sir, to receive your Rs.3500 refund directly, please accept the UPI collect request from refund.process@fakeupi. This is our official refund UPI. Contact +91-9090808070 for support.",
            "Refund not received? Please send Rs.1 to refund.process@fakeupi for bank verification. Your Rs.3500 will be credited back immediately after verification. Call +91-9090808070.",
            "Last chance to claim your Rs.3500 refund! Send Rs.1 verification to refund.process@fakeupi or call +91-9090808070. Refund will expire in 1 hour!",
        ],
    },
    {
        "scenarioId": "insurance",
        "name": "Insurance Scam",
        "scamType": "insurance",
        "metadata": {"channel": "WhatsApp", "language": "English", "locale": "IN"},
        "maxTurns": 10,
        "fakeData": {
            "phoneNumber": "+91-6600770088",
            "upiId": "lic.maturity@fakepay",
            "bankAccount": "7788990011223344"
        },
        "scammerTurns": [
            "Dear Policyholder, your LIC policy has matured. Maturity amount of Rs.8,50,000 is ready for disbursement. Contact our branch for claim processing.",
            "I am LIC Branch Manager. Your policy #LIC-482901 has matured for Rs.8.5 lakhs. Call our claims department at +91-6600770088 to initiate the disbursement process today.",
            "Sir, to release your maturity amount of Rs.8.5 lakhs, pay processing fee of Rs.3000 to LIC account 7788990011223344. Contact +91-6600770088 after payment for confirmation.",
            "For faster processing, pay Rs.3000 via UPI to lic.maturity@fakepay. Your Rs.8.5 lakh maturity amount will be transferred within 48 hours. Call +91-6600770088 for any queries.",
            "URGENT: Policy #LIC-482901 maturity lapsing! Pay Rs.3000 to lic.maturity@fakepay or account 7788990011223344. Call +91-6600770088. After today, you lose Rs.8.5 lakhs!",
        ],
    },
]


# ─── GUVI's Exact Scoring Functions ────────────────────────────────

def evaluate_scam_detection(final_output):
    """GUVI Scoring: Scam Detection (20 points)"""
    score = 0
    details = []
    if final_output.get("scamDetected", False):
        score = 20
        details.append(f"{G}✓ scamDetected: true → 20 pts{X}")
    else:
        details.append(f"{R}✗ scamDetected: false → 0 pts{X}")
    return score, details


def evaluate_intelligence_extraction(final_output, scenario):
    """GUVI Scoring: Intelligence Extraction (40 points)
    
    GUVI distributes 40 points proportionally across fakeData items.
    If scenario has N items and you extract M, score = (M/N) × 40.
    """
    details = []
    extracted = final_output.get("extractedIntelligence", {})
    fake_data = scenario.get("fakeData", {})
    total_items = len(fake_data)
    found_items = 0

    # GUVI's exact key mapping
    key_mapping = {
        "bankAccount": "bankAccounts",
        "upiId": "upiIds",
        "phoneNumber": "phoneNumbers",
        "phishingLink": "phishingLinks",
        "emailAddress": "emailAddresses"
    }

    for fake_key, fake_value in fake_data.items():
        output_key = key_mapping.get(fake_key, fake_key)
        extracted_values = extracted.get(output_key, [])

        found = False
        if isinstance(extracted_values, list):
            # GUVI's exact check: any(fake_value in str(v) for v in extracted_values)
            found = any(fake_value in str(v) for v in extracted_values)
        elif isinstance(extracted_values, str):
            found = fake_value in extracted_values

        if found:
            found_items += 1
            details.append(f"{G}✓ {fake_key} ({output_key}): '{fake_value}' found ✓{X}")
        else:
            details.append(f"{R}✗ {fake_key} ({output_key}): '{fake_value}' NOT found in {extracted_values}{X}")

    # Proportional scoring: (found/total) × 40
    score = int((found_items / total_items) * 40) if total_items > 0 else 0
    details.append(f"{D}   → {found_items}/{total_items} items extracted = {score}/40 pts{X}")
    return score, details


def evaluate_engagement_quality(final_output):
    """GUVI Scoring: Engagement Quality (20 points)"""
    score = 0
    details = []
    metrics = final_output.get("engagementMetrics", {})
    duration = metrics.get("engagementDurationSeconds", 0)
    messages = metrics.get("totalMessagesExchanged", 0)

    if duration > 0:
        score += 5
        details.append(f"{G}✓ duration > 0 ({duration}s) → 5 pts{X}")
    else:
        details.append(f"{R}✗ duration = 0 → 0 pts{X}")

    if duration > 60:
        score += 5
        details.append(f"{G}✓ duration > 60 ({duration}s) → 5 pts{X}")
    else:
        details.append(f"{Y}⚠ duration ≤ 60 ({duration}s) → 0 pts{X}")

    if messages > 0:
        score += 5
        details.append(f"{G}✓ messages > 0 ({messages}) → 5 pts{X}")
    else:
        details.append(f"{R}✗ messages = 0 → 0 pts{X}")

    if messages >= 5:
        score += 5
        details.append(f"{G}✓ messages ≥ 5 ({messages}) → 5 pts{X}")
    else:
        details.append(f"{Y}⚠ messages < 5 ({messages}) → 0 pts{X}")

    return score, details


def evaluate_response_structure(final_output):
    """GUVI Scoring: Response Structure (20 points)"""
    score = 0
    details = []

    required_fields = ["status", "scamDetected", "extractedIntelligence"]
    optional_fields = ["engagementMetrics", "agentNotes"]

    for field in required_fields:
        if field in final_output:
            score += 5
            details.append(f"{G}✓ {field} present → 5 pts{X}")
        else:
            details.append(f"{R}✗ {field} MISSING → 0 pts{X}")

    for field in optional_fields:
        if field in final_output and final_output[field]:
            score += 2.5
            details.append(f"{G}✓ {field} present → 2.5 pts{X}")
        else:
            details.append(f"{Y}⚠ {field} missing/empty → 0 pts{X}")

    score = min(score, 20)
    return score, details


def evaluate_reply_field(response_data):
    """Check that reply/message/text exists (GUVI checks in that order)"""
    reply = response_data.get("reply") or response_data.get("message") or response_data.get("text")
    return reply


# ─── Conversation Runner ───────────────────────────────────────────

def run_scenario(scenario):
    """Run a full multi-turn scenario and return the final API response for scoring."""
    session_id = str(uuid.uuid4())
    conversation_history = []
    all_responses = []
    start_time = time.time()

    print(f"\n{'='*70}")
    print(f"{B}{C}  🎯 [{scenario['scamType'].upper()}] {scenario['name']}{X}")
    print(f"  {D}Max Turns: {scenario['maxTurns']} | fakeData keys: {list(scenario['fakeData'].keys())}{X}")
    print(f"{'='*70}")

    for turn_num, scammer_msg in enumerate(scenario["scammerTurns"], 1):
        # Display scammer message
        display = scammer_msg[:120] + "..." if len(scammer_msg) > 120 else scammer_msg
        print(f"\n  {R}⬤ Turn {turn_num} [SCAMMER]:{X}")
        print(f"  {D}{display}{X}")

        # Build request (matches GUVI format exactly)
        message = {
            "sender": "scammer",
            "text": scammer_msg,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        request_body = {
            "sessionId": session_id,
            "message": message,
            "conversationHistory": conversation_history,
            "metadata": scenario.get("metadata", {})
        }

        try:
            resp = requests.post(API_URL, headers=HEADERS, json=request_body, timeout=60)

            if resp.status_code != 200:
                print(f"  {R}❌ HTTP {resp.status_code}: {resp.text[:100]}{X}")
                # Still accumulate history so subsequent turns have context
                conversation_history.append(message)
                conversation_history.append({
                    "sender": "agent",
                    "text": "(no response)",
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                continue

            response_data = resp.json()
            all_responses.append(response_data)

            # Extract reply (GUVI checks reply → message → text)
            reply = evaluate_reply_field(response_data)
            if not reply:
                print(f"  {Y}⚠ Empty reply (keys: {list(response_data.keys())}){X}")
                reply = response_data.get("reply", "(empty)")

            reply_display = reply[:120] + "..." if len(reply) > 120 else reply
            print(f"  {G}⬤ Turn {turn_num} [HONEYPOT]:{X}")
            print(f"  {D}{reply_display}{X}")

            # Show extracted intel summary
            intel = response_data.get("extractedIntelligence", {})
            intel_items = []
            for k in ["upiIds", "bankAccounts", "phoneNumbers", "phishingLinks", "emailAddresses"]:
                if intel.get(k):
                    intel_items.append(f"{k}={len(intel[k])}")
            if intel_items:
                print(f"  {Y}📊 {', '.join(intel_items)}{X}")

            scam = response_data.get("scamDetected", False)
            print(f"  {G if scam else D}{'⚡ Scam Detected' if scam else '○ No scam yet'}{X}")

            # ALWAYS update conversation history (GUVI format) — even if reply was empty
            conversation_history.append(message)
            conversation_history.append({
                "sender": "agent",
                "text": reply or "(empty)",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })

        except requests.exceptions.Timeout:
            print(f"  {R}❌ TIMEOUT (>30s) — GUVI would fail this turn{X}")
        except requests.exceptions.ConnectionError:
            print(f"\n{R}❌ Cannot connect to {API_URL}")
            print(f"   Start server or use --remote flag{X}\n")
            sys.exit(1)
        except Exception as e:
            print(f"  {R}❌ Error: {e}{X}")

        time.sleep(0.3)  # Brief pause between turns

    elapsed = time.time() - start_time
    print(f"\n  {D}Conversation completed in {elapsed:.1f}s ({len(all_responses)} responses){X}")

    # Use the LAST response as the "final output" for scoring
    if all_responses:
        return all_responses[-1], len(all_responses), elapsed
    return {}, 0, elapsed


# ─── Main Evaluator ────────────────────────────────────────────────

def main():
    scenarios_to_run = SCENARIOS
    if FAST_MODE:
        # Run 5 diverse scenarios in fast mode
        fast_ids = {"bank_fraud", "phishing_link", "lottery_scam", "tech_support", "insurance"}
        scenarios_to_run = [s for s in SCENARIOS if s["scenarioId"] in fast_ids]

    print(f"\n{B}{M}{'='*70}")
    print(f"  🏆 GUVI EVALUATION SIMULATOR (Full {'5' if FAST_MODE else '15'} Scenarios)")
    print(f"  Exact replica of GUVI's scoring algorithm")
    print(f"  Target: {API_URL}")
    print(f"{'='*70}{X}")

    # Health check
    print(f"\n{B}🏥 Health Check...{X}")
    try:
        health_url = API_URL.replace("/api/honey-pot", "/health")
        health = requests.get(health_url, timeout=15)
        if health.status_code == 200:
            print(f"  {G}✓ Server is healthy{X}")
        else:
            print(f"  {Y}⚠ Health returned {health.status_code}{X}")
    except Exception as e:
        print(f"  {R}❌ Cannot reach server: {e}")
        print(f"  Try: python tests/guvi_evaluator.py --remote{X}")
        sys.exit(1)

    # Run all scenarios
    scenario_results = []
    total_start = time.time()

    for scenario in scenarios_to_run:
        final_output, num_responses, elapsed = run_scenario(scenario)

        if not final_output:
            scenario_results.append({
                "scenario": scenario,
                "scores": {"scamDetection": 0, "intelligence": 0, "engagement": 0, "structure": 0, "total": 0},
                "details": {}, "num_responses": 0
            })
            continue

        # ─── GUVI SCORING (exact algorithm) ─────────────────────
        print(f"\n  {B}{M}📋 SCORING (GUVI Algorithm):{X}")

        s1, d1 = evaluate_scam_detection(final_output)
        print(f"\n  {B}1. Scam Detection ({s1}/20){X}")
        for d in d1: print(f"     {d}")

        s2, d2 = evaluate_intelligence_extraction(final_output, scenario)
        print(f"\n  {B}2. Intelligence Extraction ({s2}/40){X}")
        for d in d2: print(f"     {d}")

        s3, d3 = evaluate_engagement_quality(final_output)
        print(f"\n  {B}3. Engagement Quality ({s3}/20){X}")
        for d in d3: print(f"     {d}")

        s4, d4 = evaluate_response_structure(final_output)
        print(f"\n  {B}4. Response Structure ({s4}/20){X}")
        for d in d4: print(f"     {d}")

        total = s1 + s2 + s3 + s4
        color = G if total >= 90 else Y if total >= 70 else R
        print(f"\n  {color}{B}  SCENARIO SCORE: {total}/100{X}")

        scenario_results.append({
            "scenario": scenario,
            "scores": {
                "scamDetection": s1,
                "intelligence": s2,
                "engagement": s3,
                "structure": s4,
                "total": total
            },
            "details": {"d1": d1, "d2": d2, "d3": d3, "d4": d4},
            "num_responses": num_responses,
            "elapsed": elapsed
        })

    total_time = time.time() - total_start

    # ─── FINAL RESULTS ──────────────────────────────────────────
    print(f"\n\n{'='*70}")
    print(f"{B}{C}  🏆 FINAL EVALUATION RESULTS ({len(scenarios_to_run)} Scenarios){X}")
    print(f"{'='*70}\n")

    print(f"  {'Scenario':<25} {'Det':>5} {'Intel':>6} {'Eng':>5} {'Str':>5} {'Total':>7}")
    print(f"  {'─'*60}")

    overall_total = 0
    for r in scenario_results:
        s = r["scenario"]
        scores = r["scores"]
        total = scores["total"]
        overall_total += total

        color = G if total >= 90 else Y if total >= 70 else R
        print(f"  {color}{s['name']:<25} {scores['scamDetection']:>3}/20 {scores['intelligence']:>4}/40 {scores['engagement']:>3}/20 {scores['structure']:>3}/20 {total:>5}/100{X}")

    avg_score = overall_total / len(scenario_results) if scenario_results else 0
    print(f"  {'─'*60}")
    color = G if avg_score >= 90 else Y if avg_score >= 70 else R
    print(f"  {color}{B}{'AVERAGE SCORE':<25} {'':>5} {'':>6} {'':>5} {'':>5} {avg_score:>5.1f}/100{X}")

    # Score breakdown per category
    print(f"\n  {B}Score Breakdown by Category:{X}")
    categories = ["scamDetection", "intelligence", "engagement", "structure"]
    cat_labels = ["Scam Detection", "Intelligence", "Engagement", "Structure"]
    cat_max = [20, 40, 20, 20]

    for cat, label, mx in zip(categories, cat_labels, cat_max):
        avg = sum(r["scores"][cat] for r in scenario_results) / len(scenario_results)
        bar_len = int(avg / mx * 20)
        bar = "█" * bar_len + "░" * (20 - bar_len)
        color = G if avg >= mx * 0.9 else Y if avg >= mx * 0.7 else R
        print(f"  {color}  {label:<20} {bar} {avg:.1f}/{mx}{X}")

    # Recommendations
    print(f"\n  {B}💡 Recommendations:{X}")
    issues = []

    for r in scenario_results:
        s = r["scenario"]
        scores = r["scores"]

        if scores["scamDetection"] < 20:
            issues.append(f"  {R}⚠ {s['name']}: scamDetected not set to true{X}")
        if scores["intelligence"] < 40:
            issues.append(f"  {Y}⚠ {s['name']}: Intelligence extraction incomplete ({scores['intelligence']}/40){X}")
        if scores["engagement"] < 20:
            issues.append(f"  {Y}⚠ {s['name']}: Engagement not maxed ({scores['engagement']}/20){X}")
        if scores["structure"] < 20:
            issues.append(f"  {Y}⚠ {s['name']}: Missing response fields ({scores['structure']}/20){X}")

    if issues:
        for issue in issues:
            print(issue)
    else:
        print(f"  {G}✅ All checks passed! Ready for submission.{X}")

    print(f"\n  Total test time: {total_time:.1f}s")
    print(f"  Average time per scenario: {total_time/len(scenarios_to_run):.1f}s")
    print(f"{'='*70}\n")

    # Exit code based on score
    if avg_score >= 90:
        print(f"  {G}{B}🎉 EXCELLENT! Ready for GUVI submission.{X}\n")
        sys.exit(0)
    elif avg_score >= 70:
        print(f"  {Y}{B}⚠ GOOD but can be improved. Review recommendations above.{X}\n")
        sys.exit(0)
    else:
        print(f"  {R}{B}❌ NEEDS IMPROVEMENT. Fix issues before submitting.{X}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
