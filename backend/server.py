from fastapi import FastAPI, APIRouter, HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
import jwt
from passlib.context import CryptContext
import csv
from io import StringIO
from fastapi.responses import StreamingResponse, Response
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'brothers-highway-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Email configuration
SMTP_HOST = os.environ.get('SMTP_HOST', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '465'))
SMTP_EMAIL = os.environ.get('SMTP_EMAIL', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
FRONTEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'http://localhost:3000').replace('/api', '')

# Email sending function
async def send_invite_email(email: str, token: str, role: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured")
        return False
    
    invite_link = f"{FRONTEND_URL}/accept-invite?token={token}"
    
    message = MIMEMultipart("alternative")
    message["Subject"] = "Invitation to Brothers of the Highway Directory"
    message["From"] = SMTP_EMAIL
    message["To"] = email
    
    text = f"""
    You've been invited to join the Brothers of the Highway Member Directory!
    
    Role: {role}
    
    Click the link below to set up your account:
    {invite_link}
    
    This invitation will expire in 7 days.
    """
    
    html = f"""
    <html>
      <body>
        <h2>You've been invited!</h2>
        <p>You've been invited to join the <strong>Brothers of the Highway Member Directory</strong></p>
        <p><strong>Role:</strong> {role}</p>
        <p>Click the button below to set up your account:</p>
        <p><a href="{invite_link}" style="background-color: #1e293b; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; display: inline-block;">Accept Invitation</a></p>
        <p>Or copy this link: {invite_link}</p>
        <p><em>This invitation will expire in 7 days.</em></p>
      </body>
    </html>
    """
    
    part1 = MIMEText(text, "plain")
    part2 = MIMEText(html, "html")
    message.attach(part1)
    message.attach(part2)
    
    try:
        await aiosmtplib.send(
            message,
            hostname=SMTP_HOST,
            port=SMTP_PORT,
            username=SMTP_EMAIL,
            password=SMTP_PASSWORD,
            use_tls=True
        )
        logger.info(f"Invite email sent to {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Password hashing
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# JWT token creation
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# Token verification
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username = payload.get("sub")
        role = payload.get("role")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role}
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# Admin verification
async def verify_admin(current_user: dict = Depends(verify_token)):
    if current_user["role"] != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    return current_user

# Audit logging helper
async def log_activity(username: str, action: str, details: str, ip_address: str = None):
    """Log user activity to audit log"""
    try:
        log = AuditLog(
            username=username,
            action=action,
            details=details,
            ip_address=ip_address
        )
        doc = log.model_dump()
        doc['timestamp'] = doc['timestamp'].isoformat()
        await db.audit_logs.insert_one(doc)
    except Exception as e:
        logger.error(f"Failed to log activity: {str(e)}")

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str = "user"  # admin or user or custom
    permissions: dict = Field(default_factory=lambda: {
        "basic_info": True,        # Chapter, Title, Handle, Name
        "email": False,            # Email access
        "phone": False,            # Phone access
        "address": False,          # Address access
        "dues_tracking": False,    # View dues
        "meeting_attendance": False, # View/manage meeting attendance
        "admin_actions": False     # Add/Edit/Delete, Export CSV, User Management
    })
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    username: str
    password: str
    role: str = "user"
    permissions: Optional[dict] = None

class UserUpdate(BaseModel):
    password: Optional[str] = None
    role: Optional[str] = None
    permissions: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    username: str
    role: str
    permissions: dict
    created_at: datetime

class Invite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    role: str
    permissions: dict
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = False

class InviteCreate(BaseModel):
    email: EmailStr
    role: str
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

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    action: str  # e.g., "login", "member_create", "member_update", "user_delete"
    details: str  # Additional information about the action
    ip_address: Optional[str] = None

class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chapter: str  # National, AD, HA, HS
    title: str  # Prez, VP, S@A, ENF, SEC, T, CD, CC, CCLC, MD, PM
    handle: str
    name: str
    email: EmailStr
    phone: str
    address: str
    dues: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [False] * 12  # Format: {"2025": [12 months], "2024": [12 months]}
    })
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class MemberCreate(BaseModel):
    chapter: str
    title: str
    handle: str
    name: str
    email: EmailStr
    phone: str
    address: str
    dues: Optional[dict] = None

