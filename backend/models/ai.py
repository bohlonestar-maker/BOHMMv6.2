# AI-related Pydantic models
from typing import Optional
from pydantic import BaseModel


class ChatMessage(BaseModel):
    message: str


class AIKnowledgeEntry(BaseModel):
    title: str
    content: str
    category: str
    is_active: bool = True
    admin_only: bool = False


class AIKnowledgeUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    category: Optional[str] = None
    is_active: Optional[bool] = None
    admin_only: Optional[bool] = None
