"""
Document Signing Request Routes

Handles document signing workflow:
- Send documents for signing
- Get signing requests list and details
- Cancel/delete signing requests
- Submit signatures (recipient and approver)
"""
import sys
import uuid
import json
import base64
from datetime import datetime, timezone, timedelta
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, Request, Form
from fastapi.responses import StreamingResponse

from .utils import (
    get_db, get_current_user, generate_signing_token, hash_document,
    decrypt_email, check_document_permission, NATIONAL_OFFICERS
)
from .email import send_signing_email

router = APIRouter()


# =============================================================================
# SIGNING REQUEST MANAGEMENT
# =============================================================================

@router.post("/send")
async def send_document_for_signing(
    template_id: str = Form(...),
    member_id: str = Form(...),
    recipient_email: str = Form(...),
    recipient_name: str = Form(...),
    message: str = Form(None),
    expires_days: int = Form(30),
    approvers: str = Form(None),
    current_user: dict = Depends(get_current_user)
):
    """Send a document to a member for signing with optional approval chain"""
    db = get_db()
    
    if not check_document_permission(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    # Get template
    template = await db.document_templates.find_one({"id": template_id, "is_active": True})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found or inactive")
    
    # Verify member exists
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Build approval chain
    approval_chain = await _build_approval_chain(db, approvers)
    
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
        "status": "pending_recipient",
        "signing_token": signing_token,
        "sent_at": now.isoformat(),
        "sent_by": current_user.get("username", "unknown"),
        "viewed_at": None,
        "signed_at": None,
        "expires_at": (now + timedelta(days=expires_days)).isoformat(),
        "audit_trail": None,
        "approval_chain": approval_chain,
        "current_approver_index": 0,
        "recipient_fields": None,
        "final_decision": None,
        "final_notes": None
    }
    
    await db.signing_requests.insert_one(signing_request)
    
    # Send email notification
    await send_signing_email(
        recipient_email=recipient_email,
        recipient_name=recipient_name,
        template_name=template["name"],
        message=message,
        signing_token=signing_token,
        sender_name=current_user.get("username", "unknown"),
        is_approver=False
    )
    
    sys.stderr.write(f"[DOCS] Sent '{template['name']}' to {recipient_email} with {len(approval_chain)} approvers\n")
    
    # Return response without sensitive data
    response = {k: v for k, v in signing_request.items() if k not in ["_id", "signing_token"]}
    if response.get("approval_chain"):
        response["approval_chain"] = [
            {k: v for k, v in approver.items() if k != "signing_token"}
            for approver in response["approval_chain"]
        ]
    
    return response


