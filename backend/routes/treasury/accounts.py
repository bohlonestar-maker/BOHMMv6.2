"""
Treasury Module - Account Management

Handles treasury account management:
- List accounts (checking, savings, cash box, etc.)
- Create new accounts
- Update account balances
- Transfer between accounts
"""
import sys
import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List

from .utils import get_db, get_current_user, check_treasury_permission

router = APIRouter()


class AccountCreate(BaseModel):
    name: str
    type: str  # "checking", "savings", "cash", "other"
    initial_balance: float = 0.0
    description: Optional[str] = None


class AccountUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None


class BalanceAdjustment(BaseModel):
    amount: float
    reason: str


class TransferRequest(BaseModel):
    from_account_id: str
    to_account_id: str
    amount: float
    description: Optional[str] = None


@router.get("/accounts")
async def list_accounts(
    include_inactive: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Get all treasury accounts with current balances"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    query = {} if include_inactive else {"is_active": True}
    
    accounts = await db.treasury_accounts.find(
        query, {"_id": 0}
    ).sort("name", 1).to_list(50)
    
    # Calculate total balance
    total_balance = sum(acc.get("balance", 0) for acc in accounts if acc.get("is_active", True))
    
    return {
        "accounts": accounts,
        "total_balance": total_balance
    }


@router.post("/accounts")
async def create_account(
    account: AccountCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new treasury account"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if account.type not in ["checking", "savings", "cash", "other"]:
        raise HTTPException(status_code=400, detail="Invalid account type")
    
    db = get_db()
    
    # Check for duplicate name
    existing = await db.treasury_accounts.find_one({
        "name": {"$regex": f"^{account.name}$", "$options": "i"}
    })
    if existing:
        raise HTTPException(status_code=400, detail="Account name already exists")
    
    now = datetime.now(timezone.utc)
    account_doc = {
        "id": str(uuid.uuid4()),
        "name": account.name.strip(),
        "type": account.type,
        "balance": account.initial_balance,
        "description": account.description,
        "is_active": True,
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown"),
        "last_transaction_at": None
    }
    
    await db.treasury_accounts.insert_one(account_doc)
    
    # Log initial balance as transaction if not zero
    if account.initial_balance != 0:
        await _log_balance_adjustment(
            db, account_doc["id"], account.initial_balance,
            "Initial balance", current_user.get("username", "unknown")
        )
    
    sys.stderr.write(f"[TREASURY] Created account '{account.name}' with balance ${account.initial_balance:.2f}\n")
    
    return {k: v for k, v in account_doc.items() if k != "_id"}


@router.put("/accounts/{account_id}")
async def update_account(
    account_id: str,
    update: AccountUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update account details"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    account = await db.treasury_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.treasury_accounts.update_one(
        {"id": account_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Account updated"}


@router.post("/accounts/{account_id}/adjust")
async def adjust_balance(
    account_id: str,
    adjustment: BalanceAdjustment,
    current_user: dict = Depends(get_current_user)
):
    """Manually adjust account balance (for corrections)"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    account = await db.treasury_accounts.find_one({"id": account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    new_balance = account.get("balance", 0) + adjustment.amount
    
    await db.treasury_accounts.update_one(
        {"id": account_id},
        {"$set": {
            "balance": new_balance,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    await _log_balance_adjustment(
        db, account_id, adjustment.amount,
        f"Balance adjustment: {adjustment.reason}",
        current_user.get("username", "unknown")
    )
    
    sys.stderr.write(f"[TREASURY] Adjusted '{account['name']}' by ${adjustment.amount:.2f} - {adjustment.reason}\n")
    
    return {"success": True, "new_balance": new_balance}


@router.post("/accounts/transfer")
async def transfer_between_accounts(
    transfer: TransferRequest,
    current_user: dict = Depends(get_current_user)
):
    """Transfer funds between accounts"""
    if not check_treasury_permission(current_user, "manage_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if transfer.amount <= 0:
        raise HTTPException(status_code=400, detail="Transfer amount must be positive")
    
    db = get_db()
    
    from_account = await db.treasury_accounts.find_one({"id": transfer.from_account_id})
    to_account = await db.treasury_accounts.find_one({"id": transfer.to_account_id})
    
    if not from_account:
        raise HTTPException(status_code=404, detail="Source account not found")
    if not to_account:
        raise HTTPException(status_code=404, detail="Destination account not found")
    
    if from_account.get("balance", 0) < transfer.amount:
        raise HTTPException(status_code=400, detail="Insufficient funds in source account")
    
    now = datetime.now(timezone.utc)
    
    # Update both accounts
    await db.treasury_accounts.update_one(
        {"id": transfer.from_account_id},
        {"$inc": {"balance": -transfer.amount}, "$set": {"last_transaction_at": now.isoformat()}}
    )
    await db.treasury_accounts.update_one(
        {"id": transfer.to_account_id},
        {"$inc": {"balance": transfer.amount}, "$set": {"last_transaction_at": now.isoformat()}}
    )
    
    # Log transfer as transaction
    transfer_doc = {
        "id": str(uuid.uuid4()),
        "type": "transfer",
        "from_account_id": transfer.from_account_id,
        "from_account_name": from_account["name"],
        "to_account_id": transfer.to_account_id,
        "to_account_name": to_account["name"],
        "amount": transfer.amount,
        "description": transfer.description or f"Transfer from {from_account['name']} to {to_account['name']}",
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown")
    }
    await db.treasury_transactions.insert_one(transfer_doc)
    
    sys.stderr.write(f"[TREASURY] Transferred ${transfer.amount:.2f} from '{from_account['name']}' to '{to_account['name']}'\n")
    
    return {"success": True, "message": f"Transferred ${transfer.amount:.2f}"}


async def _log_balance_adjustment(db, account_id: str, amount: float, reason: str, username: str):
    """Log a balance adjustment as a transaction"""
    now = datetime.now(timezone.utc)
    
    adjustment_doc = {
        "id": str(uuid.uuid4()),
        "type": "adjustment",
        "account_id": account_id,
        "amount": amount,
        "description": reason,
        "created_at": now.isoformat(),
        "created_by": username
    }
    await db.treasury_transactions.insert_one(adjustment_doc)
