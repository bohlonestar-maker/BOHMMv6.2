"""
Treasury Module - Budget Management

Handles budget allocation and tracking:
- Create budgets by category
- Track spending against budgets
- Budget alerts
"""
import sys
import uuid
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from .utils import get_db, get_current_user, check_treasury_permission

router = APIRouter()


class BudgetCreate(BaseModel):
    category_id: str
    amount: float
    period: str  # "monthly", "quarterly", "yearly"
    year: int
    quarter: Optional[int] = None  # 1-4 for quarterly
    month: Optional[int] = None  # 1-12 for monthly


class BudgetUpdate(BaseModel):
    amount: Optional[float] = None
    is_active: Optional[bool] = None


@router.get("/budgets")
async def list_budgets(
    period: str = None,
    year: int = None,
    current_user: dict = Depends(get_current_user)
):
    """Get all budgets with spending data"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    query = {"is_active": True}
    if period:
        query["period"] = period
    if year:
        query["year"] = year
    
    budgets = await db.treasury_budgets.find(query, {"_id": 0}).to_list(200)
    
    # Calculate spending for each budget
    for budget in budgets:
        spent = await _calculate_budget_spending(db, budget)
        budget["spent"] = spent
        budget["remaining"] = budget["amount"] - spent
        budget["percent_used"] = (spent / budget["amount"] * 100) if budget["amount"] > 0 else 0
    
    return budgets


@router.post("/budgets")
async def create_budget(
    budget: BudgetCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new budget"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if budget.period not in ["monthly", "quarterly", "yearly"]:
        raise HTTPException(status_code=400, detail="Invalid period")
    
    if budget.period == "quarterly" and (not budget.quarter or budget.quarter < 1 or budget.quarter > 4):
        raise HTTPException(status_code=400, detail="Quarter must be 1-4 for quarterly budgets")
    
    if budget.period == "monthly" and (not budget.month or budget.month < 1 or budget.month > 12):
        raise HTTPException(status_code=400, detail="Month must be 1-12 for monthly budgets")
    
    db = get_db()
    
    # Verify category exists
    category = await db.treasury_categories.find_one({"id": budget.category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    # Check for duplicate
    dup_query = {
        "category_id": budget.category_id,
        "period": budget.period,
        "year": budget.year,
        "is_active": True
    }
    if budget.quarter:
        dup_query["quarter"] = budget.quarter
    if budget.month:
        dup_query["month"] = budget.month
    
    existing = await db.treasury_budgets.find_one(dup_query)
    if existing:
        raise HTTPException(status_code=400, detail="Budget already exists for this period")
    
    now = datetime.now(timezone.utc)
    budget_doc = {
        "id": str(uuid.uuid4()),
        "category_id": budget.category_id,
        "category_name": category["name"],
        "amount": budget.amount,
        "period": budget.period,
        "year": budget.year,
        "quarter": budget.quarter,
        "month": budget.month,
        "is_active": True,
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown")
    }
    
    await db.treasury_budgets.insert_one(budget_doc)
    
    sys.stderr.write(f"[TREASURY] Created {budget.period} budget for {category['name']}: ${budget.amount:.2f}\n")
    
    return {k: v for k, v in budget_doc.items() if k != "_id"}


@router.put("/budgets/{budget_id}")
async def update_budget(
    budget_id: str,
    update: BudgetUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a budget"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    budget = await db.treasury_budgets.find_one({"id": budget_id})
    if not budget:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.treasury_budgets.update_one(
        {"id": budget_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Budget updated"}


@router.delete("/budgets/{budget_id}")
async def delete_budget(
    budget_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Deactivate a budget"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    result = await db.treasury_budgets.update_one(
        {"id": budget_id},
        {"$set": {"is_active": False, "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.modified_count == 0:
        raise HTTPException(status_code=404, detail="Budget not found")
    
    return {"success": True, "message": "Budget deactivated"}


async def _calculate_budget_spending(db, budget: dict) -> float:
    """Calculate total spending for a budget period"""
    # Build date range based on period
    year = budget["year"]
    
    if budget["period"] == "yearly":
        start_date = f"{year}-01-01"
        end_date = f"{year}-12-31"
    elif budget["period"] == "quarterly":
        quarter = budget["quarter"]
        start_month = (quarter - 1) * 3 + 1
        end_month = quarter * 3
        start_date = f"{year}-{start_month:02d}-01"
        if end_month == 12:
            end_date = f"{year}-12-31"
        else:
            end_date = f"{year}-{end_month + 1:02d}-01"
    else:  # monthly
        month = budget["month"]
        start_date = f"{year}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1}-01-01"
        else:
            end_date = f"{year}-{month + 1:02d}-01"
    
    # Query expenses for this category in this period
    pipeline = [
        {
            "$match": {
                "type": "expense",
                "category_id": budget["category_id"],
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": None,
                "total": {"$sum": "$amount"}
            }
        }
    ]
    
    result = await db.treasury_transactions.aggregate(pipeline).to_list(1)
    
    return result[0]["total"] if result else 0
