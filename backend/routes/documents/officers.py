"""
Document Signing - National Officers Endpoint

Provides list of National Officers available as document approvers.
"""
from fastapi import APIRouter, Depends

from .utils import get_db, get_current_user, NATIONAL_OFFICERS

router = APIRouter()


@router.get("/national-officers")
async def get_national_officers(current_user: dict = Depends(get_current_user)):
    """Get list of National Officers available as document approvers"""
    db = get_db()
    
    officers_with_users = []
    
    for officer in NATIONAL_OFFICERS:
        user = await db.users.find_one(
            {"title": officer["title"], "chapter": "National"},
            {"_id": 0, "id": 1, "username": 1, "title": 1, "email": 1, "first_name": 1, "last_name": 1, "chapter": 1}
        )
        
        officers_with_users.append({
            "role": officer["role"],
            "title": officer["title"],
            "display_title": officer["display_title"],
            "order": officer["order"],
            "user": user
        })
    
    return officers_with_users
