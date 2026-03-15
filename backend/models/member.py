# Member-related Pydantic models
from datetime import datetime, timezone
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict
import uuid


class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chapter: str
    title: str
    handle: str
    name: str
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    experience_start: Optional[str] = None
    phone_private: bool = False
    address_private: bool = False
    email_private: bool = False
    personal_email_private: bool = False
    name_private: bool = False
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    non_dues_paying: bool = False
    actions: list = Field(default_factory=list)
    dues: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
    })
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
    })
    can_edit: Optional[bool] = None
    # Dues balance/credit system
    dues_balance: Optional[float] = 0.0
    dues_suspended: Optional[bool] = False
    dues_suspended_at: Optional[str] = None
    dues_arrangements_made: Optional[bool] = False
    dues_arrangements_date: Optional[str] = None
    dues_arrangements_by: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class MemberCreate(BaseModel):
    chapter: str
    title: str
    handle: str
    name: str
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    experience_start: Optional[str] = None
    phone_private: bool = False
    address_private: bool = False
    email_private: bool = False
    personal_email_private: bool = False
    name_private: bool = False
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    non_dues_paying: bool = False
    dues: Optional[dict] = None


class MemberUpdate(BaseModel):
    chapter: Optional[str] = None
    title: Optional[str] = None
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    personal_email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    experience_start: Optional[str] = None
    phone_private: Optional[bool] = None
    address_private: Optional[bool] = None
    email_private: Optional[bool] = None
    personal_email_private: Optional[bool] = None
    name_private: Optional[bool] = None
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    is_first_responder: Optional[bool] = None
    non_dues_paying: Optional[bool] = None
    dues: Optional[dict] = None
    meeting_attendance: Optional[dict] = None
    # Dues arrangement fields
    dues_arrangements_made: Optional[bool] = None
    dues_arrangements_date: Optional[str] = None
    dues_suspended: Optional[bool] = None


class Hangaround(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): []
    })
    actions: list = Field(default_factory=list)
    can_edit: Optional[bool] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class HangaroundCreate(BaseModel):
    handle: str
    name: str


class HangaroundUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    meeting_attendance: Optional[dict] = None


class Prospect(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    email: str
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    actions: list = Field(default_factory=list)
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): []
    })
    can_edit: Optional[bool] = None
    promoted_from_hangaround: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ProspectCreate(BaseModel):
    handle: str
    name: str
    email: str
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    meeting_attendance: Optional[dict] = None


class ProspectUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    is_first_responder: Optional[bool] = None
    meeting_attendance: Optional[dict] = None


class HangaroundToProspectPromotion(BaseModel):
    email: str
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False


class FallenMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    handle: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None
    join_date: Optional[str] = None
    tribute: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    created_by: Optional[str] = None


class FallenMemberCreate(BaseModel):
    name: str
    handle: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None
    join_date: Optional[str] = None
    tribute: Optional[str] = None
    military_service: bool = False
    military_branch: Optional[str] = None
    is_first_responder: bool = False


class FallenMemberUpdate(BaseModel):
    name: Optional[str] = None
    handle: Optional[str] = None
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None
    join_date: Optional[str] = None
    tribute: Optional[str] = None
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    is_first_responder: Optional[bool] = None
