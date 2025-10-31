from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Response
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
from cryptography.fernet import Fernet
import hashlib

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Encryption setup (AES-256)
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())

def encrypt_data(data: str) -> str:
    """Encrypt data using AES-256 encryption"""
    if not data:
        return ""
    return cipher_suite.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data: str) -> str:
    """Decrypt data using AES-256 encryption"""
    if not encrypted_data:
        return ""
    try:
        # Try to decrypt - if it fails, data might not be encrypted yet
        return cipher_suite.decrypt(encrypted_data.encode()).decode()
    except Exception as e:
        # If decryption fails, assume data is not encrypted and return as-is
        # This provides backward compatibility with existing unencrypted data
        logger.debug(f"Decryption skipped (data not encrypted): {str(e)[:50]}")
        return encrypted_data


def hash_for_duplicate_detection(data: str) -> str:
    """Create a deterministic hash for duplicate detection of encrypted fields"""
    if not data:
        return ""
    # Use SHA-256 hash for deterministic duplicate detection
    # Lowercase email before hashing for case-insensitive duplicate detection
    normalized_data = data.lower().strip()
    return hashlib.sha256(normalized_data.encode()).hexdigest()


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


# Helper functions for encrypting/decrypting member data
def encrypt_member_sensitive_data(member_data: dict) -> dict:
    """Encrypt sensitive member fields"""
    encrypted = member_data.copy()
    
    # Encrypt sensitive fields
    if 'email' in encrypted and encrypted['email']:
        encrypted['email'] = encrypt_data(encrypted['email'])
    if 'phone' in encrypted and encrypted['phone']:
        encrypted['phone'] = encrypt_data(encrypted['phone'])
    if 'address' in encrypted and encrypted['address']:
        encrypted['address'] = encrypt_data(encrypted['address'])
    
    return encrypted

def decrypt_member_sensitive_data(member_data: dict) -> dict:
    """Decrypt sensitive member fields"""
    decrypted = member_data.copy()
    
    # Decrypt sensitive fields
    if 'email' in decrypted and decrypted['email']:
        decrypted['email'] = decrypt_data(decrypted['email'])
    if 'phone' in decrypted and decrypted['phone']:
        decrypted['phone'] = decrypt_data(decrypted['phone'])
    if 'address' in decrypted and decrypted['address']:
        decrypted['address'] = decrypt_data(decrypted['address'])
    
    return decrypted

def encrypt_support_message(message_data: dict) -> dict:
    """Encrypt support message content"""
    encrypted = message_data.copy()
    
    if 'email' in encrypted and encrypted['email']:
        encrypted['email'] = encrypt_data(encrypted['email'])
    if 'message' in encrypted and encrypted['message']:
        encrypted['message'] = encrypt_data(encrypted['message'])
    if 'reply_text' in encrypted and encrypted['reply_text']:
        encrypted['reply_text'] = encrypt_data(encrypted['reply_text'])
    
    return encrypted

def decrypt_support_message(message_data: dict) -> dict:
    """Decrypt support message content"""
    decrypted = message_data.copy()
    
    if 'email' in decrypted and decrypted['email']:
        decrypted['email'] = decrypt_data(decrypted['email'])
    if 'message' in decrypted and decrypted['message']:
        decrypted['message'] = decrypt_data(decrypted['message'])
    if 'reply_text' in decrypted and decrypted['reply_text']:
        decrypted['reply_text'] = decrypt_data(decrypted['reply_text'])
    
    return decrypted

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


# Generic email sending function for support replies
async def send_email(to_email: str, subject: str, body: str):
    if not SMTP_EMAIL or not SMTP_PASSWORD:
        logger.warning("SMTP credentials not configured")
        return False
    
    message = MIMEMultipart("alternative")
    message["Subject"] = subject
    message["From"] = SMTP_EMAIL
    message["To"] = to_email
    
    # Create plain text and HTML versions
    html = f"""
    <html>
      <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
          <h2 style="color: #1e293b;">Brothers of the Highway TC Support</h2>
          <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
            {body.replace(chr(10), '<br>')}
          </div>
          <p style="color: #64748b; font-size: 12px;">
            This is an automated message from Brothers of the Highway TC Member Directory Support.
          </p>
        </div>
      </body>
    </html>
    """
    
    part1 = MIMEText(body, "plain")
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
        logger.info(f"Email sent to {to_email}")
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
    # Add encryption layer to JWT token
    encrypted_token = encrypt_data(encoded_jwt)
    return encrypted_token

