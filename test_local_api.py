import requests
import json
import time
import random

API_URL = "http://localhost:5001/api/honey-pot"
API_KEY = "sk_ironmask_hackathon_2026"
SESSION_ID = f"test_consistency_{int(time.time())}"

headers = {
    "Content-Type": "application/json",
    "x-api-key": API_KEY
}

conversation_history = []

def send_message(text):
    print(f"\n📩 Scammer: {text}")
    
    payload = {
        "sessionId": SESSION_ID,
        "message": {"text": text},
        "conversationHistory": conversation_history
    }
    
    try:
        response = requests.post(API_URL, json=payload, headers=headers)
        if response.status_code == 200:
            data = response.json()
            reply = data.get("reply", "")
            agent_notes = data.get("agentNotes", "")
            
            print(f"🤖 Agent: {reply}")
            print(f"📝 Notes: {agent_notes[:100]}...")
            
            # Update history
            conversation_history.append({"sender": "scammer", "text": text})
            conversation_history.append({"sender": "agent", "text": reply})
            
            return reply
        else:
            print(f"❌ Error: {response.status_code}")
            return ""
    except Exception as e:
        print(f"❌ Exception: {e}")
        return ""

print(f"🚀 Testing Consistency for Session: {SESSION_ID}")
time.sleep(2)

# Turn 1
reply1 = send_message("Hello, I am calling from SBI bank. Your account is blocked.")

# Turn 2
reply2 = send_message("Yes, urgent. Give me your account number immediately.")

# Turn 3
reply3 = send_message("Madam, verify quickly. What is your son's name? We need to verify with him.")

# Turn 4
reply4 = send_message("Okay, give me the OTP sent to your phone number ending in 9898.")

print("\n✅ Test Complete. Check manually for:")
print("1. Did the name/son's name change?")
print("2. Was there repetition of 'network slow'?")
