"""
Test conversation memory and personalization
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.conversation_analyzer import analyze_conversation, get_session_data, get_conversation_intel

def test_memory():
    print("=" * 60)
    print("TEST: Conversation Memory and Personalization")
    print("=" * 60)
    
    # Simulate a real conversation where scammer reveals info
    history = [
        {"sender": "scammer", "text": "I am Rajesh from SBI headquarters. Your account is blocked."},
        {"sender": "agent", "text": "Oh no! What happened?"},
        {"sender": "scammer", "text": "Share your OTP, my employee ID is SBI12345 and phone +91-9876543210"},
        {"sender": "agent", "text": "Wait..."},
        {"sender": "scammer", "text": "Please share OTP urgently! My UPI is rajesh@sbi"},
    ]
    
    analysis = analyze_conversation(
        "Share the OTP immediately now! This is your last chance!",
        history, [], "test_memory_session"
    )
    
    print("\n=== SCAMMER MEMORY ===")
    print(f"  Name: {analysis['scammer_memory']['name']}")
    print(f"  Bank: {analysis['scammer_memory']['bank']}")
    print(f"  Employee ID: {analysis['scammer_memory']['employee_id']}")
    print(f"  Times asked OTP: {analysis['scammer_memory']['times_asked_otp']}")
    print(f"  Urgency level: {analysis['scammer_memory']['urgency_level']}")
    print(f"  Scam type: {analysis['scam_type']}")
    print(f"  Scammer frustrated: {analysis['scammer_frustrated']}")
    
    print("\n=== RESPONSE ===")
    print(f"  {analysis['suggested_fallback']}")
    
    # Check memory extraction worked
    mem = analysis['scammer_memory']
    success = (
        mem['name'] == "Rajesh" and
        mem['bank'] == "SBI" and
        mem['employee_id'] is not None
    )
    
    print(f"\n=== RESULT: {'✅ PASS' if success else '❌ FAIL'} ===")
    return success

if __name__ == "__main__":
    test_memory()