# Token verification
async def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        encrypted_token = credentials.credentials
        # Decrypt the token first
        token = decrypt_data(encrypted_token)
        if not token:
            raise HTTPException(status_code=401, detail="Invalid token format")
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
    except Exception as e:
        logger.error(f"Token verification error: {str(e)}")
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
    role: str = "member"  # admin, member, or prospect
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
    role: str = "member"
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
        str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
        # Format: {"2025": [{"status": "paid|unpaid|late", "note": "reason if late"}, ...], "2024": [...]}
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

class PrivateMessage(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    recipient: str
    message: str
    timestamp: str
    read: bool = False
    archived_by: List[str] = Field(default_factory=list)  # List of users who archived this conversation

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
    status: str = "open"  # open, closed
    reply_text: Optional[str] = None
    replied_at: Optional[str] = None

class SupportMessageCreate(BaseModel):
    name: str
    email: str
    message: str

class SupportReply(BaseModel):
    reply_text: str

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
    user_role = current_user.get('role')
    
    for i, member in enumerate(members):
        # Decrypt sensitive data
        members[i] = decrypt_member_sensitive_data(member)
        
        # Redact contact info for National chapter members if user is not admin
        if user_role != 'admin' and members[i].get('chapter') == 'National':
            members[i]['email'] = 'restricted@admin-only.com'
            members[i]['phone'] = 'Admin Only'
            members[i]['address'] = 'Admin Only'
        
        if isinstance(members[i].get('created_at'), str):
            members[i]['created_at'] = datetime.fromisoformat(members[i]['created_at'])
        if isinstance(members[i].get('updated_at'), str):
            members[i]['updated_at'] = datetime.fromisoformat(members[i]['updated_at'])
    return members

@api_router.get("/members/{member_id}", response_model=Member)
async def get_member(member_id: str, current_user: dict = Depends(verify_token)):
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Decrypt sensitive data
    member = decrypt_member_sensitive_data(member)
    
    # Redact contact info for National chapter members if user is not admin
    user_role = current_user.get('role')
    if user_role != 'admin' and member.get('chapter') == 'National':
        member['email'] = 'restricted@admin-only.com'
        member['phone'] = 'Admin Only'
        member['address'] = 'Admin Only'
    
    if isinstance(member.get('created_at'), str):
        member['created_at'] = datetime.fromisoformat(member['created_at'])
    if isinstance(member.get('updated_at'), str):
        member['updated_at'] = datetime.fromisoformat(member['updated_at'])
    return member

@api_router.post("/members", response_model=Member, status_code=201)
async def create_member(member_data: MemberCreate, current_user: dict = Depends(verify_admin)):
    # Check for duplicate handle
    existing_by_handle = await db.members.find_one({"handle": member_data.handle})
    if existing_by_handle:
        raise HTTPException(
            status_code=400, 
            detail=f"A member with handle '{member_data.handle}' already exists"
        )
    
    # Check for duplicate email using hash comparison
    if member_data.email:
        email_hash = hash_for_duplicate_detection(member_data.email)
        existing_by_email_hash = await db.members.find_one({"email_hash": email_hash})
        
        if existing_by_email_hash:
            raise HTTPException(
                status_code=400,
                detail=f"A member with email '{member_data.email}' already exists"
            )
    
    # Filter out None values to allow default factories to work
    member_dict = {k: v for k, v in member_data.model_dump().items() if v is not None}
    member = Member(**member_dict)
    doc = member.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    
    # Add email hash for duplicate detection before encryption
    if doc.get('email'):
        doc['email_hash'] = hash_for_duplicate_detection(doc['email'])
    
    # Encrypt sensitive data before storing
    doc = encrypt_member_sensitive_data(doc)
    
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
    
    # Check for duplicate handle if being updated
    if member_data.handle and member_data.handle != member.get('handle'):
        existing_by_handle = await db.members.find_one({
            "handle": member_data.handle,
            "id": {"$ne": member_id}  # Exclude current member
        })
        if existing_by_handle:
            raise HTTPException(
                status_code=400,
                detail=f"A member with handle '{member_data.handle}' already exists"
            )
    
    # Check for duplicate email using hash comparison if being updated
    if member_data.email:
        current_email_hash = member.get('email_hash', '')
        new_email_hash = hash_for_duplicate_detection(member_data.email)
        
        if new_email_hash != current_email_hash:
            existing_by_email_hash = await db.members.find_one({
                "email_hash": new_email_hash,
                "id": {"$ne": member_id}
            })
            
            if existing_by_email_hash:
                raise HTTPException(
                    status_code=400,
                    detail=f"A member with email '{member_data.email}' already exists"
                )
    
    update_data = {k: v for k, v in member_data.model_dump().items() if v is not None}
    update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
    
    # Add email hash if email is being updated
    if update_data.get('email'):
        update_data['email_hash'] = hash_for_duplicate_detection(update_data['email'])
    
    # Encrypt sensitive fields in update data
    update_data = encrypt_member_sensitive_data(update_data)
    
    await db.members.update_one({"id": member_id}, {"$set": update_data})
    
    updated_member = await db.members.find_one({"id": member_id}, {"_id": 0})
    # Decrypt for response
    updated_member = decrypt_member_sensitive_data(updated_member)
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
                    dues_months = dues.get(export_year, [{"status": "unpaid", "note": ""} for _ in range(12)])
                else:
                    export_year = str(datetime.now(timezone.utc).year)
                    dues_months = [{"status": "unpaid", "note": ""} for _ in range(12)]
            else:
                export_year = str(datetime.now(timezone.utc).year)
                dues_months = [{"status": "unpaid", "note": ""} for _ in range(12)]
            
            # Convert dues to status strings with notes
            dues_data = []
            for month_due in dues_months:
                if isinstance(month_due, dict):
                    status = month_due.get('status', 'unpaid')
                    note = month_due.get('note', '')
                    if status == 'late' and note:
                        dues_data.append(f'Late ({note})')
                    else:
                        dues_data.append(status.capitalize())
                elif isinstance(month_due, bool):
                    # Handle old boolean format for backward compatibility
                    dues_data.append('Paid' if month_due else 'Unpaid')
                else:
                    dues_data.append('Unpaid')
            
            row.append(export_year)
            row.extend(dues_data)
        
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

@api_router.get("/users/admins")
async def get_admin_users(current_user: dict = Depends(verify_token)):
    """Get list of admin users - accessible to all authenticated users for messaging"""
    admin_users = await db.users.find(
        {"role": "admin"},
        {"_id": 0, "password_hash": 0, "permissions": 0}
    ).to_list(1000)
    
    # Return simple user info for messaging
    return [
        {
            "id": user.get("id", str(uuid.uuid4())),
            "username": user["username"],
            "role": user["role"]
        }
        for user in admin_users
    ]

@api_router.get("/users/all")
async def get_all_users_for_messaging(current_user: dict = Depends(verify_token)):
    """Get list of all users - accessible to all authenticated users for messaging"""
    all_users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0, "permissions": 0}
    ).to_list(1000)
    
    # Return simple user info for messaging
    return [
        {
            "id": user.get("id", str(uuid.uuid4())),
            "username": user["username"],
            "role": user["role"]
        }
        for user in all_users
    ]

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