async def _build_approval_chain(db, approvers: str):
    """Build approval chain from JSON string of approver roles"""
    approval_chain = []
    
    if not approvers:
        return approval_chain
    
    try:
        approver_roles = json.loads(approvers)
        for i, role in enumerate(approver_roles[:7]):  # Max 7 approvers
            officer_info = next((o for o in NATIONAL_OFFICERS if o["role"] == role), None)
            if not officer_info:
                continue
            
            # Find user with this position
            user = await db.users.find_one(
                {"title": officer_info["title"], "chapter": "National"},
                {"_id": 0, "id": 1, "username": 1, "title": 1, "email": 1, "first_name": 1, "last_name": 1}
            )
            
            # Get BOH email from members table
            boh_email = None
            if user:
                member = await db.members.find_one(
                    {"handle": user.get("username")},
                    {"_id": 0, "email": 1}
                )
                if member and member.get("email"):
                    boh_email = decrypt_email(member.get("email"))
            
            approval_chain.append({
                "order": i + 1,
                "role": role,
                "title": officer_info["display_title"],
                "user_id": user.get("id") if user else None,
                "username": user.get("username") if user else None,
                "email": boh_email or (user.get("email") if user else None),
                "status": "pending",
                "decision": None,
                "notes": None,
                "signing_token": generate_signing_token(),
                "signed_at": None,
                "signature_type": None,
                "typed_name": None,
                "signature_image": None
            })
    except json.JSONDecodeError:
        pass
    
    return approval_chain


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
        {"_id": 0, "signing_token": 0}
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
async def cancel_or_delete_signing_request(
    request_id: str,
    permanent: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Cancel or permanently delete a signing request"""
    db = get_db()
    
    if not check_document_permission(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    doc = await db.signing_requests.find_one({"id": request_id}, {"status": 1})
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
    
    current_status = doc.get("status")
    
    # Handle final states (allow permanent deletion)
    if current_status in ["cancelled", "completed", "expired", "denied"]:
        if permanent:
            await db.signing_requests.delete_one({"id": request_id})
            await db.signatures.delete_many({"signing_request_id": request_id})
            sys.stderr.write(f"[DOCS] Permanently deleted {request_id} by {current_user.get('username')}\n")
            return {"success": True, "message": "Document permanently deleted"}
        return {"success": True, "message": f"Document already {current_status}"}
    
    # Handle active requests (cancel them)
    if current_status in ["pending", "pending_recipient", "pending_approval", "viewed"]:
        await db.signing_requests.update_one(
            {"id": request_id},
            {"$set": {"status": "cancelled"}}
        )
        sys.stderr.write(f"[DOCS] Cancelled {request_id} by {current_user.get('username')}\n")
        return {"success": True, "message": "Signing request cancelled"}
    
    raise HTTPException(status_code=400, detail=f"Cannot process document with status: {current_status}")


# =============================================================================
# PUBLIC SIGNING ENDPOINTS (No auth required - uses signing token)
# =============================================================================

@router.get("/sign/{signing_token}")
async def get_signing_page(signing_token: str, request: Request):
    """Get document for signing (public endpoint)"""
    db = get_db()
    
    # Check if recipient or approver token
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    is_approver = False
    approver_info = None
    approver_index = -1
    
    if not signing_request:
        # Check approver tokens
        signing_request = await db.signing_requests.find_one({
            "approval_chain.signing_token": signing_token
        })
        if signing_request:
            is_approver = True
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
    
    # Validate approver turn
    if is_approver:
        current_index = signing_request.get("current_approver_index", 0)
        if approver_index != current_index - 1:
            raise HTTPException(status_code=400, detail="It is not your turn to review this document yet")
        if approver_info.get("status") != "pending":
            raise HTTPException(status_code=400, detail="You have already reviewed this document")
    else:
        # Recipient validation
        if signing_request["status"] not in ["pending_recipient", "pending", "viewed"]:
            raise HTTPException(status_code=400, detail="This document has already been signed by the recipient")
        
        # Mark as viewed
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
    response = _build_signing_page_response(template, signing_request, is_approver, approver_info, approver_index)
    return response


def _build_signing_page_response(template, signing_request, is_approver, approver_info, approver_index):
    """Build response for signing page"""
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
        "requires_decision": is_approver,
    }
    
    if is_approver:
        response["approver_title"] = approver_info.get("title")
        response["approver_order"] = approver_index + 1
        response["total_approvers"] = len(signing_request.get("approval_chain", []))
        
        # Previous approvals for context
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
        response["recipient_signed_at"] = signing_request.get("signed_at")
        response["recipient_fields"] = signing_request.get("recipient_fields")
    else:
        approval_chain = signing_request.get("approval_chain", [])
        response["has_approvers"] = len(approval_chain) > 0
        if approval_chain:
            response["approver_titles"] = [a.get("title") for a in approval_chain]
    
    # Filter field placements by signer type
    field_placements = template.get("field_placements", [])
    signature_placements = template.get("signature_placements", [])
    
    if is_approver:
        signer_type = f"approver_{approver_index}"
        response["field_placements"] = [fp for fp in field_placements if fp.get("signer_type") == signer_type]
        response["signature_placements"] = [sp for sp in signature_placements if sp.get("signer_type") == signer_type]
    else:
        response["field_placements"] = [fp for fp in field_placements if fp.get("signer_type") == "recipient"]
        response["signature_placements"] = [sp for sp in signature_placements if sp.get("signer_type") == "recipient"]
    
    response["filled_fields"] = signing_request.get("filled_fields", {})
    return response


@router.get("/sign/{signing_token}/pdf")
async def get_signing_pdf(signing_token: str):
    """Get PDF document for display (public endpoint)"""
    db = get_db()
    
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    
    if not signing_request:
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
    signature_type: str = Form(...),
    typed_name: str = Form(...),
    signature_image: str = Form(None),
    consent_agreed: bool = Form(...),
    recipient_fields: str = Form(None),
    decision: str = Form(None),
    approver_notes: str = Form(None)
):
    """Submit a signature for a document (handles both recipient and approver)"""
    db = get_db()
    
    if not consent_agreed:
        raise HTTPException(status_code=400, detail="You must agree to the consent statement")
    
    # Determine if recipient or approver
    signing_request = await db.signing_requests.find_one({"signing_token": signing_token})
    is_approver = False
    approver_index = -1
    
    if not signing_request:
        signing_request = await db.signing_requests.find_one({
            "approval_chain.signing_token": signing_token
        })
        if signing_request:
            is_approver = True
            for i, approver in enumerate(signing_request.get("approval_chain", [])):
                if approver.get("signing_token") == signing_token:
                    approver_index = i
                    break
    
    if not signing_request:
        raise HTTPException(status_code=404, detail="Invalid signing link")
    
    # Validate status
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
    
    # Get template
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    # Capture audit info
    now = datetime.now(timezone.utc)
    client_ip = request.client.host if request.client else "unknown"
    user_agent = request.headers.get("user-agent", "unknown")
    
    if is_approver:
        return await _process_approver_signature(
            db, signing_request, template, approver_index, decision, approver_notes,
            signature_type, typed_name, signature_image, client_ip, user_agent, now
        )
    else:
        return await _process_recipient_signature(
            db, signing_request, template, signature_type, typed_name, signature_image,
            consent_agreed, recipient_fields, client_ip, user_agent, now
        )


async def _process_approver_signature(
    db, signing_request, template, approver_index, decision, approver_notes,
    signature_type, typed_name, signature_image, client_ip, user_agent, now
):
    """Process approver signature submission"""
    approval_chain = signing_request.get("approval_chain", [])
    
    # Verify approver turn
    current_index = signing_request.get("current_approver_index", 0)
    if approver_index != current_index - 1:
        raise HTTPException(status_code=400, detail="It is not your turn to approve this document")
    
    if decision not in ["approved", "denied"]:
        raise HTTPException(status_code=400, detail="You must approve or deny this document")
    
    # Update approver record
    approval_chain[approver_index].update({
        "status": decision,
        "decision": decision,
        "notes": approver_notes,
        "signed_at": now.isoformat(),
        "signature_type": signature_type,
        "typed_name": typed_name,
        "signature_image": signature_image if signature_type == "drawn" else None,
        "ip_address": client_ip,
        "user_agent": user_agent
    })
    
    next_approver_index = approver_index + 1
    is_last_approver = next_approver_index >= len(approval_chain)
    
    if is_last_approver:
        update_data = {
            "status": "completed",
            "approval_chain": approval_chain,
            "current_approver_index": next_approver_index + 1,
            "final_decision": decision,
            "final_notes": approver_notes
        }
    else:
        update_data = {
            "status": "pending_approval",
            "approval_chain": approval_chain,
            "current_approver_index": next_approver_index + 1
        }
        
        # Notify next approver
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


async def _process_recipient_signature(
    db, signing_request, template, signature_type, typed_name, signature_image,
    consent_agreed, recipient_fields, client_ip, user_agent, now
):
    """Process recipient signature submission"""
    if signing_request["status"] not in ["pending_recipient", "pending", "viewed"]:
        raise HTTPException(status_code=400, detail="This document has already been signed by the recipient")
    
    consent_text = "I agree that this electronic signature is my legal signature and I intend to sign this document."
    
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
    
    # Store signature
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
    
    # Parse recipient fields
    parsed_recipient_fields = None
    if recipient_fields:
        try:
            parsed_recipient_fields = json.loads(recipient_fields)
        except json.JSONDecodeError:
            pass
    
    approval_chain = signing_request.get("approval_chain", [])
    
    if approval_chain:
        new_status = "pending_approval"
        
        # Notify first approver
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
            "current_approver_index": 1
        }
    else:
        update_data = {
            "status": "completed",
            "signed_at": now.isoformat(),
            "audit_trail": audit_trail,
            "recipient_fields": parsed_recipient_fields,
            "final_decision": "approved"
        }
    
    await db.signing_requests.update_one(
        {"signing_token": signing_request["signing_token"]},
        {"$set": update_data}
    )
    
    sys.stderr.write(f"[DOCS] Document signed by {typed_name} ({signing_request['recipient_email']})\n")
    
    return {
        "success": True,
        "message": "Document signed successfully" + (" - Sent for approval" if approval_chain else ""),
        "has_approvers": len(approval_chain) > 0,
        "signed_at": now.isoformat()
    }
