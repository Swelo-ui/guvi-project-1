import requests
import json
import sys

# Your Render Deployment URL (from your screenshot)
BASE_URL = "https://guvi-project-1-wefr.onrender.com"
API_URL = f"{BASE_URL}/api/honey-pot"
API_KEY = "sk_ironmask_hackathon_2026"

def main():
    payload = {
        "sessionId": "test_manual_verifier_001",
        "message": {
            "text": "Hello sir, I am calling from the bank. We need your OTP to verify your account."
        },
        "conversationHistory": []
    }

    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY
    }

    print(f"🚀 Testing Remote API at: {API_URL}")
    print("-" * 50)

    try:
        response = requests.post(API_URL, json=payload, headers=headers)

        print(f"Status Code: {response.status_code}")
        print("\nResponse Body:")
        print(json.dumps(response.json(), indent=2))

        if response.status_code == 200:
            print("\n✅ SUCCESS: API is reachable and authorized!")
        else:
            print("\n❌ FAILED: API returned an error.")

    except Exception as e:
        print(f"\n❌ ERROR: Could not connect to API. {e}")
        print("Check if the Render service is fully deployed and awake (it might take a minute to wake up).")

if __name__ == "__main__":
    main()