# Password change endpoint
class PasswordChange(BaseModel):
    new_password: str

@api_router.put("/users/{user_id}/password")
async def change_user_password(user_id: str, password_data: PasswordChange, current_user: dict = Depends(verify_admin)):
    """Change password for a user - admin only"""
    # Validate password
    if len(password_data.new_password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters")
    
    # Hash new password
    password_hash = bcrypt.hashpw(password_data.new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Update user password
    result = await db.users.update_one(
        {"id": user_id},
        {"$set": {"password_hash": password_hash}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Get username for logging
    user = await db.users.find_one({"id": user_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="password_change",
        details=f"Changed password for user: {user['username']}"
    )
    
    return {"message": "Password changed successfully"}

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


@api_router.post("/invites/{token}/resend")
async def resend_invite(token: str, current_user: dict = Depends(verify_admin)):
    """Resend an invitation email"""
    invite = await db.invites.find_one({"token": token})
    if not invite:
        raise HTTPException(status_code=404, detail="Invitation not found")
    
    if invite['used']:
        raise HTTPException(status_code=400, detail="This invitation has already been used")
    
    # Check if expired
    expires_at = datetime.fromisoformat(invite['expires_at']) if isinstance(invite['expires_at'], str) else invite['expires_at']
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="This invitation has expired. Please create a new one.")
    
    # Resend email
    email_sent = await send_invite_email(invite['email'], invite['token'], invite['role'])
    
    if not email_sent:
        raise HTTPException(status_code=500, detail="Failed to send invitation email")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="invite_resend",
        details=f"Resent invitation to {invite['email']}"
    )
    
    return {
        "message": "Invitation email resent successfully",
        "email_sent": email_sent
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

# Private messaging endpoints (all authenticated users)
@api_router.post("/messages", response_model=PrivateMessage)
async def send_private_message(message: PrivateMessageCreate, current_user: dict = Depends(verify_token)):
    """Send a private message to another user"""
    # Verify recipient exists
    recipient_user = await db.users.find_one({"username": message.recipient})
    if not recipient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    private_message = PrivateMessage(
        sender=current_user['username'],
        recipient=message.recipient,
        message=message.message,
        timestamp=datetime.now(timezone.utc).isoformat(),
        read=False
    )
    
    await db.private_messages.insert_one(private_message.model_dump())
    
    return private_message

@api_router.get("/messages/conversations")
async def get_conversations(current_user: dict = Depends(verify_token)):
    """Get list of conversations with last message"""
    username = current_user['username']
    
    # Get all messages where user is sender or recipient, sorted by timestamp
    # Exclude archived conversations
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username},
                {"recipient": username}
            ],
            "archived_by": {"$ne": username}  # Exclude archived
        },
        {"_id": 0}  # Exclude MongoDB ObjectId
    ).sort("timestamp", -1).to_list(None)
    
    # Group by conversation partner
    conversations_dict = {}
    for msg in messages:
        # Determine the other user in the conversation
        other_user = msg['recipient'] if msg['sender'] == username else msg['sender']
        
        if other_user not in conversations_dict:
            conversations_dict[other_user] = {
                "username": other_user,
                "lastMessage": msg,
                "unreadCount": 0
            }
        
        # Count unread messages (where current user is recipient and message is unread)
        if msg['recipient'] == username and not msg['read']:
            conversations_dict[other_user]['unreadCount'] += 1
    
    # Convert dict to list and sort by last message timestamp
    conversations = list(conversations_dict.values())
    conversations.sort(key=lambda x: x['lastMessage']['timestamp'], reverse=True)
    
    return conversations

