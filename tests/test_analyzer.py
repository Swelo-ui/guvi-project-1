"""
Quick test for the conversation analyzer module
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.conversation_analyzer import detect_intents, ScammerIntent, analyze_conversation, CONTEXTUAL_RESPONSES

def test_intent_detection():
    print("=" * 50)
    print("Testing Intent Detection")
    print("=" * 50)
    
    test_cases = [
        ("Share your OTP immediately to verify", ["otp"]),
        ("Your account will be blocked. Give account number", ["account_number", "fear_tactic"]),
        ("You are under digital arrest by CBI", ["fear_tactic"]),
        ("Send Rs.5000 to verify your identity", ["money_transfer"]),
        ("Click this link to update KYC: bit.ly/xyz", ["click_link"]),
        ("Install AnyDesk app for remote support", ["install_app"]),
        ("Give me your UPI ID urgently", ["upi_id", "urgency"]),
    ]
    
    for message, expected in test_cases:
        intents = detect_intents(message)
        intent_values = [i.value for i in intents]
        status = "✅" if any(e in intent_values for e in expected) else "❌"
        print(f"{status} '{message[:40]}...'")
        print(f"   Expected: {expected}")
        print(f"   Got: {intent_values}")
        print()

def test_contextual_responses():
    print("=" * 50)
    print("Testing Contextual Response Pools")
    print("=" * 50)
    
    for intent in [ScammerIntent.OTP, ScammerIntent.ACCOUNT_NUMBER, ScammerIntent.UPI_ID, ScammerIntent.FEAR_TACTIC]:
        responses = CONTEXTUAL_RESPONSES.get(intent, [])
        print(f"\n{intent.value.upper()} ({len(responses)} responses):")
        for r in responses[:2]:
            print(f"  - {r[:50]}...")

def test_full_analysis():
    print("\n" + "=" * 50)
    print("Testing Full Conversation Analysis")
    print("=" * 50)
    
    message = "URGENT: Your SBI account will be blocked. Share OTP now to verify."
    history = []
    used = []
    
    analysis = analyze_conversation(message, history, used)
    print(f"\nMessage: {message}")
    print(f"Primary Intent: {analysis['primary_intent']}")
    print(f"All Intents: {analysis['detected_intents']}")
    print(f"Phase: {analysis['conversation_phase']}")
    print(f"Suggested Response: {analysis['suggested_fallback']}")
    print(f"Should Extract: {analysis['should_reverse_extract']}")
    if analysis.get('reverse_extraction_prompt'):
        print(f"Extraction Prompt: {analysis['reverse_extraction_prompt']}")

if __name__ == "__main__":
    test_intent_detection()
    test_contextual_responses()
    test_full_analysis()
    print("\n✅ All tests completed!")
