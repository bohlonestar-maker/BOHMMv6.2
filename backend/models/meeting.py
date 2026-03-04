# Meeting-related Pydantic models
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Meeting(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    date: str
    name: Optional[str] = None
    year: str = Field(default_factory=lambda: str(datetime.now(timezone.utc).year))
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None


class MeetingCreate(BaseModel):
    date: str
    name: Optional[str] = None


class MeetingAttendanceRecord(BaseModel):
    meeting_id: str
    member_id: str
    status: int = 0
    note: Optional[str] = None
