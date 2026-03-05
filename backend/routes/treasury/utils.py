"""
Treasury Module - Shared Utilities and Configuration

Provides shared utilities for the treasury system:
- Database and auth initialization
- Permission checking
- Common constants
"""
import os
import sys
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Security
security = HTTPBearer()

# Global state
_db = None
_verify_token_func = None

# Default categories
DEFAULT_INCOME_CATEGORIES = [
    "Dues", "Donations", "Merchandise", "Fundraising", "Events", "Sponsorships", "Other Income"
]

DEFAULT_EXPENSE_CATEGORIES = [
    "Fuel", "Food & Beverages", "Merchandise Cost", "Event Expenses", "Supplies", 
    "Equipment", "Repairs & Maintenance", "Insurance", "Fees & Licenses", 
    "Charity/Donations", "Marketing", "Administrative", "Other Expense"
]


def init_treasury_module(database, token_verifier):
    """Initialize treasury module with database and auth dependencies"""
    global _db, _verify_token_func
    _db = database
    _verify_token_func = token_verifier


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
