"""
Treasury Module - Shared Utilities and Configuration

Provides shared utilities for the treasury system:
- Database and auth initialization
- Permission checking
- Encryption for sensitive financial data
- Common constants
"""
import os
import sys
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from cryptography.fernet import Fernet

# Security
security = HTTPBearer()

# Global state
_db = None
_verify_token_func = None
_cipher_suite = None

# Default categories
DEFAULT_INCOME_CATEGORIES = [
    "Dues", "Donations", "Merchandise", "Fundraising", "Events", "Sponsorships", "Other Income"
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Fuel", "Food & Beverages", "Merchandise Cost", "Event Expenses", "Supplies", 
    "Equipment", "Repairs & Maintenance", "Insurance", "Fees & Licenses", 
    "Charity/Donations", "Marketing", "Administrative", "Other Expense"
]

# Sensitive fields that need encryption
ENCRYPTED_TRANSACTION_FIELDS = ['description', 'vendor_payee', 'reference_number', 'notes']
ENCRYPTED_ACCOUNT_FIELDS = ['name', 'description']


def init_treasury_module(database, token_verifier):
    """Initialize treasury module with database and auth dependencies"""
    global _db, _verify_token_func, _cipher_suite
    _db = database
    _verify_token_func = token_verifier
    
    # Initialize encryption
    encryption_key = os.environ.get('ENCRYPTION_KEY')
    if encryption_key:
        _cipher_suite = Fernet(encryption_key.encode())
        sys.stderr.write("✅ [TREASURY] Encryption enabled for financial data\n")
    else:
        sys.stderr.write("⚠️ [TREASURY] WARNING: ENCRYPTION_KEY not set - financial data will NOT be encrypted!\n")


def get_db():
    """Get database instance"""
    if _db is None:
        raise HTTPException(status_code=500, detail="Database not initialized")
    return _db


def encrypt_value(value: str) -> str:
    """Encrypt a single value using AES-256 (Fernet)"""
    if not value or not _cipher_suite:
        return value
    try:
        return _cipher_suite.encrypt(value.encode()).decode()
    except Exception as e:
        sys.stderr.write(f"[TREASURY] Encryption error: {e}\n")
        return value


def decrypt_value(encrypted_value: str) -> str:
    """Decrypt a single value"""
    if not encrypted_value or not _cipher_suite:
        return encrypted_value
    try:
        return _cipher_suite.decrypt(encrypted_value.encode()).decode()
    except Exception:
        # If decryption fails, data might not be encrypted (backward compatibility)
        return encrypted_value


def encrypt_transaction(transaction: dict) -> dict:
    """Encrypt sensitive transaction fields before storing"""
    encrypted = transaction.copy()
    for field in ENCRYPTED_TRANSACTION_FIELDS:
        if field in encrypted and encrypted[field]:
            encrypted[field] = encrypt_value(str(encrypted[field]))
    return encrypted


def decrypt_transaction(transaction: dict) -> dict:
    """Decrypt sensitive transaction fields for display"""
    if not transaction:
        return transaction
    decrypted = transaction.copy()
    for field in ENCRYPTED_TRANSACTION_FIELDS:
        if field in decrypted and decrypted[field]:
            decrypted[field] = decrypt_value(decrypted[field])
    return decrypted


def encrypt_account(account: dict) -> dict:
    """Encrypt sensitive account fields before storing"""
    encrypted = account.copy()
    for field in ENCRYPTED_ACCOUNT_FIELDS:
        if field in encrypted and encrypted[field]:
            encrypted[field] = encrypt_value(str(encrypted[field]))
    return encrypted


def decrypt_account(account: dict) -> dict:
    """Decrypt sensitive account fields for display"""
    if not account:
        return account
    decrypted = account.copy()
    for field in ENCRYPTED_ACCOUNT_FIELDS:
        if field in decrypted and decrypted[field]:
            decrypted[field] = decrypt_value(decrypted[field])
    return decrypted


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Verify token and return current user"""
    if _verify_token_func is None:
        raise HTTPException(status_code=500, detail="Auth not initialized")
    return await _verify_token_func(credentials)


def check_treasury_permission(current_user: dict, permission: str) -> bool:
    """Check if user has specific treasury permission
    
    Permissions:
    - view_treasury: Can view financial data (read-only)
    - manage_treasury: Can add/edit/delete transactions
    - treasury_admin: Full access including reports and settings
    """
    if current_user.get("role") == "admin":
        return True
    
    permissions = current_user.get("permissions", {})
    
    # treasury_admin has all permissions
    if permissions.get("treasury_admin"):
        return True
    
    # manage_treasury includes view
    if permission == "view_treasury" and permissions.get("manage_treasury"):
        return True
    
    return permissions.get(permission, False)


def require_treasury_permission(permission: str):
    """Decorator-style permission check that raises HTTPException"""
    def check(current_user: dict):
        if not check_treasury_permission(current_user, permission):
            raise HTTPException(
                status_code=403, 
                detail=f"Permission denied. Required: {permission}"
            )
        return True
    return check
