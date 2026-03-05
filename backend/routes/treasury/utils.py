"""
Treasury Module - Shared Utilities and Configuration

Provides shared utilities for the treasury system:
- Database and auth initialization
- Permission checking
- Encryption for sensitive financial data
- Audit logging for compliance
- Common constants
"""
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional, Any, Dict
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


# =====================
# AUDIT LOGGING
# =====================

# Audit action types
AUDIT_ACTIONS = {
    # Account actions
    "account_created": "Account Created",
    "account_updated": "Account Updated",
    "account_deleted": "Account Deleted",
    "account_balance_adjusted": "Balance Adjusted",
    "account_transfer": "Funds Transferred",
    
    # Transaction actions
    "transaction_created": "Transaction Created",
    "transaction_updated": "Transaction Updated",
    "transaction_deleted": "Transaction Deleted",
    "receipt_uploaded": "Receipt Uploaded",
    
    # Category actions
    "category_created": "Category Created",
    "category_updated": "Category Updated",
    "category_deleted": "Category Deleted",
    
    # Budget actions
    "budget_created": "Budget Created",
    "budget_updated": "Budget Updated",
    "budget_deleted": "Budget Deleted",
}


async def log_audit(
    action: str,
    entity_type: str,
    entity_id: str,
    entity_name: str,
    user: dict,
    details: Optional[Dict[str, Any]] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None
):
    """
    Log an audit event for Treasury operations
    
    Args:
        action: Action type (e.g., 'account_created', 'transaction_deleted')
        entity_type: Type of entity ('account', 'transaction', 'category', 'budget')
        entity_id: ID of the affected entity
        entity_name: Human-readable name of the entity
        user: Current user dict with username, role
        details: Additional details about the action
        old_values: Previous values (for updates)
        new_values: New values (for updates)
    """
    db = get_db()
    
    audit_entry = {
        "id": str(uuid.uuid4()),
        "action": action,
        "action_display": AUDIT_ACTIONS.get(action, action),
        "entity_type": entity_type,
        "entity_id": entity_id,
        "entity_name": entity_name,
        "user_id": user.get("id") or user.get("_id"),
        "username": user.get("username", "unknown"),
        "user_role": user.get("role", "unknown"),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "details": details,
        "old_values": old_values,
        "new_values": new_values
    }
    
    try:
        await db.treasury_audit_log.insert_one(audit_entry)
    except Exception as e:
        # Don't fail the main operation if audit logging fails
        sys.stderr.write(f"[TREASURY AUDIT] Error logging audit: {e}\n")


async def get_audit_logs(
    entity_type: str = None,
    entity_id: str = None,
    action: str = None,
    username: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0
) -> dict:
    """
    Retrieve audit logs with filtering
    
    Returns:
        Dict with 'logs' list and 'total' count
    """
    db = get_db()
    
    query = {}
    
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id
    if action:
        query["action"] = action
    if username:
        query["username"] = {"$regex": username, "$options": "i"}
    if start_date:
        query["timestamp"] = {"$gte": start_date}
    if end_date:
        if "timestamp" in query:
            query["timestamp"]["$lte"] = end_date
        else:
            query["timestamp"] = {"$lte": end_date}
    
    total = await db.treasury_audit_log.count_documents(query)
    
    logs = await db.treasury_audit_log.find(
        query, {"_id": 0}
    ).sort("timestamp", -1).skip(offset).limit(limit).to_list(limit)
    
    return {
        "logs": logs,
        "total": total,
        "limit": limit,
        "offset": offset
    }
