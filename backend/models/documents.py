# Document Signing Models - In-house replacement for SignNow
from typing import Optional, List
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Document Template Models
# =============================================================================

class DocumentTemplateCreate(BaseModel):
    """Create a new document template"""
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    template_type: str = Field(..., description="'pdf' or 'text'")
    # For PDF templates - base64 encoded PDF or file reference
    pdf_data: Optional[str] = None
    pdf_filename: Optional[str] = None
    # For text templates - the actual content
    text_content: Optional[str] = None
    # Common fields
    is_active: bool = True
    category: Optional[str] = None  # e.g., "Financial Hardship", "Honorary Application", "Bylaws", "SOPs"


class DocumentTemplateUpdate(BaseModel):
    """Update an existing document template"""
    name: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None


class DocumentTemplateResponse(BaseModel):
    """Template response model"""
    id: str
    name: str
    description: Optional[str] = None
    template_type: str
    pdf_filename: Optional[str] = None
    text_content: Optional[str] = None
    is_active: bool
    category: Optional[str] = None
    created_at: datetime
    created_by: str
    updated_at: Optional[datetime] = None


# =============================================================================
# Signing Request Models
# =============================================================================

class SigningRequestCreate(BaseModel):
    """Create a new signing request"""
    template_id: str
    member_id: str
    recipient_email: str
    recipient_name: str
    message: Optional[str] = None
    expires_days: int = Field(default=30, ge=1, le=90)


class SigningRequestResponse(BaseModel):
    """Signing request response model"""
    id: str
    template_id: str
    template_name: str
    member_id: str
    recipient_email: str
    recipient_name: str
    status: str  # 'pending', 'viewed', 'signed', 'expired', 'cancelled'
    message: Optional[str] = None
    sent_at: datetime
    sent_by: str
    viewed_at: Optional[datetime] = None
    signed_at: Optional[datetime] = None
    expires_at: datetime
    signing_token: Optional[str] = None  # Only included for sender


# =============================================================================
# Signature Capture Models
# =============================================================================

class SignatureSubmit(BaseModel):
    """Submit a signature"""
    signing_token: str
    signature_type: str = Field(..., description="'drawn' or 'typed'")
    # For drawn signatures - base64 encoded image
    signature_image: Optional[str] = None
    # For typed signatures
    typed_name: str
    # Legal consent
    consent_agreed: bool = Field(..., description="Must be True")
    consent_text: str = Field(default="I agree that this electronic signature is my legal signature and I intend to sign this document.")


class SignatureAuditTrail(BaseModel):
    """Audit trail for legal compliance"""
    signer_name: str
    signer_email: str
    signature_type: str
    ip_address: str
    user_agent: str
    consent_text: str
    consent_agreed: bool
    signed_at: datetime
    document_hash: str  # SHA-256 hash of original document


# =============================================================================
# Signed Document Models
# =============================================================================

class SignedDocumentResponse(BaseModel):
    """Response after successful signing"""
    success: bool
    message: str
    signed_document_id: str
    signed_at: datetime
