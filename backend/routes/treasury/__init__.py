"""
Treasury Module - BOH Financial Management

This package provides comprehensive financial management:
- Transaction tracking (income/expenses)
- Account management (multiple accounts)
- Budget allocation and tracking
- Dynamic category management
- Financial reports (monthly, quarterly, yearly)
- Receipt/invoice attachments
- Audit logging for compliance

Module Structure:
- utils.py       - Shared utilities, auth, permissions, audit helpers
- categories.py  - Category CRUD
- accounts.py    - Account management
- transactions.py - Income/expense tracking
- budgets.py     - Budget management
- reports.py     - Financial reports
- audit.py       - Audit log viewing

Permissions:
- view_treasury   - Read-only access to financial data
- manage_treasury - Can add/edit/delete transactions
- treasury_admin  - Full access including settings and audit logs
"""
from fastapi import APIRouter

from .utils import init_treasury_module
from .categories import router as categories_router
from .accounts import router as accounts_router
from .transactions import router as transactions_router
from .budgets import router as budgets_router
from .reports import router as reports_router
from .audit import router as audit_router

# Create combined router with prefix
router = APIRouter(prefix="/treasury", tags=["treasury"])

# Include all sub-routers
router.include_router(categories_router)
router.include_router(accounts_router)
router.include_router(transactions_router)
router.include_router(budgets_router)
router.include_router(reports_router)
router.include_router(audit_router)


def init_router(database, token_verifier):
    """Initialize treasury module with dependencies
    
    Args:
        database: MongoDB database instance
        token_verifier: Async function to verify JWT tokens
    """
    init_treasury_module(database, token_verifier)


__all__ = ['router', 'init_router']
