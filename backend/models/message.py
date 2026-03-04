# Message-related Pydantic models
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class PrivateMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message: str
    timestamp: str
    read: bool = False
    archived_by: List[str] = Field(default_factory=list)


class PrivateMessageCreate(BaseModel):
    recipient: str
    message: str


class SupportMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    message: str
    timestamp: str
    status: str = "open"
    reply_text: Optional[str] = None
    replied_at: Optional[str] = None


class SupportMessageCreate(BaseModel):
    name: str
    email: str
    message: str


class SupportReply(BaseModel):
    reply_text: str


class SupportRequest(BaseModel):
    name: str
    handle: Optional[str] = None
    contact_info: str
    reason: str
