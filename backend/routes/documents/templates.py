"""
Document Templates API Routes

Handles document template CRUD operations:
- List templates
- Create templates (PDF and text-based)
- Update templates
- Delete/deactivate templates
- PDF page rendering for visual editor
- Field and signature placement management
"""
import sys
import uuid
import base64
from datetime import datetime, timezone
from io import BytesIO

from fastapi import APIRouter, HTTPException, Depends, Request, UploadFile, File, Form
from fastapi.responses import StreamingResponse

from .utils import get_db, get_current_user, hash_document, check_document_permission

router = APIRouter()


# =============================================================================
# TEMPLATE CRUD ENDPOINTS
# =============================================================================

@router.get("/templates")
async def list_document_templates(current_user: dict = Depends(get_current_user)):
    """Get all document templates"""
    db = get_db()
    
    templates = []
    cursor = db.document_templates.find(
        {"is_active": True},
        {"_id": 0, "pdf_data": 0}  # Exclude large PDF data from list
    ).sort("created_at", -1)
    
    async for template in cursor:
        templates.append(template)
    
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
    template_type: str = Form(...),
    category: str = Form(None),
    text_content: str = Form(None),
    pdf_file: UploadFile = File(None),
    current_user: dict = Depends(get_current_user)
):
    """Create a new document template"""
    db = get_db()
    
    if not check_document_permission(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    
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
    
    if not check_document_permission(current_user):
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
# PDF PAGE RENDERING ENDPOINTS
# =============================================================================

@router.get("/templates/{template_id}/pages")
async def get_template_pages(
    template_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get page count and field placements for a PDF template"""
    db = get_db()
    
    template = await db.document_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.get("template_type") != "pdf" or not template.get("pdf_data"):
        raise HTTPException(status_code=400, detail="Template is not a PDF")
    
    try:
        from PyPDF2 import PdfReader
        pdf_bytes = base64.b64decode(template["pdf_data"])
        reader = PdfReader(BytesIO(pdf_bytes))
        
        pages_info = []
        for i, page in enumerate(reader.pages):
            media_box = page.mediabox
            pages_info.append({
                "page": i + 1,
                "width": float(media_box.width),
                "height": float(media_box.height)
            })
        
        return {
            "page_count": len(reader.pages),
            "pages": pages_info,
            "field_placements": template.get("field_placements", []),
            "signature_placements": template.get("signature_placements", [])
        }
    except Exception as e:
        sys.stderr.write(f"[DOCS] Error reading PDF pages: {e}\n")
        raise HTTPException(status_code=500, detail="Failed to read PDF")


@router.get("/templates/{template_id}/page/{page_num}/image")
async def get_template_page_image(
    template_id: str,
    page_num: int,
    current_user: dict = Depends(get_current_user)
):
    """Render a PDF page as an image for the visual editor"""
    db = get_db()
    
    template = await db.document_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    if template.get("template_type") != "pdf" or not template.get("pdf_data"):
        raise HTTPException(status_code=400, detail="Template is not a PDF")
    
    try:
        import fitz  # PyMuPDF
        pdf_bytes = base64.b64decode(template["pdf_data"])
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        
        if page_num < 1 or page_num > len(doc):
            raise HTTPException(status_code=404, detail="Page not found")
        
        page = doc[page_num - 1]
        mat = fitz.Matrix(1.5, 1.5)  # 1.5x zoom for quality
        pix = page.get_pixmap(matrix=mat)
        img_bytes = pix.tobytes("png")
        doc.close()
        
        return StreamingResponse(
            BytesIO(img_bytes),
            media_type="image/png",
            headers={"Cache-Control": "max-age=3600"}  # Cache for 1 hour
        )
    except ImportError:
        sys.stderr.write("[DOCS] PyMuPDF not installed\n")
        raise HTTPException(status_code=501, detail="PDF rendering not available")
    except Exception as e:
        sys.stderr.write(f"[DOCS] Error rendering PDF page: {e}\n")
        raise HTTPException(status_code=500, detail="Failed to render PDF page")


@router.put("/templates/{template_id}/placements")
async def update_template_placements(
    template_id: str,
    request: Request,
    current_user: dict = Depends(get_current_user)
):
    """Update field and signature placements for a template"""
    db = get_db()
    
    if not check_document_permission(current_user):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    template = await db.document_templates.find_one({"id": template_id})
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    
    body = await request.json()
    field_placements = body.get("field_placements", [])
    signature_placements = body.get("signature_placements", [])
    
    # Validate field placements
    required_field_keys = ["id", "field_type", "label", "page", "x", "y", "width", "height"]
    for fp in field_placements:
        if not all(k in fp for k in required_field_keys):
            raise HTTPException(status_code=400, detail="Invalid field placement format")
    
    # Validate signature placements
    required_sig_keys = ["id", "label", "page", "x", "y", "width", "height", "signer_type"]
    for sp in signature_placements:
        if not all(k in sp for k in required_sig_keys):
            raise HTTPException(status_code=400, detail="Invalid signature placement format")
    
    await db.document_templates.update_one(
        {"id": template_id},
        {"$set": {
            "field_placements": field_placements,
            "signature_placements": signature_placements,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    sys.stderr.write(f"[DOCS] Updated placements for '{template_id}': {len(field_placements)} fields, {len(signature_placements)} signatures\n")
    
    return {
        "success": True,
        "message": "Placements updated",
        "field_placements": field_placements,
        "signature_placements": signature_placements
    }
