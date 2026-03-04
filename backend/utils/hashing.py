# Hashing utilities for duplicate detection and data integrity
import hashlib


def hash_for_duplicate_detection(data: str) -> str:
    """
    Create a deterministic hash for duplicate detection of encrypted fields.
    Uses SHA-256 hash with normalized (lowercase, stripped) input.
    """
    if not data:
        return ""
    # Lowercase and strip before hashing for case-insensitive duplicate detection
    normalized_data = data.lower().strip()
    return hashlib.sha256(normalized_data.encode()).hexdigest()


def hash_email_for_lookup(email: str) -> str:
    """
    Create a hash of email for fast duplicate lookups.
    Same as hash_for_duplicate_detection but with explicit email context.
    """
    return hash_for_duplicate_detection(email)
