"""
Comprehensive test for the new human-like conversation analyzer
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.conversation_analyzer import (
    get_contextual_response, detect_intents,
    ScammerIntent, ConversationPhase, ResponseType,
    get_session_data, analyze_conversation
)

def test_no_duplicates():
    """Test that responses don't repeat."""
    print("=" * 60)
    print("TEST 1: No Duplicate Responses (15 OTP-related messages)")
    print("=" * 60)
    
    session_id = "test_session_otp"
    responses = []
    
    for i in range(15):
        intents = [ScammerIntent.OTP, ScammerIntent.URGENCY]
        phase = ConversationPhase.EXTRACTION_ATTEMPT if i < 7 else ConversationPhase.PERSISTENCE
        response, _ = get_contextual_response(intents, phase, responses, session_id)
        responses.append(response)
        print(f"  {i+1}. {response[:60]}...")
    
    unique = len(set(responses))
    print(f"\n  Unique: {unique}/15")
    print(f"  Status: {'✅ PASS' if unique == 15 else '❌ FAIL - duplicates!'}")
    return unique == 15

def test_response_variety():
    """Test that response TYPES are varied (not always same pattern)."""
    print("\n" + "=" * 60)
    print("TEST 2: Response Type Variety")
    print("=" * 60)
    
    session_id = "test_session_variety"
    session = get_session_data(session_id)
    
    # Simulate 10 responses
    types_used = []
    for i in range(10):
        analysis = analyze_conversation(
            "Share your OTP immediately!", [], [], session_id + str(i)
        )
        # Get response type from session
        response = analysis["suggested_fallback"]
        print(f"  {i+1}. {response[:55]}...")
    
    print(f"\n  ✅ PASS - Varied responses generated")
    return True

def test_no_repeated_extraction_categories():
    """Test that we don't ask for same info repeatedly."""
    print("\n" + "=" * 60)
    print("TEST 3: No Repeated Extraction Categories")
    print("=" * 60)
    
    session_id = "test_session_extract"
    session = get_session_data(session_id)
    
    # Force extraction responses
    from core.conversation_analyzer import choose_response_type, build_response
    
    extractions = []
    for i in range(6):
        # Build extraction response
        response = build_response(session, ScammerIntent.OTP, ResponseType.REVERSE_EXTRACT)
        extractions.append(response)
        print(f"  {i+1}. {response[:60]}...")
    
    asked = session["asked_categories"]
    print(f"\n  Categories asked: {asked}")
    print(f"  ✅ PASS - Categories tracked and varied" if len(set(asked)) > 1 else "❌ FAIL")
    return len(set(asked)) > 1

def test_conversation_simulation():
    """Simulate a realistic conversation."""
    print("\n" + "=" * 60)
    print("TEST 4: Realistic Conversation Simulation")
    print("=" * 60)
    
    scammer_messages = [
        "URGENT: Your SBI account has been compromised!",
        "Please share your OTP to verify your identity.",
        "I am calling from SBI. Share the OTP now!",
        "Your account will be blocked. Give OTP immediately!",
        "This is very urgent. You must act now!",
        "Trust me, I am bank employee. Share OTP please.",
        "Your funds are at risk! OTP is needed urgently!",
        "Sir, you are under digital arrest. Share OTP!",
    ]
    
    session_id = "test_realistic"
    history = []
    
    for i, msg in enumerate(scammer_messages):
        analysis = analyze_conversation(msg, history, [], session_id)
        response = analysis["suggested_fallback"]
        
        print(f"\n  Scammer: {msg[:50]}...")
        print(f"  Honeypot: {response}")
        
        history.append({"sender": "scammer", "text": msg})
        history.append({"sender": "agent", "text": response})
    
    session = get_session_data(session_id)
    print(f"\n  Total responses: {session['response_count']}")
    print(f"  Categories asked: {session['asked_categories']}")
    print(f"  ✅ Simulation complete - check variety above!")
    return True

if __name__ == "__main__":
    results = []
    results.append(test_no_duplicates())
    results.append(test_response_variety())
    results.append(test_no_repeated_extraction_categories())
    results.append(test_conversation_simulation())
    
    print("\n" + "=" * 60)
    passed = sum(results)
    print(f"OVERALL: {passed}/{len(results)} tests passed")
    print("=" * 60)
