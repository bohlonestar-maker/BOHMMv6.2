"""
Document Signing Routes - In-house e-signature system

This module provides a complete document signing solution:
- Document template management (PDF upload and text-based templates)
- Signing request creation and tracking
- Multi-signer approval workflow (sequential National Officer approvals)
- Signature capture (drawn and typed)
- Legal audit trails
- Signed PDF generation
"""
import os
import sys
import uuid
import hashlib
import base64
import json
from datetime import datetime, timezone, timedelta
from typing import Optional, List
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

router = APIRouter(prefix="/documents", tags=["documents"])
security = HTTPBearer()

# National Officers who can be selected as approvers (in order of typical hierarchy)
# These match the abbreviated titles used in the database for chapter="National"
NATIONAL_OFFICERS = [
    {"role": "national_secretary", "title": "SEC", "display_title": "National Secretary", "order": 1},
    {"role": "national_treasurer", "title": "T", "display_title": "National Treasurer", "order": 2},
    {"role": "national_sergeant_at_arms", "title": "S@A", "display_title": "National Sergeant at Arms", "order": 3},
    {"role": "national_road_captain", "title": "RC", "display_title": "National Road Captain", "order": 4},
    {"role": "national_vice_president", "title": "VP", "display_title": "National Vice President", "order": 5},
    {"role": "coo", "title": "COO", "display_title": "COO", "order": 6},
    {"role": "national_president", "title": "Prez", "display_title": "National President", "order": 7},
]

# Will be populated when router is included in main app
_db = None
_verify_token_func = None
_verify_admin_func = None


def init_router(database, token_verifier, admin_verifier):
    """Initialize router with database and auth dependencies"""
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


def generate_signing_token():
    """Generate a secure, unique signing token"""
    return str(uuid.uuid4()) + "-" + str(uuid.uuid4())


def hash_document(content: bytes) -> str:
    """Generate SHA-256 hash of document content for integrity verification"""
    return hashlib.sha256(content).hexdigest()


# =============================================================================
# NATIONAL OFFICERS ENDPOINT
# =============================================================================

@router.get("/national-officers")
async def get_national_officers(current_user: dict = Depends(get_current_user)):
    """Get list of National Officers available as document approvers"""
    db = get_db()
    
    # Get actual users who hold these positions (chapter = National)
    officers_with_users = []
    
    for officer in NATIONAL_OFFICERS:
        # Find user with this title AND chapter = National
        user = await db.users.find_one(
            {"title": officer["title"], "chapter": "National"},
            {"_id": 0, "id": 1, "username": 1, "title": 1, "email": 1, "first_name": 1, "last_name": 1, "chapter": 1}
        )
        
        officers_with_users.append({
            "role": officer["role"],
            "title": officer["title"],
            "display_title": officer["display_title"],
            "order": officer["order"],
            "user": user  # May be None if no one holds this position
        })
    
    return officers_with_users


