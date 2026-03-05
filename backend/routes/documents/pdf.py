"""
Document Signing - PDF Generation

Handles generation of signed PDFs with:
- Filled form fields overlaid on PDF
- Signatures overlaid at specified positions
- Signature certificate page
"""
import sys
import base64
from datetime import datetime
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse

from .utils import get_db, get_current_user

router = APIRouter()


@router.get("/signed/{request_id}/download")
async def download_signed_document(
    request_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Download the signed document with signature overlay"""
    db = get_db()
    
    signing_request = await db.signing_requests.find_one({
        "id": request_id,
        "status": {"$in": ["signed", "completed"]}
    })
    if not signing_request:
        raise HTTPException(status_code=404, detail="Signed document not found")
    
    signature = await db.signatures.find_one({"signing_request_id": request_id})
    if not signature:
        raise HTTPException(status_code=404, detail="Signature not found")
    
    template = await db.document_templates.find_one({"id": signing_request["template_id"]})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    signed_pdf = await generate_signed_pdf(template, signing_request, signature)
    
    filename = f"signed_{template['name']}_{signing_request['recipient_name']}.pdf"
    filename = filename.replace(" ", "_")
    
    return StreamingResponse(
        BytesIO(signed_pdf),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


async def generate_signed_pdf(template: dict, signing_request: dict, signature: dict) -> bytes:
    """Generate a PDF with filled fields and signatures overlaid at specified positions"""
    try:
        import fitz  # PyMuPDF
        
        audit = signing_request.get("audit_trail", {})
        filled_fields = signing_request.get("recipient_fields", {}) or {}
        approval_chain = signing_request.get("approval_chain", [])
        
        if template.get("template_type") == "pdf" and template.get("pdf_data"):
            pdf_bytes = base64.b64decode(template["pdf_data"])
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            field_placements = template.get("field_placements", [])
            signature_placements = template.get("signature_placements", [])
            
            # Process each page
            for page_num in range(len(doc)):
                page = doc[page_num]
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                
                # Overlay text fields
                _overlay_text_fields(page, field_placements, filled_fields, page_num + 1, page_width, page_height)
                
                # Overlay signatures
                _overlay_signatures(page, signature_placements, signature, approval_chain, audit, page_num + 1, page_width, page_height)
            
            # Add signature certificate page
            _add_certificate_page(doc, template, signing_request, audit, approval_chain)
            
            output = BytesIO()
            doc.save(output)
            doc.close()
            return output.getvalue()
        else:
            # Generate PDF from text template
            return _generate_text_template_pdf(template, signing_request, signature, audit)
            
    except ImportError as e:
        sys.stderr.write(f"[DOCS] PDF generation requires PyMuPDF: {e}\n")
        raise HTTPException(status_code=500, detail="PDF generation not available")


def _overlay_text_fields(page, field_placements, filled_fields, page_num, page_width, page_height):
    """Overlay filled text fields on a PDF page"""
    import fitz
    
    for field in field_placements:
        if field.get("page") != page_num:
            continue
        
        field_value = filled_fields.get(field.get("id"), "")
        if not field_value:
            continue
        
        x = (field.get("x", 0) / 100) * page_width
        y = (field.get("y", 0) / 100) * page_height
        
        text_point = fitz.Point(x, y + 12)
        fontsize = 9 if field.get("field_type") == "textarea" else 10
        
        # Handle multi-line text
        if field.get("field_type") == "textarea" and "\n" in str(field_value):
            lines = str(field_value).split("\n")
            for i, line in enumerate(lines[:10]):
                line_point = fitz.Point(x, y + 12 + (i * 12))
                page.insert_text(line_point, line[:80], fontsize=fontsize, color=(0, 0, 0))
        else:
            page.insert_text(text_point, str(field_value)[:100], fontsize=fontsize, color=(0, 0, 0))


def _overlay_signatures(page, signature_placements, signature, approval_chain, audit, page_num, page_width, page_height):
    """Overlay signatures on a PDF page"""
    import fitz
    
    for sig_placement in signature_placements:
        if sig_placement.get("page") != page_num:
            continue
        
        signer_type = sig_placement.get("signer_type", "recipient")
        sig_data = None
        typed_name = None
        signed_at = None
        
        if signer_type == "recipient":
            sig_data = signature.get("signature_image")
            typed_name = signature.get("typed_name")
            signed_at = audit.get("signed_at", "")
        elif signer_type.startswith("approver_"):
            try:
                approver_idx = int(signer_type.split("_")[1])
                if approver_idx < len(approval_chain):
                    approver = approval_chain[approver_idx]
                    sig_data = approver.get("signature_image")
                    typed_name = approver.get("typed_name")
                    signed_at = approver.get("signed_at", "")
            except (ValueError, IndexError):
                pass
        
        if not typed_name:
            continue
        
        x = (sig_placement.get("x", 0) / 100) * page_width
        y = (sig_placement.get("y", 0) / 100) * page_height
        width = (sig_placement.get("width", 20) / 100) * page_width
        height = (sig_placement.get("height", 5) / 100) * page_height
        
        # Draw signature image or typed name
        if sig_data:
            try:
                if "," in sig_data:
                    sig_data = sig_data.split(",")[1]
                img_bytes = base64.b64decode(sig_data)
                sig_rect = fitz.Rect(x, y, x + width, y + height)
                page.insert_image(sig_rect, stream=img_bytes)
            except Exception as e:
                sys.stderr.write(f"[DOCS] Could not overlay signature image: {e}\n")
                text_point = fitz.Point(x, y + height/2)
                page.insert_text(text_point, typed_name, fontsize=12, color=(0, 0, 0.5))
        else:
            text_point = fitz.Point(x, y + height * 0.7)
            page.insert_text(text_point, typed_name, fontsize=14, color=(0, 0, 0.3))
        
        # Add date if specified
        if sig_placement.get("include_date") and signed_at:
            date_x = sig_placement.get("date_x")
            date_y = sig_placement.get("date_y")
            if date_x is not None and date_y is not None:
                dx = (date_x / 100) * page_width
                dy = (date_y / 100) * page_height
            else:
                dx = x + width + 10
                dy = y + height * 0.7
            
            try:
                dt = datetime.fromisoformat(signed_at.replace('Z', '+00:00'))
                date_str = dt.strftime("%m/%d/%Y")
            except:
                date_str = signed_at[:10] if signed_at else ""
            
            if date_str:
                page.insert_text(fitz.Point(dx, dy), date_str, fontsize=10, color=(0, 0, 0))


def _add_certificate_page(doc, template, signing_request, audit, approval_chain):
    """Add signature certificate page to the document"""
    import fitz
    
    cert_page = doc.new_page(-1, width=612, height=792)
    
    cert_page.insert_text(fitz.Point(72, 72), "SIGNATURE CERTIFICATE", fontsize=16, color=(0, 0, 0))
    
    y_pos = 110
    cert_page.insert_text(fitz.Point(72, y_pos), f"Document: {template['name']}", fontsize=11)
    y_pos += 20
    cert_page.insert_text(fitz.Point(72, y_pos), f"Recipient: {signing_request.get('recipient_name', 'N/A')}", fontsize=11)
    y_pos += 20
    cert_page.insert_text(fitz.Point(72, y_pos), f"Email: {signing_request.get('recipient_email', 'N/A')}", fontsize=11)
    y_pos += 20
    cert_page.insert_text(fitz.Point(72, y_pos), f"Signed At: {audit.get('signed_at', 'N/A')}", fontsize=11)
    y_pos += 20
    cert_page.insert_text(fitz.Point(72, y_pos), f"IP Address: {audit.get('ip_address', 'N/A')}", fontsize=11)
    y_pos += 30
    
    # List approvers
    if approval_chain:
        cert_page.insert_text(fitz.Point(72, y_pos), "APPROVAL CHAIN:", fontsize=12, color=(0, 0, 0))
        y_pos += 20
        for i, approver in enumerate(approval_chain):
            status = approver.get("decision", approver.get("status", "pending"))
            color = (0, 0.5, 0) if status == "approved" else (0.8, 0, 0) if status == "denied" else (0.5, 0.5, 0.5)
            cert_page.insert_text(
                fitz.Point(72, y_pos),
                f"{i+1}. {approver.get('title', 'Unknown')}: {status.upper()} - {approver.get('typed_name', 'N/A')} ({approver.get('signed_at', 'pending')[:10] if approver.get('signed_at') else 'pending'})",
                fontsize=10,
                color=color
            )
            y_pos += 18
            if approver.get("notes"):
                cert_page.insert_text(fitz.Point(90, y_pos), f"Notes: {approver.get('notes')[:60]}", fontsize=9, color=(0.3, 0.3, 0.3))
                y_pos += 15
    
    y_pos += 20
    cert_page.insert_text(fitz.Point(72, y_pos), "Document Hash (SHA-256):", fontsize=9, color=(0.5, 0.5, 0.5))
    y_pos += 15
    cert_page.insert_text(fitz.Point(72, y_pos), audit.get("document_hash", "N/A")[:64], fontsize=8, color=(0.5, 0.5, 0.5))


def _generate_text_template_pdf(template, signing_request, signature, audit):
    """Generate PDF from text template"""
    import fitz
    
    doc = fitz.open()
    page = doc.new_page(-1, width=612, height=792)
    
    page.insert_text(fitz.Point(72, 72), template["name"], fontsize=18, color=(0, 0, 0))
    
    y_pos = 110
    text_content = template.get("text_content", "")
    for line in text_content.split("\n"):
        if y_pos > 720:
            page = doc.new_page(-1, width=612, height=792)
            y_pos = 72
        page.insert_text(fitz.Point(72, y_pos), line[:90], fontsize=11)
        y_pos += 15
    
    # Signature section
    y_pos += 30
    if y_pos > 650:
        page = doc.new_page(-1, width=612, height=792)
        y_pos = 72
    
    page.insert_text(fitz.Point(72, y_pos), "SIGNATURE", fontsize=14, color=(0, 0, 0))
    y_pos += 25
    page.insert_text(fitz.Point(72, y_pos), f"Signed by: {signature.get('typed_name', 'N/A')}", fontsize=11)
    y_pos += 18
    page.insert_text(fitz.Point(72, y_pos), f"Date: {audit.get('signed_at', 'N/A')}", fontsize=11)
    y_pos += 18
    page.insert_text(fitz.Point(72, y_pos), f"IP: {audit.get('ip_address', 'N/A')}", fontsize=11)
    
    output = BytesIO()
    doc.save(output)
    doc.close()
    return output.getvalue()