@api_router.get("/messages/{other_user}")
async def get_messages_with_user(other_user: str, current_user: dict = Depends(verify_token)):
    """Get messages with a specific user"""
    username = current_user['username']
    
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ]
        },
        {"_id": 0}
    ).sort("timestamp", 1).limit(100).to_list(100)
    
    return messages

@api_router.post("/messages/mark_read/{other_user}")
async def mark_private_messages_read(other_user: str, current_user: dict = Depends(verify_token)):
    """Mark all messages from a specific user as read"""
    username = current_user['username']
    
    await db.private_messages.update_many(
        {
            "sender": other_user,
            "recipient": username,
            "read": False
        },
        {"$set": {"read": True}}
    )
    
    return {"message": "Messages marked as read"}

@api_router.get("/messages/unread/count")
async def get_unread_private_messages_count(current_user: dict = Depends(verify_token)):
    """Get count of unread private messages"""
    username = current_user['username']
    
    count = await db.private_messages.count_documents({
        "recipient": username,
        "read": False
    })
    
    return {"unread_count": count}

@api_router.post("/messages/conversation/{other_user}/archive")
async def archive_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Archive conversation with a specific user"""
    username = current_user['username']
    
    # Add current user to archived_by list for all messages in this conversation
    result = await db.private_messages.update_many(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ],
            "archived_by": {"$ne": username}
        },
        {"$push": {"archived_by": username}}
    )
    
    return {
        "message": f"Conversation with {other_user} archived",
        "modified_count": result.modified_count
    }

@api_router.post("/messages/conversation/{other_user}/unarchive")
async def unarchive_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Unarchive conversation with a specific user"""
    username = current_user['username']
    
    # Remove current user from archived_by list for all messages in this conversation
    result = await db.private_messages.update_many(
        {
            "$or": [
                {"sender": username, "recipient": other_user},
                {"sender": other_user, "recipient": username}
            ]
        },
        {"$pull": {"archived_by": username}}
    )
    
    return {
        "message": f"Conversation with {other_user} unarchived",
        "modified_count": result.modified_count
    }

@api_router.get("/messages/conversations/archived")
async def get_archived_conversations(current_user: dict = Depends(verify_token)):
    """Get list of archived conversations"""
    username = current_user['username']
    
    # Get all messages where user is sender or recipient AND has archived the conversation
    messages = await db.private_messages.find(
        {
            "$or": [
                {"sender": username},
                {"recipient": username}
            ],
            "archived_by": username
        },
        {"_id": 0}
    ).sort("timestamp", -1).to_list(None)
    
    # Group by conversation partner
    conversations_dict = {}
    for msg in messages:
        other_user = msg['recipient'] if msg['sender'] == username else msg['sender']
        
        if other_user not in conversations_dict:
            conversations_dict[other_user] = {
                "username": other_user,
                "lastMessage": msg,
                "unreadCount": 0
            }
        
        if msg['recipient'] == username and not msg['read']:
            conversations_dict[other_user]['unreadCount'] += 1
    
    conversations = list(conversations_dict.values())
    conversations.sort(key=lambda x: x['lastMessage']['timestamp'], reverse=True)
    
    return conversations

