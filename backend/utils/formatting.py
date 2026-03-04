# Phone number and data formatting utilities
import re


def format_phone_number(phone: str) -> str:
    """Format phone number to (xxx) xxx-xxxx format"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Return original if not 10 digits
    return phone


def normalize_name(name: str) -> str:
    """Normalize a name by removing extra spaces and standardizing whitespace"""
    if not name:
        return ""
    # Replace multiple spaces with single space, strip leading/trailing
    return ' '.join(name.split())


def fuzzy_name_match(name1: str, name2: str) -> bool:
    """
    Check if two names match after normalization.
    Handles variations in spacing and case.
    """
    if not name1 or not name2:
        return False
    return normalize_name(name1).lower() == normalize_name(name2).lower()
