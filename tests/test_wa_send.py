
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def main():
    PHONE_ID = os.getenv("WHATSAPP_PHONE_ID")
    TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
    TO_NUMBER = "916265643703"

    if not PHONE_ID or not TOKEN:
        print("❌ Error: Missing credentials in .env")
        exit(1)

    print(f"Testing WhatsApp Send...")
    print(f"Phone ID: {PHONE_ID}")
    print(f"To: {TO_NUMBER}")

    url = f"https://graph.facebook.com/v18.0/{PHONE_ID}/messages"
    headers = {
        "Authorization": f"Bearer {TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": TO_NUMBER,
        "type": "text",
        "text": {"body": "🔔 Test message from Iron-Mask Honeypot Debugger"}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")

        if response.status_code == 200:
            print("✅ SUCCESS! Message sent.")
        else:
            print("❌ FAILED. Check credentials.")
    except Exception as e:
        print(f"Exception: {e}")

if __name__ == "__main__":
    main()
