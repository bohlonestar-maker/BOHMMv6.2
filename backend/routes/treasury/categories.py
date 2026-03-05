"""
Treasury Module - Category Management

Handles dynamic category CRUD:
- List categories by type (income/expense)
- Create new categories
- Update categories
- Delete/deactivate categories
"""
import sys
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from .utils import (
    get_db, get_current_user, check_treasury_permission,
    DEFAULT_INCOME_CATEGORIES, DEFAULT_EXPENSE_CATEGORIES
)

router = APIRouter()


class CategoryCreate(BaseModel):
    name: str
    type: str  # "income" or "expense"
    description: Optional[str] = None
    color: Optional[str] = None


class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    color: Optional[str] = None
    is_active: Optional[bool] = None


@router.get("/categories")
async def list_categories(
    type: str = None,
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all treasury categories"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    # Check if categories collection exists, if not seed defaults
    count = await db.treasury_categories.count_documents({})
    if count == 0:
        await _seed_default_categories(db)
    
    query = {}
    if type:
        query["type"] = type
    if not include_inactive:
        query["is_active"] = True
    
    categories = await db.treasury_categories.find(
        query, {"_id": 0}
    ).sort("name", 1).to_list(100)
    
    return categories


@router.post("/categories")
async def create_category(
    category: CategoryCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new category"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if category.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    db = get_db()
    
    # Check for duplicate
    existing = await db.treasury_categories.find_one({
        "name": {"$regex": f"^{category.name}$", "$options": "i"},
        "type": category.type
    })
    if existing:
        raise HTTPException(status_code=400, detail="Category already exists")
    
    now = datetime.now(timezone.utc)
    category_doc = {
        "id": str(uuid.uuid4()),
        "name": category.name.strip(),
        "type": category.type,
        "description": category.description,
        "color": category.color or _get_default_color(category.type),
        "is_active": True,
        "is_default": False,
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown")
    }
    
    await db.treasury_categories.insert_one(category_doc)
    
    sys.stderr.write(f"[TREASURY] Created category '{category.name}' ({category.type})\n")
    
    return {k: v for k, v in category_doc.items() if k != "_id"}


@router.put("/categories/{category_id}")
async def update_category(
    category_id: str,
    update: CategoryUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a category"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    category = await db.treasury_categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.treasury_categories.update_one(
        {"id": category_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Category updated"}


@router.delete("/categories/{category_id}")
async def delete_category(
    category_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a category (soft delete)"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    category = await db.treasury_categories.find_one({"id": category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    if category.get("is_default"):
        raise HTTPException(status_code=400, detail="Cannot delete default categories")
    
    await db.treasury_categories.update_one(
        {"id": category_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    return {"success": True, "message": "Category deactivated"}


async def _seed_default_categories(db):
    """Seed default categories"""
    now = datetime.now(timezone.utc).isoformat()
    
    categories = []
    
    for name in DEFAULT_INCOME_CATEGORIES:
        categories.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "type": "income",
            "description": None,
            "color": _get_default_color("income"),
            "is_active": True,
            "is_default": True,
            "created_at": now,
            "created_by": "system"
        })
    
    for name in DEFAULT_EXPENSE_CATEGORIES:
        categories.append({
            "id": str(uuid.uuid4()),
            "name": name,
            "type": "expense",
            "description": None,
            "color": _get_default_color("expense"),
            "is_active": True,
            "is_default": True,
            "created_at": now,
            "created_by": "system"
        })
    
    if categories:
        await db.treasury_categories.insert_many(categories)
        sys.stderr.write(f"[TREASURY] Seeded {len(categories)} default categories\n")


def _get_default_color(type: str) -> str:
    """Get default color based on type"""
    return "#22c55e" if type == "income" else "#ef4444"
