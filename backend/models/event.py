# Event-related Pydantic models
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    created_by: str
    creator_chapter: Optional[str] = None
    creator_title: Optional[str] = None
    creator_handle: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    discord_notifications_enabled: bool = True
    discord_channel: Optional[str] = "member-chat"
    notification_24h_sent: bool = False
    notification_3h_sent: bool = False
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = 1
    repeat_end_date: Optional[str] = None
    repeat_count: Optional[int] = None
    repeat_days: Optional[List[int]] = None
    parent_event_id: Optional[str] = None
    is_recurring_instance: bool = False


class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: bool = True
    discord_channel: Optional[str] = "member-chat"
    repeat_type: Optional[str] = None
    repeat_interval: Optional[int] = 1
    repeat_end_date: Optional[str] = None
    repeat_count: Optional[int] = None
    repeat_days: Optional[List[int]] = None


class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: Optional[bool] = None
    discord_channel: Optional[str] = None
