# Document Signing Models - In-house replacement for SignNow
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


# =============================================================================
# Field and Signature Placement Models
# =============================================================================

class FieldPlacement(BaseModel):
    """Defines a form field placement on a PDF"""
    id: str  # Unique field ID
    field_type: str  # 'text', 'date', 'textarea', 'initials', 'checkbox'
    label: str  # Display label for the field
    page: int  # 1-indexed page number
    x: float  # X coordinate (percentage from left, 0-100)
    y: float  # Y coordinate (percentage from top, 0-100)
    width: float  # Width (percentage, 0-100)
    height: float  # Height (percentage, 0-100)
    required: bool = True
    placeholder: Optional[str] = None
    signer_type: str = "recipient"  # 'recipient' or 'approver_{index}'


class SignaturePlacement(BaseModel):
    """Defines a signature placement on a PDF"""
    id: str  # Unique signature ID
    label: str  # e.g., "Applicant Signature", "Committee Officer Signature"
    page: int  # 1-indexed page number
    x: float  # X coordinate (percentage from left, 0-100)
    y: float  # Y coordinate (percentage from top, 0-100)
    width: float  # Width (percentage, 0-100)
    height: float  # Height (percentage, 0-100)
    signer_type: str  # 'recipient' or 'approver_{index}' (0-indexed)
    include_date: bool = True  # Whether to include signed date next to signature
    date_x: Optional[float] = None  # X offset for date
    date_y: Optional[float] = None  # Y offset for date


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
    # Field and signature placements for PDF templates
    field_placements: Optional[List[FieldPlacement]] = None
    signature_placements: Optional[List[SignaturePlacement]] = None


class DocumentTemplateUpdate(BaseModel):
    """Update an existing document template"""
    name: Optional[str] = None
    description: Optional[str] = None
    text_content: Optional[str] = None
    is_active: Optional[bool] = None
    category: Optional[str] = None
    field_placements: Optional[List[FieldPlacement]] = None
    signature_placements: Optional[List[SignaturePlacement]] = None


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
    field_placements: Optional[List[FieldPlacement]] = None
    signature_placements: Optional[List[SignaturePlacement]] = None
    page_count: Optional[int] = None  # Number of pages in PDF


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
