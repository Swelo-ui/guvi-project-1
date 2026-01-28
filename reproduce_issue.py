import json
import logging
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.llm_client import clean_json_string

# Mock logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def parse_response(raw_response):
    try:
        # USE THE REAL CLEANING FUNCTION
        cleaned = clean_json_string(raw_response)
        return json.loads(cleaned)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse JSON even after cleaning. Raw: {raw_response}")
    
    return None

# Test Cases
test_cases = [
    # Case 1: Clean JSON
    """{
        "scam_detected": true,
        "response": "Hello beta"
    }""",
    
    # Case 2: JSON with markdown code blocks
    """```json
    {
        "scam_detected": true,
        "response": "Hello beta"
    }
    ```""",
    
    # Case 3: JSON with text before and after
    """Here is the response:
    {
        "scam_detected": true,
        "response": "Hello beta"
    }
    Hope this helps.""",
    
    # Case 4: Malformed JSON (trailing comma - common LLM error)
    """{
        "scam_detected": true,
        "response": "Hello beta",
    }""",
    
    # Case 5: Malformed JSON (single quotes)
    """{
        'scam_detected': True,
        'response': 'Hello beta'
    }"""
]

print("--- Testing JSON Parsing Logic ---")
for i, case in enumerate(test_cases):
    print(f"\nCase {i+1}:")
    print(f"Input:\n{case}")
    result = parse_response(case)
    if result:
        print(f"SUCCESS: Parsed: {result}")
    else:
        print("FAILURE: Could not parse")
