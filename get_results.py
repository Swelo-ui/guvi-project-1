"""
Get Full Conversation Results from Supabase
This shows all the extracted intelligence from your honeypot sessions
"""
import requests
import json

# Supabase Config
SUPABASE_URL = "https://bmdoouzqinpydwzktmfz.supabase.co"
SUPABASE_KEY = "sb_publishable_KkVlZEWWHJki51t8eUvfEA_eHoDvAVv"

headers = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}

print("📊 Fetching Honeypot Results from Supabase...")
print("=" * 60)

# Get intelligence data
try:
    # Get all intelligence records
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/intelligence?order=created_at.desc&limit=10",
        headers=headers,
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n🔍 Found {len(data)} intelligence records:\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        # Save to file
        with open("guvi_intelligence.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n✅ Saved to guvi_intelligence.json")
    else:
        print(f"Status: {response.status_code}")
        print(response.text)
        
except Exception as e:
    print(f"Error: {e}")

print("\n" + "=" * 60)

# Get conversations
try:
    response = requests.get(
        f"{SUPABASE_URL}/rest/v1/conversations?order=created_at.desc&limit=5",
        headers=headers,
        timeout=15
    )
    
    if response.status_code == 200:
        data = response.json()
        print(f"\n💬 Found {len(data)} conversation records:\n")
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
        with open("guvi_conversations.json", "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        print("\n✅ Saved to guvi_conversations.json")
    else:
        print(f"Status: {response.status_code}")
        
except Exception as e:
    print(f"Error: {e}")
