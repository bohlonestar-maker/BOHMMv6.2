# Dues-related Pydantic models
from typing import Optional
from pydantic import BaseModel


class AttendanceRecord(BaseModel):
    member_id: str
    meeting_date: str
    meeting_type: str
    status: str
    notes: Optional[str] = None


class DuesRecord(BaseModel):
    member_id: str
    month: str
    status: str
    notes: Optional[str] = None


class DuesExtensionCreate(BaseModel):
    member_id: str
    extension_until: str
    reason: str = ""


class DuesExtensionUpdate(BaseModel):
    extension_until: str
    reason: str = ""


class SuspendMemberRequest(BaseModel):
    reason: str = "Manual suspension"


class ForgiveDuesRequest(BaseModel):
    member_id: str
    reason: str = ""


class BulkDuesCorrectionRequest(BaseModel):
    member_id: str
    start_month: str
    end_month: str
    status: str = "paid"
    note: str = ""
    revoke_extension: bool = True


class DuesEmailTemplateUpdate(BaseModel):
    subject: str
    body: str
    is_active: bool = True


class LinkSubscriptionRequest(BaseModel):
    member_id: str
    square_customer_id: str
