#!/usr/bin/env python3
import asyncio
import os
import sys
from pathlib import Path
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
from datetime import datetime, timezone
import uuid

# Add backend to path
sys.path.append('/app/backend')

# Load environment
from dotenv import load_dotenv
load_dotenv('/app/backend/.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

async def create_test_admin():
    """Create testadmin user"""
    print("Creating testadmin user...")
    
    # Check if testadmin exists
    existing = await db.users.find_one({"username": "testadmin"})
    if existing:
        print("testadmin user already exists")
        return
    
    # Create testadmin user
    admin_user = {
        "id": str(uuid.uuid4()),
        "username": "testadmin",
        "password_hash": hash_password("testpass123"),
        "role": "admin",
        "permissions": {
            "basic_info": True,
            "email": True,
            "phone": True,
            "address": True,
            "dues_tracking": True,
            "meeting_attendance": True,
            "admin_actions": True
        },
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.users.insert_one(admin_user)
    print("testadmin user created successfully")
    
    # Also create default admin if it doesn't exist
    admin_exists = await db.users.find_one({"username": "admin"})
    if not admin_exists:
        default_admin = {
            "id": str(uuid.uuid4()),
            "username": "admin",
            "password_hash": hash_password("admin123"),
            "role": "admin",
            "permissions": {
                "basic_info": True,
                "email": True,
                "phone": True,
                "address": True,
                "dues_tracking": True,
                "meeting_attendance": True,
                "admin_actions": True
            },
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(default_admin)
        print("Default admin user created successfully")

async def main():
    try:
        await create_test_admin()
        print("User creation completed")
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())