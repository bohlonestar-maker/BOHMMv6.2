"""
Document Signing - Shared Utilities and Configuration

This module provides shared utilities for the document signing system:
- Database and auth initialization
- Encryption/decryption helpers
- Token generation
- Document hashing
- National Officers configuration
"""
import os
import sys
import uuid
import hashlib
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet

# Security
security = HTTPBearer()

# National Officers who can be selected as approvers
NATIONAL_OFFICERS = [
    {"role": "national_secretary", "title": "SEC", "display_title": "National Secretary", "order": 1},
    {"role": "national_treasurer", "title": "T", "display_title": "National Treasurer", "order": 2},
    {"role": "national_sergeant_at_arms", "title": "S@A", "display_title": "National Sergeant at Arms", "order": 3},
    {"role": "national_vice_president", "title": "VP", "display_title": "National Vice President", "order": 4},
    {"role": "coo", "title": "COO", "display_title": "COO", "order": 5},
    {"role": "national_president", "title": "Prez", "display_title": "National President", "order": 6},
]

# Global state for database and auth
_db = None
_verify_token_func = None
_verify_admin_func = None
_cipher_suite = None


def init_documents_module(database, token_verifier, admin_verifier):
    """Initialize document module with database and auth dependencies"""
    global _db, _verify_token_func, _verify_admin_func
    _db = database
    _verify_token_func = token_verifier
    _verify_admin_func = admin_verifier


def get_db():
    """Get database instance"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token and return current user"""
    if _verify_token_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _verify_token_func(credentials)


def get_cipher():
    """Get or initialize cipher suite for email decryption"""
    global _cipher_suite
    if _cipher_suite is None:
        encryption_key = os.environ.get('ENCRYPTION_KEY', '').strip('"')
        if encryption_key:
            try:
                _cipher_suite = Fernet(encryption_key.encode())
            except Exception as e:
                sys.stderr.write(f"[DOCS] Warning: Encryption setup failed: {e}\n")
    return _cipher_suite


def decrypt_email(encrypted_data: str) -> str:
    """Decrypt email data, returns original if decryption fails"""
    if not encrypted_data:
        return encrypted_data
    cipher = get_cipher()
    if not cipher:
        return encrypted_data
    try:
        return cipher.decrypt(encrypted_data.encode()).decode()
    except Exception:
        return encrypted_data


def generate_signing_token() -> str:
    """Generate a secure, unique signing token"""
    return f"{uuid.uuid4()}-{uuid.uuid4()}"


def hash_document(content: bytes) -> str:
    """Generate SHA-256 hash of document content for integrity verification"""
    return hashlib.sha256(content).hexdigest()


def check_document_permission(current_user: dict) -> bool:
    """Check if user has permission to manage documents"""
    permissions = current_user.get("permissions", {})
    return permissions.get("send_documents") or current_user.get("role") == "admin"
