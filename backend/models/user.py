# User-related Pydantic models
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict
import uuid


class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    email: str
    password_hash: str
    role: str = "member"
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict = Field(default_factory=lambda: {
        "basic_info": True,
        "email": False,
        "phone": False,
        "address": False,
        "dues_tracking": False,
        "meeting_attendance": False,
        "admin_actions": False
    })
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    role: str = "member"
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None


class UserUpdate(BaseModel):
    email: Optional[str] = None
    password: Optional[str] = None
    role: Optional[str] = None
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None


class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    created_at: datetime


class Invite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = False


class InviteCreate(BaseModel):
    email: str
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict


class InviteAccept(BaseModel):
    token: str
    username: str
    password: str


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None


class PasswordResetRequest(BaseModel):
    email: str


class PasswordResetConfirm(BaseModel):
    email: str
    code: str
    new_password: str


class PasswordChange(BaseModel):
    new_password: str


class OwnPasswordChange(BaseModel):
    current_password: str
    new_password: str


class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    action: str
    details: str
    ip_address: Optional[str] = None