# =============================================================================
# TEMPLATE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/templates")
async def get_document_templates(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all document templates"""
    db = get_db()
    
    query = {} if include_inactive else {"is_active": True}
    templates = await db.document_templates.find(
        query,
        {"_id": 0, "pdf_data": 0}  # Exclude large PDF data from list
    ).sort("name", 1).to_list(100)
    
    return templates


@router.get("/templates/{template_id}")
async def get_document_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific document template"""
    db = get_db()
    
    template = await db.document_templates.find_one(
        {"id": template_id},
        {"_id": 0}
    )
    
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    return template


@router.post("/templates")
async def create_document_template(
    name: str = Form(...),
    description: str = Form(None),
    template_type: str = Form(...),  # 'pdf' or 'text'
    category: str = Form(None),
    text_content: str = Form(None),
    pdf_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Create a new document template"""
    db = get_db()
    
    # Check permission
    permissions = current_user.get("permissions", {})
    if not (permissions.get("send_documents") or current_user.get("role") == "admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Validate template type
    if template_type not in ["pdf", "text"]:
        raise HTTPException(status_code=400, detail="template_type must be 'pdf' or 'text'")
    
    template_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc)
    
    template_doc = {
        "id": template_id,
        "name": name,
        "description": description,
        "template_type": template_type,
        "category": category,
        "is_active": True,
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown"),
        "updated_at": None
    }
    
    if template_type == "pdf":
        if not pdf_file:
            raise HTTPException(status_code=400, detail="PDF file required for PDF template")
        
        # Read and store PDF
        pdf_content = await pdf_file.read()
        template_doc["pdf_data"] = base64.b64encode(pdf_content).decode('utf-8')
        template_doc["pdf_filename"] = pdf_file.filename
        template_doc["pdf_hash"] = hash_document(pdf_content)
        template_doc["text_content"] = None
    else:
        if not text_content:
            raise HTTPException(status_code=400, detail="text_content required for text template")
        
        template_doc["text_content"] = text_content
        template_doc["pdf_data"] = None
        template_doc["pdf_filename"] = None
        template_doc["pdf_hash"] = hash_document(text_content.encode('utf-8'))
    
    await db.document_templates.insert_one(template_doc)
    
    # Return without pdf_data and _id
    response = {k: v for k, v in template_doc.items() if k not in ["_id", "pdf_data"]}
    
    sys.stderr.write(f"[DOCS] Created template '{name}' ({template_type}) by {current_user.get('username')}\n")
    
    return response


@router.put("/templates/{template_id}")
async def update_document_template(
    template_id: str,
    name: str = Form(None),
    description: str = Form(None),
    category: str = Form(None),
    text_content: str = Form(None),
    is_active: bool = Form(None),
    pdf_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Update a document template"""
    db = get_db()
    
    # Check permission
    permissions = current_user.get("permissions", {})
    if not (permissions.get("send_documents") or current_user.get("role") == "admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    template = await db.document_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    update_data = {"updated_at": datetime.now(timezone.utc).isoformat()}
    
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    if category is not None:
        update_data["category"] = category
    if is_active is not None:
        update_data["is_active"] = is_active
    if text_content is not None and template.get("template_type") == "text":
        update_data["text_content"] = text_content
        update_data["pdf_hash"] = hash_document(text_content.encode('utf-8'))
    if pdf_file and template.get("template_type") == "pdf":
        pdf_content = await pdf_file.read()
        update_data["pdf_data"] = base64.b64encode(pdf_content).decode('utf-8')
        update_data["pdf_filename"] = pdf_file.filename
        update_data["pdf_hash"] = hash_document(pdf_content)
    
    await db.document_templates.update_one(
        {"id": template_id},
        {"$set": update_data}
    )
    
    sys.stderr.write(f"[DOCS] Updated template '{template_id}' by {current_user.get('username')}\n")
    
    return {"success": True, "message": "Template updated"}


@router.delete("/templates/{template_id}")
async def delete_document_template(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete (deactivate) a document template"""
    db = get_db()
    
    # Only admin can delete
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Only admins can delete templates")
    
    result = await db.document_templates.update_one(
        {"id": template_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Template not found")
    
    sys.stderr.write(f"[DOCS] Deactivated template '{template_id}' by {current_user.get('username')}\n")
    
    return {"success": True, "message": "Template deactivated"}


# =============================================================================
# SIGNING REQUEST ENDPOINTS
# =============================================================================

@router.post("/send")
async def send_document_for_signing(
    template_id: str = Form(...),
    member_id: str = Form(...),
    recipient_email: str = Form(...),
    recipient_name: str = Form(...),
    message: str = Form(None),
    expires_days: int = Form(30),
    approvers: str = Form(None),  # JSON array of approver roles in order
    current_user: dict = Depends(get_current_user)
):
    """Send a document to a member for signing with optional approval chain"""
    db = get_db()
    
    # Check permission
    permissions = current_user.get("permissions", {})
    if not (permissions.get("send_documents") or current_user.get("role") == "admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get template
    template = await db.document_templates.find_one({"id": template_id, "is_active": True})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or inactive")
    
    # Verify member exists
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Parse approvers if provided
    approval_chain = []
    if approvers:
        try:
            approver_roles = json.loads(approvers)
            for i, role in enumerate(approver_roles[:5]):  # Max 5 approvers
                # Find the officer info
                officer_info = next((o for o in NATIONAL_OFFICERS if o["role"] == role), None)
                if officer_info:
                    # Find the user who holds this position (chapter = National)
                    user = await db.users.find_one(
                        {"title": officer_info["title"], "chapter": "National"},
                        {"_id": 0, "id": 1, "username": 1, "title": 1, "email": 1, "first_name": 1, "last_name": 1}
                    )
                    
                    approval_chain.append({
                        "order": i + 1,
                        "role": role,
                        "title": officer_info["display_title"],  # Use display title for UI
                        "user_id": user.get("id") if user else None,
                        "username": user.get("username") if user else None,
                        "email": user.get("email") if user else None,
                        "status": "pending",  # pending, approved, denied
                        "decision": None,  # Will be "approved" or "denied"
                        "notes": None,  # Approver's comments
                        "signing_token": generate_signing_token(),
                        "signed_at": None,
                        "signature_type": None,
                        "typed_name": None,
                        "signature_image": None
                    })
        except json.JSONDecodeError:
            pass
    
    # Create signing request
    now = datetime.now(timezone.utc)
    signing_token = generate_signing_token()
    request_id = str(uuid.uuid4())
    
    signing_request = {
        "id": request_id,
        "template_id": template_id,
        "template_name": template["name"],
        "template_type": template["template_type"],
        "member_id": member_id,
        "recipient_email": recipient_email,
        "recipient_name": recipient_name,
        "message": message,
        "status": "pending_recipient",  # pending_recipient, pending_approval, approved, denied, completed
        "signing_token": signing_token,
        "sent_at": now.isoformat(),
        "sent_by": current_user.get("username", "unknown"),
        "viewed_at": None,
        "signed_at": None,
        "expires_at": (now + timedelta(days=expires_days)).isoformat(),
        "audit_trail": None,
        # Multi-signer fields
        "approval_chain": approval_chain,
        "current_approver_index": 0,  # Which approver is currently active (0 = recipient hasn't signed yet)
        "recipient_fields": None,  # Fields filled by recipient
        "final_decision": None,  # Overall final decision
        "final_notes": None  # Final approver's notes
    }
    
    await db.signing_requests.insert_one(signing_request)
    
    # Send email notification to primary recipient
    await send_signing_email(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        template_name=template["name"],
        message=message,
        signing_token=signing_token,
        sender_name=current_user.get("username", "unknown"),
        is_approver=False
    )
    
    approver_count = len(approval_chain)
    sys.stderr.write(f"[DOCS] Sent '{template['name']}' to {recipient_email} with {approver_count} approvers by {current_user.get('username')}\n")
    
    # Return without sensitive data
    response = {k: v for k, v in signing_request.items() if k not in ["_id", "signing_token"]}
    # Also remove signing tokens from approval chain in response
    if response.get("approval_chain"):
        response["approval_chain"] = [
            {k: v for k, v in approver.items() if k != "signing_token"}
            for approver in response["approval_chain"]
        ]
    
    return response


@router.get("/requests")
async def get_signing_requests(
    member_id: str = None,
    status: str = None,
    current_user: dict = Depends(get_current_user)
):
    """Get signing requests (filtered by member_id or status)"""
    db = get_db()
    
    query = {}
    if member_id:
        query["member_id"] = member_id
    if status:
        query["status"] = status
    
    requests = await db.signing_requests.find(
        query,
        {"_id": 0, "signing_token": 0}  # Never expose signing token in lists
    ).sort("sent_at", -1).to_list(200)
    
    return requests


@router.get("/requests/{request_id}")
async def get_signing_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a specific signing request"""
    db = get_db()
    
    request = await db.signing_requests.find_one(
        {"id": request_id},
        {"_id": 0, "signing_token": 0}
    )
    
    if not request:
        raise HTTPException(status_code=404, detail="Signing request not found")
    
    return request


@router.delete("/requests/{request_id}")
async def cancel_signing_request(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Cancel a pending signing request"""
    db = get_db()
    
    # Check permission
    permissions = current_user.get("permissions", {})
    if not (permissions.get("send_documents") or current_user.get("role") == "admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    result = await db.signing_requests.update_one(
        {"id": request_id, "status": "pending"},
        {"$set": {"status": "cancelled"}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Request not found or already processed")
    
    return {"success": True, "message": "Signing request cancelled"}


# =============================================================================
# PUBLIC SIGNING ENDPOINTS (No auth required - uses signing token)
# =============================================================================

@router.get("/sign/{signing_token}")
async def get_signing_page(signing_token: str, request: Request):
    """Get the document for signing (public endpoint - no auth)"""
    db = get_db()
    
    # Check if this is a recipient token or an approver token
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    is_approver = False
    approver_info = None
    approver_index = -1
    
    if not signing_request:
        # Check if this is an approver's token
        signing_request = await db.signing_requests.find_one({
            "approval_chain.signing_token": signing_token
        })
        if signing_request:
            is_approver = True
            # Find which approver this is
            for i, approver in enumerate(signing_request.get("approval_chain", [])):
                if approver.get("signing_token") == signing_token:
                    approver_info = approver
                    approver_index = i
                    break
    
    if not signing_request:
        raise HTTPException(status_code=404, detail="Invalid or expired signing link")
    
    # Check expiration
    expires_at = datetime.fromisoformat(signing_request["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.signing_requests.update_one(
            {"id": signing_request["id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=410, detail="This signing link has expired")
    
    if signing_request["status"] in ["completed", "cancelled", "expired"]:
        raise HTTPException(status_code=400, detail="This signing request is no longer active")
    
    if is_approver:
        # Verify this approver is the current one in the chain
        current_index = signing_request.get("current_approver_index", 0)
        if approver_index != current_index - 1:
            raise HTTPException(status_code=400, detail="It is not your turn to review this document yet")
        
        if approver_info.get("status") != "pending":
            raise HTTPException(status_code=400, detail="You have already reviewed this document")
    else:
        # Recipient signing
        if signing_request["status"] not in ["pending_recipient", "pending", "viewed"]:
            raise HTTPException(status_code=400, detail="This document has already been signed by the recipient")
        
        # Mark as viewed if first time
        if signing_request["status"] in ["pending", "pending_recipient"]:
            await db.signing_requests.update_one(
                {"signing_token": signing_token},
                {"$set": {"status": "viewed", "viewed_at": datetime.now(timezone.utc).isoformat()}}
            )
    
    # Get template
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Document template not found")
    
    # Build response
    response = {
        "template_name": template["name"],
        "template_type": template["template_type"],
        "text_content": template.get("text_content"),
        "has_pdf": template.get("pdf_data") is not None,
        "recipient_name": signing_request["recipient_name"],
        "recipient_email": signing_request["recipient_email"],
        "message": signing_request.get("message"),
        "sent_by": signing_request["sent_by"],
        "sent_at": signing_request["sent_at"],
        "is_approver": is_approver,
        "requires_decision": is_approver,  # Approvers must approve/deny
    }
    
    if is_approver:
        response["approver_title"] = approver_info.get("title")
        response["approver_order"] = approver_index + 1
        response["total_approvers"] = len(signing_request.get("approval_chain", []))
        # Include previous approvals for context
        previous_approvals = []
        for i, approver in enumerate(signing_request.get("approval_chain", [])):
            if i < approver_index and approver.get("status") != "pending":
                previous_approvals.append({
                    "title": approver.get("title"),
                    "decision": approver.get("decision"),
                    "notes": approver.get("notes"),
                    "signed_at": approver.get("signed_at")
                })
        response["previous_approvals"] = previous_approvals
        # Include recipient info
        response["recipient_signed_at"] = signing_request.get("signed_at")
        response["recipient_fields"] = signing_request.get("recipient_fields")
    else:
        # For recipient, show if there will be approvers
        approval_chain = signing_request.get("approval_chain", [])
        response["has_approvers"] = len(approval_chain) > 0
        if approval_chain:
            response["approver_titles"] = [a.get("title") for a in approval_chain]
    
    return response


@router.get("/sign/{signing_token}/pdf")
async def get_signing_pdf(signing_token: str):
    """Get the PDF document for display (public endpoint)"""
    db = get_db()
    
    # Check if this is a recipient token or an approver token
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    
    if not signing_request:
        # Check if this is an approver's token
        signing_request = await db.signing_requests.find_one({
            "approval_chain.signing_token": signing_token
        })
    
    if not signing_request:
        raise HTTPException(status_code=404, detail="Invalid signing link")
    
    if signing_request["status"] in ["completed", "cancelled", "expired"]:
        raise HTTPException(status_code=400, detail="Document not available")
    
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template or not template.get("pdf_data"):
        raise HTTPException(status_code=404, detail="PDF not found")
    
    pdf_bytes = base64.b64decode(template["pdf_data"])
    
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"inline; filename={template.get('pdf_filename', 'document.pdf')}",
            "X-Frame-Options": "ALLOWALL",
            "Content-Security-Policy": "frame-ancestors *"
        }
    )


@router.post("/sign/{signing_token}/submit")
async def submit_signature(
    signing_token: str,
    request: Request,
    signature_type: str = Form(...),  # 'drawn' or 'typed'
    typed_name: str = Form(...),
    signature_image: str = Form(None),  # Base64 encoded image for drawn signatures
    consent_agreed: bool = Form(...),
    recipient_fields: str = Form(None),  # JSON object with fields filled by recipient
    decision: str = Form(None),  # 'approved' or 'denied' (for approvers only)
    approver_notes: str = Form(None)  # Notes from approver
):
    """Submit a signature for a document (handles both recipient and approver signatures)"""
    db = get_db()
    
    if not consent_agreed:
        raise HTTPException(status_code=400, detail="You must agree to the consent statement")
    
    # First check if this is a recipient signing or an approver signing
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    is_approver = False
    approver_index = -1
    
    if not signing_request:
        # Check if this is an approver's token
        signing_request = await db.signing_requests.find_one({
            "approval_chain.signing_token": signing_token
        })
        if signing_request:
            is_approver = True
            # Find which approver this is
            for i, approver in enumerate(signing_request.get("approval_chain", [])):
                if approver.get("signing_token") == signing_token:
                    approver_index = i
                    break
    
    if not signing_request:
        raise HTTPException(status_code=404, detail="Invalid signing link")
    
    # Check various status conditions
    if signing_request["status"] in ["cancelled", "expired", "completed"]:
        raise HTTPException(status_code=400, detail="This signing request is no longer active")
    
    # Check expiration
    expires_at = datetime.fromisoformat(signing_request["expires_at"].replace('Z', '+00:00'))
    if datetime.now(timezone.utc) > expires_at:
        await db.signing_requests.update_one(
            {"id": signing_request["id"]},
            {"$set": {"status": "expired"}}
        )
        raise HTTPException(status_code=410, detail="This signing link has expired")
    
    # Get template for document hash
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Capture audit trail
    now = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    consent_text = "I agree that this electronic signature is my legal signature and I intend to sign this document."
    
    if is_approver:
        # APPROVER SIGNING
        approval_chain = signing_request.get("approval_chain", [])
        
        # Verify this approver is the current one in the chain
        current_index = signing_request.get("current_approver_index", 0)
        if approver_index != current_index - 1:  # current_approver_index is 1-based after recipient signs
            raise HTTPException(status_code=400, detail="It is not your turn to approve this document")
        
        # Validate approver has made a decision
        if decision not in ["approved", "denied"]:
            raise HTTPException(status_code=400, detail="You must approve or deny this document")
        
        # Update the approver in the chain
        approval_chain[approver_index]["status"] = decision
        approval_chain[approver_index]["decision"] = decision
        approval_chain[approver_index]["notes"] = approver_notes
        approval_chain[approver_index]["signed_at"] = now.isoformat()
        approval_chain[approver_index]["signature_type"] = signature_type
        approval_chain[approver_index]["typed_name"] = typed_name
        approval_chain[approver_index]["signature_image"] = signature_image if signature_type == "drawn" else None
        approval_chain[approver_index]["ip_address"] = client_ip
        approval_chain[approver_index]["user_agent"] = user_agent
        
        # Determine next steps
        next_approver_index = approver_index + 1
        is_last_approver = next_approver_index >= len(approval_chain)
        
        if is_last_approver:
            # This was the final approver
            new_status = "completed"
            final_decision = decision
            update_data = {
                "status": new_status,
                "approval_chain": approval_chain,
                "current_approver_index": next_approver_index + 1,
                "final_decision": final_decision,
                "final_notes": approver_notes
            }
        else:
            # Move to next approver
            new_status = "pending_approval"
            update_data = {
                "status": new_status,
                "approval_chain": approval_chain,
                "current_approver_index": next_approver_index + 1
            }
            
            # Send email to next approver
            next_approver = approval_chain[next_approver_index]
            if next_approver.get("email"):
                await send_signing_email(
                    recipient_email=next_approver["email"],
                    recipient_name=next_approver.get("username") or next_approver["title"],
                    template_name=template["name"],
                    message=f"Document from {signing_request['recipient_name']} requires your approval.",
                    signing_token=next_approver["signing_token"],
                    sender_name=signing_request["sent_by"],
                    is_approver=True
                )
        
        await db.signing_requests.update_one(
            {"id": signing_request["id"]},
            {"$set": update_data}
        )
        
        sys.stderr.write(f"[DOCS] Document {decision} by {typed_name} (Approver {approver_index + 1})\n")
        
        return {
            "success": True,
            "message": f"Document {decision} successfully",
            "decision": decision,
            "is_final": is_last_approver,
            "signed_at": now.isoformat()
        }
    
    else:
        # RECIPIENT SIGNING
        if signing_request["status"] not in ["pending_recipient", "pending", "viewed"]:
            raise HTTPException(status_code=400, detail="This document has already been signed by the recipient")
        
        audit_trail = {
            "signer_name": typed_name,
            "signer_email": signing_request["recipient_email"],
            "signature_type": signature_type,
            "ip_address": client_ip,
            "user_agent": user_agent,
            "consent_text": consent_text,
            "consent_agreed": True,
            "signed_at": now.isoformat(),
            "document_hash": template.get("pdf_hash", "")
        }
        
        # Store signature data
        signature_record = {
            "id": str(uuid.uuid4()),
            "signing_request_id": signing_request["id"],
            "signer_type": "recipient",
            "signature_type": signature_type,
            "typed_name": typed_name,
            "signature_image": signature_image if signature_type == "drawn" else None,
            "created_at": now.isoformat()
        }
        
        await db.signatures.insert_one(signature_record)
        
        # Parse recipient fields if provided
        parsed_recipient_fields = None
        if recipient_fields:
            try:
                parsed_recipient_fields = json.loads(recipient_fields)
            except json.JSONDecodeError:
                pass
        
        # Check if there are approvers
        approval_chain = signing_request.get("approval_chain", [])
        
        if approval_chain:
            # Has approvers - move to pending approval
            new_status = "pending_approval"
            
            # Send email to first approver
            first_approver = approval_chain[0]
            if first_approver.get("email"):
                await send_signing_email(
                    recipient_email=first_approver["email"],
                    recipient_name=first_approver.get("username") or first_approver["title"],
                    template_name=template["name"],
                    message=f"Document from {signing_request['recipient_name']} requires your approval.",
                    signing_token=first_approver["signing_token"],
                    sender_name=signing_request["sent_by"],
                    is_approver=True
                )
            
            update_data = {
                "status": new_status,
                "signed_at": now.isoformat(),
                "audit_trail": audit_trail,
                "recipient_fields": parsed_recipient_fields,
                "current_approver_index": 1  # First approver
            }
        else:
            # No approvers - mark as completed
            new_status = "completed"
            update_data = {
                "status": new_status,
                "signed_at": now.isoformat(),
                "audit_trail": audit_trail,
                "recipient_fields": parsed_recipient_fields,
                "final_decision": "approved"  # Auto-approved if no approval chain
            }
        
        await db.signing_requests.update_one(
            {"signing_token": signing_token},
            {"$set": update_data}
        )
        
        sys.stderr.write(f"[DOCS] Document signed by {typed_name} ({signing_request['recipient_email']})\n")
        
        return {
            "success": True,
            "message": "Document signed successfully" + (" - Sent for approval" if approval_chain else ""),
            "has_approvers": len(approval_chain) > 0,
            "signed_at": now.isoformat()
        }


# =============================================================================
# SIGNED DOCUMENT RETRIEVAL
# =============================================================================

@router.get("/signed/{request_id}/download")
async def download_signed_document(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download the signed document with signature overlay"""
    db = get_db()
    
    signing_request = await db.signing_requests.find_one({"id": request_id, "status": "signed"})
    if not signing_request:
        raise HTTPException(status_code=404, detail="Signed document not found")
    
    # Get signature
    signature = await db.signatures.find_one({"signing_request_id": request_id})
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    # Get template
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Generate signed PDF
    signed_pdf = await generate_signed_pdf(template, signing_request, signature)
    
    filename = f"signed_{template['name']}_{signing_request['recipient_name']}.pdf"
    filename = filename.replace(" ", "_")
    
    return StreamingResponse(
        BytesIO(signed_pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

async def send_signing_email(
    recipient_email: str,
    recipient_name: str,
    template_name: str,
    message: str,
    signing_token: str,
    sender_name: str,
    is_approver: bool = False
):
    """Send email notification with signing link"""
    try:
        import aiosmtplib
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart
        
        # Use SUPPORT SMTP credentials for document signing emails
        smtp_host = os.environ.get('SMTP_HOST')
        smtp_port = int(os.environ.get('SMTP_PORT', 465))
        # Use support credentials for document signing
        smtp_username = os.environ.get('SUPPORT_SMTP_USERNAME', os.environ.get('SMTP_USERNAME'))
        smtp_password = os.environ.get('SUPPORT_SMTP_PASSWORD', os.environ.get('SMTP_PASSWORD'))
        smtp_from = os.environ.get('SUPPORT_SMTP_USERNAME', os.environ.get('SMTP_FROM_EMAIL'))
        
        if not all([smtp_host, smtp_username, smtp_password, smtp_from]):
            sys.stderr.write("[DOCS] SMTP not configured, skipping email\n")
            return
        
        # Get the frontend URL from environment
        frontend_url = os.environ.get('FRONTEND_URL', os.environ.get('REACT_APP_BACKEND_URL', ''))
        # Remove /api if present and ensure we have the base URL
        if '/api' in frontend_url:
            frontend_url = frontend_url.replace('/api', '')
        signing_url = f"{frontend_url}/sign/{signing_token}"
        
        msg = MIMEMultipart('alternative')
        
        if is_approver:
            msg['Subject'] = f"Approval Required: {template_name}"
            action_text = "approval"
            button_text = "Review & Approve"
            header_text = "Document Requires Your Approval"
        else:
            msg['Subject'] = f"Document Ready for Signature: {template_name}"
            action_text = "signature"
            button_text = "Review & Sign Document"
            header_text = "Document Ready for Signature"
        
        msg['From'] = smtp_from
        msg['To'] = recipient_email
        
        # Plain text version
        text_content = f"""
Hello {recipient_name},

{sender_name if not is_approver else "A document"} {"has sent you" if not is_approver else "requires your"} {"a document" if not is_approver else "approval"} "{template_name}" that requires your {action_text}.

{f"Message: {message}" if message else ""}

Click the link below to review and {"sign" if not is_approver else "approve/deny"} the document:
{signing_url}

This link will expire in 30 days.

Thank you,
BOH Document System
        """
        
        # HTML version
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
        .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: {"#dc2626" if is_approver else "#1e293b"}; color: white; padding: 20px; text-align: center; border-radius: 8px 8px 0 0; }}
        .content {{ background: #f8fafc; padding: 30px; border: 1px solid #e2e8f0; }}
        .button {{ display: inline-block; background: {"#dc2626" if is_approver else "#7c3aed"}; color: white; padding: 12px 30px; text-decoration: none; border-radius: 6px; margin: 20px 0; }}
        .footer {{ text-align: center; padding: 20px; color: #64748b; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{header_text}</h1>
        </div>
        <div class="content">
            <p>Hello <strong>{recipient_name}</strong>,</p>
            <p>{"<strong>" + sender_name + "</strong> has sent you a document" if not is_approver else "A document"} that requires your {action_text}:</p>
            <p style="font-size: 18px; color: {"#dc2626" if is_approver else "#7c3aed"};"><strong>{template_name}</strong></p>
            {f"<p><em>{message}</em></p>" if message else ""}
            <p style="text-align: center;">
                <a href="{signing_url}" class="button">{button_text}</a>
            </p>
            <p style="font-size: 12px; color: #64748b;">This link will expire in 30 days.</p>
        </div>
        <div class="footer">
            <p>BOH Document Signing System</p>
        </div>
    </div>
</body>
</html>
        """
        
        msg.attach(MIMEText(text_content, 'plain'))
        msg.attach(MIMEText(html_content, 'html'))
        
        await aiosmtplib.send(
            msg,
            hostname=smtp_host,
            port=smtp_port,
            username=smtp_username,
            password=smtp_password,
            use_tls=True
        )
        
        sys.stderr.write(f"[DOCS] {'Approval' if is_approver else 'Signing'} email sent to {recipient_email}\n")
        
    except Exception as e:
        sys.stderr.write(f"[DOCS] Failed to send signing email: {e}\n")


async def generate_signed_pdf(template: dict, signing_request: dict, signature: dict) -> bytes:
    """Generate a PDF with the signature embedded"""
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
        from reportlab.lib.units import inch
        from reportlab.lib import colors
        from PyPDF2 import PdfReader, PdfWriter
        
        audit = signing_request.get("audit_trail", {})
        
        if template.get("template_type") == "pdf" and template.get("pdf_data"):
            # For PDF templates, add signature page to existing PDF
            original_pdf = base64.b64decode(template["pdf_data"])
            reader = PdfReader(BytesIO(original_pdf))
            writer = PdfWriter()
            
            # Copy all pages
            for page in reader.pages:
                writer.add_page(page)
            
            # Create signature page
            sig_buffer = BytesIO()
            c = canvas.Canvas(sig_buffer, pagesize=letter)
            width, height = letter
            
            # Add signature page content
            c.setFont("Helvetica-Bold", 16)
            c.drawString(1*inch, height - 1*inch, "SIGNATURE CERTIFICATE")
            
            c.setFont("Helvetica", 11)
            y = height - 1.5*inch
            
            c.drawString(1*inch, y, f"Document: {template['name']}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Signer: {signature['typed_name']}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Email: {audit.get('signer_email', 'N/A')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Signed At: {audit.get('signed_at', 'N/A')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"IP Address: {audit.get('ip_address', 'N/A')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Signature Type: {signature['signature_type'].title()}")
            y -= 0.5*inch
            
            # Draw signature if it exists
            if signature.get("signature_image"):
                try:
                    sig_data = base64.b64decode(signature["signature_image"].split(",")[-1])
                    from PIL import Image
                    sig_img = Image.open(BytesIO(sig_data))
                    
                    # Save to temp buffer for reportlab
                    img_buffer = BytesIO()
                    sig_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    from reportlab.lib.utils import ImageReader
                    c.drawImage(ImageReader(img_buffer), 1*inch, y - 1.5*inch, width=3*inch, height=1*inch, preserveAspectRatio=True)
                    y -= 2*inch
                except Exception as e:
                    sys.stderr.write(f"[DOCS] Could not embed signature image: {e}\n")
                    c.drawString(1*inch, y, f"Typed Signature: {signature['typed_name']}")
                    y -= 0.5*inch
            else:
                c.setFont("Helvetica-Oblique", 14)
                c.drawString(1*inch, y, f"Typed Signature: {signature['typed_name']}")
                y -= 0.5*inch
            
            # Consent statement
            c.setFont("Helvetica", 9)
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Consent: {audit.get('consent_text', 'N/A')}")
            
            # Document hash
            y -= 0.5*inch
            c.setFont("Helvetica", 8)
            c.setFillColor(colors.gray)
            c.drawString(1*inch, y, f"Document Hash (SHA-256): {audit.get('document_hash', 'N/A')[:64]}")
            
            c.save()
            sig_buffer.seek(0)
            
            # Add signature page
            sig_reader = PdfReader(sig_buffer)
            writer.add_page(sig_reader.pages[0])
            
            # Output
            output = BytesIO()
            writer.write(output)
            return output.getvalue()
            
        else:
            # For text templates, generate PDF from scratch
            buffer = BytesIO()
            c = canvas.Canvas(buffer, pagesize=letter)
            width, height = letter
            
            # Title
            c.setFont("Helvetica-Bold", 18)
            c.drawString(1*inch, height - 1*inch, template["name"])
            
            # Content
            c.setFont("Helvetica", 11)
            y = height - 1.5*inch
            
            text_content = template.get("text_content", "")
            for line in text_content.split("\n"):
                if y < 2*inch:
                    c.showPage()
                    y = height - 1*inch
                c.drawString(1*inch, y, line[:90])  # Truncate long lines
                y -= 0.2*inch
            
            # Signature section
            c.showPage()
            y = height - 1*inch
            
            c.setFont("Helvetica-Bold", 14)
            c.drawString(1*inch, y, "SIGNATURE")
            y -= 0.5*inch
            
            c.setFont("Helvetica", 11)
            c.drawString(1*inch, y, f"Signed by: {signature['typed_name']}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"Date: {audit.get('signed_at', 'N/A')}")
            y -= 0.3*inch
            c.drawString(1*inch, y, f"IP: {audit.get('ip_address', 'N/A')}")
            
            # Draw signature image if available
            if signature.get("signature_image"):
                try:
                    sig_data = base64.b64decode(signature["signature_image"].split(",")[-1])
                    from PIL import Image
                    sig_img = Image.open(BytesIO(sig_data))
                    
                    img_buffer = BytesIO()
                    sig_img.save(img_buffer, format='PNG')
                    img_buffer.seek(0)
                    
                    from reportlab.lib.utils import ImageReader
                    y -= 0.5*inch
                    c.drawImage(ImageReader(img_buffer), 1*inch, y - 1*inch, width=3*inch, height=1*inch, preserveAspectRatio=True)
                except Exception as e:
                    sys.stderr.write(f"[DOCS] Could not embed signature image: {e}\n")
            
            c.save()
            return buffer.getvalue()
            
    except ImportError as e:
        sys.stderr.write(f"[DOCS] PDF generation requires reportlab and PyPDF2: {e}\n")
        raise HTTPException(status_code=500, detail="PDF generation not available")
