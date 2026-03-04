# Input sanitization utilities for security
import re


def sanitize_for_regex(input_str: str) -> str:
    """
    Sanitize user input for safe use in MongoDB regex queries.
    Escapes all regex special characters to prevent ReDoS and injection attacks.
    """
    if not isinstance(input_str, str):
        return ""
    # Escape all regex metacharacters
    return re.escape(input_str)


def sanitize_string_input(input_val) -> str:
    """
    Ensure input is a plain string - prevents NoSQL injection via object injection.
    If input is not a string, convert it or return empty string.
    """
    if input_val is None:
        return ""
    if isinstance(input_val, str):
        return input_val
    # If someone tries to pass {"$ne": ""} or similar, convert to string representation
    return str(input_val)


def sanitize_search_query(query: str) -> str:
    """
    Sanitize search query input.
    Combines string sanitization and regex escaping.
    """
    sanitized = sanitize_string_input(query)
    return sanitize_for_regex(sanitized)
