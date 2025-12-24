import sys
import os

# Critical: Write to stderr immediately to test if module is loading
sys.stderr.write("🚀 [INIT] Starting server.py module import...\n")
sys.stderr.flush()

# Also try writing to a file as a fallback
try:
    with open('/tmp/server_import.log', 'w') as f:
        f.write("server.py module is being imported\n")
except:
    pass

sys.stderr.write("  [INIT] Importing FastAPI...\n")
sys.stderr.flush()
from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Response, UploadFile, File
sys.stderr.write("  [INIT] Importing security...\n")
sys.stderr.flush()
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
sys.stderr.write("  [INIT] Importing dotenv...\n")
sys.stderr.flush()
from dotenv import load_dotenv
sys.stderr.write("  [INIT] Importing CORS...\n")
sys.stderr.flush()
from starlette.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
sys.stderr.write("  [INIT] Importing Motor (MongoDB async)...\n")
sys.stderr.flush()
from motor.motor_asyncio import AsyncIOMotorClient

sys.stderr.write("  [INIT] Importing logging & pathlib...\n")
sys.stderr.flush()
import os
import logging
from pathlib import Path

sys.stderr.write("✅ [INIT] Core imports successful\n")
sys.stderr.flush()
sys.stderr.write("  [INIT] Importing Pydantic...\n")
sys.stderr.flush()
from pydantic import BaseModel, Field, ConfigDict, EmailStr
sys.stderr.write("  [INIT] Importing typing & utils...\n")
sys.stderr.flush()
from typing import List, Optional
import uuid
from datetime import datetime, timezone, timedelta
sys.stderr.write("  [INIT] Importing JWT...\n")
sys.stderr.flush()
import jwt
sys.stderr.write("  [INIT] Importing passlib (bcrypt)...\n")
sys.stderr.flush()
from passlib.context import CryptContext
sys.stderr.write("  [INIT] Importing CSV & IO...\n")
sys.stderr.flush()
import csv
from io import StringIO
sys.stderr.write("  [INIT] Importing responses...\n")
sys.stderr.flush()
from fastapi.responses import StreamingResponse, Response
sys.stderr.write("  [INIT] Importing aiosmtplib...\n")
sys.stderr.flush()
import aiosmtplib
sys.stderr.write("  [INIT] Importing email MIME...\n")
sys.stderr.flush()
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
sys.stderr.write("  [INIT] Importing cryptography (Fernet)...\n")
sys.stderr.flush()
from cryptography.fernet import Fernet
sys.stderr.write("  [INIT] Importing hashlib...\n")
sys.stderr.flush()
import hashlib
sys.stderr.write("  [INIT] Importing Discord.py...\n")
sys.stderr.flush()
import discord
import asyncio
import aiohttp

sys.stderr.write("✅ [INIT] All imports completed successfully\n")
sys.stderr.flush()

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection - deferred initialization to avoid blocking at import time
sys.stderr.write("🔧 [INIT] Preparing MongoDB configuration...\n")
sys.stderr.flush()
mongo_url = os.environ['MONGO_URL']
# Don't connect immediately - let Motor connect lazily on first use
client = AsyncIOMotorClient(mongo_url, serverSelectionTimeoutMS=5000)
db = client[os.environ['DB_NAME']]
sys.stderr.write("✅ [INIT] MongoDB client configured (will connect on first use)\n")
sys.stderr.flush()

# Encryption setup (AES-256)
sys.stderr.write("🔧 [INIT] Setting up encryption...\n")
sys.stderr.flush()
ENCRYPTION_KEY = os.environ.get('ENCRYPTION_KEY')
if not ENCRYPTION_KEY:
    raise ValueError("ENCRYPTION_KEY not found in environment variables")
cipher_suite = Fernet(ENCRYPTION_KEY.encode())
sys.stderr.write("✅ [INIT] Encryption configured\n")
sys.stderr.flush()

# Discord configuration
sys.stderr.write("🔧 [INIT] Setting up Discord...\n")
sys.stderr.flush()
DISCORD_BOT_TOKEN = os.environ.get('DISCORD_BOT_TOKEN')
DISCORD_CLIENT_ID = os.environ.get('DISCORD_CLIENT_ID')
DISCORD_CLIENT_SECRET = os.environ.get('DISCORD_CLIENT_SECRET')
DISCORD_PUBLIC_KEY = os.environ.get('DISCORD_PUBLIC_KEY')

# Discord bot for activity tracking
discord_bot = None
discord_task = None

async def start_discord_bot():
    """Start Discord analytics bot with voice and text tracking"""
    global discord_bot, discord_task
    try:
        sys.stderr.write("🔧 [DISCORD] Starting Discord analytics bot...\n")
        sys.stderr.flush()
        
        if not DISCORD_BOT_TOKEN:
            sys.stderr.write("❌ [DISCORD] Bot token not found\n")
            sys.stderr.flush()
            return
        
        # Import Discord bot components
        import discord
        from datetime import timezone
        
        # Discord Analytics Bot Class with Voice and Text Tracking
        class DiscordActivityBot(discord.Client):
            def __init__(self):
                intents = discord.Intents.default()
                intents.voice_states = True
                intents.message_content = True
                intents.members = True
                super().__init__(intents=intents)
                self.voice_sessions = {}
                
            async def on_ready(self):
                sys.stderr.write(f"✅ [DISCORD] Bot logged in as {self.user}\n")
                sys.stderr.write(f"✅ [DISCORD] Monitoring {len(self.guilds)} guild(s):\n")
                for guild in self.guilds:
                    sys.stderr.write(f"   - {guild.name} ({guild.id}): {guild.member_count} members\n")
                    
                    # Scan for users already in voice channels and start tracking them
                    for voice_channel in guild.voice_channels:
                        for member in voice_channel.members:
                            if not member.bot:
                                user_id = str(member.id)
                                if user_id not in self.voice_sessions:
                                    self.voice_sessions[user_id] = {
                                        'joined_at': datetime.now(timezone.utc),
                                        'channel_id': str(voice_channel.id),
                                        'channel_name': voice_channel.name
                                    }
                                    sys.stderr.write(f"🎤 [DISCORD] Tracking {member.display_name} already in {voice_channel.name}\n")
                    
                sys.stderr.write(f"✅ [DISCORD] Now tracking {len(self.voice_sessions)} user(s) already in voice\n")
                sys.stderr.flush()
                
            async def on_voice_state_update(self, member, before, after):
                """Track voice channel activity"""
                if member.bot:
                    return
                    
                user_id = str(member.id)
                now = datetime.now(timezone.utc)
                
                try:
                    # User joined voice channel
                    if before.channel is None and after.channel is not None:
                        self.voice_sessions[user_id] = {
                            'joined_at': now,
                            'channel_id': str(after.channel.id),
                            'channel_name': after.channel.name
                        }
                        sys.stderr.write(f"🎤 [DISCORD] {member.display_name} joined {after.channel.name}\n")
                        sys.stderr.flush()
                        
                    # User left voice channel
                    elif before.channel is not None and after.channel is None:
                        if user_id in self.voice_sessions:
                            # We have a tracked session - calculate duration
                            session = self.voice_sessions[user_id]
                            duration = (now - session['joined_at']).total_seconds()
                            
                            # Only save if duration is at least 1 second
                            if duration >= 1:
                                voice_activity = {
                                    'id': str(uuid.uuid4()),
                                    'discord_user_id': user_id,
                                    'channel_id': session['channel_id'],
                                    'channel_name': session['channel_name'],
                                    'joined_at': session['joined_at'],
                                    'left_at': now,
                                    'duration_seconds': int(duration),
                                    'date': now.date().isoformat()
                                }
                                
                                await db.discord_voice_activity.insert_one(voice_activity)
                                sys.stderr.write(f"💾 [DISCORD] Saved {member.display_name} voice session: {duration/60:.1f} min in {session['channel_name']}\n")
                                sys.stderr.flush()
                            else:
                                sys.stderr.write(f"⏭️ [DISCORD] Skipping {member.display_name} session < 1s\n")
                                sys.stderr.flush()
                            del self.voice_sessions[user_id]
                        else:
                            # User was already in voice when bot started but we didn't catch them in on_ready
                            # Start tracking them now for future sessions
                            sys.stderr.write(f"🎤 [DISCORD] {member.display_name} left {before.channel.name} (untracked session)\n")
                            sys.stderr.flush()
                            
                    # User moved between channels
                    elif before.channel is not None and after.channel is not None and before.channel != after.channel:
                        # End previous session
                        if user_id in self.voice_sessions:
                            session = self.voice_sessions[user_id]
                            duration = (now - session['joined_at']).total_seconds()
                            
                            voice_activity = {
                                'id': str(uuid.uuid4()),
                                'discord_user_id': user_id,
                                'channel_id': session['channel_id'],
                                'channel_name': session['channel_name'],
                                'joined_at': session['joined_at'],
                                'left_at': now,
                                'duration_seconds': int(duration),
                                'date': now.date().isoformat()
                            }
                            
                            await db.discord_voice_activity.insert_one(voice_activity)
                        
                        # Start new session
                        self.voice_sessions[user_id] = {
                            'joined_at': now,
                            'channel_id': str(after.channel.id),
                            'channel_name': after.channel.name
                        }
                
                except Exception as e:
                    sys.stderr.write(f"❌ [DISCORD] Voice tracking error: {str(e)}\n")
                    sys.stderr.flush()
                        
            async def on_message(self, message):
                """Track text message activity"""
                if message.author.bot or not message.guild:
                    return
                    
                user_id = str(message.author.id)
                channel_id = str(message.channel.id)
                channel_name = message.channel.name
                today = datetime.now(timezone.utc).date().isoformat()
                
                try:
                    # Check existing record for today
                    existing_record = await db.discord_text_activity.find_one({
                        'discord_user_id': user_id,
                        'channel_id': channel_id,
                        'date': today
                    })
                    
                    if existing_record:
                        await db.discord_text_activity.update_one(
                            {'_id': existing_record['_id']},
                            {
                                '$inc': {'message_count': 1},
                                '$set': {'last_message_at': datetime.now(timezone.utc)}
                            }
                        )
                    else:
                        text_activity = {
                            'id': str(uuid.uuid4()),
                            'discord_user_id': user_id,
                            'channel_id': channel_id,
                            'channel_name': channel_name,
                            'message_count': 1,
                            'date': today,
                            'last_message_at': datetime.now(timezone.utc)
                        }
                        await db.discord_text_activity.insert_one(text_activity)
                
                except Exception as e:
                    sys.stderr.write(f"❌ [DISCORD] Text tracking error: {str(e)}\n")
                    sys.stderr.flush()
        
        # Start the bot
        discord_bot = DiscordActivityBot()
        discord_task = asyncio.create_task(discord_bot.start(DISCORD_BOT_TOKEN))
        
        sys.stderr.write("✅ [DISCORD] Analytics bot started (tracking voice & text)\n")
        sys.stderr.flush()
        
    except Exception as e:
        sys.stderr.write(f"❌ [DISCORD] Error starting bot: {str(e)}\n")
        sys.stderr.flush()

sys.stderr.write("✅ [INIT] Discord configuration loaded\n")
sys.stderr.flush()

# Configure logging (must be early so it's available throughout the module)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

def format_phone_number(phone: str) -> str:
    """Format phone number to (xxx) xxx-xxxx format"""
    if not phone:
        return phone
    
    # Remove all non-digit characters
    digits = ''.join(c for c in phone if c.isdigit())
    
    # Format if we have 10 digits
    if len(digits) == 10:
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    
    # Return original if not 10 digits
    return phone

def decrypt_member_sensitive_data(member_data: dict) -> dict:
    """Decrypt sensitive member fields"""
    decrypted = member_data.copy()
    
    # Decrypt sensitive fields
    if 'email' in decrypted and decrypted['email']:
        decrypted['email'] = decrypt_data(decrypted['email'])
    if 'phone' in decrypted and decrypted['phone']:
        decrypted_phone = decrypt_data(decrypted['phone'])
        decrypted['phone'] = format_phone_number(decrypted_phone)
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

# Support request model
class SupportRequest(BaseModel):
    name: str
    handle: Optional[str] = None
    contact_info: str
    reason: str

# Support email address
SUPPORT_EMAIL = "support@boh2158.org"


# Create the main app without a prefix
app = FastAPI()

# Health check endpoint for Kubernetes - must be at root level (not /api/health)
@app.get("/health")
async def health_check():
    """Health check endpoint for Kubernetes liveness/readiness probes"""
    return {"status": "healthy", "service": "backend"}

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
        chapter = payload.get("chapter")
        title = payload.get("title")
        if username is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        return {"username": username, "role": role, "chapter": chapter, "title": title}
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
    email: str  # Changed from EmailStr to allow "Private" for hidden emails  # Required email field
    password_hash: str
    role: str = "member"  # admin, member, or prospect
    chapter: Optional[str] = None  # National, AD, HA, HS
    title: Optional[str] = None  # Prez, VP, S@A, Member, etc.
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
    email: str  # Changed from EmailStr to allow "Private" for hidden emails  # Required email field
    password: str
    role: str = "member"
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None

class UserUpdate(BaseModel):
    email: Optional[str] = None  # Allow email updates - Changed from EmailStr to allow "Private"
    password: Optional[str] = None
    role: Optional[str] = None
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: Optional[dict] = None

class UserResponse(BaseModel):
    id: str
    username: str
    email: Optional[str] = None  # Optional for backward compatibility
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    created_at: datetime

