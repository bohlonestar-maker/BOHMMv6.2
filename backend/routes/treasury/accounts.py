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

from .utils import (
    get_db, get_current_user, check_treasury_permission,
    encrypt_account, decrypt_account, encrypt_value, log_audit
)

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
    
    # Decrypt account names for display
    decrypted_accounts = [decrypt_account(acc) for acc in accounts]
    
    # Calculate total balance
    total_balance = sum(acc.get("balance", 0) for acc in decrypted_accounts if acc.get("is_active", True))
    
    return {
        "accounts": decrypted_accounts,
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
    
    # Check for duplicate name (check encrypted names)
    all_accounts = await db.treasury_accounts.find({}, {"_id": 0, "name": 1}).to_list(100)
    for acc in all_accounts:
        decrypted_name = decrypt_account(acc).get("name", "")
        if decrypted_name.lower() == account.name.strip().lower():
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
    
    # Encrypt sensitive fields before storing
    encrypted_doc = encrypt_account(account_doc)
    await db.treasury_accounts.insert_one(encrypted_doc)
    
    # Log initial balance as transaction if not zero
    if account.initial_balance != 0:
        await _log_balance_adjustment(
            db, account_doc["id"], account.initial_balance,
            "Initial balance", current_user.get("username", "unknown")
        )
    
    # Audit log
    await log_audit(
        action="account_created",
        entity_type="account",
        entity_id=account_doc["id"],
        entity_name=account.name.strip(),
        user=current_user,
        details={
            "type": account.type,
            "initial_balance": account.initial_balance
        }
    )
    
    sys.stderr.write(f"[TREASURY] Created account (encrypted) with balance ${account.initial_balance:.2f}\n")
    
    # Return unencrypted for display
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
    
    # Get decrypted account for audit log
    decrypted_account = decrypt_account(account)
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Encrypt name/description if being updated
    encrypted_update = update_data.copy()
    if "name" in encrypted_update and encrypted_update["name"]:
        encrypted_update["name"] = encrypt_value(encrypted_update["name"])
    if "description" in encrypted_update and encrypted_update["description"]:
        encrypted_update["description"] = encrypt_value(encrypted_update["description"])
    
    await db.treasury_accounts.update_one(
        {"id": account_id},
        {"$set": encrypted_update}
    )
    
    # Audit log
    await log_audit(
        action="account_updated",
        entity_type="account",
        entity_id=account_id,
        entity_name=decrypted_account.get("name", "Unknown"),
        user=current_user,
        old_values={k: decrypted_account.get(k) for k in update_data.keys() if k != "updated_at"},
        new_values={k: v for k, v in update_data.items() if k != "updated_at"}
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
    
    # Get decrypted account for audit log
    decrypted_account = decrypt_account(account)
    old_balance = account.get("balance", 0)
    new_balance = old_balance + adjustment.amount
    
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
    
    # Audit log
    await log_audit(
        action="account_balance_adjusted",
        entity_type="account",
        entity_id=account_id,
        entity_name=decrypted_account.get("name", "Unknown"),
        user=current_user,
        details={
            "reason": adjustment.reason,
            "adjustment_amount": adjustment.amount
        },
        old_values={"balance": old_balance},
        new_values={"balance": new_balance}
    )
    
    sys.stderr.write(f"[TREASURY] Adjusted '{decrypted_account['name']}' by ${adjustment.amount:.2f} - {adjustment.reason}\n")
    
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
    
    # Decrypt account names
    from_decrypted = decrypt_account(from_account)
    to_decrypted = decrypt_account(to_account)
    
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
        "from_account_name": from_decrypted["name"],
        "to_account_id": transfer.to_account_id,
        "to_account_name": to_decrypted["name"],
        "amount": transfer.amount,
        "description": transfer.description or f"Transfer from {from_decrypted['name']} to {to_decrypted['name']}",
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown")
    }
    await db.treasury_transactions.insert_one(transfer_doc)
    
    # Audit log
    await log_audit(
        action="account_transfer",
        entity_type="account",
        entity_id=transfer_doc["id"],
        entity_name=f"{from_decrypted['name']} -> {to_decrypted['name']}",
        user=current_user,
        details={
            "from_account": from_decrypted["name"],
            "to_account": to_decrypted["name"],
            "amount": transfer.amount,
            "description": transfer.description
        }
    )
    
    sys.stderr.write(f"[TREASURY] Transferred ${transfer.amount:.2f} from '{from_decrypted['name']}' to '{to_decrypted['name']}'\n")
    
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