@api_router.delete("/messages/conversation/{other_user}")
async def delete_conversation(other_user: str, current_user: dict = Depends(verify_token)):
    """Delete entire conversation with a specific user"""
    username = current_user['username']
    
    # Delete all messages between current user and the other user
    result = await db.private_messages.delete_many({
        "$or": [
            {"sender": username, "recipient": other_user},
            {"sender": other_user, "recipient": username}
        ]
    })
    
    return {
        "message": f"Conversation with {other_user} deleted",
        "deleted_count": result.deleted_count
    }

@api_router.get("/messages/monitor/all")
async def get_all_messages_for_monitoring(current_user: dict = Depends(verify_token)):
    """Get all private messages for monitoring - Lonestar only"""
    username = current_user['username']
    
    # Only allow user 'Lonestar' to access this endpoint
    if username.lower() != 'lonestar':
        raise HTTPException(status_code=403, detail="Access denied. This feature is restricted to Lonestar only.")
    
    # Get all private messages, sorted by timestamp (newest first)
    messages = await db.private_messages.find(
        {},
        {"_id": 0}
    ).sort("timestamp", -1).limit(1000).to_list(1000)
    
    return messages


# Support Message endpoints
@api_router.post("/support/messages")
async def create_support_message(support_msg: SupportMessageCreate):
    """Create a new support message (no authentication required)"""
    message = SupportMessage(
        name=support_msg.name,
        email=support_msg.email,
        message=support_msg.message,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
    
    doc = message.model_dump()
    # Encrypt sensitive data
    doc = encrypt_support_message(doc)
    await db.support_messages.insert_one(doc)
    
    return {"message": "Support message submitted successfully", "id": message.id}

@api_router.get("/support/messages")
async def get_support_messages(current_user: dict = Depends(verify_token)):
    """Get all support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    messages = await db.support_messages.find({}).sort("timestamp", -1).to_list(length=None)
    
    for i, msg in enumerate(messages):
        messages[i].pop('_id', None)
        # Decrypt sensitive data
        messages[i] = decrypt_support_message(messages[i])
    
    return messages

@api_router.post("/support/messages/{message_id}/reply")
async def reply_to_support_message(message_id: str, reply: SupportReply, current_user: dict = Depends(verify_token)):
    """Reply to a support message and send email (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    # Get the support message
    message = await db.support_messages.find_one({"id": message_id})
    if not message:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    # Update message with reply
    await db.support_messages.update_one(
        {"id": message_id},
        {
            "$set": {
                "reply_text": reply.reply_text,
                "replied_at": datetime.now(timezone.utc).isoformat(),
                "status": "closed"
            }
        }
    )
    
    # Send email reply
    try:
        await send_email(
            to_email=message['email'],
            subject=f"Re: Support Request - {message['name']}",
            body=f"""Hello {message['name']},

Thank you for contacting Brothers of the Highway TC support.

Your message:
{message['message']}

Our response:
{reply.reply_text}

Best regards,
Brothers of the Highway TC Support Team
"""
        )
        
        return {"message": "Reply sent successfully"}
    except Exception as e:
        logger.error(f"Failed to send email reply: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to send email reply")


@api_router.delete("/support/messages/{message_id}")
async def delete_support_message(message_id: str, current_user: dict = Depends(verify_token)):
    """Delete a single support message (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    result = await db.support_messages.delete_one({"id": message_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Support message not found")
    
    return {"message": "Support message deleted successfully"}


@api_router.get("/support/messages/count")
async def get_open_support_count(current_user: dict = Depends(verify_token)):
    """Get count of open support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    count = await db.support_messages.count_documents({"status": "open"})
    
    return {"count": count}


@api_router.delete("/support/messages/closed/all")
async def delete_closed_messages(current_user: dict = Depends(verify_token)):
    """Delete all closed/replied support messages (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    result = await db.support_messages.delete_many({"status": "closed"})
    
    return {
        "message": f"Deleted {result.deleted_count} closed messages",
        "deleted_count": result.deleted_count
    }

@api_router.get("/support/messages/export")
async def export_support_messages(current_user: dict = Depends(verify_token)):
    """Export support messages to CSV (Lonestar only)"""
    # Check if user is Lonestar
    if current_user['username'] != "Lonestar":
        raise HTTPException(status_code=403, detail="Access denied. This feature is only available to Lonestar.")
    
    messages = await db.support_messages.find({}).sort("timestamp", -1).to_list(length=None)
    
    if not messages:
        raise HTTPException(status_code=404, detail="No messages to export")
    
    # Create CSV content
    csv_content = "ID,Name,Email,Message,Status,Submitted At,Reply,Replied At\n"
    
    for msg in messages:
        # Escape fields that might contain commas or quotes
        name = msg.get('name', '').replace('"', '""')
        email = msg.get('email', '').replace('"', '""')
        message = msg.get('message', '').replace('"', '""').replace('\n', ' ')
        status = msg.get('status', '')
        timestamp = msg.get('timestamp', '')
        reply = msg.get('reply_text', '').replace('"', '""').replace('\n', ' ') if msg.get('reply_text') else ''
        replied_at = msg.get('replied_at', '') if msg.get('replied_at') else ''
        
        csv_content += f'"{msg.get("id", "")}","{name}","{email}","{message}","{status}","{timestamp}","{reply}","{replied_at}"\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=support_messages.csv"}
    )


# AI Chatbot endpoint
class ChatMessage(BaseModel):
    message: str

@api_router.post("/chat")
async def chat_with_bot(chat_msg: ChatMessage, current_user: dict = Depends(verify_token)):
    """AI chatbot for BOH knowledge - authenticated users only"""
    try:
        from emergentintegrations.llm.openai import LlmChat
        
        # Get Emergent LLM key
        api_key = os.environ.get('EMERGENT_LLM_KEY')
        if not api_key:
            raise HTTPException(status_code=500, detail="LLM key not configured")
        
        # Check if user is admin
        is_admin = current_user.get('role') == 'admin'
        
        # Base knowledge for all users
        base_context = """You are an AI assistant for Brothers of the Highway Trucker Club (BOH TC), a 501(c)(3) organization for professional truck drivers. Your role is to answer questions about the organization using ONLY the information provided below.

ORGANIZATION OVERVIEW:
- Brothers of the Highway TC is a men-only trucking organization
- Mission: Support and unite professional truck drivers
- Requirements: Must have Class A CDL, cannot be in 1% MC clubs
- Structure: National Board oversees Chapters (National, AD, HA, HS)
- Legal Status: 501(c)(3) non-profit organization

MISSION STATEMENT:
"We are a Trucker Club that is family oriented, community minded and dedicated to shaping the future while honoring the past. We are a Trucker Club working on bringing back the old school ways of trucking. We are committed to doing what it takes to bring back the respect to the industry by bringing a brotherhood to the industry again."

CORE VALUES & ACTIVITIES:
- Respect To Others While Driving
- Help Other Drivers In Need
- Doing Trash Pick Ups To Keep Lots Clean
- Creating The Family Away From Family
- Donating To Various Charities
- Create A Brotherhood
- Showing All Around Respect
- Doing What It Takes To Make A Change
- Most Of All Bring The Respect Back To Drivers

LOGO ELEMENTS & MEANINGS:
- Phoenix Wings: Represents "Rise of The Old School Brotherhood from the Ashes"
- Old School Truck: Represents Old School Trucking Ways
- Chains: Represents Unity among members
- Tombstones: Represents Our Fallen Brothers
- Truck Number (2158): Alphanumeric identifier for BOH
- TC: Truckers Club designation

MEMBERSHIP PROCESS:
1. Open Enrollment - Public recruiting phase
2. Vetting - Initial interview with Training Chapter
3. Hangaround Phase - Test commitment, chat activity
4. Prospect Phase - 4-6 weeks with assignments, weekly meetings
5. Brother - Full member after vote

CHAIN OF COMMAND:
National Officers: 
- National President (NPrez): Q-Ball - CEO, Chairman of National Board, handles external relations
- National Vice President (NVP): Keltic Reaper - Second in command, assumes NPrez duties in absence
- National Sergeant at Arms (NS@A): Repo - "Legal office" of organization, enforces and interprets By-laws
- National Enforcer (NENF): Gear Jammer - Prospect management oversight
- National Treasurer (NT): California Kid - Budget Committee member, handles finances
- National Secretary (NSEC): Lonestar - Budget Committee member, administrative duties
- National Chapter Director (NCD): Shooter - Administrative position (not in Chain of Command)

ADDITIONAL NATIONAL POSITIONS:
- Club Chaplain (CC): Sancho
- Club Media Director (CMD): Grizz
- Club Counselor & Life Coach (CCLC): Scar

HIGHWAY ASYLUM (HA) CHAPTER OFFICERS (Chain of Command):
- HA President (HAPrez): Chap
- HA Vice President (HAVP): Sancho
- HA Sergeant at Arms (HAS@A): Tapeworm
- HA Enforcer (HAENF): *Vacant*
- HA Secretary (HASEC): Hee Haw
- HA Prospect Manager (HAPM): Phantom

HIGHWAY SOULS (HS) CHAPTER OFFICERS:
- HS President (HSPrez): Bobkat
- HS Vice President (HSVP): Graveyard
- HS Sergeant at Arms (HSS@A): Trucker Dave
- HS Enforcer (HSENF): Rainwater
- HS Secretary (HSSEC): Sodbuster

ASPHALT DEMONS (AD) CHAPTER OFFICERS:
- AD President (ADPrez): Hotshot
- AD Vice President (ADVP): Clutch
- AD Sergeant at Arms (ADS@A): *Vacant*
- AD Enforcer (ADENF): Rookie
- AD Secretary (ADSEC): Two Stacks

CHAPTER OFFICER STRUCTURE:
- President - Chapter leader
- Vice President - Second in command
- Sergeant at Arms (S@A) - "Legal office" of chapter, enforces By-laws
- Enforcer - Prospect management
- Secretary - Administrative duties
- Prospect Manager (PM) - Manages prospects (last in CoC reporting structure)

PROSPECT REQUIREMENTS:
- Attend weekly meetings (Thursdays 4pm CST - MANDATORY)
- Complete weekly assignments (essays, trash pickup, meet-ups)
- Purchase 2 supporter gear items before membering
- Learn: Mission Statement, Logo Elements, Chain of Command
- 100% meeting attendance required
- Active chat participation in Discord
- Must memorize Chain of Command structure

KEY BYLAWS:
- No criminal activity, discrimination, or harassment
- Respect all officers, members, prospects at all times
- Follow Chain of Command always - MUST follow CoC without deviation
- No 1% MC affiliation while in BOH
- Class A CDL required (students with permit may prospect)
- No sex offenders, no drug use/possession
- No reckless driving or property damage

MEET-UPS & EVENTS:
- 3 annual sanctioned meet-ups
- Driver appreciation events
- Family days
- Community service (trash pickups)

SOCIAL MEDIA & COMMUNICATIONS:
- Discord: Primary platform for voice/text chat
- Facebook Family Page: Public outreach, professional posts only
- TikTok: Recruiting tool, PG-level content, 21+ only
- Respect and professional presentation required on all platforms

If asked about something not covered in this knowledge base, politely say you don't have that information and suggest they contact their Chain of Command or check Discord channels.

Be helpful, respectful, and direct. Use BOH terminology (handles, Chain of Command, COC, prospects, Brother, S@A, NPrez, NVP, etc.)."""

        # Admin-only additional context
        admin_context = """

ARTICLE I: GENERAL RULES OF ORDER
- Voting: Officers cannot vote for themselves for promotion/demotion/removal
- Service: Officers serve at pleasure of NPrez and National Board
- Observation Period: 7 days, new officers have no authority during this time
- Probation: 90 days with training and evaluation, can be removed for poor performance
- Guidance: Officers can meet with National Officer equivalents for guidance without subverting CoC

ARTICLE II: OFFICER DUTIES & RESPONSIBILITIES
- Officers must fulfill duties while upholding Member By-laws
- Chain of Command must always be followed
- Officer Meetings: National (Wed 3pm EST), Chapter (Wed 5pm EST)
- 100% attendance required unless approved by CoC
- Officers must obtain missed information if absent
- Cannot comment/vote if not current on events

ARTICLE III: CHAPTER OFFICER EXPECTATIONS
- Responsible for daily management of chapter members
- Conduct meetings, monitor activity, report infractions
- Approach members with respect and courtesy
- Chapter Ranks: President, Vice President, Sergeant at Arms, Enforcer, Secretary

ARTICLE IV: OFFICER NON-PERFORMANCE
- Dereliction of Duty: Can result in sanction up to removal
- 2/3 vote required to discipline (majority for National Board)
- Officers can be voted out except National Committee officers (NPrez removes them)

ARTICLE V: OFFICER DISCIPLINARY PROCESS
- Sanction requests must be submitted within 72 hours to NENF
- Investigation begins within 72 hours by Chapter President
- NS@A drafts Notification of Sanction
- NRC convenes Disciplinary Hearing (with NVP, NS@A, NRC)
- Officer receives notification within 7 days for signature
- Appeals: Submit within 72 hours to NENF, committee reviews within 72 hours
- Officers limited to 2 strikes (vs 3 for members)
- Strikes remain 90 days on record

ARTICLE VI: OFFICER RESIGNATION
- Voluntary positions, can resign anytime
- Must email NS@A AND NRC
- Complete formal letter of resignation

ARTICLE VII: MISCELLANEOUS RULES
- No solicitation, special favors, or personal gain from BOH business
- Higher standards at public events (less intoxicated, professional demeanor)
- Retired NPrez (2+ years): "OG Legacy President" or "BOH NP(r)"
- No voting power but can provide advice/consultation

NATIONAL GOVERNING BODIES:
- National Budget Committee: Oversees quarterly/annual budget, maintains IRS compliance
  Members: National President (Q-Ball), National Treasurer (California Kid), National Secretary (Lonestar)
- National Board: All National Officers (sans National President for voting to maintain odd number)
  Includes: National Vice President (Keltic Reaper), National Sergeant at Arms (Repo), National Enforcer (Gear Jammer), National Treasurer (California Kid), National Secretary (Lonestar)
  Responsible for: Policy creation, membership roll, general operating orders

OFFICER-SPECIFIC BYLAWS:
- Officers serve at pleasure of National President and National Board
- 7-day observation period for newly promoted officers (no authority during this time)
- 90-day probationary period with training and evaluation
- Officers limited to 2 strikes (vs 3 for members)
- 100% attendance required at officer meetings
- Officer meetings: National (Wed 3pm EST), Chapter (Wed 5pm EST)
- Voting: Officers cannot vote for themselves for promotion/demotion/removal
- Sanctions must be requested within 72 hours of infraction
- Officers can resign at any time (notify NS@A and NRC via email)
- No solicitation, special favors, or use of BOH for personal gain
- Higher standard of conduct at public events
- Retired National Presidents (2+ years service) become "BOH NP(r)" or "OG Legacy President"

MEETINGS:
- National Officer: Wednesdays 3pm EST
- Chapter Officer: Wednesdays 5pm EST  
- Prospect: Thursdays 4pm CST (mandatory, 100% attendance)
- Member meetings vary by chapter
- Meeting rules: Microphones muted in app, cameras on (when <20 people), follow Robert's Rules of Order

SANCTIONS (Progressive Discipline):
1. Verbal Warning - Least severe, discussion with Officer
2. Written Warning - Progressive step, documented in Member file
3. Strike - Most severe (3 strikes for members = removal, 2 strikes for Officers = removal)
- Special Assignments may be given instead of standard sanctions
- Chapter Presidents approve sanctions with ½ majority of Officer corp vote
- Prospects can appeal sanctions to National Board

FINANCIAL:
- Monthly member dues (National + Chapter)
- Financial Assistance Program available for hardship cases
- Financial Hardship applications reviewed by Budget Committee
- Merchandise: 2 supporter items required for prospects before membering
- All merchandise sold only on sanctioned BOH platforms

ADDITIONAL OFFICER DUTIES:
- Sergeant at Arms: Activity reports (monthly/weekly/daily), By-law enforcement, interpretation guidance
- National President: External liaison, Executive Orders, conflict resolution, CEO/Chairman, tie-breaking vote
- National Vice President: Information relay, assumes duties in absences, coordinates committees, second in command
- National Sergeant at Arms: Maintains bylaws, ensures National Board orders executed, Discord access management, membership records, protects organization reputation
- National Road Captain: Assists NS@A and NENF, mediates conflicts, project manager for events, ensures bylaw integrity
- National Enforcer: First reportable position, oversees prospect rounds, liaison for disciplinary action, protects organization reputation
- National Treasurer: Oversees spending, maintains financial records, manages dues collection, quarterly financial reports
- National Secretary: Keeps all records/minutes, performs roll calls, handles correspondence, reports to NPrez
- Club Chaplain: Counselor for members, confidential conversations, mental health support (limited capacity)"""

        # Combine contexts based on user role
        if is_admin:
            system_context = base_context + admin_context
        else:
            system_context = base_context

        # Initialize LLM Chat with Emergent key
        session_id = f"chat_{current_user['username']}_{hash(chat_msg.message) % 10000}"
        client = LlmChat(
            api_key=api_key,
            session_id=session_id,
            system_message=system_context
        )
        
        # Send user message and get response
        from emergentintegrations.llm.openai import UserMessage
        user_msg = UserMessage(text=chat_msg.message)
        bot_response = await client.send_message(user_msg)
        
        return {"response": bot_response}
        
    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


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