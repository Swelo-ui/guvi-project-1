"""
Realistic Indian Fake Data Generators
Bank accounts, UPI IDs, IFSC codes, phone numbers - all following real formats
"""

import random
import json
import os
from typing import Dict, Any
from utils.luhn import generate_valid_card_number


# Load Indian data
DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'indian_data.json')

def load_indian_data() -> Dict[str, Any]:
    """Load the Indian data JSON file."""
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


INDIAN_DATA = None

def get_indian_data() -> Dict[str, Any]:
    """Get cached Indian data."""
    global INDIAN_DATA
    if INDIAN_DATA is None:
        INDIAN_DATA = load_indian_data()
    return INDIAN_DATA


def generate_bank_account(bank: Dict[str, Any], rng: random.Random = None) -> str:
    """
    Generate realistic bank account number based on bank-specific format.
    
    Args:
        bank: Bank configuration dict with account_length and account_prefixes
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Bank account number string
    """
    rng = rng or random
    length = bank['account_length']
    prefixes = bank['account_prefixes']
    
    # Select a prefix
    prefix = rng.choice(prefixes) if prefixes and prefixes[0] else ""
    
    # Generate remaining digits
    remaining = length - len(prefix)
    account = prefix + ''.join([str(rng.randint(0, 9)) for _ in range(remaining)])
    
    return account


def generate_ifsc_code(bank: Dict[str, Any], rng: random.Random = None) -> str:
    """
    Generate valid IFSC code for the bank.
    Format: [4 letters bank code][0][6 alphanumeric branch code]
    
    Args:
        bank: Bank configuration dict with ifsc_prefix
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Valid IFSC code string
    """
    rng = rng or random
    prefix = bank['ifsc_prefix']  # e.g., "SBIN0"
    
    # Generate 6-digit branch code (mostly numeric for Indian banks)
    branch_code = ''.join([str(rng.randint(0, 9)) for _ in range(6)])
    
    return prefix + branch_code


def generate_upi_id(name: str, bank: Dict[str, Any], rng: random.Random = None) -> str:
    """
    Generate realistic UPI ID based on name.
    
    Args:
        name: Person's first name
        bank: Bank configuration dict with upi_handle
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Realistic UPI ID like "kamala67@ybl"
    """
    rng = rng or random
    # Clean name for UPI (lowercase, no spaces)
    clean_name = name.lower().replace(' ', '').replace('.', '')
    
    # Add random 2-digit suffix (common pattern)
    suffix = rng.randint(10, 99)
    
    # Select UPI handle - prioritize PhonePe/GPay handles as they're most common
    common_handles = ['@ybl', '@okicici', '@oksbi', '@paytm', '@axl']
    bank_handle = bank.get('upi_handle', '@ybl')
    
    # 70% chance of common handle, 30% bank-specific
    handle = rng.choice(common_handles) if rng.random() > 0.3 else bank_handle
    
    return f"{clean_name}{suffix}{handle}"


def generate_phone_number(rng: random.Random = None) -> str:
    """
    Generate realistic Indian mobile number.
    Format: +91 9XXXX XXXXX (starting with 6-9)
    
    Args:
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Indian phone number string
    """
    rng = rng or random
    first_digit = rng.choice(['6', '7', '8', '9'])
    rest = ''.join([str(rng.randint(0, 9)) for _ in range(9)])
    
    # Format with spaces for readability
    full = first_digit + rest
    return f"+91 {full[:5]} {full[5:]}"


def generate_card_details(rng: random.Random = None) -> Dict[str, str]:
    """
    Generate realistic debit card details.
    
    Args:
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Dict with card_type, card_number, last_four, expiry
    """
    rng = rng or random
    data = get_indian_data()
    
    # RuPay is most common in India
    card_types = data['card_types']
    weights = [0.7, 0.2, 0.1]  # RuPay most common
    card_type = rng.choices(card_types, weights=weights)[0]
    
    prefix = rng.choice(card_type['prefixes'])
    card_number = generate_valid_card_number(prefix, 16)
    
    # Generate expiry (2-4 years in future)
    month = str(rng.randint(1, 12)).zfill(2)
    year = str(rng.randint(27, 30))
    
    return {
        'type': card_type['type'],
        'number': card_number,
        'last_four': card_number[-4:],
        'expiry': f"{month}/{year}"
    }


def generate_complete_financial_identity(first_name: str, rng: random.Random = None) -> Dict[str, Any]:
    """
    Generate complete financial identity for a persona.
    
    Args:
        first_name: Person's first name for UPI generation
        rng: Optional seeded Random instance for deterministic output
    
    Returns:
        Dict with bank, account, IFSC, UPI, card details
    """
    rng = rng or random
    data = get_indian_data()
    
    # Select a bank
    bank = rng.choice(data['banks'])
    
    # Generate all financial data
    account_number = generate_bank_account(bank, rng)
    ifsc_code = generate_ifsc_code(bank, rng)
    upi_id = generate_upi_id(first_name, bank, rng)
    card = generate_card_details(rng)
    phone = generate_phone_number(rng)
    
    return {
        'bank': {
            'name': bank['name'],
            'short': bank['short'],
            'account_number': account_number,
            'ifsc': ifsc_code,
            'branch': f"{rng.choice(data['cities'])['name']} Main Branch"
        },
        'upi': {
            'primary': upi_id,
            'phone_linked': phone.replace(' ', '').replace('+91', '') + '@ybl'
        },
        'card': card,
        'phone': phone
    }
