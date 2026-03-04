# SignNow-related Pydantic models
from typing import Optional
from pydantic import BaseModel


class SendDocumentRequest(BaseModel):
    template_id: str
    member_id: str
    recipient_email: Optional[str] = None
    role_name: Optional[str] = None
    role_id: Optional[str] = None
    message: Optional[str] = ""