class Invite(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    role: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    permissions: dict
    token: str = Field(default_factory=lambda: str(uuid.uuid4()))
    expires_at: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    used: bool = False

class InviteCreate(BaseModel):
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
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

class AuditLog(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    username: str
    action: str  # e.g., "login", "member_create", "member_update", "user_delete"
    details: str  # Additional information about the action
    ip_address: Optional[str] = None

class Event(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    date: str  # ISO date string (YYYY-MM-DD)
    time: Optional[str] = None  # Time in HH:MM format
    location: Optional[str] = None
    chapter: Optional[str] = None  # National, AD, HA, HS, or None for all chapters
    title_filter: Optional[str] = None  # Prez, VP, etc., or None for all titles
    created_by: str  # Username of creator
    creator_chapter: Optional[str] = None  # Creator's chapter
    creator_title: Optional[str] = None  # Creator's title
    creator_handle: Optional[str] = None  # Creator's handle from members collection
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    discord_notifications_enabled: bool = True  # Allow Discord notifications for this event
    notification_24h_sent: bool = False  # Track if 24h notification was sent
    notification_3h_sent: bool = False   # Track if 3h notification was sent

class EventCreate(BaseModel):
    title: str
    description: Optional[str] = None
    date: str  # ISO date string (YYYY-MM-DD)
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: bool = True

class EventUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    date: Optional[str] = None
    time: Optional[str] = None
    location: Optional[str] = None
    chapter: Optional[str] = None
    title_filter: Optional[str] = None
    discord_notifications_enabled: Optional[bool] = None

class Member(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    chapter: str  # National, AD, HA, HS
    title: str  # Prez, VP, S@A, ENF, SEC, T, CD, CC, CCLC, MD, PM
    handle: str
    name: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None  # Date of Birth (YYYY-MM-DD format)
    join_date: Optional[str] = None  # Anniversary Date (MM/YYYY format)
    phone_private: bool = False  # If True, only admins can see phone
    address_private: bool = False  # If True, only admins can see address
    email_private: bool = False  # If True, only National members and chapter officers (Prez, VP, S@A, Enf, SEC) can see email
    # Military Service
    military_service: bool = False  # If True, member has served in military
    military_branch: Optional[str] = None  # Army, Navy, Air Force, Marines, Coast Guard, Space Force, National Guard
    # First Responder Service
    is_first_responder: bool = False  # If True, member has served as Police, Fire, or EMS
    actions: list = Field(default_factory=list)  # Merit, Promotion, Disciplinary actions
    # Format: [{"type": "merit|promotion|disciplinary", "date": "YYYY-MM-DD", "description": "...", "added_by": "username", "added_at": "ISO timestamp"}]
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
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    phone_private: bool = False
    address_private: bool = False
    email_private: bool = False
    # Military Service
    military_service: bool = False
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: bool = False
    dues: Optional[dict] = None

class MemberUpdate(BaseModel):
    chapter: Optional[str] = None
    title: Optional[str] = None
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None  # Changed from EmailStr to allow "Private" for hidden emails
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    phone_private: Optional[bool] = None
    address_private: Optional[bool] = None
    email_private: Optional[bool] = None
    # Military Service
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: Optional[bool] = None
    dues: Optional[dict] = None
    meeting_attendance: Optional[dict] = None

# Prospect models (Hangarounds/Prospects)
class Prospect(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    handle: str
    name: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None  # Date of Birth (YYYY-MM-DD format)
    join_date: Optional[str] = None  # Anniversary Date (MM/YYYY format)
    # Military Service
    military_service: bool = False  # If True, prospect has served in military
    military_branch: Optional[str] = None  # Army, Navy, Air Force, Marines, Coast Guard, Space Force, National Guard
    # First Responder Service
    is_first_responder: bool = False  # If True, prospect has served as Police, Fire, or EMS
    actions: list = Field(default_factory=list)  # Merit, Promotion, Disciplinary actions
    meeting_attendance: dict = Field(default_factory=lambda: {
        str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
    })  # Format: {"2025": [meetings], "2024": [meetings], ...}
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ProspectCreate(BaseModel):
    handle: str
    name: str
    email: str  # Changed from EmailStr to allow "Private" for hidden emails
    phone: str
    address: str
    dob: Optional[str] = None
    join_date: Optional[str] = None
    # Military Service
    military_service: bool = False
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: bool = False
    meeting_attendance: Optional[dict] = None

class ProspectUpdate(BaseModel):
    handle: Optional[str] = None
    name: Optional[str] = None
    email: Optional[str] = None  # Changed from EmailStr to allow "Private" for hidden emails
    phone: Optional[str] = None
    address: Optional[str] = None
    dob: Optional[str] = None
    join_date: Optional[str] = None
    # Military Service
    military_service: Optional[bool] = None
    military_branch: Optional[str] = None
    # First Responder Service
    is_first_responder: Optional[bool] = None
    meeting_attendance: Optional[dict] = None

# Fallen Member (Wall of Honor) models
class FallenMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    handle: str
    chapter: Optional[str] = None
    title: Optional[str] = None
    photo_url: Optional[str] = None
    date_of_passing: Optional[str] = None  # YYYY-MM-DD format
    join_date: Optional[str] = None  # When they joined the club
    tribute: Optional[str] = None  # Memorial message
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

# Discord Analytics Models
class DiscordMember(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    discord_id: str  # Discord user ID
    username: str    # Discord username
    display_name: Optional[str] = None  # Discord display name/nickname
    avatar_url: Optional[str] = None
    joined_at: Optional[datetime] = None  # When they joined the Discord server
    roles: List[str] = Field(default_factory=list)  # Discord role IDs
    is_bot: bool = False
    member_id: Optional[str] = None  # Link to our member database
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
    duration_seconds: Optional[int] = None  # Calculated when they leave
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

# Initialize default admin user
@app.on_event("startup")
async def create_default_admin():
    try:
        import sys
        print("🔧 [STARTUP] Checking for default admin user...", file=sys.stderr, flush=True)
        admin_exists = await db.users.find_one({"username": "admin"})
        if not admin_exists:
            print("🔧 [STARTUP] Creating default admin user...", file=sys.stderr, flush=True)
            admin_user = User(
                username="admin",
                email="admin@brothersofthehighway.com",  # Required email field
                password_hash=hash_password("admin123"),
                role="admin",
                permissions={
                    "basic_info": True,
                    "email": True,
                    "phone": True,
                    "address": True,
                    "dues_tracking": True,
                    "meeting_attendance": True,  # All admins need access to all features
                    "admin_actions": True
                }
            )
            doc = admin_user.model_dump()
            doc['created_at'] = doc['created_at'].isoformat()
            await db.users.insert_one(doc)
            logger.info("Default admin user created: username=admin, password=admin123")
            print("✅ [STARTUP] Default admin user created", file=sys.stderr, flush=True)
        else:
            print("✅ [STARTUP] Default admin user already exists", file=sys.stderr, flush=True)
    except Exception as e:
        print(f"❌ [STARTUP] Error in create_default_admin: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        raise

@app.on_event("startup")
async def start_scheduler():
    """Start the APScheduler for Discord event notifications and birthday checks"""
    import sys
    global scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler
        from apscheduler.triggers.cron import CronTrigger
        
        sys.stderr.write("🔧 [SCHEDULER] Initializing Discord notification system...\n")
        sys.stderr.flush()
        
        scheduler = BackgroundScheduler()
        
        # Event notifications - check every 30 minutes
        scheduler.add_job(
            run_notification_check,
            'interval',
            minutes=30,
            id='event_notifications',
            replace_existing=True
        )
        
        # Birthday notifications - run daily at 9:00 AM CST (15:00 UTC)
        scheduler.add_job(
            run_birthday_check,
            CronTrigger(hour=15, minute=0),  # 9:00 AM CST = 15:00 UTC
            id='birthday_notifications',
            replace_existing=True
        )
        
        # Anniversary notifications - run on 1st of each month at 9:00 AM CST (15:00 UTC)
        scheduler.add_job(
            run_anniversary_check,
            CronTrigger(day=1, hour=15, minute=0),  # 1st of month, 9:00 AM CST = 15:00 UTC
            id='anniversary_notifications',
            replace_existing=True
        )
        
        scheduler.start()
        sys.stderr.write("✅ [SCHEDULER] Discord notification system started:\n")
        sys.stderr.write("   📅 Event notifications: every 30 minutes\n")
        sys.stderr.write("   🎂 Birthday notifications: daily at 9:00 AM CST\n")
        sys.stderr.write("   🎉 Anniversary notifications: 1st of month at 9:00 AM CST\n")
        sys.stderr.flush()
    except Exception as e:
        sys.stderr.write(f"⚠️ [SCHEDULER] Failed to start scheduler (app will continue without it): {str(e)}\n")
        sys.stderr.flush()
        # Don't crash the application if scheduler fails to start - this is non-critical functionality
        import traceback
        traceback.print_exc(file=sys.stderr)
        scheduler = None

@app.on_event("startup")
async def start_discord_activity_bot():
    """Start Discord activity tracking bot"""
    if DISCORD_BOT_TOKEN:
        asyncio.create_task(start_discord_bot())

# Auth endpoints
@api_router.post("/auth/login", response_model=LoginResponse)
async def login(login_data: LoginRequest):
    user = await db.users.find_one({"username": login_data.username})
    if not user:
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    if not verify_password(login_data.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    token = create_access_token({
        "sub": user["username"], 
        "role": user["role"],
        "chapter": user.get("chapter"),  # Include chapter for privacy/access control
        "title": user.get("title")  # Include title for email privacy access control
    })
    
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
        "chapter": current_user.get("chapter"),  # Include chapter from JWT token
        "permissions": user.get("permissions", {
            "basic_info": True,
            "email": False,
            "phone": False,
            "address": False,
            "dues_tracking": False,
            "admin_actions": False
        })
    }

# Support request endpoint (no auth required - accessible from login page)
@api_router.post("/support/request")
async def submit_support_request(request: SupportRequest):
    """Submit a support request from the login page"""
    try:
        # Determine if contact info is an email
        contact_is_email = "@" in request.contact_info
        reply_to_email = request.contact_info if contact_is_email else None
        
        # Build the email body
        body = f"""
New Support Request

From: {request.name}
Handle: {request.handle or 'Not provided'}
Contact: {request.contact_info}

Reason for Request:
{request.reason}

---
{"Reply directly to this email to respond to " + request.name if contact_is_email else "Note: Contact provided is not an email. Please use: " + request.contact_info}
        """.strip()
        
        # Send email to support
        if SMTP_EMAIL and SMTP_PASSWORD:
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Support Request from {request.name}"
            message["From"] = SMTP_EMAIL
            message["To"] = SUPPORT_EMAIL
            
            # Set Reply-To so clicking "Reply" goes to the requester
            if reply_to_email:
                message["Reply-To"] = reply_to_email
            
            # Build HTML with clear reply instructions
            reply_instruction = f'''
                <div style="background-color: #dbeafe; padding: 12px; border-radius: 6px; margin-top: 16px; border-left: 4px solid #3b82f6;">
                    <p style="margin: 0; color: #1e40af; font-size: 14px;">
                        <strong>💡 To respond:</strong> {"Simply reply to this email - it will go directly to " + request.name + " at " + request.contact_info if contact_is_email else "Contact " + request.name + " at: <strong>" + request.contact_info + "</strong> (phone number provided)"}
                    </p>
                </div>
            ''' if True else ''
            
            html = f"""
            <html>
              <body>
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                  <h2 style="color: #1e293b;">New Support Request</h2>
                  <div style="background-color: #f8fafc; padding: 20px; border-radius: 8px; margin: 20px 0;">
                    <p><strong>From:</strong> {request.name}</p>
                    <p><strong>Handle:</strong> {request.handle or 'Not provided'}</p>
                    <p><strong>Contact:</strong> {request.contact_info}</p>
                    <hr style="border: 1px solid #e2e8f0; margin: 16px 0;">
                    <p><strong>Reason for Request:</strong></p>
                    <p style="white-space: pre-wrap;">{request.reason}</p>
                  </div>
                  {reply_instruction}
                </div>
              </body>
            </html>
            """
            
            part1 = MIMEText(body, "plain")
            part2 = MIMEText(html, "html")
            message.attach(part1)
            message.attach(part2)
            
            await aiosmtplib.send(
                message,
                hostname=SMTP_HOST,
                port=SMTP_PORT,
                username=SMTP_EMAIL,
                password=SMTP_PASSWORD,
                use_tls=True
            )
            logger.info(f"Support request sent from {request.name}")
            return {"success": True, "message": "Support request submitted successfully"}
        else:
            # Log the request if email isn't configured
            logger.warning(f"SMTP not configured. Support request from {request.name}: {request.reason}")
            return {"success": True, "message": "Support request received (email notification pending)"}
            
    except Exception as e:
        logger.error(f"Failed to submit support request: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to submit support request")

# Member endpoints
@api_router.get("/members", response_model=List[Member])
async def get_members(current_user: dict = Depends(verify_token)):
    members = await db.members.find({}, {"_id": 0}).to_list(10000)
    user_role = current_user.get('role')
    user_chapter = current_user.get('chapter')
    user_title = current_user.get('title', '')
    
    # Titles that can see private emails
    officer_titles = ['Prez', 'VP', 'S@A', 'Enf', 'SEC']
    
    # Check if user can see private emails:
    # - National chapter members can see all private emails
    # - Officers (Prez, VP, S@A, Enf, SEC) of any chapter can see private emails
    is_national_member = user_chapter == 'National'
    is_officer = user_title in officer_titles
    can_see_private_emails = is_national_member or is_officer
    
    # Debug logging
    print(f"[EMAIL PRIVACY DEBUG] User: chapter={user_chapter}, title={user_title}, is_national={is_national_member}, is_officer={is_officer}, can_see_private={can_see_private_emails}")
    
    # For phone/address privacy, only National Chapter admins can see
    is_national_admin = user_role == 'admin' and user_chapter == 'National'
    
    for i, member in enumerate(members):
        # Decrypt sensitive data
        members[i] = decrypt_member_sensitive_data(member)
        
        # Hide names for prospect users
        if user_role == 'prospect':
            members[i]['name'] = 'Hidden'
        
        # Apply email privacy settings
        # Private emails visible to: National members, and officers (Prez, VP, S@A, Enf, SEC)
        if members[i].get('email_private', False) and not can_see_private_emails:
            members[i]['email'] = 'Private'
        
        # Apply phone/address privacy settings (only National Chapter admins can see)
        if not is_national_admin:
            if members[i].get('phone_private', False):
                members[i]['phone'] = 'Private'
            if members[i].get('address_private', False):
                members[i]['address'] = 'Private'
        
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
    
    user_role = current_user.get('role')
    user_chapter = current_user.get('chapter')
    user_title = current_user.get('title', '')
    
    # Titles that can see private emails
    officer_titles = ['Prez', 'VP', 'S@A', 'Enf', 'SEC']
    
    # Check if user can see private emails
    is_national_member = user_chapter == 'National'
    is_officer = user_title in officer_titles
    can_see_private_emails = is_national_member or is_officer
    
    # For phone/address privacy, only National Chapter admins can see
    is_national_admin = user_role == 'admin' and user_chapter == 'National'
    
    # Hide names for prospect users
    if user_role == 'prospect':
        member['name'] = 'Hidden'
    
    # Apply email privacy settings
    if member.get('email_private', False) and not can_see_private_emails:
        member['email'] = 'Private'
    
    # Apply phone/address privacy settings (only National Chapter admins can see)
    if not is_national_admin:
        if member.get('phone_private', False):
            member['phone'] = 'Private'
        if member.get('address_private', False):
            member['address'] = 'Private'
    
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
async def delete_member(
    member_id: str, 
    reason: str,
    current_user: dict = Depends(verify_admin)
):
    """Archive a member with deletion reason"""
    # Get member info before archiving
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Create archived record
    archived_member = {
        **member,
        "deletion_reason": reason,
        "deleted_by": current_user["username"],
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Move to archived collection
    await db.archived_members.insert_one(archived_member)
    
    # Remove from active members
    await db.members.delete_one({"id": member_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_archive",
        details=f"Archived member: {member.get('name', 'Unknown')} ({member.get('handle', 'Unknown')}) - Reason: {reason}"
    )
    
    return {"message": "Member archived successfully"}

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
    
    # Decrypt sensitive data for all members
    decrypted_members = [decrypt_member_sensitive_data(member) for member in members]
    
    # Define sort order
    CHAPTERS = ["National", "AD", "HA", "HS"]
    TITLES = ["Prez", "VP", "S@A", "ENF", "SEC", "T", "CD", "CC", "CCLC", "MD", "PM"]
    
    # Sort members by chapter and title
    def sort_key(member):
        chapter_index = CHAPTERS.index(member.get('chapter', '')) if member.get('chapter', '') in CHAPTERS else 999
        title_index = TITLES.index(member.get('title', '')) if member.get('title', '') in TITLES else 999
        return (chapter_index, title_index)
    
    sorted_members = sorted(decrypted_members, key=sort_key)
    
    output = StringIO()
    writer = csv.writer(output)
    
    # Build header based on permissions with better formatting
    header = []
    if is_admin or permissions.get("basic_info"):
        header.extend(['Chapter', 'Title', 'Member Handle', 'Name'])
    if is_admin or permissions.get("email"):
        header.append('Email Address')
    if is_admin or permissions.get("phone"):
        header.append('Phone Number')
    if is_admin or permissions.get("address"):
        header.append('Mailing Address')
    
    # Always include Military and First Responder fields for admin
    if is_admin:
        header.extend(['Military Service', 'Military Branch', 'First Responder'])
    
    if is_admin or permissions.get("dues_tracking"):
        month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                      'July', 'August', 'September', 'October', 'November', 'December']
        header.append('Dues Year')
        header.extend([f'Dues - {month}' for month in month_names])
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
        
        # Generate meeting dates for the year with better formatting
        meeting_labels = []
        full_month_names = ['January', 'February', 'March', 'April', 'May', 'June', 
                           'July', 'August', 'September', 'October', 'November', 'December']
        for month_idx, month_name in enumerate(full_month_names, start=1):
            first_wed = get_nth_weekday(current_year, month_idx, 2, 1)  # Wednesday is 2
            third_wed = get_nth_weekday(current_year, month_idx, 2, 3)
            
            first_str = first_wed.strftime("%m/%d") if first_wed else ""
            third_str = third_wed.strftime("%m/%d") if third_wed else ""
            
            meeting_labels.extend([
                f'Meeting - {month_name} 1st Wed ({first_str})', 
                f'Meeting - {month_name} 1st Note',
                f'Meeting - {month_name} 3rd Wed ({third_str})',
                f'Meeting - {month_name} 3rd Note'
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
        
        # Always include Military and First Responder fields for admin
        if is_admin:
            row.append('Yes' if member.get('military_service', False) else 'No')
            row.append(member.get('military_branch', '') or '')
            row.append('Yes' if member.get('is_first_responder', False) else 'No')
        
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
    # Add UTF-8 BOM for proper encoding detection in Excel/Google Sheets
    csv_content = '\ufeff' + output.getvalue()
    
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv; charset=utf-8",
        headers={
            "Content-Disposition": "attachment; filename=members.csv",
            "Content-Type": "text/csv; charset=utf-8"
        }
    )

# Member Actions endpoints (admin only)
@api_router.post("/members/{member_id}/actions")
async def add_member_action(
    member_id: str,
    action_type: str,
    date: str,
    description: str,
    current_user: dict = Depends(verify_admin)
):
    """Add a merit, promotion, or disciplinary action to a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Create action record
    action = {
        "id": str(uuid.uuid4()),
        "type": action_type,  # merit, promotion, disciplinary
        "date": date,
        "description": description,
        "added_by": current_user["username"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add action to member's actions list
    actions = member.get("actions", [])
    actions.append(action)
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "add_action",
        f"Added {action_type} action for member {member['handle']}"
    )
    
    return {"message": "Action added successfully", "action": action}

@api_router.delete("/members/{member_id}/actions/{action_id}")
async def delete_member_action(
    member_id: str,
    action_id: str,
    current_user: dict = Depends(verify_admin)
):
    """Delete an action from a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    actions = member.get("actions", [])
    actions = [a for a in actions if a.get("id") != action_id]
    
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "delete_action",
        f"Deleted action from member {member['handle']}"
    )
    
    return {"message": "Action deleted successfully"}

@api_router.put("/members/{member_id}/actions/{action_id}")
async def update_member_action(
    member_id: str,
    action_id: str,
    action_data: dict,
    current_user: dict = Depends(verify_admin)
):
    """Update an action for a member"""
    member = await db.members.find_one({"id": member_id}, {"_id": 0})
    if not member:
        raise HTTPException(status_code=404, detail="Member not found")
    
    # Extract action data
    action_type = action_data.get("action_type")
    date = action_data.get("date")
    description = action_data.get("description")
    
    if not all([action_type, date, description]):
        raise HTTPException(status_code=400, detail="Missing required fields: action_type, date, description")
    
    # Validate action type
    if action_type not in ["merit", "promotion", "disciplinary"]:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    # Find and update the action
    actions = member.get("actions", [])
    action_found = False
    for action in actions:
        if action.get("id") == action_id:
            action["type"] = action_type
            action["date"] = date
            action["description"] = description
            action["updated_at"] = datetime.now(timezone.utc).isoformat()
            action_found = True
            break
    
    if not action_found:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Update the member document
    await db.members.update_one(
        {"id": member_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "update_action",
        f"Updated action for member {member['handle']}: {action_type}"
    )
    
    return {"message": "Action updated successfully"}

# Prospect Actions endpoints (admin only)
@api_router.post("/prospects/{prospect_id}/actions")
async def add_prospect_action(
    prospect_id: str,
    action_type: str,
    date: str,
    description: str,
    current_user: dict = Depends(verify_admin)
):
    """Add a merit, promotion, or disciplinary action to a prospect"""
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create action record
    action = {
        "id": str(uuid.uuid4()),
        "type": action_type,  # merit, promotion, disciplinary
        "date": date,
        "description": description,
        "added_by": current_user["username"],
        "added_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Add action to prospect's actions list
    actions = prospect.get("actions", [])
    actions.append(action)
    
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "add_action",
        f"Added {action_type} action for prospect {prospect['handle']}"
    )
    
    return {"message": "Action added successfully", "action": action}

@api_router.delete("/prospects/{prospect_id}/actions/{action_id}")
async def delete_prospect_action(
    prospect_id: str,
    action_id: str,
    current_user: dict = Depends(verify_admin)
):
    """Delete an action from a prospect"""
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    actions = prospect.get("actions", [])
    actions = [a for a in actions if a.get("id") != action_id]
    
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "delete_action",
        f"Deleted action from prospect {prospect['handle']}"
    )
    
    return {"message": "Action deleted successfully"}

@api_router.put("/prospects/{prospect_id}/actions/{action_id}")
async def update_prospect_action(
    prospect_id: str,
    action_id: str,
    action_data: dict,
    current_user: dict = Depends(verify_admin)
):
    """Update an action for a prospect"""
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Extract action data
    action_type = action_data.get("action_type")
    date = action_data.get("date")
    description = action_data.get("description")
    
    if not all([action_type, date, description]):
        raise HTTPException(status_code=400, detail="Missing required fields: action_type, date, description")
    
    # Validate action type
    if action_type not in ["merit", "promotion", "disciplinary"]:
        raise HTTPException(status_code=400, detail="Invalid action type")
    
    # Find and update the action
    actions = prospect.get("actions", [])
    action_found = False
    for action in actions:
        if action.get("id") == action_id:
            action["type"] = action_type
            action["date"] = date
            action["description"] = description
            action["updated_at"] = datetime.now(timezone.utc).isoformat()
            action_found = True
            break
    
    if not action_found:
        raise HTTPException(status_code=404, detail="Action not found")
    
    # Update the prospect document
    await db.prospects.update_one(
        {"id": prospect_id},
        {"$set": {"actions": actions, "updated_at": datetime.now(timezone.utc)}}
    )
    
    await log_activity(
        current_user["username"],
        "update_action",
        f"Updated action for prospect {prospect['handle']}: {action_type}"
    )
    
    return {"message": "Action updated successfully"}

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
async def delete_prospect(
    prospect_id: str,
    reason: str,
    current_user: dict = Depends(verify_admin)
):
    """Archive a prospect with deletion reason"""
    # Get prospect info before archiving
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create archived record
    archived_prospect = {
        **prospect,
        "deletion_reason": reason,
        "deleted_by": current_user["username"],
        "deleted_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Move to archived collection
    await db.archived_prospects.insert_one(archived_prospect)
    
    # Remove from active prospects
    await db.prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_archive",
        details=f"Archived prospect: {prospect.get('name', 'Unknown')} ({prospect.get('handle', 'Unknown')}) - Reason: {reason}"
    )
    
    return {"message": "Prospect archived successfully"}

@api_router.get("/prospects/export/csv")
async def export_prospects_csv(current_user: dict = Depends(verify_admin)):
    prospects = await db.prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all prospects
    decrypted_prospects = [decrypt_member_sensitive_data(prospect) for prospect in prospects]
    
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
    csv_content = "Handle,Name,Email,Phone,Address,Military Service,Military Branch,First Responder,Meeting Attendance Year"
    
    for idx, month in enumerate(months):
        first_date, third_date = meeting_dates[idx]
        first_str = first_date.strftime("%m/%d") if first_date else ""
        third_str = third_date.strftime("%m/%d") if third_date else ""
        csv_content += f",{month}-1st ({first_str}),{month}-1st Note,{month}-3rd ({third_str}),{month}-3rd Note"
    csv_content += "\n"
    
    # Add data rows
    for prospect in decrypted_prospects:
        attendance = prospect.get('meeting_attendance', {})
        
        # Handle new format (dict with years as keys) and old format (single year dict)
        year_data = attendance.get(str(current_year), {})
        meetings = year_data if isinstance(year_data, list) else year_data.get('meetings', [])
        
        # Ensure we have 24 meetings
        while len(meetings) < 24:
            meetings.append({"status": 0, "note": ""})
        
        # Military and First Responder status
        military_service = "Yes" if prospect.get('military_service', False) else "No"
        military_branch = prospect.get('military_branch', '') or ''
        is_first_responder = "Yes" if prospect.get('is_first_responder', False) else "No"
        
        row = f"{prospect['handle']},{prospect['name']},{prospect['email']},{prospect['phone']},{prospect['address']},{military_service},{military_branch},{is_first_responder},{current_year}"
        
        for i in range(24):
            meeting = meetings[i] if i < len(meetings) else {"status": 0, "note": ""}
            status_map = {0: "Absent", 1: "Present", 2: "Excused"}
            status = status_map.get(meeting.get('status', 0), "Absent")
            note = meeting.get('note', '').replace(',', ';').replace('\n', ' ')
            row += f",{status},{note}"
        
        csv_content += row + "\n"
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=prospects_export.csv"}
    )

@api_router.post("/prospects/{prospect_id}/promote", response_model=Member, status_code=201)
async def promote_prospect_to_member(
    prospect_id: str,
    chapter: str,
    title: str,
    current_user: dict = Depends(verify_admin)
):
    """
    Promote a prospect to a member by copying their data to members collection
    and deleting from prospects collection
    """
    # Get the prospect
    prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not prospect:
        raise HTTPException(status_code=404, detail="Prospect not found")
    
    # Create member data from prospect data
    member_data = {
        "id": str(uuid.uuid4()),  # Generate new ID for member
        "chapter": chapter,
        "title": title,
        "handle": prospect["handle"],
        "name": prospect["name"],
        "email": prospect["email"],
        "phone": prospect["phone"],
        "address": prospect["address"],
        "dob": prospect.get("dob"),
        "join_date": prospect.get("join_date"),
        "phone_private": False,
        "address_private": False,
        "actions": prospect.get("actions", []),  # Carry over actions history
        "dues": {
            str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
        },
        "meeting_attendance": prospect.get("meeting_attendance", {
            str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
        }),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat()
    }
    
    # Encrypt sensitive data
    member_data = encrypt_member_sensitive_data(member_data)
    
    # Check for duplicate handle or email
    existing_handle = await db.members.find_one({"handle": member_data["handle"]})
    if existing_handle:
        raise HTTPException(status_code=400, detail="A member with this handle already exists")
    
    email_hash = hashlib.sha256(member_data["email"].lower().encode()).hexdigest()
    existing_email = await db.members.find_one({"email_hash": email_hash})
    if existing_email:
        raise HTTPException(status_code=400, detail="A member with this email already exists")
    
    member_data["email_hash"] = email_hash
    
    # Insert into members collection
    await db.members.insert_one(member_data)
    
    # Delete from prospects collection
    await db.prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "promote_prospect",
        f"Promoted prospect {prospect['handle']} to member in chapter {chapter}"
    )
    
    # Decrypt for response
    member_data = decrypt_member_sensitive_data(member_data)
    
    return member_data

@api_router.post("/prospects/bulk-promote")
async def bulk_promote_prospects(
    prospect_ids: list[str],
    chapter: str,
    title: str,
    current_user: dict = Depends(verify_admin)
):
    """
    Bulk promote multiple prospects to members with same chapter and title
    """
    promoted_count = 0
    failed_prospects = []
    
    for prospect_id in prospect_ids:
        try:
            # Get the prospect
            prospect = await db.prospects.find_one({"id": prospect_id}, {"_id": 0})
            if not prospect:
                failed_prospects.append({"id": prospect_id, "reason": "Prospect not found"})
                continue
            
            # Create member data from prospect data
            member_data = {
                "id": str(uuid.uuid4()),
                "chapter": chapter,
                "title": title,
                "handle": prospect["handle"],
                "name": prospect["name"],
                "email": prospect["email"],
                "phone": prospect["phone"],
                "address": prospect["address"],
                "dob": prospect.get("dob"),
                "join_date": prospect.get("join_date"),
                "phone_private": False,
                "address_private": False,
                "actions": prospect.get("actions", []),
                "dues": {
                    str(datetime.now(timezone.utc).year): [{"status": "unpaid", "note": ""} for _ in range(12)]
                },
                "meeting_attendance": prospect.get("meeting_attendance", {
                    str(datetime.now(timezone.utc).year): [{"status": 0, "note": ""} for _ in range(24)]
                }),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat()
            }
            
            # Encrypt sensitive data
            member_data = encrypt_member_sensitive_data(member_data)
            
            # Check for duplicate handle or email
            existing_handle = await db.members.find_one({"handle": member_data["handle"]})
            if existing_handle:
                failed_prospects.append({"id": prospect_id, "handle": prospect["handle"], "reason": "Handle already exists in members"})
                continue
            
            email_hash = hashlib.sha256(member_data["email"].lower().encode()).hexdigest()
            existing_email = await db.members.find_one({"email_hash": email_hash})
            if existing_email:
                failed_prospects.append({"id": prospect_id, "handle": prospect["handle"], "reason": "Email already exists in members"})
                continue
            
            member_data["email_hash"] = email_hash
            
            # Insert into members collection
            await db.members.insert_one(member_data)
            
            # Delete from prospects collection
            await db.prospects.delete_one({"id": prospect_id})
            
            promoted_count += 1
            
        except Exception as e:
            failed_prospects.append({"id": prospect_id, "reason": str(e)})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "bulk_promote_prospects",
        f"Bulk promoted {promoted_count} prospects to {chapter} chapter"
    )
    
    return {
        "message": f"Successfully promoted {promoted_count} prospects",
        "promoted_count": promoted_count,
        "failed_count": len(failed_prospects),
        "failed_prospects": failed_prospects
    }

# ==================== WALL OF HONOR (Fallen Members) ====================

@api_router.get("/fallen", response_model=List[FallenMember])
async def get_fallen_members(current_user: dict = Depends(verify_token)):
    """Get all fallen members for the Wall of Honor"""
    fallen = await db.fallen_members.find({}, {"_id": 0}).to_list(1000)
    # Sort by date_of_passing (most recent first), then by name
    fallen.sort(key=lambda x: (x.get('date_of_passing') or '0000-00-00', x.get('name', '')), reverse=True)
    return fallen

@api_router.post("/fallen", response_model=FallenMember, status_code=201)
async def create_fallen_member(
    fallen: FallenMemberCreate,
    current_user: dict = Depends(verify_admin)
):
    """Add a fallen member to the Wall of Honor (admin only)"""
    fallen_dict = fallen.model_dump()
    fallen_dict["id"] = str(uuid.uuid4())
    fallen_dict["created_at"] = datetime.now(timezone.utc)
    fallen_dict["created_by"] = current_user["username"]
    
    await db.fallen_members.insert_one(fallen_dict)
    
    # Log activity
    await log_activity(
        current_user["username"],
        "add_fallen_member",
        f"Added {fallen.handle} ({fallen.name}) to the Wall of Honor"
    )
    
    return FallenMember(**fallen_dict)

@api_router.put("/fallen/{fallen_id}", response_model=FallenMember)
async def update_fallen_member(
    fallen_id: str,
    fallen_update: FallenMemberUpdate,
    current_user: dict = Depends(verify_admin)
):
    """Update a fallen member entry (admin only)"""
    existing = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Fallen member not found")
    
    update_data = {k: v for k, v in fallen_update.model_dump().items() if v is not None}
    
    if update_data:
        await db.fallen_members.update_one(
            {"id": fallen_id},
            {"$set": update_data}
        )
        
        # Log activity
        await log_activity(
            current_user["username"],
            "update_fallen_member",
            f"Updated Wall of Honor entry for {existing.get('handle', existing.get('name'))}"
        )
    
    updated = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    return FallenMember(**updated)

@api_router.delete("/fallen/{fallen_id}")
async def delete_fallen_member(
    fallen_id: str,
    current_user: dict = Depends(verify_admin)
):
    """Remove a fallen member from the Wall of Honor (admin only)"""
    existing = await db.fallen_members.find_one({"id": fallen_id}, {"_id": 0})
    if not existing:
        raise HTTPException(status_code=404, detail="Fallen member not found")
    
    await db.fallen_members.delete_one({"id": fallen_id})
    
    # Log activity
    await log_activity(
        current_user["username"],
        "delete_fallen_member",
        f"Removed {existing.get('handle', existing.get('name'))} from the Wall of Honor"
    )
    
    return {"message": "Fallen member removed from Wall of Honor"}

# ==================== END WALL OF HONOR ====================

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
    current_username = current_user['username']
    user_role = current_user.get('role')
    
    # Define HA chapter officers (only these can be messaged by prospects)
    ha_officers = ['Chap', 'Sancho', 'Tapeworm', 'Hee Haw', 'Phantom']
    
    all_users = await db.users.find(
        {},
        {"_id": 0, "password_hash": 0, "permissions": 0}
    ).to_list(1000)
    
    # Filter based on role
    filtered_users = []
    for user in all_users:
        # Don't include current user
        if user["username"] == current_username:
            continue
            
        # If user is prospect, only show HA chapter officers
        if user_role == 'prospect':
            if user["username"] in ha_officers:
                filtered_users.append({
                    "id": user.get("id", str(uuid.uuid4())),
                    "username": user["username"],
                    "role": user["role"]
                })
        else:
            # Admin and member users can see all users
            filtered_users.append({
                "id": user.get("id", str(uuid.uuid4())),
                "username": user["username"],
                "role": user["role"]
            })
    
    return filtered_users

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
    
    # Check if email exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(status_code=400, detail="Email already exists")
    
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
        email=user_data.email,
        password_hash=hash_password(user_data.password),
        role=user_data.role,
        chapter=user_data.chapter,
        title=user_data.title,
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
    if user_data.email:
        # Check if email is already used by another user
        existing_email = await db.users.find_one({"email": user_data.email, "id": {"$ne": user_id}})
        if existing_email:
            raise HTTPException(status_code=400, detail="Email already exists")
        update_data['email'] = user_data.email
    if user_data.password:
        update_data['password_hash'] = hash_password(user_data.password)
    if user_data.role:
        update_data['role'] = user_data.role
    if user_data.chapter is not None:
        update_data['chapter'] = user_data.chapter
    if user_data.title is not None:
        update_data['title'] = user_data.title
    if user_data.permissions is not None:
        update_data['permissions'] = user_data.permissions
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
    # Log activity
    updates = []
    if user_data.email:
        updates.append(f"email to {user_data.email}")
    if user_data.password:
        updates.append("password")
    if user_data.role:
        updates.append(f"role to {user_data.role}")
    if user_data.chapter is not None:
        updates.append(f"chapter to {user_data.chapter}")
    if user_data.title is not None:
        updates.append(f"title to {user_data.title}")
    if user_data.permissions is not None:
        updates.append("permissions")
    
    await log_activity(
        username=current_user["username"],
        action="user_update",
        details=f"Updated user: {user['username']} - changed: {', '.join(updates)}"
    )
    
    # Get updated user data to return
    updated_user = await db.users.find_one({"id": user_id}, {"_id": 0, "password_hash": 0})
    if isinstance(updated_user.get('created_at'), str):
        updated_user['created_at'] = datetime.fromisoformat(updated_user['created_at'])
    
    return updated_user

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
    
    # Hash new password using helper function
    password_hash = hash_password(password_data.new_password)
    
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
    token = create_access_token({
        "sub": user.username, 
        "role": user.role,
        "chapter": user.chapter,  # Include chapter for privacy/access control
        "title": user.title  # Include title for email privacy access control
    })
    
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

# Archived records endpoints (admin only)
@api_router.get("/archived/members")
async def get_archived_members(current_user: dict = Depends(verify_admin)):
    """Get all archived members"""
    archived = await db.archived_members.find({}, {"_id": 0}).to_list(1000)
    # Sort by deletion date (newest first)
    archived.sort(key=lambda x: x.get('deleted_at', ''), reverse=True)
    return archived

@api_router.get("/archived/prospects")
async def get_archived_prospects(current_user: dict = Depends(verify_admin)):
    """Get all archived prospects"""
    archived = await db.archived_prospects.find({}, {"_id": 0}).to_list(1000)
    # Sort by deletion date (newest first)
    archived.sort(key=lambda x: x.get('deleted_at', ''), reverse=True)
    return archived

@api_router.post("/archived/members/{member_id}/restore")
async def restore_archived_member(member_id: str, current_user: dict = Depends(verify_admin)):
    """Restore an archived member back to active members"""
    # Get archived member
    archived_member = await db.archived_members.find_one({"id": member_id}, {"_id": 0})
    if not archived_member:
        raise HTTPException(status_code=404, detail="Archived member not found")
    
    # Remove archive-specific fields
    archived_member.pop("deletion_reason", None)
    archived_member.pop("deleted_by", None)
    archived_member.pop("deleted_at", None)
    
    # Update timestamps
    archived_member["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Move back to active members
    await db.members.insert_one(archived_member)
    
    # Remove from archived collection
    await db.archived_members.delete_one({"id": member_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="member_restore",
        details=f"Restored member: {archived_member.get('name', 'Unknown')} ({archived_member.get('handle', 'Unknown')})"
    )
    
    return {"message": "Member restored successfully"}

@api_router.post("/archived/prospects/{prospect_id}/restore")
async def restore_archived_prospect(prospect_id: str, current_user: dict = Depends(verify_admin)):
    """Restore an archived prospect back to active prospects"""
    # Get archived prospect
    archived_prospect = await db.archived_prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not archived_prospect:
        raise HTTPException(status_code=404, detail="Archived prospect not found")
    
    # Remove archive-specific fields
    archived_prospect.pop("deletion_reason", None)
    archived_prospect.pop("deleted_by", None)
    archived_prospect.pop("deleted_at", None)
    
    # Update timestamps
    archived_prospect["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Move back to active prospects
    await db.prospects.insert_one(archived_prospect)
    
    # Remove from archived collection
    await db.archived_prospects.delete_one({"id": prospect_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="prospect_restore",
        details=f"Restored prospect: {archived_prospect.get('name', 'Unknown')} ({archived_prospect.get('handle', 'Unknown')})"
    )
    
    return {"message": "Prospect restored successfully"}

@api_router.delete("/archived/members/{member_id}")
async def delete_archived_member(member_id: str, current_user: dict = Depends(verify_admin)):
    """Permanently delete an archived member"""
    # Get archived member
    archived_member = await db.archived_members.find_one({"id": member_id}, {"_id": 0})
    if not archived_member:
        raise HTTPException(status_code=404, detail="Archived member not found")
    
    # Delete from archived collection
    result = await db.archived_members.delete_one({"id": member_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete archived member")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="archived_member_delete",
        details=f"Permanently deleted archived member: {archived_member.get('name', 'Unknown')} ({archived_member.get('handle', 'Unknown')})"
    )
    
    return {"message": "Archived member permanently deleted"}

@api_router.delete("/archived/prospects/{prospect_id}")
async def delete_archived_prospect(prospect_id: str, current_user: dict = Depends(verify_admin)):
    """Permanently delete an archived prospect"""
    # Get archived prospect
    archived_prospect = await db.archived_prospects.find_one({"id": prospect_id}, {"_id": 0})
    if not archived_prospect:
        raise HTTPException(status_code=404, detail="Archived prospect not found")
    
    # Delete from archived collection
    result = await db.archived_prospects.delete_one({"id": prospect_id})
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Failed to delete archived prospect")
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="archived_prospect_delete",
        details=f"Permanently deleted archived prospect: {archived_prospect.get('name', 'Unknown')} ({archived_prospect.get('handle', 'Unknown')})"
    )
    
    return {"message": "Archived prospect permanently deleted"}

@api_router.get("/archived/members/export/csv")
async def export_archived_members_csv(current_user: dict = Depends(verify_admin)):
    """Export archived members to CSV"""
    archived = await db.archived_members.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all archived members
    decrypted_archived = [decrypt_member_sensitive_data(member) for member in archived]
    
    # Create CSV content
    csv_content = "Handle,Name,Email,Phone,Address,Chapter,Title,Date of Birth,Join Date,Deletion Reason,Archived By,Archived At (CST)\n"
    
    for member in decrypted_archived:
        # Convert archived timestamp to CST
        deleted_at = member.get('deleted_at', '')
        if deleted_at:
            from datetime import datetime
            dt = datetime.fromisoformat(deleted_at.replace('Z', '+00:00'))
            # Convert to CST (UTC-6)
            import pytz
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt.astimezone(cst)
            archived_time = dt_cst.strftime('%m/%d/%Y %I:%M %p')
        else:
            archived_time = ''
        
        row = [
            member.get('handle', ''),
            member.get('name', ''),
            member.get('email', ''),
            member.get('phone', ''),
            member.get('address', ''),
            member.get('chapter', ''),
            member.get('title', ''),
            member.get('dob', ''),
            member.get('join_date', ''),
            member.get('deletion_reason', '').replace(',', ';').replace('\n', ' '),
            member.get('deleted_by', ''),
            archived_time
        ]
        csv_content += ','.join(f'"{str(v)}"' for v in row) + '\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=archived_members.csv"}
    )

@api_router.get("/archived/prospects/export/csv")
async def export_archived_prospects_csv(current_user: dict = Depends(verify_admin)):
    """Export archived prospects to CSV"""
    archived = await db.archived_prospects.find({}, {"_id": 0}).to_list(1000)
    
    # Decrypt sensitive data for all archived prospects
    decrypted_archived = [decrypt_member_sensitive_data(prospect) for prospect in archived]
    
    # Create CSV content
    csv_content = "Handle,Name,Email,Phone,Address,Date of Birth,Join Date,Deletion Reason,Archived By,Archived At (CST)\n"
    
    for prospect in decrypted_archived:
        # Convert archived timestamp to CST
        deleted_at = prospect.get('deleted_at', '')
        if deleted_at:
            from datetime import datetime
            dt = datetime.fromisoformat(deleted_at.replace('Z', '+00:00'))
            # Convert to CST (UTC-6)
            import pytz
            cst = pytz.timezone('America/Chicago')
            dt_cst = dt.astimezone(cst)
            archived_time = dt_cst.strftime('%m/%d/%Y %I:%M %p')
        else:
            archived_time = ''
        
        row = [
            prospect.get('handle', ''),
            prospect.get('name', ''),
            prospect.get('email', ''),
            prospect.get('phone', ''),
            prospect.get('address', ''),
            prospect.get('dob', ''),
            prospect.get('join_date', ''),
            prospect.get('deletion_reason', '').replace(',', ';').replace('\n', ' '),
            prospect.get('deleted_by', ''),
            archived_time
        ]
        csv_content += ','.join(f'"{str(v)}"' for v in row) + '\n'
    
    return Response(
        content=csv_content,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=archived_prospects.csv"}
    )

# Private messaging endpoints (all authenticated users)
@api_router.post("/messages", response_model=PrivateMessage)
async def send_private_message(message: PrivateMessageCreate, current_user: dict = Depends(verify_token)):
    """Send a private message to another user"""
    user_role = current_user.get('role')
    
    # Verify recipient exists
    recipient_user = await db.users.find_one({"username": message.recipient})
    if not recipient_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Recipient not found"
        )
    
    # If sender is prospect, verify recipient is HA chapter officer
    if user_role == 'prospect':
        ha_officers = ['Chap', 'Sancho', 'Tapeworm', 'Hee Haw', 'Phantom']
        if message.recipient not in ha_officers:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Prospects can only message Highway Asylum chapter officers"
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


# Discord Analytics Endpoints
@api_router.get("/discord/test-activity")
async def test_discord_activity(current_user: dict = Depends(verify_admin)):
    """Test endpoint to check if Discord activity is being recorded"""
    try:
        # Check if there's any voice or text activity in the database
        voice_count = await db.discord_voice_activity.count_documents({})
        text_count = await db.discord_text_activity.count_documents({})
        
        # Get recent activity (last 24 hours)
        from datetime import datetime, timedelta
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)
        recent_voice = await db.discord_voice_activity.find({
            "joined_at": {"$gte": yesterday}
        }, {"_id": 0}).limit(5).to_list(None)
        
        recent_text = await db.discord_text_activity.find({
            "last_message_at": {"$gte": yesterday}
        }, {"_id": 0}).limit(5).to_list(None)
        
        # Check bot status and guild info
        bot_info = {
            "connected": discord_bot is not None,
            "guilds": len(discord_bot.guilds) if discord_bot else 0,
            "guild_info": []
        }
        
        if discord_bot:
            for guild in discord_bot.guilds:
                bot_info["guild_info"].append({
                    "name": guild.name,
                    "id": str(guild.id), 
                    "member_count": guild.member_count,
                    "voice_channels": len(guild.voice_channels),
                    "text_channels": len(guild.text_channels),
                    "bot_permissions": guild.me.guild_permissions.value
                })
        
        # Convert datetime objects to ISO strings for JSON serialization
        for record in recent_voice:
            if 'joined_at' in record and isinstance(record['joined_at'], datetime):
                record['joined_at'] = record['joined_at'].isoformat()
            if 'left_at' in record and isinstance(record['left_at'], datetime):
                record['left_at'] = record['left_at'].isoformat()
        
        for record in recent_text:
            if 'last_message_at' in record and isinstance(record['last_message_at'], datetime):
                record['last_message_at'] = record['last_message_at'].isoformat()
        
        return {
            "bot_status": "running" if discord_bot else "not_running",
            "bot_info": bot_info,
            "total_voice_records": voice_count,
            "total_text_records": text_count,
            "recent_voice_activity": len(recent_voice),
            "recent_text_activity": len(recent_text),
            "recent_voice_records": recent_voice,
            "recent_text_records": recent_text,
            "currently_tracking": len(discord_bot.voice_sessions) if discord_bot and hasattr(discord_bot, 'voice_sessions') else 0,
            "message": f"Bot is {'active' if discord_bot else 'inactive'}. Voice: {voice_count} records, Text: {text_count} records"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test error: {str(e)}")


@api_router.post("/discord/resync-voice")
async def resync_discord_voice_tracking(current_user: dict = Depends(verify_admin)):
    """Resync voice tracking by scanning all voice channels for connected users"""
    try:
        if not discord_bot:
            raise HTTPException(status_code=503, detail="Discord bot is not running")
        
        # Clear existing tracked sessions (they may be stale)
        old_count = len(discord_bot.voice_sessions)
        discord_bot.voice_sessions.clear()
        
        # Scan all guilds for users in voice channels
        new_tracked = []
        from datetime import timezone
        now = datetime.now(timezone.utc)
        
        for guild in discord_bot.guilds:
            for voice_channel in guild.voice_channels:
                for member in voice_channel.members:
                    if not member.bot:
                        user_id = str(member.id)
                        discord_bot.voice_sessions[user_id] = {
                            'joined_at': now,
                            'channel_id': str(voice_channel.id),
                            'channel_name': voice_channel.name
                        }
                        new_tracked.append({
                            "user": member.display_name,
                            "channel": voice_channel.name
                        })
        
        return {
            "success": True,
            "previous_tracking": old_count,
            "now_tracking": len(discord_bot.voice_sessions),
            "users": new_tracked,
            "message": f"Resynced voice tracking. Now tracking {len(new_tracked)} user(s) in voice channels."
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Resync error: {str(e)}")


@api_router.post("/discord/sync-members")
async def sync_discord_members(current_user: dict = Depends(verify_admin)):
    """Sync Discord members - remove members who left the server and update existing ones"""
    try:
        if not discord_bot:
            raise HTTPException(status_code=503, detail="Discord bot is not running")
        
        # Get current Discord members from the bot
        current_discord_ids = set()
        updated_count = 0
        added_count = 0
        
        for guild in discord_bot.guilds:
            for member in guild.members:
                discord_id = str(member.id)
                current_discord_ids.add(discord_id)
                
                # Update or insert member
                existing = await db.discord_members.find_one({"discord_id": discord_id})
                
                member_data = {
                    "discord_id": discord_id,
                    "username": member.name,
                    "display_name": member.display_name,
                    "avatar_url": str(member.avatar.url) if member.avatar else None,
                    "is_bot": member.bot,
                    "last_seen": datetime.now(timezone.utc)
                }
                
                if existing:
                    # Preserve linked member_id if exists
                    if existing.get("member_id"):
                        member_data["member_id"] = existing["member_id"]
                    await db.discord_members.update_one(
                        {"discord_id": discord_id},
                        {"$set": member_data}
                    )
                    updated_count += 1
                else:
                    await db.discord_members.insert_one(member_data)
                    added_count += 1
        
        # Remove members no longer in Discord
        db_members = await db.discord_members.find({}, {"discord_id": 1}).to_list(None)
        removed_count = 0
        removed_members = []
        
        for db_member in db_members:
            if db_member["discord_id"] not in current_discord_ids:
                # Get member info before removing
                full_member = await db.discord_members.find_one({"discord_id": db_member["discord_id"]})
                removed_members.append({
                    "discord_id": db_member["discord_id"],
                    "username": full_member.get("username") if full_member else "Unknown",
                    "display_name": full_member.get("display_name") if full_member else "Unknown"
                })
                await db.discord_members.delete_one({"discord_id": db_member["discord_id"]})
                removed_count += 1
        
        # Get final count
        final_count = await db.discord_members.count_documents({})
        
        return {
            "success": True,
            "discord_server_count": len(current_discord_ids),
            "database_count": final_count,
            "updated": updated_count,
            "added": added_count,
            "removed": removed_count,
            "removed_members": removed_members,
            "message": f"Synced members. Updated: {updated_count}, Added: {added_count}, Removed: {removed_count}"
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Sync error: {str(e)}")

@api_router.post("/discord/simulate-activity")
async def simulate_discord_activity(current_user: dict = Depends(verify_admin)):
    """Simulate Discord activity for testing purposes"""
    try:
        # Create sample voice activity
        now = datetime.now(timezone.utc)
        thirty_min_ago = now - timedelta(minutes=30)
        
        voice_activity = {
            'id': str(uuid.uuid4()),
            'discord_user_id': '12345678901234567890',  # Test user ID
            'channel_id': '98765432109876543210',
            'channel_name': 'General Voice',
            'joined_at': thirty_min_ago,
            'left_at': now,
            'duration_seconds': 1800,  # 30 minutes
            'date': now.date().isoformat()
        }
        
        # Create sample text activity
        text_activity = {
            'id': str(uuid.uuid4()),
            'discord_user_id': '12345678901234567890',  # Test user ID
            'channel_id': '11111111111111111111',
            'channel_name': 'general',
            'message_count': 5,
            'date': now.date().isoformat(),
            'last_message_at': now
        }
        
        # Insert test data (MongoDB will add _id automatically)
        voice_result = await db.discord_voice_activity.insert_one(voice_activity)
        text_result = await db.discord_text_activity.insert_one(text_activity)
        
        # Convert datetime objects to ISO strings for JSON serialization
        voice_activity_response = voice_activity.copy()
        voice_activity_response['joined_at'] = voice_activity['joined_at'].isoformat()
        voice_activity_response['left_at'] = voice_activity['left_at'].isoformat()
        
        text_activity_response = text_activity.copy()
        text_activity_response['last_message_at'] = text_activity['last_message_at'].isoformat()
        
        return {
            "message": "Test activity created successfully",
            "voice_activity": voice_activity_response,
            "text_activity": text_activity_response
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@api_router.get("/discord/members")
async def get_discord_members(current_user: dict = Depends(verify_admin)):
    """Get Discord server members list - returns cached data from database"""
    try:
        # First try to fetch fresh data from Discord API
        api_success = False
        async with aiohttp.ClientSession() as session:
            headers = {'Authorization': f'Bot {DISCORD_BOT_TOKEN}'}
            guild_id = "991898490743574628"  # Brothers of the Highway Discord server
            async with session.get(f'https://discord.com/api/v10/guilds/{guild_id}/members?limit=1000', headers=headers) as resp:
                if resp.status == 200:
                    api_success = True
                    discord_members = await resp.json()
                    
                    # Store/update members in database
                    for member in discord_members:
                        user = member['user']
                        discord_member = DiscordMember(
                            discord_id=user['id'],
                            username=user['username'],
                            display_name=member.get('nick') or user.get('display_name'),
                            avatar_url=f"https://cdn.discordapp.com/avatars/{user['id']}/{user['avatar']}.png" if user.get('avatar') else None,
                            joined_at=datetime.fromisoformat(member['joined_at'].replace('Z', '+00:00')) if member.get('joined_at') else None,
                            roles=member.get('roles', []),
                            is_bot=user.get('bot', False)
                        )
                        
                        # Upsert to database - preserve member_id if it exists
                        discord_data = discord_member.model_dump()
                        # Remove member_id from the update to preserve existing links
                        discord_data.pop('member_id', None)
                        
                        await db.discord_members.update_one(
                            {"discord_id": user['id']},
                            {"$set": discord_data},
                            upsert=True
                        )
                    
                    # Return stored members with linked member information
                    stored_members = await db.discord_members.find({}, {"_id": 0}).to_list(1000)
                    
                    # Enrich with linked member information
                    for discord_member in stored_members:
                        if discord_member.get("member_id"):
                            # Fetch the linked database member
                            db_member = await db.members.find_one(
                                {"id": discord_member["member_id"]},
                                {"_id": 0, "handle": 1, "name": 1}
                            )
                            if db_member:
                                discord_member["linked_member"] = {
                                    "handle": db_member.get("handle"),
                                    "name": db_member.get("name")
                                }
                    
                    return stored_members
        
        # If Discord API failed, return cached data from database
        if not api_success:
            print("⚠️ Discord API failed, returning cached members from database")
            stored_members = await db.discord_members.find(
                {"is_bot": {"$ne": True}},
                {"_id": 0}
            ).sort("display_name", 1).to_list(1000)
            
            # Enrich with linked member info
            for discord_member in stored_members:
                if discord_member.get("member_id"):
                    db_member = await db.members.find_one(
                        {"id": discord_member["member_id"]},
                        {"_id": 0, "handle": 1, "name": 1}
                    )
                    if db_member:
                        discord_member["linked_member"] = {
                            "handle": db_member.get("handle"),
                            "name": db_member.get("name")
                        }
            
            return stored_members
                
    except Exception as e:
        # On any error, try to return cached data
        try:
            print(f"⚠️ Error fetching Discord members: {str(e)}, returning cached data")
            stored_members = await db.discord_members.find(
                {"is_bot": {"$ne": True}},
                {"_id": 0}
            ).sort("display_name", 1).to_list(1000)
            
            for discord_member in stored_members:
                if discord_member.get("member_id"):
                    db_member = await db.members.find_one(
                        {"id": discord_member["member_id"]},
                        {"_id": 0, "handle": 1, "name": 1}
                    )
                    if db_member:
                        discord_member["linked_member"] = {
                            "handle": db_member.get("handle"),
                            "name": db_member.get("name")
                        }
            
            return stored_members
        except Exception as inner_e:
            raise HTTPException(status_code=500, detail=f"Discord API error: {str(e)}")


class DiscordLinkRequest(BaseModel):
    discord_id: str
    member_id: str


@api_router.post("/discord/link")
async def link_discord_member(request: DiscordLinkRequest, current_user: dict = Depends(verify_admin)):
    """Link a Discord member to a database member"""
    try:
        # Verify the database member exists
        db_member = await db.members.find_one({"id": request.member_id}, {"_id": 0, "handle": 1, "name": 1})
        if not db_member:
            raise HTTPException(status_code=404, detail="Database member not found")
        
        # Verify the Discord member exists
        discord_member = await db.discord_members.find_one({"discord_id": request.discord_id})
        if not discord_member:
            raise HTTPException(status_code=404, detail="Discord member not found")
        
        # Update the Discord member with the link
        result = await db.discord_members.update_one(
            {"discord_id": request.discord_id},
            {"$set": {
                "member_id": request.member_id,
                "linked_member_handle": db_member.get("handle"),
                "linked_member_name": db_member.get("name")
            }}
        )
        
        return {
            "message": f"Discord member linked to {db_member.get('handle')}",
            "discord_id": request.discord_id,
            "member_id": request.member_id,
            "linked_to": {
                "handle": db_member.get("handle"),
                "name": db_member.get("name")
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error linking member: {str(e)}")


@api_router.post("/discord/unlink/{discord_id}")
async def unlink_discord_member(discord_id: str, current_user: dict = Depends(verify_admin)):
    """Unlink a Discord member from their database member"""
    try:
        # Verify the Discord member exists
        discord_member = await db.discord_members.find_one({"discord_id": discord_id})
        if not discord_member:
            raise HTTPException(status_code=404, detail="Discord member not found")
        
        # Remove the link
        result = await db.discord_members.update_one(
            {"discord_id": discord_id},
            {"$unset": {
                "member_id": "",
                "linked_member_handle": "",
                "linked_member_name": ""
            }}
        )
        
        return {
            "message": "Discord member unlinked successfully",
            "discord_id": discord_id
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error unlinking member: {str(e)}")


@api_router.get("/discord/linked-members")
async def get_linked_members_with_activity(current_user: dict = Depends(verify_admin)):
    """Get all linked Discord members with their last activity time"""
    try:
        # Get all linked Discord members
        linked_members = await db.discord_members.find(
            {"member_id": {"$exists": True, "$ne": None}},
            {"_id": 0}
        ).to_list(1000)
        
        result = []
        for dm in linked_members:
            discord_id = dm.get("discord_id")
            
            # Get last voice activity
            last_voice = await db.discord_voice_activity.find_one(
                {"discord_user_id": discord_id},
                {"_id": 0, "left_at": 1, "channel_name": 1},
                sort=[("left_at", -1)]
            )
            
            # Get last text activity
            last_text = await db.discord_text_activity.find_one(
                {"discord_user_id": discord_id},
                {"_id": 0, "last_message_at": 1, "channel_name": 1},
                sort=[("last_message_at", -1)]
            )
            
            # Get database member info
            db_member = None
            if dm.get("member_id"):
                db_member = await db.members.find_one(
                    {"id": dm["member_id"]},
                    {"_id": 0, "handle": 1, "name": 1, "chapter": 1, "title": 1}
                )
            
            # Helper to format time in CST using pytz
            def format_time_cst(dt):
                if not dt:
                    return None
                import pytz
                cst_tz = pytz.timezone('America/Chicago')
                
                if isinstance(dt, str):
                    dt = datetime.fromisoformat(dt.replace('Z', '+00:00'))
                
                # If datetime is naive (no timezone), assume it's UTC
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                
                # Convert to CST/CDT (handles DST automatically)
                cst_time = dt.astimezone(cst_tz)
                
                # Check if it's today in CST
                now_cst = datetime.now(timezone.utc).astimezone(cst_tz)
                if cst_time.date() == now_cst.date():
                    # Today: show only time
                    return cst_time.strftime("%-I:%M %p")
                else:
                    # Not today: show date and time
                    return cst_time.strftime("%b %-d, %-I:%M %p")
            
            # Format voice activity
            last_voice_time = None
            last_voice_time_raw = None
            last_voice_channel = None
            if last_voice and last_voice.get("left_at"):
                last_voice_time_raw = last_voice["left_at"].isoformat() if isinstance(last_voice["left_at"], datetime) else last_voice["left_at"]
                last_voice_time = format_time_cst(last_voice["left_at"])
                last_voice_channel = last_voice.get("channel_name")
            
            # Format text activity
            last_text_time = None
            last_text_time_raw = None
            last_text_channel = None
            if last_text and last_text.get("last_message_at"):
                last_text_time_raw = last_text["last_message_at"].isoformat() if isinstance(last_text["last_message_at"], datetime) else last_text["last_message_at"]
                last_text_time = format_time_cst(last_text["last_message_at"])
                last_text_channel = last_text.get("channel_name")
            
            # Determine overall last activity for sorting
            last_activity = None
            if last_voice_time_raw and last_text_time_raw:
                last_activity = max(last_voice_time_raw, last_text_time_raw)
            elif last_voice_time_raw:
                last_activity = last_voice_time_raw
            elif last_text_time_raw:
                last_activity = last_text_time_raw
            
            result.append({
                "discord_id": discord_id,
                "discord_username": dm.get("username"),
                "discord_display_name": dm.get("display_name"),
                "avatar_url": dm.get("avatar_url"),
                "member_id": dm.get("member_id"),
                "member_handle": db_member.get("handle") if db_member else dm.get("linked_member_handle"),
                "member_name": db_member.get("name") if db_member else dm.get("linked_member_name"),
                "member_chapter": db_member.get("chapter") if db_member else None,
                "member_title": db_member.get("title") if db_member else None,
                "last_activity": last_activity,
                "last_voice_time": last_voice_time,
                "last_voice_channel": last_voice_channel,
                "last_text_time": last_text_time,
                "last_text_channel": last_text_channel
            })
        
        # Sort by last activity (most recent first), with None values at the end
        result.sort(key=lambda x: x.get("last_activity") or "0000-00-00", reverse=True)
        
        return result
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching linked members: {str(e)}")


@api_router.get("/discord/analytics")
async def get_discord_analytics(days: int = 90, current_user: dict = Depends(verify_admin)):
    """Get Discord analytics for specified number of days"""
    try:
        end_date = datetime.now(timezone.utc).date()
        start_date = end_date - timedelta(days=days)
        
        # Get voice activity stats (most active)
        voice_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id",
                "total_sessions": {"$sum": 1},
                "total_duration": {"$sum": "$duration_seconds"},
                "username": {"$first": "$discord_user_id"}  # We'll replace this with actual username
            }},
            {"$sort": {"total_duration": -1}},
            {"$limit": 10}
        ]
        
        # Get text activity stats (most active)
        text_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$discord_user_id", 
                "total_messages": {"$sum": "$message_count"},
                "username": {"$first": "$discord_user_id"}  # We'll replace this with actual username
            }},
            {"$sort": {"total_messages": -1}},
            {"$limit": 10}
        ]
        
        # Get daily activity aggregation
        daily_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": "$date",
                "voice_sessions": {"$sum": 1},
                "total_voice_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"_id": 1}}
        ]
        
        # Execute aggregations
        voice_stats = await db.discord_voice_activity.aggregate(voice_pipeline).to_list(None)
        text_stats = await db.discord_text_activity.aggregate(text_pipeline).to_list(None)
        daily_activity = await db.discord_voice_activity.aggregate(daily_pipeline).to_list(None)
        
        # Get total members count
        total_members = await db.discord_members.count_documents({})
        
        # Get all Discord members for least active analysis
        all_members = await db.discord_members.find({}, {"discord_id": 1, "username": 1, "display_name": 1, "is_bot": 1, "_id": 0}).to_list(None)
        
        # Create member map for username resolution
        member_map = {}
        for member in all_members:
            member_map[member["discord_id"]] = {
                "username": member["username"],
                "display_name": member.get("display_name"),
                "is_bot": member.get("is_bot", False)
            }
        
        # Get all users who had voice activity
        voice_active_users = {stat["_id"] for stat in voice_stats}
        all_voice_users = await db.discord_voice_activity.distinct("discord_user_id", {
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        voice_active_users.update(all_voice_users)
        
        # Get all users who had text activity  
        text_active_users = {stat["_id"] for stat in text_stats}
        all_text_users = await db.discord_text_activity.distinct("discord_user_id", {
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        text_active_users.update(all_text_users)
        
        # Find least active members (no voice AND no text activity)
        # Filter out bots and excluded usernames
        EXCLUDED_USERNAMES = ['bot', 'tv', 'aoh', 'craig', 'testdummy', 'gearjammerbot']
        
        least_active_members = []
        for member in all_members:
            if member.get("is_bot"):
                continue  # Skip bots
            
            username = member.get("username", "").lower()
            display_name = (member.get("display_name") or "").lower()
            
            # Skip excluded usernames
            is_excluded = False
            for excluded in EXCLUDED_USERNAMES:
                if excluded in username or excluded in display_name or username.startswith(excluded) or display_name.startswith(excluded):
                    is_excluded = True
                    break
            
            if is_excluded:
                continue
                
            discord_id = member["discord_id"]
            has_voice_activity = discord_id in voice_active_users
            has_text_activity = discord_id in text_active_users
            
            if not has_voice_activity and not has_text_activity:
                least_active_members.append({
                    "discord_id": discord_id,
                    "username": member["username"],
                    "display_name": member.get("display_name") or member["username"],
                    "voice_activity": False,
                    "text_activity": False,
                    "activity_score": 0
                })
        
        # Sort least active by username for consistency
        least_active_members.sort(key=lambda x: x["username"].lower())
        
        # Limit to top 15 least active to avoid overwhelming the UI
        least_active_members = least_active_members[:15]
        
        # Add usernames to most active stats
        for stat in voice_stats:
            member_info = member_map.get(stat["_id"], {})
            stat["username"] = member_info.get("display_name") or member_info.get("username") or f"User {stat['_id'][:8]}"
        
        for stat in text_stats:
            member_info = member_map.get(stat["_id"], {})
            stat["username"] = member_info.get("display_name") or member_info.get("username") or f"User {stat['_id'][:8]}"
        
        # Calculate correct totals
        total_voice_sessions = sum(s["total_sessions"] for s in voice_stats) if voice_stats else 0
        total_text_messages = sum(s["total_messages"] for s in text_stats) if text_stats else 0
        
        # Get all voice sessions (not just top users)
        all_voice_sessions = await db.discord_voice_activity.count_documents({
            "date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}
        })
        
        # Get all text messages (not just top users)
        all_text_messages_result = await db.discord_text_activity.aggregate([
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {"_id": None, "total": {"$sum": "$message_count"}}}
        ]).to_list(None)
        all_text_messages = all_text_messages_result[0]["total"] if all_text_messages_result else 0
        
        # Get top users per voice channel
        channel_voice_pipeline = [
            {"$match": {"date": {"$gte": start_date.isoformat(), "$lte": end_date.isoformat()}}},
            {"$group": {
                "_id": {
                    "channel_name": "$channel_name",
                    "channel_id": "$channel_id",
                    "user_id": "$discord_user_id"
                },
                "total_sessions": {"$sum": 1},
                "total_duration": {"$sum": "$duration_seconds"}
            }},
            {"$sort": {"_id.channel_name": 1, "total_duration": -1}}
        ]
        
        channel_voice_stats = await db.discord_voice_activity.aggregate(channel_voice_pipeline).to_list(None)
        
        # Organize by channel with top 5 users per channel
        channels_data = {}
        for stat in channel_voice_stats:
            channel_name = stat["_id"]["channel_name"]
            user_id = stat["_id"]["user_id"]
            
            if channel_name not in channels_data:
                channels_data[channel_name] = {
                    "channel_name": channel_name,
                    "channel_id": stat["_id"]["channel_id"],
                    "total_sessions": 0,
                    "total_duration": 0,
                    "top_users": []
                }
            
            channels_data[channel_name]["total_sessions"] += stat["total_sessions"]
            channels_data[channel_name]["total_duration"] += stat["total_duration"]
            
            # Add to top users (limit to 5 per channel)
            if len(channels_data[channel_name]["top_users"]) < 5:
                member_info = member_map.get(user_id, {})
                username = member_info.get("display_name") or member_info.get("username") or f"User {user_id[:8]}"
                channels_data[channel_name]["top_users"].append({
                    "user_id": user_id,
                    "username": username,
                    "sessions": stat["total_sessions"],
                    "duration": stat["total_duration"]
                })
        
        # Convert to list and sort by total duration
        channel_stats = list(channels_data.values())
        channel_stats.sort(key=lambda x: x["total_duration"], reverse=True)
        
        analytics = DiscordAnalytics(
            total_members=total_members,
            voice_stats={"total_sessions": all_voice_sessions, "top_users": voice_stats},
            text_stats={"total_messages": all_text_messages, "top_users": text_stats},
            top_voice_users=voice_stats,
            top_text_users=text_stats,
            daily_activity=daily_activity
        )
        
        # Add least active members to response
        analytics_dict = analytics.model_dump()
        analytics_dict["least_active_members"] = least_active_members
        analytics_dict["channel_stats"] = channel_stats
        analytics_dict["engagement_stats"] = {
            "total_members": total_members,
            "voice_active_members": len(voice_active_users),
            "text_active_members": len(text_active_users),
            "inactive_members": len(least_active_members),
            "engagement_rate": round(((len(voice_active_users) + len(text_active_users)) / total_members * 100), 1) if total_members > 0 else 0
        }
        
        return analytics_dict
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@api_router.post("/discord/import-members")
async def import_discord_members(current_user: dict = Depends(verify_admin)):
    """Import Discord members and link to existing members using enhanced fuzzy matching"""
    try:
        from rapidfuzz import fuzz, process
        
        # Fetch Discord members and database members
        discord_members = await db.discord_members.find({}, {"_id": 0}).to_list(None)
        database_members = await db.members.find({}, {"_id": 0, "id": 1, "handle": 1, "name": 1}).to_list(None)
        
        matched_count = 0
        match_details = []
        
        # Create lookup dictionaries for database members
        handle_to_member = {m.get("handle", "").lower(): m for m in database_members if m.get("handle")}
        name_to_member = {m.get("name", "").lower(): m for m in database_members if m.get("name")}
        
        for discord_member in discord_members:
            username = (discord_member.get("username") or "").strip()
            display_name = (discord_member.get("display_name") or "").strip()
            
            if not username:
                continue
            
            best_match = None
            best_score = 0
            match_type = ""
            
            # Strategy 1: Exact case-insensitive match on username/display_name with handle/name
            username_lower = username.lower()
            display_name_lower = display_name.lower() if display_name else ""
            
            if username_lower in handle_to_member:
                best_match = handle_to_member[username_lower]
                best_score = 100
                match_type = "exact_handle"
            elif display_name_lower and display_name_lower in handle_to_member:
                best_match = handle_to_member[display_name_lower]
                best_score = 100
                match_type = "exact_display_handle"
            elif username_lower in name_to_member:
                best_match = name_to_member[username_lower]
                best_score = 100
                match_type = "exact_name"
            elif display_name_lower and display_name_lower in name_to_member:
                best_match = name_to_member[display_name_lower]
                best_score = 100
                match_type = "exact_display_name"
            
            # Strategy 2: Partial contains matching (e.g., "lonestar379" contains "lonestar")
            if not best_match:
                for db_member in database_members:
                    handle = (db_member.get("handle") or "").lower()
                    name = (db_member.get("name") or "").lower()
                    
                    # Check if handle/name is contained in username or display_name
                    if handle and len(handle) >= 3:
                        if handle in username_lower or handle in display_name_lower:
                            score = 85
                            if score > best_score:
                                best_match = db_member
                                best_score = score
                                match_type = "partial_handle"
                    
                    # Check if username/display_name is contained in handle/name
                    if username_lower and len(username_lower) >= 3:
                        if username_lower in handle or username_lower in name:
                            score = 85
                            if score > best_score:
                                best_match = db_member
                                best_score = score
                                match_type = "partial_username"
            
            # Strategy 3: Fuzzy matching with threshold
            if not best_match or best_score < 90:
                # Build list of all possible matches
                match_candidates = []
                for db_member in database_members:
                    handle = db_member.get("handle", "")
                    name = db_member.get("name", "")
                    if handle:
                        match_candidates.append((handle, db_member, "handle"))
                    if name:
                        match_candidates.append((name, db_member, "name"))
                
                # Try fuzzy matching with username
                if username and match_candidates:
                    for candidate_str, db_member, field_type in match_candidates:
                        # Use token_sort_ratio for better matching with different word orders
                        score1 = fuzz.token_sort_ratio(username.lower(), candidate_str.lower())
                        score2 = fuzz.ratio(username.lower(), candidate_str.lower())
                        score = max(score1, score2)
                        
                        if score > best_score and score >= 80:  # 80% similarity threshold
                            best_match = db_member
                            best_score = score
                            match_type = f"fuzzy_{field_type}"
                
                # Try fuzzy matching with display_name
                if display_name and match_candidates:
                    for candidate_str, db_member, field_type in match_candidates:
                        score1 = fuzz.token_sort_ratio(display_name.lower(), candidate_str.lower())
                        score2 = fuzz.ratio(display_name.lower(), candidate_str.lower())
                        score = max(score1, score2)
                        
                        if score > best_score and score >= 80:
                            best_match = db_member
                            best_score = score
                            match_type = f"fuzzy_display_{field_type}"
            
            # Link if we found a good match (score >= 80)
            if best_match and best_score >= 80:
                await db.discord_members.update_one(
                    {"discord_id": discord_member["discord_id"]},
                    {"$set": {"member_id": best_match["id"]}}
                )
                matched_count += 1
                match_details.append({
                    "discord_user": username,
                    "discord_display": display_name,
                    "matched_handle": best_match.get("handle"),
                    "matched_name": best_match.get("name"),
                    "score": round(best_score, 1),
                    "method": match_type
                })
        
        # Log the activity
        await log_activity(
            current_user['username'],
            "discord_import",
            f"Imported Discord members with enhanced matching. Matched {matched_count} members."
        )
        
        return {
            "message": f"Imported Discord members. Matched {matched_count} with existing members.",
            "matched_count": matched_count,
            "total_discord_members": len(discord_members),
            "match_details": match_details[:10]  # Return first 10 matches for review
        }
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Import error: {str(e)}")


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
- Prospect Manager (PM) - Manages prospects (only HA chapter has this position)

NOTE: Prospect Manager position exists only in Highway Asylum (HA) chapter. Other chapters (HS, AD) do not have this position.

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


# ==================== EVENT ENDPOINTS ====================

@api_router.get("/events")
async def get_events(
    chapter: Optional[str] = None,
    title_filter: Optional[str] = None,
    current_user: dict = Depends(verify_token)
):
    """Get all events, optionally filtered by chapter and title"""
    query = {}
    
    # Filter by chapter if specified
    if chapter:
        query["$or"] = [{"chapter": chapter}, {"chapter": None}]
    
    # Filter by title if specified
    if title_filter:
        if "$or" not in query:
            query["$or"] = []
        query["$or"].append({"title_filter": title_filter})
        query["$or"].append({"title_filter": None})
    
    events = await db.events.find(query, {"_id": 0}).to_list(length=None)
    
    # Convert datetime objects to ISO strings
    for event in events:
        if isinstance(event.get('created_at'), datetime):
            event['created_at'] = event['created_at'].isoformat()
    
    # Sort by date (newest first)
    events.sort(key=lambda x: x.get('date', ''), reverse=False)
    
    return events

@api_router.get("/events/upcoming-count")
async def get_upcoming_events_count(current_user: dict = Depends(verify_token)):
    """Get count of upcoming events for badge"""
    from datetime import date
    today = date.today().isoformat()
    
    # Build query based on user's chapter and title
    query = {"date": {"$gte": today}}
    
    # If user has a chapter, show events for their chapter or all chapters
    user_chapter = current_user.get("chapter")
    if user_chapter:
        query["$or"] = [{"chapter": user_chapter}, {"chapter": None}]
    
    count = await db.events.count_documents(query)
    return {"count": count}

@api_router.post("/events")
async def create_event(event_data: EventCreate, current_user: dict = Depends(verify_admin)):
    """Create a new event (admin only)"""
    
    # Get creator's chapter and title from current_user
    creator_chapter = current_user.get("chapter")
    creator_title = current_user.get("title")
    
    # Find creator's handle from members collection
    creator_handle = None
    member = await db.members.find_one({"email": current_user.get("email")}, {"_id": 0, "handle": 1})
    if member:
        creator_handle = member.get("handle")
    
    event = Event(
        title=event_data.title,
        description=event_data.description,
        date=event_data.date,
        time=event_data.time,
        location=event_data.location,
        chapter=event_data.chapter,
        title_filter=event_data.title_filter,
        discord_notifications_enabled=event_data.discord_notifications_enabled,
        created_by=current_user["username"],
        creator_chapter=creator_chapter,
        creator_title=creator_title,
        creator_handle=creator_handle
    )
    
    doc = event.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.events.insert_one(doc)
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="event_create",
        details=f"Created event: {event.title} on {event.date}"
    )
    
    return {"message": "Event created successfully", "id": event.id}

@api_router.put("/events/{event_id}")
async def update_event(
    event_id: str,
    event_data: EventUpdate,
    current_user: dict = Depends(verify_admin)
):
    """Update an event (admin only)"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    update_data = {}
    if event_data.title:
        update_data['title'] = event_data.title
    if event_data.description is not None:
        update_data['description'] = event_data.description
    if event_data.date:
        update_data['date'] = event_data.date
    if event_data.time is not None:
        update_data['time'] = event_data.time
    if event_data.location is not None:
        update_data['location'] = event_data.location
    if event_data.chapter is not None:
        update_data['chapter'] = event_data.chapter
    if event_data.title_filter is not None:
        update_data['title_filter'] = event_data.title_filter
    if event_data.discord_notifications_enabled is not None:
        update_data['discord_notifications_enabled'] = event_data.discord_notifications_enabled
    
    if update_data:
        await db.events.update_one({"id": event_id}, {"$set": update_data})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="event_update",
        details=f"Updated event: {event.get('title', event_id)}"
    )
    
    return {"message": "Event updated successfully"}

@api_router.post("/events/{event_id}/send-discord-notification")
async def send_event_discord_notification_now(event_id: str, current_user: dict = Depends(verify_admin)):
    """Manually send Discord notification for an event immediately (admin only)"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    # Check if Discord notifications are enabled for this event
    if not event.get('discord_notifications_enabled', True):
        raise HTTPException(status_code=400, detail="Discord notifications are disabled for this event")
    
    # Send notification immediately (0 means "now")
    success = await send_discord_notification(event, 0)
    
    if success:
        # Log activity
        await log_activity(
            username=current_user["username"],
            action="event_discord_manual",
            details=f"Manually sent Discord notification for event: {event.get('title', event_id)}"
        )
        return {"message": "Discord notification sent successfully"}
    else:
        raise HTTPException(status_code=500, detail="Failed to send Discord notification")

@api_router.delete("/events/{event_id}")
async def delete_event(event_id: str, current_user: dict = Depends(verify_admin)):
    """Delete an event (admin only)"""
    event = await db.events.find_one({"id": event_id})
    if not event:
        raise HTTPException(status_code=404, detail="Event not found")
    
    await db.events.delete_one({"id": event_id})
    
    # Log activity
    await log_activity(
        username=current_user["username"],
        action="event_delete",
        details=f"Deleted event: {event.get('title', event_id)}"
    )
    
    return {"message": "Event deleted successfully"}


@api_router.post("/events/trigger-notification-check")
async def trigger_notification_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the scheduler's notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_notification_check)
    thread.start()
    
    return {"message": "Notification check triggered. Check backend logs for results."}


@api_router.post("/birthdays/trigger-check")
async def trigger_birthday_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the birthday notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_birthday_check)
    thread.start()
    
    return {"message": "Birthday check triggered. Check backend logs for results."}


@api_router.post("/anniversaries/trigger-check")
async def trigger_anniversary_check(current_user: dict = Depends(verify_admin)):
    """Manually trigger the anniversary notification check (admin only, for testing)"""
    import threading
    
    # Run in a separate thread to avoid blocking
    thread = threading.Thread(target=run_anniversary_check)
    thread.start()
    
    return {"message": "Anniversary check triggered. Check backend logs for results."}


@api_router.get("/anniversaries/this-month")
async def get_anniversaries_this_month(current_user: dict = Depends(verify_token)):
    """Get list of members with anniversaries this month"""
    from datetime import datetime
    
    today = datetime.now()
    current_month = today.strftime("%m")
    current_year = today.year
    
    # Fetch all members with join_date
    members = await db.members.find(
        {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    anniversary_members = []
    for member in members:
        join_date = member.get('join_date', '')
        if not join_date or '/' not in join_date:
            continue
        
        try:
            join_month = join_date.split('/')[0].zfill(2)
            join_year_str = join_date.split('/')[1]
            
            if join_month == current_month:
                try:
                    join_year = int(join_year_str)
                    years = current_year - join_year
                    
                    if years >= 1:
                        # Decrypt member data
                        decrypted = decrypt_member_sensitive_data(member.copy())
                        anniversary_members.append({
                            "id": member.get('id'),
                            "handle": decrypted.get('handle'),
                            "name": decrypted.get('name'),
                            "chapter": decrypted.get('chapter'),
                            "title": decrypted.get('title'),
                            "join_date": join_date,
                            "years": years
                        })
                except ValueError:
                    continue
        except Exception:
            continue
    
    # Sort by years (longest first)
    anniversary_members.sort(key=lambda x: x["years"], reverse=True)
    
    return {
        "month": today.strftime("%B %Y"),
        "count": len(anniversary_members),
        "members": anniversary_members
    }


@api_router.get("/anniversaries/upcoming")
async def get_upcoming_anniversaries(months: int = 3, current_user: dict = Depends(verify_token)):
    """Get list of members with anniversaries in the next N months"""
    from datetime import datetime
    
    today = datetime.now()
    current_month = today.month
    current_year = today.year
    
    # Fetch all members with join_date
    members = await db.members.find(
        {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    upcoming_anniversaries = []
    for member in members:
        join_date = member.get('join_date', '')
        if not join_date or '/' not in join_date:
            continue
        
        try:
            join_month = int(join_date.split('/')[0])
            join_year_str = join_date.split('/')[1]
            join_year = int(join_year_str)
            
            # Calculate months until anniversary
            if join_month >= current_month:
                months_until = join_month - current_month
                anniversary_year = current_year
            else:
                months_until = (12 - current_month) + join_month
                anniversary_year = current_year + 1
            
            # Check if within range
            if months_until <= months:
                years = anniversary_year - join_year
                
                if years >= 1:
                    # Decrypt member data
                    decrypted = decrypt_member_sensitive_data(member.copy())
                    upcoming_anniversaries.append({
                        "id": member.get('id'),
                        "handle": decrypted.get('handle'),
                        "name": decrypted.get('name'),
                        "chapter": decrypted.get('chapter'),
                        "title": decrypted.get('title'),
                        "join_date": join_date,
                        "years": years,
                        "months_until": months_until
                    })
        except (ValueError, IndexError):
            continue
    
    # Sort by months_until (soonest first)
    upcoming_anniversaries.sort(key=lambda x: x["months_until"])
    
    return {
        "from_date": today.strftime("%Y-%m-%d"),
        "months_ahead": months,
        "count": len(upcoming_anniversaries),
        "members": upcoming_anniversaries
    }


@api_router.get("/birthdays/today")
async def get_todays_birthdays(current_user: dict = Depends(verify_token)):
    """Get list of members with birthdays today"""
    from datetime import datetime
    
    today = datetime.now()
    today_mm_dd = today.strftime("%m-%d")
    
    # Fetch all members with DOB set
    members = await db.members.find(
        {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    birthday_members = []
    for member in members:
        dob = member.get('dob', '')
        if not dob:
            continue
        try:
            dob_mm_dd = dob[5:10]  # Gets MM-DD portion
            if dob_mm_dd == today_mm_dd:
                birthday_members.append({
                    "id": member.get("id"),
                    "handle": member.get("handle"),
                    "name": member.get("name"),
                    "chapter": member.get("chapter"),
                    "title": member.get("title"),
                    "dob": dob
                })
        except:
            pass
    
    return {
        "date": today.strftime("%Y-%m-%d"),
        "count": len(birthday_members),
        "members": birthday_members
    }


@api_router.get("/birthdays/upcoming")
async def get_upcoming_birthdays(days: int = 30, current_user: dict = Depends(verify_token)):
    """Get list of members with birthdays in the next N days"""
    from datetime import datetime, timedelta
    
    today = datetime.now()
    
    # Fetch all members with DOB set
    members = await db.members.find(
        {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
        {"_id": 0}
    ).to_list(1000)
    
    upcoming_birthdays = []
    for member in members:
        dob = member.get('dob', '')
        if not dob:
            continue
        try:
            # Parse DOB and calculate this year's birthday
            dob_date = datetime.strptime(dob, "%Y-%m-%d")
            this_year_birthday = dob_date.replace(year=today.year)
            
            # If birthday already passed this year, check next year
            if this_year_birthday.date() < today.date():
                this_year_birthday = dob_date.replace(year=today.year + 1)
            
            # Check if within the next N days
            days_until = (this_year_birthday.date() - today.date()).days
            
            if 0 <= days_until <= days:
                upcoming_birthdays.append({
                    "id": member.get("id"),
                    "handle": member.get("handle"),
                    "name": member.get("name"),
                    "chapter": member.get("chapter"),
                    "title": member.get("title"),
                    "dob": dob,
                    "birthday_date": this_year_birthday.strftime("%Y-%m-%d"),
                    "days_until": days_until
                })
        except:
            pass
    
    # Sort by days_until
    upcoming_birthdays.sort(key=lambda x: x["days_until"])
    
    return {
        "from_date": today.strftime("%Y-%m-%d"),
        "to_date": (today + timedelta(days=days)).strftime("%Y-%m-%d"),
        "count": len(upcoming_birthdays),
        "members": upcoming_birthdays
    }



# ==================== DISCORD NOTIFICATION SYSTEM ====================

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta

DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL')

async def send_discord_notification(event: dict, hours_before: int):
    """Send Discord notification for an event
    
    Args:
        event: Event dictionary
        hours_before: 24, 3, or 0 (0 = send now/manual trigger)
    """
    if not DISCORD_WEBHOOK_URL:
        print("⚠️  Discord webhook URL not configured")
        return False
    
    try:
        # Format the event time with Central Time indicator
        event_datetime_str = f"{event['date']}"
        if event.get('time'):
            event_datetime_str += f" at {event['time']} CST"
        else:
            event_datetime_str += " (Time TBD)"
        
        # Determine color and footer based on hours_before
        if hours_before == 0:
            color = 0x0099ff  # Blue for manual/immediate
            footer_text = "Manual notification"
            content = f"@everyone **Event Announcement!** 🚛"
        elif hours_before == 24:
            color = 0x00ff00  # Green for 24h
            footer_text = "Tomorrow!"
            content = f"@everyone **Reminder: Event tomorrow!** 🚛"
        else:  # 3 hours
            color = 0xff9900  # Orange for 3h
            footer_text = "Starting soon!"
            content = f"@everyone **Event starting in 3 hours!** ⏰"
        
        # Create embed for Discord
        embed = {
            "title": f"🚛 {event['title']}",
            "description": event.get('description', 'No description provided'),
            "color": color,
            "fields": [
                {
                    "name": "📅 Date & Time",
                    "value": event_datetime_str,
                    "inline": True
                }
            ],
            "footer": {
                "text": footer_text
            }
        }
        
        # Add location if available
        if event.get('location'):
            embed["fields"].append({
                "name": "📍 Location",
                "value": event['location'],
                "inline": True
            })
        
        # Add chapter filter if specified
        if event.get('chapter'):
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": event['chapter'],
                "inline": True
            })
        
        # Add title filter if specified
        if event.get('title_filter'):
            embed["fields"].append({
                "name": "👥 For",
                "value": event['title_filter'],
                "inline": True
            })
        
        # Add creator information
        creator_parts = []
        if event.get('creator_chapter'):
            creator_parts.append(event['creator_chapter'])
        if event.get('creator_title'):
            creator_parts.append(event['creator_title'])
        if event.get('creator_handle'):
            creator_parts.append(event['creator_handle'])
        
        if creator_parts:
            embed["fields"].append({
                "name": "📋 Created By",
                "value": " | ".join(creator_parts),
                "inline": False
            })
        
        payload = {
            "content": content,
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            hours_text = "now" if hours_before == 0 else f"{hours_before}h before"
            print(f"✅ Discord notification sent for event: {event['title']} ({hours_text})")
            return True
        else:
            print(f"❌ Discord notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending Discord notification: {str(e)}")
        return False

async def check_and_send_event_notifications():
    """Check for upcoming events and send notifications"""
    import sys
    from motor.motor_asyncio import AsyncIOMotorClient
    
    try:
        # Create a fresh MongoDB client for this thread's event loop
        scheduler_client = AsyncIOMotorClient(mongo_url)
        scheduler_db = scheduler_client[os.environ['DB_NAME']]
        
        # Use Central Time for all event calculations
        import pytz
        central = pytz.timezone('America/Chicago')
        now = datetime.now(central)
        
        print(f"🔍 [SCHEDULER] Running notification check at {now.strftime('%Y-%m-%d %H:%M:%S %Z')}", file=sys.stderr, flush=True)
        
        # Get all events
        events = await scheduler_db.events.find({}, {"_id": 0}).to_list(length=None)
        print(f"📋 [SCHEDULER] Found {len(events)} total events", file=sys.stderr, flush=True)
        
        for event in events:
            try:
                # Parse event date and time in Central Time
                event_date = datetime.strptime(event['date'], '%Y-%m-%d')
                
                # If time is specified, add it
                if event.get('time'):
                    time_parts = event['time'].split(':')
                    event_date = event_date.replace(
                        hour=int(time_parts[0]),
                        minute=int(time_parts[1])
                    )
                else:
                    # Default to noon if no time specified
                    event_date = event_date.replace(hour=12, minute=0)
                
                # Make timezone aware as Central Time
                event_date = central.localize(event_date)
                
                # Calculate time until event
                time_until_event = event_date - now
                hours_until_event = time_until_event.total_seconds() / 3600
                
                print(f"  📅 Event '{event.get('title')}': {hours_until_event:.2f}h away (Discord enabled: {event.get('discord_notifications_enabled', True)})", file=sys.stderr, flush=True)
                
                # Skip if Discord notifications are disabled for this event
                if not event.get('discord_notifications_enabled', True):
                    print(f"  ⏭️  Skipping - Discord notifications disabled", file=sys.stderr, flush=True)
                    continue
                
                # Skip past events
                if hours_until_event < 0:
                    print(f"  ⏭️  Skipping - Event is in the past", file=sys.stderr, flush=True)
                    continue
                
                # Check for 24-hour notification (between 23.5 and 24.5 hours)
                if 23.5 <= hours_until_event <= 24.5 and not event.get('notification_24h_sent'):
                    print(f"📢 [SCHEDULER] Sending 24h notification for: {event['title']}", file=sys.stderr, flush=True)
                    success = await send_discord_notification(event, 24)
                    if success:
                        await scheduler_db.events.update_one(
                            {"id": event['id']},
                            {"$set": {"notification_24h_sent": True}}
                        )
                        print(f"✅ [SCHEDULER] 24h notification sent successfully", file=sys.stderr, flush=True)
                    else:
                        print(f"❌ [SCHEDULER] 24h notification failed", file=sys.stderr, flush=True)
                
                # Check for 3-hour notification (between 2.5 and 3.5 hours)
                elif 2.5 <= hours_until_event <= 3.5 and not event.get('notification_3h_sent'):
                    print(f"📢 [SCHEDULER] Sending 3h notification for: {event['title']}", file=sys.stderr, flush=True)
                    success = await send_discord_notification(event, 3)
                    if success:
                        await scheduler_db.events.update_one(
                            {"id": event['id']},
                            {"$set": {"notification_3h_sent": True}}
                        )
                        print(f"✅ [SCHEDULER] 3h notification sent successfully", file=sys.stderr, flush=True)
                    else:
                        print(f"❌ [SCHEDULER] 3h notification failed", file=sys.stderr, flush=True)
                        
            except Exception as e:
                print(f"❌ [SCHEDULER] Error processing event {event.get('id')}: {str(e)}", file=sys.stderr, flush=True)
                import traceback
                traceback.print_exc(file=sys.stderr)
                continue
        
        print(f"✅ [SCHEDULER] Notification check completed", file=sys.stderr, flush=True)
        
        # Close the scheduler-specific client
        scheduler_client.close()
                
    except Exception as e:
        print(f"❌ [SCHEDULER] Error in check_and_send_event_notifications: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)
        # Ensure client is closed even on error
        try:
            scheduler_client.close()
        except:
            pass

def run_notification_check():
    """Wrapper to run async notification check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🚀 [SCHEDULER] Starting notification check job...", file=sys.stderr, flush=True)
        
        # APScheduler runs this in a separate thread, so we need a new event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_event_notifications())
            print(f"✅ [SCHEDULER] Notification check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running notification check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


# ==================== BIRTHDAY NOTIFICATIONS ====================

async def send_birthday_notification(member: dict):
    """Send Discord notification for a member's birthday"""
    if not DISCORD_WEBHOOK_URL:
        print("⚠️  Discord webhook URL not configured for birthday notification")
        return False
    
    try:
        # Get member details
        member_name = member.get('name', member.get('handle', 'Brother'))
        member_handle = member.get('handle', '')
        member_chapter = member.get('chapter', '')
        member_title = member.get('title', '')
        
        # Create a festive birthday embed
        embed = {
            "title": "🎂 Happy Birthday! 🎉",
            "description": f"Today we celebrate **{member_name}**!\n\nWishing you a fantastic birthday filled with joy and many great drives ahead! 🚛",
            "color": 0xFFD700,  # Gold color for birthday
            "fields": [],
            "footer": {
                "text": "Brothers of the Highway | Birthday Wishes"
            }
        }
        
        # Add member info
        if member_handle:
            embed["fields"].append({
                "name": "🏷️ Handle",
                "value": member_handle,
                "inline": True
            })
        
        if member_chapter:
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": member_chapter,
                "inline": True
            })
        
        if member_title:
            embed["fields"].append({
                "name": "👤 Title",
                "value": member_title,
                "inline": True
            })
        
        # Add call to action
        embed["fields"].append({
            "name": "🎊 Join the Celebration!",
            "value": "All Brothers are invited to wish them a Happy Birthday!",
            "inline": False
        })
        
        payload = {
            "content": f"@everyone **🎂 Birthday Alert!** 🎂\n\nLet's all wish **{member_name}** a very Happy Birthday! 🎉",
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print(f"✅ Birthday notification sent for: {member_name}")
            return True
        else:
            print(f"❌ Birthday notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending birthday notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def check_and_send_birthday_notifications():
    """Check for members with birthdays today and send Discord notifications"""
    import sys
    from datetime import datetime
    
    try:
        print(f"🎂 [BIRTHDAY] Checking for birthdays today...", file=sys.stderr, flush=True)
        
        # Get today's date in MM-DD format for comparison
        today = datetime.now()
        today_mm_dd = today.strftime("%m-%d")
        
        # Create a new MongoDB connection for this thread
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        thread_db = client[db_name]
        
        # Fetch all members with DOB set
        members = await thread_db.members.find(
            {"dob": {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0}
        ).to_list(1000)
        
        print(f"🎂 [BIRTHDAY] Found {len(members)} members with DOB records", file=sys.stderr, flush=True)
        
        # Check today's date key to avoid duplicate notifications
        today_key = today.strftime("%Y-%m-%d")
        
        birthday_count = 0
        for member in members:
            dob = member.get('dob', '')
            if not dob:
                continue
            
            try:
                # DOB format: YYYY-MM-DD, extract MM-DD
                dob_mm_dd = dob[5:10]  # Gets MM-DD portion
                
                if dob_mm_dd == today_mm_dd:
                    member_id = member.get('id', member.get('handle', ''))
                    
                    # Check if we already sent notification today
                    existing = await thread_db.birthday_notifications.find_one({
                        "member_id": member_id,
                        "notification_date": today_key
                    })
                    
                    if existing:
                        print(f"   ⏭️ Already notified for {member.get('name', member.get('handle'))}", file=sys.stderr, flush=True)
                        continue
                    
                    # Send birthday notification
                    print(f"   🎉 Birthday found: {member.get('name', member.get('handle'))} - {dob}", file=sys.stderr, flush=True)
                    success = await send_birthday_notification(member)
                    
                    if success:
                        # Record that we sent the notification
                        await thread_db.birthday_notifications.insert_one({
                            "member_id": member_id,
                            "member_name": member.get('name', member.get('handle', '')),
                            "notification_date": today_key,
                            "sent_at": datetime.now()
                        })
                        birthday_count += 1
                        
            except Exception as e:
                print(f"   ❌ Error processing DOB for {member.get('handle', 'unknown')}: {str(e)}", file=sys.stderr, flush=True)
        
        print(f"🎂 [BIRTHDAY] Sent {birthday_count} birthday notification(s) today", file=sys.stderr, flush=True)
        client.close()
        
    except Exception as e:
        print(f"❌ [BIRTHDAY] Error checking birthdays: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


def run_birthday_check():
    """Wrapper to run async birthday check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🎂 [SCHEDULER] Starting birthday check job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_birthday_notifications())
            print(f"✅ [SCHEDULER] Birthday check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running birthday check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)

# ==================== ANNIVERSARY NOTIFICATIONS ====================

async def send_anniversary_notification(member: dict, years: int):
    """Send Discord notification for a member's anniversary"""
    if not DISCORD_WEBHOOK_URL:
        print("⚠️  Discord webhook URL not configured for anniversary notification")
        return False
    
    try:
        # Get member details
        member_name = member.get('name', member.get('handle', 'Brother'))
        member_handle = member.get('handle', '')
        member_chapter = member.get('chapter', '')
        member_title = member.get('title', '')
        
        # Create trucker-themed anniversary message
        year_text = "year" if years == 1 else "years"
        
        # Milestone messages based on years
        if years >= 10:
            milestone_msg = "A true road warrior and pillar of the Brotherhood! 🏆"
        elif years >= 5:
            milestone_msg = "A seasoned veteran of the highway! Keep on truckin'! 🛣️"
        elif years >= 3:
            milestone_msg = "Rolling strong through the years! 💪"
        else:
            milestone_msg = "Keep those wheels turning, Brother! 🚛"
        
        # Create a festive anniversary embed
        embed = {
            "title": "🎉 Member Anniversary! 🎊",
            "description": f"**{member_name}** is celebrating **{years} {year_text}** as a Brother of the Highway!\n\n{milestone_msg}",
            "color": 0x4169E1,  # Royal blue for anniversary
            "fields": [],
            "footer": {
                "text": "Brothers of the Highway | Anniversary Celebration"
            }
        }
        
        # Add member info
        if member_handle:
            embed["fields"].append({
                "name": "🏷️ Handle",
                "value": member_handle,
                "inline": True
            })
        
        if member_chapter:
            embed["fields"].append({
                "name": "🏴 Chapter",
                "value": member_chapter,
                "inline": True
            })
        
        if member_title:
            embed["fields"].append({
                "name": "👤 Title",
                "value": member_title,
                "inline": True
            })
        
        # Add years milestone
        embed["fields"].append({
            "name": "📅 Years of Brotherhood",
            "value": f"**{years}** {year_text} on the road together!",
            "inline": False
        })
        
        # Add call to action
        embed["fields"].append({
            "name": "🎊 Congratulations!",
            "value": "All Brothers are invited to congratulate them on their anniversary!",
            "inline": False
        })
        
        payload = {
            "content": f"@everyone **🎉 Anniversary Alert!** 🎉\n\nLet's all congratulate **{member_name}** on **{years} {year_text}** with the Brotherhood! 🚛💨",
            "embeds": [embed]
        }
        
        response = requests.post(DISCORD_WEBHOOK_URL, json=payload)
        
        if response.status_code == 204:
            print(f"✅ Anniversary notification sent for: {member_name} ({years} years)")
            return True
        else:
            print(f"❌ Anniversary notification failed: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error sending anniversary notification: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


async def check_and_send_anniversary_notifications():
    """Check for members with anniversaries this month and send Discord notifications (runs on 1st of month)"""
    import sys
    from datetime import datetime
    
    try:
        print(f"🎉 [ANNIVERSARY] Checking for member anniversaries this month...", file=sys.stderr, flush=True)
        
        # Get current month and year
        today = datetime.now()
        current_month = today.strftime("%m")  # MM format
        current_year = today.year
        
        # Create a new MongoDB connection for this thread
        from motor.motor_asyncio import AsyncIOMotorClient
        mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
        db_name = os.environ.get('DB_NAME', 'test_database')
        client = AsyncIOMotorClient(mongo_url)
        thread_db = client[db_name]
        
        # Fetch all members with join_date set
        members = await thread_db.members.find(
            {"join_date": {"$exists": True, "$ne": None, "$ne": ""}},
            {"_id": 0}
        ).to_list(1000)
        
        print(f"🎉 [ANNIVERSARY] Found {len(members)} members with join_date records", file=sys.stderr, flush=True)
        
        # Check today's date key to avoid duplicate notifications (use year-month)
        month_key = today.strftime("%Y-%m")
        
        anniversary_count = 0
        for member in members:
            join_date = member.get('join_date', '')
            if not join_date:
                continue
            
            try:
                # join_date format: MM/YYYY, extract MM portion
                if '/' in join_date:
                    join_month = join_date.split('/')[0].zfill(2)  # Get MM, pad with 0 if needed
                    join_year_str = join_date.split('/')[1]
                    
                    # Check if this member's anniversary is this month
                    if join_month == current_month:
                        # Calculate years of membership
                        try:
                            join_year = int(join_year_str)
                            years = current_year - join_year
                            
                            # Skip if less than 1 year or join year is in the future
                            if years < 1:
                                continue
                                
                        except ValueError:
                            print(f"   ⚠️ Invalid year in join_date for {member.get('handle', 'unknown')}: {join_date}", file=sys.stderr, flush=True)
                            continue
                        
                        member_id = member.get('id', member.get('handle', ''))
                        
                        # Check if we already sent notification this month
                        existing = await thread_db.anniversary_notifications.find_one({
                            "member_id": member_id,
                            "notification_month": month_key
                        })
                        
                        if existing:
                            print(f"   ⏭️ Already notified for {member.get('name', member.get('handle'))} this month", file=sys.stderr, flush=True)
                            continue
                        
                        # Decrypt sensitive data for the notification
                        decrypted_member = decrypt_member_sensitive_data(member.copy())
                        
                        # Send anniversary notification
                        print(f"   🎉 Anniversary found: {decrypted_member.get('name', decrypted_member.get('handle'))} - {years} year(s) (joined {join_date})", file=sys.stderr, flush=True)
                        success = await send_anniversary_notification(decrypted_member, years)
                        
                        if success:
                            # Record that we sent the notification
                            await thread_db.anniversary_notifications.insert_one({
                                "member_id": member_id,
                                "member_name": decrypted_member.get('name', decrypted_member.get('handle', '')),
                                "notification_month": month_key,
                                "years": years,
                                "sent_at": datetime.now()
                            })
                            anniversary_count += 1
                            
            except Exception as e:
                print(f"   ❌ Error processing join_date for {member.get('handle', 'unknown')}: {str(e)}", file=sys.stderr, flush=True)
        
        print(f"🎉 [ANNIVERSARY] Sent {anniversary_count} anniversary notification(s) this month", file=sys.stderr, flush=True)
        client.close()
        
    except Exception as e:
        print(f"❌ [ANNIVERSARY] Error checking anniversaries: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


def run_anniversary_check():
    """Wrapper to run async anniversary check in sync context (called by scheduler in thread)"""
    import asyncio
    import sys
    try:
        print(f"🎉 [SCHEDULER] Starting anniversary check job...", file=sys.stderr, flush=True)
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            loop.run_until_complete(check_and_send_anniversary_notifications())
            print(f"✅ [SCHEDULER] Anniversary check job completed", file=sys.stderr, flush=True)
        finally:
            loop.close()
            
    except Exception as e:
        print(f"❌ [SCHEDULER] Error running anniversary check: {str(e)}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc(file=sys.stderr)


# Initialize scheduler variable (will be started in startup event)
import sys
scheduler = None


# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    # Stop scheduler if it's running
    global scheduler
    if scheduler and scheduler.running:
        try:
            scheduler.shutdown()
            print("✅ [SCHEDULER] Discord event notification scheduler stopped", file=sys.stderr, flush=True)
        except Exception as e:
            print(f"⚠️ [SCHEDULER] Error stopping scheduler: {str(e)}", file=sys.stderr, flush=True)
    
    # Close MongoDB client
    client.close()


sys.stderr.write("✅ [INIT] Server module fully loaded and ready\n")
sys.stderr.flush()
