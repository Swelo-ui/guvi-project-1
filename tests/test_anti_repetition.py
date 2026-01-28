"""
Quick test for anti-repetition in fallback system
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import get_random_fallback, get_contextual_fallback, track_response, get_used_responses

def test_anti_repetition():
    print("=" * 50)
    print("Testing Anti-Repetition System")
    print("=" * 50)
    
    session = "test_session_123"
    
    # Test generic fallback anti-repetition
    print("\n1. Testing get_random_fallback (10 calls):")
    responses = []
    for i in range(10):
        r = get_random_fallback(session)
        responses.append(r)
        print(f"   {i+1}. {r[:45]}...")
    
    unique = len(set(responses))
    print(f"\n   Unique responses: {unique}/10")
    print(f"   Status: {'✅ PASS' if unique == 10 else '❌ FAIL - duplicates found'}")
    
    # Test contextual fallback anti-repetition
    print("\n2. Testing get_contextual_fallback (5 calls with same message):")
    session2 = "test_session_456"
    message = "Share your OTP immediately"
    
    ctx_responses = []
    for i in range(5):
        r = get_contextual_fallback(message, session2, [])
        ctx_responses.append(r)
        print(f"   {i+1}. {r[:50]}...")
    
    ctx_unique = len(set(ctx_responses))
    print(f"\n   Unique responses: {ctx_unique}/5")
    print(f"   Status: {'✅ PASS' if ctx_unique == 5 else '❌ FAIL - duplicates found'}")
    
    print("\n" + "=" * 50)
    print(f"Overall: {'✅ ALL TESTS PASSED' if unique == 10 and ctx_unique == 5 else '❌ SOME TESTS FAILED'}")
    print("=" * 50)

if __name__ == "__main__":
    test_anti_repetition()
