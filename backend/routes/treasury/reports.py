"""
Treasury Module - Financial Reports

Generates financial reports:
- Monthly summaries
- Quarterly reports
- Yearly reports
- Category breakdowns
"""
import sys
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends

from .utils import get_db, get_current_user, check_treasury_permission

router = APIRouter()


@router.get("/reports/summary")
async def get_summary(
    year: int = None,
    month: int = None,
    current_user: dict = Depends(get_current_user)
):
    """Get financial summary for a period"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    now = datetime.now(timezone.utc)
    year = year or now.year
    month = month or now.month
    
    # Build date range
    start_date = f"{year}-{month:02d}-01"
    if month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{month + 1:02d}-01"
    
    # Get totals
    income_total = await _get_total(db, "income", start_date, end_date)
    expense_total = await _get_total(db, "expense", start_date, end_date)
    
    # Get category breakdowns
    income_by_category = await _get_by_category(db, "income", start_date, end_date)
    expense_by_category = await _get_by_category(db, "expense", start_date, end_date)
    
    # Get account balances
    accounts = await db.treasury_accounts.find(
        {"is_active": True}, {"_id": 0, "id": 1, "name": 1, "balance": 1, "type": 1}
    ).to_list(50)
    
    total_balance = sum(acc.get("balance", 0) for acc in accounts)
    
    return {
        "period": {
            "year": year,
            "month": month,
            "start_date": start_date,
            "end_date": end_date
        },
        "income": {
            "total": income_total,
            "by_category": income_by_category
        },
        "expenses": {
            "total": expense_total,
            "by_category": expense_by_category
        },
        "net": income_total - expense_total,
        "accounts": accounts,
        "total_balance": total_balance
    }


@router.get("/reports/quarterly")
async def get_quarterly_report(
    year: int,
    quarter: int,
    current_user: dict = Depends(get_current_user)
):
    """Get quarterly financial report"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if quarter < 1 or quarter > 4:
        raise HTTPException(status_code=400, detail="Quarter must be 1-4")
    
    db = get_db()
    
    # Calculate date range
    start_month = (quarter - 1) * 3 + 1
    end_month = quarter * 3
    
    start_date = f"{year}-{start_month:02d}-01"
    if end_month == 12:
        end_date = f"{year + 1}-01-01"
    else:
        end_date = f"{year}-{end_month + 1:02d}-01"
    
    # Get totals
    income_total = await _get_total(db, "income", start_date, end_date)
    expense_total = await _get_total(db, "expense", start_date, end_date)
    
    # Get monthly breakdown
    monthly_data = []
    for m in range(start_month, end_month + 1):
        m_start = f"{year}-{m:02d}-01"
        if m == 12:
            m_end = f"{year + 1}-01-01"
        else:
            m_end = f"{year}-{m + 1:02d}-01"
        
        m_income = await _get_total(db, "income", m_start, m_end)
        m_expense = await _get_total(db, "expense", m_start, m_end)
        
        monthly_data.append({
            "month": m,
            "month_name": datetime(year, m, 1).strftime("%B"),
            "income": m_income,
            "expenses": m_expense,
            "net": m_income - m_expense
        })
    
    # Get category breakdowns
    income_by_category = await _get_by_category(db, "income", start_date, end_date)
    expense_by_category = await _get_by_category(db, "expense", start_date, end_date)
    
    # Get budget vs actual
    budgets = await db.treasury_budgets.find({
        "period": "quarterly",
        "year": year,
        "quarter": quarter,
        "is_active": True
    }, {"_id": 0}).to_list(100)
    
    budget_comparison = []
    for budget in budgets:
        spent = next((e["total"] for e in expense_by_category if e["category_id"] == budget["category_id"]), 0)
        budget_comparison.append({
            "category_name": budget["category_name"],
            "budgeted": budget["amount"],
            "spent": spent,
            "remaining": budget["amount"] - spent,
            "percent_used": (spent / budget["amount"] * 100) if budget["amount"] > 0 else 0
        })
    
    return {
        "period": {
            "year": year,
            "quarter": quarter,
            "quarter_name": f"Q{quarter}",
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_income": income_total,
            "total_expenses": expense_total,
            "net": income_total - expense_total
        },
        "monthly_breakdown": monthly_data,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category,
        "budget_comparison": budget_comparison
    }


@router.get("/reports/yearly")
async def get_yearly_report(
    year: int,
    current_user: dict = Depends(get_current_user)
):
    """Get yearly financial report"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    start_date = f"{year}-01-01"
    end_date = f"{year + 1}-01-01"
    
    # Get totals
    income_total = await _get_total(db, "income", start_date, end_date)
    expense_total = await _get_total(db, "expense", start_date, end_date)
    
    # Get quarterly breakdown
    quarterly_data = []
    for q in range(1, 5):
        q_start_month = (q - 1) * 3 + 1
        q_end_month = q * 3
        
        q_start = f"{year}-{q_start_month:02d}-01"
        if q_end_month == 12:
            q_end = f"{year + 1}-01-01"
        else:
            q_end = f"{year}-{q_end_month + 1:02d}-01"
        
        q_income = await _get_total(db, "income", q_start, q_end)
        q_expense = await _get_total(db, "expense", q_start, q_end)
        
        quarterly_data.append({
            "quarter": q,
            "quarter_name": f"Q{q}",
            "income": q_income,
            "expenses": q_expense,
            "net": q_income - q_expense
        })
    
    # Get monthly breakdown
    monthly_data = []
    for m in range(1, 13):
        m_start = f"{year}-{m:02d}-01"
        if m == 12:
            m_end = f"{year + 1}-01-01"
        else:
            m_end = f"{year}-{m + 1:02d}-01"
        
        m_income = await _get_total(db, "income", m_start, m_end)
        m_expense = await _get_total(db, "expense", m_start, m_end)
        
        monthly_data.append({
            "month": m,
            "month_name": datetime(year, m, 1).strftime("%b"),
            "income": m_income,
            "expenses": m_expense,
            "net": m_income - m_expense
        })
    
    # Get category breakdowns
    income_by_category = await _get_by_category(db, "income", start_date, end_date)
    expense_by_category = await _get_by_category(db, "expense", start_date, end_date)
    
    return {
        "period": {
            "year": year,
            "start_date": start_date,
            "end_date": end_date
        },
        "summary": {
            "total_income": income_total,
            "total_expenses": expense_total,
            "net": income_total - expense_total
        },
        "quarterly_breakdown": quarterly_data,
        "monthly_breakdown": monthly_data,
        "income_by_category": income_by_category,
        "expense_by_category": expense_by_category
    }


async def _get_total(db, type: str, start_date: str, end_date: str) -> float:
    """Get total for a transaction type in a date range"""
    pipeline = [
        {
            "$match": {
                "type": type,
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


async def _get_by_category(db, type: str, start_date: str, end_date: str) -> list:
    """Get totals by category for a date range"""
    pipeline = [
        {
            "$match": {
                "type": type,
                "date": {"$gte": start_date, "$lt": end_date}
            }
        },
        {
            "$group": {
                "_id": "$category_id",
                "category_name": {"$first": "$category_name"},
                "total": {"$sum": "$amount"},
                "count": {"$sum": 1}
            }
        },
        {"$sort": {"total": -1}}
    ]
    
    results = await db.treasury_transactions.aggregate(pipeline).to_list(100)
    
    return [
        {
            "category_id": r["_id"],
            "category_name": r["category_name"],
            "total": r["total"],
            "count": r["count"]
        }
        for r in results
    ]
