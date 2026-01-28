"""
Luhn Algorithm Implementation for Valid Card Number Generation
"""


def calculate_luhn_checksum(partial_number: str) -> int:
    """
    Calculate the Luhn check digit for a partial card number.
    
    Args:
        partial_number: Card number without the check digit (15 digits for 16-digit card)
    
    Returns:
        The check digit (0-9) that makes the full number valid
    """
    digits = [int(d) for d in partial_number]
    
    # Double every second digit from the right (which is every first from left for partial)
    for i in range(len(digits) - 1, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    
    total = sum(digits)
    check_digit = (10 - (total % 10)) % 10
    
    return check_digit


def is_valid_luhn(card_number: str) -> bool:
    """
    Validate a card number using Luhn algorithm.
    
    Args:
        card_number: Full card number as string
    
    Returns:
        True if valid, False otherwise
    """
    if not card_number.isdigit():
        return False
    
    digits = [int(d) for d in card_number]
    
    # Double every second digit from the right
    for i in range(len(digits) - 2, -1, -2):
        digits[i] *= 2
        if digits[i] > 9:
            digits[i] -= 9
    
    return sum(digits) % 10 == 0


def generate_valid_card_number(prefix: str, total_length: int = 16) -> str:
    """
    Generate a valid card number with given prefix.
    
    Args:
        prefix: Card prefix (e.g., "4" for Visa, "6521" for RuPay)
        total_length: Total length of card number (default 16)
    
    Returns:
        A valid card number that passes Luhn check
    """
    import random
    
    # Generate random digits for the middle part
    remaining_length = total_length - len(prefix) - 1  # -1 for check digit
    middle = ''.join([str(random.randint(0, 9)) for _ in range(remaining_length)])
    
    # Combine prefix and middle
    partial = prefix + middle
    
    # Calculate check digit
    check_digit = calculate_luhn_checksum(partial)
    
    return partial + str(check_digit)
