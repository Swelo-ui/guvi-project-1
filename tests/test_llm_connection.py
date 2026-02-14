import os
import sys
from dotenv import load_dotenv

# Load env vars
load_dotenv()

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.llm_client import call_openrouter, OPENROUTER_MODEL

def run_connection_test():
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        print("❌ ERROR: OPENROUTER_API_KEY is not set in environment or .env file")
        return

    print(f"🔑 API Key found: {api_key[:5]}...{api_key[-4:]}")
    print(f"🤖 Testing Model: {OPENROUTER_MODEL}")

    messages = [{"role": "user", "content": "Hello, are you active? Reply with 'Yes working'."}]
    
    print("\n⏳ Sending request to OpenRouter...")
    response = call_openrouter(messages, model=OPENROUTER_MODEL)

    if response:
        print(f"\n✅ SUCCESS: LLM Responded:\n{response}")
    else:
        print("\n❌ FAILURE: No response from LLM.")

if __name__ == "__main__":
    run_connection_test()
