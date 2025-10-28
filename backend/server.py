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
from fastapi.responses import StreamingResponse

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

# Models
class User(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    role: str = "user"  # admin or user or custom
    permissions: dict = Field(default_factory=lambda: {
        "basic_info": True,        # Chapter, Title, Handle, Name
        "contact_info": False,     # Email, Phone, Address
        "dues_tracking": False,    # View dues
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

class LoginRequest(BaseModel):
    username: str
    password: str

class LoginResponse(BaseModel):
    token: str
    username: str
    role: str

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
        "year": datetime.now(timezone.utc).year,
        "months": [False] * 12  # Jan-Dec, False = unpaid, True = paid
    })
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
                "contact_info": True,
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
            "contact_info": False,
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
    member = Member(**member_data.model_dump())
    doc = member.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['updated_at'] = doc['updated_at'].isoformat()
    await db.members.insert_one(doc)
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
    return updated_member

@api_router.delete("/members/{member_id}")
async def delete_member(member_id: str, current_user: dict = Depends(verify_admin)):
    result = await db.members.delete_one({"id": member_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Member not found")
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

# CSV Export endpoint
@api_router.get("/members/export/csv")
async def export_members_csv(current_user: dict = Depends(verify_admin)):
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
    
    # Write header
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    header = ['Chapter', 'Title', 'Member Handle', 'Name', 'Email', 'Phone', 'Address', 'Dues Year'] + month_names
    writer.writerow(header)
    
    # Write data
    for member in sorted_members:
        dues = member.get('dues', {})
        dues_year = dues.get('year', '') if dues else ''
        dues_months = dues.get('months', [False] * 12) if dues else [False] * 12
        
        # Convert boolean dues to Paid/Unpaid
        dues_status = ['Paid' if paid else 'Unpaid' for paid in dues_months]
        
        row = [
            member.get('chapter', ''),
            member.get('title', ''),
            member.get('handle', ''),
            member.get('name', ''),
            member.get('email', ''),
            member.get('phone', ''),
            member.get('address', ''),
            dues_year
        ] + dues_status
        
        writer.writerow(row)
    
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=members.csv"}
    )

# User management endpoints (admin only)
@api_router.get("/users", response_model=List[UserResponse])
async def get_users(current_user: dict = Depends(verify_admin)):
    users = await db.users.find({}, {"_id": 0, "password_hash": 0}).to_list(1000)
    for user in users:
        if isinstance(user.get('created_at'), str):
            user['created_at'] = datetime.fromisoformat(user['created_at'])
    return users

@api_router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(user_data: UserCreate, current_user: dict = Depends(verify_admin)):
    # Check if username exists
    existing = await db.users.find_one({"username": user_data.username})
    if existing:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    user = User(
        username=user_data.username,
        password_hash=hash_password(user_data.password),
        role=user_data.role
    )
    doc = user.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.users.insert_one(doc)
    
    return UserResponse(
        id=user.id,
        username=user.username,
        role=user.role,
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
    
    if update_data:
        await db.users.update_one({"id": user_id}, {"$set": update_data})
    
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
    return {"message": "User deleted successfully"}

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