"""
Document Signing Module - In-House E-Signature System

This package provides a complete document signing solution:
- Document template management (PDF and text-based)
- Visual field/signature placement editor
- Signing request creation and tracking
- Multi-signer approval workflow
- Signature capture (drawn and typed)
- Legal audit trails
- Signed PDF generation

Module Structure:
- utils.py     - Shared utilities, auth, encryption, constants
- email.py     - Email notification functions
- templates.py - Template CRUD and PDF rendering endpoints
- signing.py   - Signing request and submission endpoints
- officers.py  - National officers list endpoint
- pdf.py       - Signed PDF generation and download
"""
from fastapi import APIRouter

from .utils import init_documents_module
from .templates import router as templates_router
from .signing import router as signing_router
from .officers import router as officers_router
from .pdf import router as pdf_router

# Create combined router with prefix
router = APIRouter(prefix="/documents", tags=["documents"])

# Include all sub-routers
router.include_router(officers_router)
router.include_router(templates_router)
router.include_router(signing_router)
router.include_router(pdf_router)


def init_router(database, token_verifier, admin_verifier):
    """Initialize document signing module with dependencies
    
    Args:
        database: MongoDB database instance
        token_verifier: Async function to verify JWT tokens
        admin_verifier: Async function to verify admin tokens
    """
    init_documents_module(database, token_verifier, admin_verifier)


# Export for backwards compatibility
__all__ = ['router', 'init_router']