class MemberUpdate(BaseModel):
    chapter: Optional[str] = None
    title: Optional[str] = None
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    dues: Optional[dict] = None
    meeting_attendance: Optional[dict] = None

# Prospect models (Hangarounds/Prospects)
class Prospect(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    email: EmailStr
    phone: str
    address: str
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProspectCreate(BaseModel):
    handle: str
    name: str
    email: EmailStr
    phone: str
    address: str
    meeting_attendance: Optional[dict] = None

class ProspectUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    address: Optional[str] = None
    meeting_attendance: Optional[dict] = None

class ChatMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    message: str
    timestamp: str
    read_by: List[str] = Field(default_factory=list)

class ChatMessageCreate(BaseModel):
    message: str

class PrivateMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message: str
    timestamp: str
    read: bool = False

class PrivateMessageCreate(BaseModel):
    recipient: str
    message: str

# Initialize default admin user
@app.on_event("startup")
async def create_default_admin():
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        admin_user = User(
            username="admin",
            password_hash=hash_password("admin123"),
            role="admin",
            permissions={
                "basic_info": True,
                "email": True,
                "phone": True,
                "address": True,
                "dues_tracking": True,
                "admin_actions": True
            }
        )
        doc = admin_user.model_dump()
        doc['created_at'] = doc['created_at'].isoformat()
        await db.users.insert_one(doc)
        logger.info("Default admin user created: username=admin, password=admin123")

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = await db.users.find_one({"username": login_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({"sub": user["username"], "role": user["role"]})
    
    # Log login activity
    await log_activity(
        username=user["username"],
        action="login",
        details="User logged in successfully"
    )
    
    return LoginResponse(token=token, username=user["username"], role=user["role"])

@api_router.get("/auth/verify")
async def verify(current_user: dict = Depends(verify_token)):
    # Get full user details including permissions
    user = await db.users.find_one({"username": current_user["username"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return {
        "username": user["username"],
        "role": user["role"],
        "permissions": user.get("permissions", {
            "basic_info": True,
            "email": False,
            "phone": False,
            "address": False,
            "dues_tracking": False,
            "admin_actions": False
        })
    }

# Member endpoints
@api_router.get("/members", response_model=List[Member])
async def get_members(current_user: dict = Depends(verify_token)):
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    for member in members:
        if isinstance(member.get('created_at'), str):
            member['created_at'] = datetime.fromisoformat(member['created_at'])
        if isinstance(member.get('updated_at'), str):
            member['updated_at'] = datetime.fromisoformat(member['updated_at'])
    return members

@api_router.get("/members/{member_id}", response_model=Member)
async def get_member(member_id: str, current_user: dict = Depends(verify_token)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    if isinstance(member.get('created_at'), str):
        member['created_at'] = datetime.fromisoformat(member['created_at'])
    if isinstance(member.get('updated_at'), str):
        member['updated_at'] = datetime.fromisoformat(member['updated_at'])
    return member

@api_router.post("/members", response_model=Member, status_code=201)
async def create_member(member_data: MemberCreate, current_user: dict = Depends(verify_admin)):
    # Filter out None values to allow default factories to work
    member_dict = {k: v for k, v in member_data.model_dump().items() if v is not None}
    member = Member(**member_dict)
    doc = member.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.members.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_create",
        details=f"Created member: {member.name} ({member.handle})"
    )
    
    return member

@api_router.put("/members/{member_id}", response_model=Member)
async def update_member(member_id: str, member_data: MemberUpdate, current_user: dict = Depends(verify_admin)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    update_data = {k: v for k, v in member_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_update",
        details=f"Updated member: {updated_member.get('name', 'Unknown')} ({updated_member.get('handle', 'Unknown')})"
    )
    
    return updated_member

@api_router.delete("/members/{member_id}")
async def delete_member(member_id: str, current_user: dict = Depends(verify_admin)):
    # Get member info before deleting
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    
    result = await db.members.delete_one({"id": member_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Log activity
    if member:
        await log_activity(
            username=current_user["username"],
            action="member_delete",
            details=f"Deleted member: {member.get('name', 'Unknown')} ({member.get('handle', 'Unknown')})"
        )
    
    return {"message": "Member deleted successfully"}

# Dues tracking endpoint
@api_router.put("/members/{member_id}/dues")
async def update_member_dues(member_id: str, dues_data: dict, current_user: dict = Depends(verify_admin)):
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    update_data = {
        'dues': dues_data,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    return updated_member

# Meeting attendance tracking endpoint
@api_router.put("/members/{member_id}/attendance")
async def update_member_attendance(member_id: str, attendance_data: dict, current_user: dict = Depends(verify_admin)):
    member = await db.members.find_one({"id": member_id})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    update_data = {
        'meeting_attendance': attendance_data,
        'updated_at': datetime.now(timezone.utc).isoformat()
    }
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if isinstance(updated_member.get('created_at'), str):
        updated_member['created_at'] = datetime.fromisoformat(updated_member['created_at'])
    if isinstance(updated_member.get('updated_at'), str):
        updated_member['updated_at'] = datetime.fromisoformat(updated_member['updated_at'])
    return updated_member

# CSV Export endpoint
@api_router.get("/members/export/csv")
async def export_members_csv(current_user: dict = Depends(verify_token)):
    # Get user permissions
    user = await db.users.find_one({"username": current_user["username"]}, {"_id": 0, "role": 1, "permissions": 1})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    permissions = user.get("permissions", {})
    is_admin = user.get("role") == "admin"
    
    # Check if user has admin_actions permission or any data permission (required to export)
    has_data_permission = any([
        permissions.get("basic_info"),
        permissions.get("email"),
        permissions.get("phone"),
        permissions.get("address"),
        permissions.get("dues_tracking"),
        permissions.get("meeting_attendance")
    ])
    
    if not is_admin and not permissions.get("admin_actions") and not has_data_permission:
        raise HTTPException(status_code=403, detail="Data access permission required to export CSV")
    
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    
    # Define sort order
    CHAPTERS = ["National", "AD", "HA", "HS"]
    TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM"]
    
    # Sort members by chapter and title
    def sort_key(member):
        chapter_index = CHAPTERS.index(member.get('chapter', '')) if member.get('chapter', '') in CHAPTERS else 999
        title_index = TITLES.index(member.get('title', '')) if member.get('title', '') in TITLES else 999
        return (chapter_index, title_index)
    
    sorted_members = sorted(members, key=sort_key)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Build header based on permissions
    header = []
    if is_admin or permissions.get("basic_info"):
        header.extend(['Chapter', 'Title', 'Member Handle', 'Name'])
    if is_admin or permissions.get("email"):
        header.append('Email')
    if is_admin or permissions.get("phone"):
        header.append('Phone')
    if is_admin or permissions.get("address"):
        header.append('Address')
    if is_admin or permissions.get("dues_tracking"):
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        header.append('Dues Year')
        header.extend(month_names)
    if is_admin or permissions.get("meeting_attendance"):
        # Helper function to get nth weekday of month
        def get_nth_weekday(year, month, weekday, n):
            from datetime import date, timedelta
            d = date(year, month, 1)
            count = 0
            while d.month == month:
                if d.weekday() == weekday:
                    count += 1
                    if count == n:
                        return d
                d += timedelta(days=1)
            return None
        
        # Get current year
        current_year = datetime.now(timezone.utc).year
        
        # Generate meeting dates for the year
        meeting_labels = []
        for month_idx, month_name in enumerate(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'], start=1):
            first_wed = get_nth_weekday(current_year, month_idx, 2, 1)  # Wednesday is 2
            third_wed = get_nth_weekday(current_year, month_idx, 2, 3)
            
            first_str = first_wed.strftime("%m/%d") if first_wed else ""
            third_str = third_wed.strftime("%m/%d") if third_wed else ""
            
            meeting_labels.extend([
                f'{month_name}-1st ({first_str})', 
                f'{month_name}-1st Note',
                f'{month_name}-3rd ({third_str})',
                f'{month_name}-3rd Note'
            ])
        
        header.append('Attendance Year')
        header.extend(meeting_labels)
    
    writer.writerow(header)
    
    # Write data based on permissions
    for member in sorted_members:
        row = []
        
        if is_admin or permissions.get("basic_info"):
            row.extend([
                member.get('chapter', ''),
                member.get('title', ''),
                member.get('handle', ''),
                member.get('name', '')
            ])
        
        if is_admin or permissions.get("email"):
            row.append(member.get('email', ''))
        
        if is_admin or permissions.get("phone"):
            row.append(member.get('phone', ''))
        
        if is_admin or permissions.get("address"):
            row.append(member.get('address', ''))
        
        if is_admin or permissions.get("dues_tracking"):
            dues = member.get('dues', {})
            
            # Handle new format (dict with years as keys) and old format (has 'year' key)
            if dues and isinstance(dues, dict):
                if 'year' in dues:
                    # Old format - convert
                    old_year = str(dues.get('year', ''))
                    old_months = dues.get('months', [False] * 12)
                    dues = {old_year: old_months}
                
                # Get most recent year
                years = sorted(dues.keys(), reverse=True)
                if years:
                    export_year = years[0]
                    dues_months = dues.get(export_year, [False] * 12)
                else:
                    export_year = str(datetime.now(timezone.utc).year)
                    dues_months = [False] * 12
            else:
                export_year = str(datetime.now(timezone.utc).year)
                dues_months = [False] * 12
            
            dues_status = ['Paid' if paid else 'Unpaid' for paid in dues_months]
            row.append(export_year)
            row.extend(dues_status)
        
        if is_admin or permissions.get("meeting_attendance"):
            attendance = member.get('meeting_attendance', {})
            
            # Handle new format (dict with years as keys) and old format (single year dict)
            if attendance and isinstance(attendance, dict):
                # Check if it's the new format (years as keys) or old format (has 'year' key)
                if 'year' in attendance:
                    # Old format - convert to new format
                    old_year = str(attendance.get('year', ''))
                    old_meetings = attendance.get('meetings', [])
                    attendance = {old_year: old_meetings}
                
                # Get all years sorted
                years = sorted(attendance.keys(), reverse=True)
                
                # Export most recent year
                if years:
                    current_year = years[0]
                    meetings = attendance.get(current_year, [{"status": 0, "note": ""} for _ in range(24)])
                else:
                    current_year = str(datetime.now(timezone.utc).year)
                    meetings = [{"status": 0, "note": ""} for _ in range(24)]
                
                # Interleave status and notes for each meeting
                meeting_data = []
                for meeting in meetings:
                    if isinstance(meeting, dict):
                        status = meeting.get('status', 0)
                        note = meeting.get('note', '')
                    else:
                        status = meeting
                        note = ''
                    
                    if status == 1:
                        status_text = 'Present'
                    elif status == 2:
                        status_text = 'Excused'
                    else:
                        status_text = 'Absent'
                    
                    meeting_data.append(status_text)
                    meeting_data.append(note)
                
                row.append(current_year)
                row.extend(meeting_data)
            else:
                # No attendance data - interleave empty status and notes
                row.append('')
                for _ in range(24):
                    row.append('Absent')
                    row.append('')
        
        writer.writerow(row)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"}
    )

# Prospect management endpoints (admin only)
@api_router.get("/prospects", response_model=List[Prospect])
async def get_prospects(current_user: dict = Depends(verify_admin)):
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    
    for prospect in prospects:
        if isinstance(prospect.get('created_at'), str):
            prospect['created_at'] = datetime.fromisoformat(prospect['created_at'])
        if isinstance(prospect.get('updated_at'), str):
            prospect['updated_at'] = datetime.fromisoformat(prospect['updated_at'])
    
    return prospects

@api_router.post("/prospects", response_model=Prospect, status_code=201)
async def create_prospect(prospect_data: ProspectCreate, current_user: dict = Depends(verify_admin)):
    prospect_dict = {k: v for k, v in prospect_data.model_dump().items() if v is not None}
    prospect = Prospect(**prospect_dict)
    doc = prospect.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.prospects.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_create",
        details=f"Created prospect: {prospect.name} ({prospect.handle})"
    )
    
    return prospect

@api_router.put("/prospects/{prospect_id}", response_model=Prospect)
async def update_prospect(prospect_id: str, prospect_data: ProspectUpdate, current_user: dict = Depends(verify_admin)):
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    update_data = {k: v for k, v in prospect_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.prospects.update_one({"id": prospect_id}, {"$set": update_data})
    
    updated_prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if isinstance(updated_prospect.get('created_at'), str):
        updated_prospect['created_at'] = datetime.fromisoformat(updated_prospect['created_at'])
    if isinstance(updated_prospect.get('updated_at'), str):
        updated_prospect['updated_at'] = datetime.fromisoformat(updated_prospect['updated_at'])
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_update",
        details=f"Updated prospect: {updated_prospect.get('name', 'Unknown')} ({updated_prospect.get('handle', 'Unknown')})"
    )
    
    return updated_prospect

@api_router.delete("/prospects/{prospect_id}")
async def delete_prospect(prospect_id: str, current_user: dict = Depends(verify_admin)):
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    
    result = await db.prospects.delete_one({"id": prospect_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Log activity
    if prospect:
        await log_activity(
            username=current_user["username"],
            action="prospect_delete",
            details=f"Deleted prospect: {prospect.get('name', 'Unknown')} ({prospect.get('handle', 'Unknown')})"
        )
    
    return {"message": "Prospect deleted successfully"}

@api_router.get("/prospects/export/csv")
async def export_prospects_csv(current_user: dict = Depends(verify_admin)):
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Helper function to get nth weekday of month
    def get_nth_weekday(year, month, weekday, n):
        from datetime import date, timedelta
        d = date(year, month, 1)
        count = 0
        while d.month == month:
            if d.weekday() == weekday:
                count += 1
                if count == n:
                    return d
            d += timedelta(days=1)
        return None
    
    # Get current year or most recent year from data
    current_year = datetime.now(timezone.utc).year
    
    # Generate meeting dates for the year
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    meeting_dates = []
    for month_idx in range(1, 13):
        first_wed = get_nth_weekday(current_year, month_idx, 2, 1)  # Wednesday is 2
        third_wed = get_nth_weekday(current_year, month_idx, 2, 3)
        meeting_dates.append((first_wed, third_wed))
    
    # Create CSV header with dates
    csv_content = "Handle,Name,Email,Phone,Address,Meeting Attendance Year"
    
    for idx, month in enumerate(months):
        first_date, third_date = meeting_dates[idx]
        first_str = first_date.strftime("%m/%d") if first_date else ""
        third_str = third_date.strftime("%m/%d") if third_date else ""
        csv_content += f",{month}-1st ({first_str}),{month}-1st Note,{month}-3rd ({third_str}),{month}-3rd Note"
    csv_content += "\n"
    
    # Add data rows
    for prospect in prospects:
        attendance = prospect.get('meeting_attendance', {})
        
        # Handle new format (dict with years as keys) and old format (single year dict)
        if attendance and isinstance(attendance, dict):
            if 'year' in attendance:
                # Old format - convert
                old_year = str(attendance.get('year', ''))
                old_meetings = attendance.get('meetings', [])
                attendance = {old_year: old_meetings}
            
            # Get most recent year
            years = sorted(attendance.keys(), reverse=True)
            if years:
                export_year = years[0]
                meetings = attendance.get(export_year, [{"status": 0, "note": ""} for _ in range(24)])
            else:
                export_year = str(datetime.now(timezone.utc).year)
                meetings = [{"status": 0, "note": ""} for _ in range(24)]
        else:
            export_year = str(datetime.now(timezone.utc).year)
            meetings = [{"status": 0, "note": ""} for _ in range(24)]
        
        row = [
            prospect.get('handle', ''),
            prospect.get('name', ''),
            prospect.get('email', ''),
            prospect.get('phone', ''),
            prospect.get('address', ''),
            export_year
        ]
        
        # Add meeting attendance
        for meeting in meetings:
            if isinstance(meeting, dict):
                status = meeting.get('status', 0)
                note = meeting.get('note', '')
            else:
                status = meeting
                note = ''
            
            status_text = 'Present' if status == 1 else ('Excused' if status == 2 else 'Absent')
            row.append(status_text)
            row.append(note)
        
        csv_content += ','.join(f'"{str(item)}"' for item in row) + "\n"
    
    return Response(content=csv_content, media_type="text/csv", headers={
        "Content-Disposition": "attachment; filename=prospects.csv"
    })

# User management endpoints (admin only)
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(verify_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    
    # Convert and add default permissions if missing
    result = []
    for user in users:
        # Add id if missing (for old users)
        if 'id' not in user:
            user['id'] = str(uuid.uuid4())
            await db.users.update_one(
                {"username": user['username']},
                {"$set": {"id": user['id']}}
            )
        
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
        
        # Add default permissions if not present
        if 'permissions' not in user:
            if user.get('role') == 'admin':
                user['permissions'] = {
                    "basic_info": True,
                    "email": True,
                    "phone": True,
                    "address": True,
                    "dues_tracking": True,
                    "meeting_attendance": True,
                    "admin_actions": True
                }
            else:
                user['permissions'] = {
                    "basic_info": True,
                    "email": False,
                    "phone": False,
                    "address": False,
                    "dues_tracking": False,
                    "meeting_attendance": False,
                    "admin_actions": False
                }
            # Update the user in database
            await db.users.update_one(
                {"id": user['id']},
                {"$set": {"permissions": user['permissions']}}
            )
        
        result.append(user)
    
    return result

# Audit Logs endpoints
@api_router.get("/logs")
async def get_logs(
    limit: int = 100,
    skip: int = 0,
    username: str = None,
    action: str = None,
    current_user: dict = Depends(verify_admin)
):
    """Get audit logs with optional filters"""
    query = {}
    if username:
        query["username"] = username
    if action:
        query["action"] = action
    
    logs = await db.audit_logs.find(query, {"_id": 0}).sort("timestamp", -1).skip(skip).limit(limit).to_list(limit)
    
    return logs

@api_router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, current_user: dict = Depends(verify_admin)):
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Set default permissions if not provided
    permissions = user_data.permissions
    if permissions is None:
        if user_data.role == "admin":
            permissions = {
                "basic_info": True,
                "email": True,
                "phone": True,
                "address": True,
                "dues_tracking": True,
                "meeting_attendance": True,
                "admin_actions": True
            }
        else:
            permissions = {
                "basic_info": True,
                "email": False,
                "phone": False,
                "address": False,
                "dues_tracking": False,
                "meeting_attendance": False,
                "admin_actions": False
            }
    
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        permissions=permissions
    )
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="user_create",
        details=f"Created user: {user.username} (role: {user.role})"
    )
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
        permissions=user.permissions,
        created_at=user.created_at
    )

@api_router.put("/users/{user_id}")
async def update_user(user_id: str, user_data: UserUpdate, current_user: dict = Depends(verify_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    update_data = {}
    if user_data.password:
        update_data['password_hash'] = hash_password(user_data.password)
    if user_data.role:
        update_data['role'] = user_data.role
    if user_data.permissions is not None:
        update_data['permissions'] = user_data.permissions
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log activity
    updates = []
    if user_data.password:
        updates.append("password")
    if user_data.role:
        updates.append(f"role to {user_data.role}")
    if user_data.permissions is not None:
        updates.append("permissions")
    
    await log_activity(
        username=current_user["username"],
        action="user_update",
        details=f"Updated user: {user['username']} - changed: {', '.join(updates)}"
    )
    
    return {"message": "User updated successfully"}

@api_router.delete("/users/{user_id}")
async def delete_user(user_id: str, current_user: dict = Depends(verify_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Prevent deleting the last admin
    if user['role'] == 'admin':
        admin_count = await db.users.count_documents({"role": "admin"})
        if admin_count <= 1:
            raise HTTPException(status_code=400, detail="Cannot delete the last admin user")
    
    result = await db.users.delete_one({"id": user_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="user_delete",
        details=f"Deleted user: {user['username']} (role: {user['role']})"
    )
    
    return {"message": "User deleted successfully"}

# Invite endpoints
@api_router.post("/invites")
async def create_invite(invite_data: InviteCreate, current_user: dict = Depends(verify_admin)):
    # Check if user with email already exists
    existing = await db.users.find_one({"username": invite_data.email})
    if existing:
        raise HTTPException(status_code=400, detail="User with this email already exists")
    
    # Check for existing unused invite
    existing_invite = await db.invites.find_one({"email": invite_data.email, "used": False})
    if existing_invite:
        raise HTTPException(status_code=400, detail="An active invitation already exists for this email")
    
    # Create invite
    invite = Invite(
        email=invite_data.email,
        role=invite_data.role,
        permissions=invite_data.permissions,
        expires_at=datetime.now(timezone.utc) + timedelta(days=7)
    )
    
    doc = invite.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['expires_at'] = doc['expires_at'].isoformat()
    await db.invites.insert_one(doc)
    
    # Send email
    email_sent = await send_invite_email(invite.email, invite.token, invite.role)
    
    return {
        "message": "Invitation created and email sent" if email_sent else "Invitation created (email failed to send)",
        "invite_link": f"{FRONTEND_URL}/accept-invite?token={invite.token}",
        "email_sent": email_sent
    }

@api_router.get("/invites/{token}")
async def get_invite(token: str):
    invite = await db.invites.find_one({"token": token, "used": False}, {"_id": 0})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    
    # Check if expired
    if isinstance(invite['expires_at'], str):
        expires_at = datetime.fromisoformat(invite['expires_at'])
    else:
        expires_at = invite['expires_at']
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    return {
        "email": invite['email'],
        "role": invite['role'],
        "permissions": invite['permissions']
    }

@api_router.post("/invites/accept")
async def accept_invite(accept_data: InviteAccept):
    invite = await db.invites.find_one({"token": accept_data.token, "used": False})
    if not invite:
        raise HTTPException(status_code=404, detail="Invite not found or already used")
    
    # Check if expired
    if isinstance(invite['expires_at'], str):
        expires_at = datetime.fromisoformat(invite['expires_at'])
    else:
        expires_at = invite['expires_at']
    
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Invite has expired")
    
    # Check if username exists
    existing = await db.users.find_one({"username": accept_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create user
    user = User(
        username=accept_data.username,
        password_hash=hash_password(accept_data.password),
        role=invite['role'],
        permissions=invite['permissions']
    )
    
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    # Mark invite as used
    await db.invites.update_one(
        {"token": accept_data.token},
        {"$set": {"used": True}}
    )
    
    # Generate login token
    token = create_access_token({"sub": user.username, "role": user.role})
    
    return {
        "message": "Account created successfully",
        "token": token,
        "username": user.username,
        "role": user.role
    }

@api_router.get("/invites")
async def list_invites(current_user: dict = Depends(verify_admin)):
    """List all invites (used and unused)"""
    invites = await db.invites.find({}, {"_id": 0}).to_list(1000)
    
    # Convert datetime strings for display
    for invite in invites:
        if isinstance(invite.get('created_at'), str):
            invite['created_at'] = invite['created_at']
        if isinstance(invite.get('expires_at'), str):
            invite['expires_at'] = invite['expires_at']
    
    return invites

@api_router.delete("/invites/{token}")
async def delete_invite(token: str, current_user: dict = Depends(verify_admin)):
    """Delete a specific invite by token"""
    result = await db.invites.delete_one({"token": token})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Invite not found")
    return {"message": "Invite deleted successfully"}

@api_router.delete("/invites/clear/unused")
async def clear_unused_invites(current_user: dict = Depends(verify_admin)):
    """Clear all unused invites"""
    result = await db.invites.delete_many({"used": False})
    return {
        "message": f"Cleared {result.deleted_count} unused invite(s)",
        "deleted_count": result.deleted_count
    }

# Chat endpoints (admin only)
@api_router.post("/chat/messages", response_model=ChatMessage)
async def create_chat_message(message: ChatMessageCreate, current_user: dict = Depends(verify_admin)):
    """Create a new chat message"""
    chat_message = ChatMessage(
        username=current_user['username'],
        message=message.message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        read_by=[current_user['username']]  # Mark as read by sender
    )
    
    await db.chat_messages.insert_one(chat_message.model_dump())
    
    # Log activity
    await log_activity(
        username=current_user['username'],
        action="chat_message",
        details=f"Posted chat message"
    )
    
    return chat_message

@api_router.get("/chat/messages", response_model=List[ChatMessage])
async def get_chat_messages(current_user: dict = Depends(verify_admin)):
    """Get last 100 chat messages"""
    messages = await db.chat_messages.find({}, {"_id": 0}).sort("timestamp", -1).limit(100).to_list(100)
    # Reverse to show oldest first
    messages.reverse()
    return messages

@api_router.get("/chat/unread_count")
async def get_unread_count(current_user: dict = Depends(verify_admin)):
    """Get count of unread messages for current user"""
    username = current_user['username']
    count = await db.chat_messages.count_documents({
        "read_by": {"$ne": username}
    })
    return {"unread_count": count}

@api_router.post("/chat/mark_read")
async def mark_messages_read(current_user: dict = Depends(verify_admin)):
    """Mark all messages as read for current user"""
    username = current_user['username']
    await db.chat_messages.update_many(
        {"read_by": {"$ne": username}},
        {"$push": {"read_by": username}}
    )
    return {"message": "Messages marked as read"}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()