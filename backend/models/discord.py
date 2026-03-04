# Discord-related Pydantic models
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class DiscordMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_id: str
    username: str
    display_name: Optional[str] = None
    avatar_url: Optional[str] = None
    joined_at: Optional[datetime] = None
    roles: List[str] = Field(default_factory=list)
    is_bot: bool = False
    member_id: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscordVoiceActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_user_id: str
    channel_id: str
    channel_name: str
    joined_at: datetime
    left_at: Optional[datetime] = None
    duration_seconds: Optional[int] = None
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())


class DiscordTextActivity(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_user_id: str
    channel_id: str
    channel_name: str
    message_count: int = 1
    date: str = Field(default_factory=lambda: datetime.now(timezone.utc).date().isoformat())
    last_message_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class DiscordAnalytics(BaseModel):
    total_members: int
    voice_stats: dict
    text_stats: dict
    top_voice_users: List[dict]
    top_text_users: List[dict]
    daily_activity: List[dict]


class DiscordLinkRequest(BaseModel):
    discord_id: str
    member_id: str


class UpdateRolesRequest(BaseModel):
    role_ids: List[str]


class UpdateNicknameRequest(BaseModel):
    nickname: str
