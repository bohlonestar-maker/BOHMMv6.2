"""
Treasury Module - Transaction Management

Handles income and expense transactions:
- List transactions with filtering
- Create income/expense transactions
- Update transactions
- Delete transactions
- Attach receipts/invoices
"""
import sys
import uuid
import base64
from datetime import datetime, timezone
from typing import Optional, List

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel

from .utils import get_db, get_current_user, check_treasury_permission

router = APIRouter()


class TransactionCreate(BaseModel):
    type: str  # "income" or "expense"
    account_id: str
    category_id: str
    amount: float
    description: str
    date: str  # ISO date string
    reference_number: Optional[str] = None
    vendor_payee: Optional[str] = None
    notes: Optional[str] = None


class TransactionUpdate(BaseModel):
    category_id: Optional[str] = None
    amount: Optional[float] = None
    description: Optional[str] = None
    date: Optional[str] = None
    reference_number: Optional[str] = None
    vendor_payee: Optional[str] = None
    notes: Optional[str] = None


@router.get("/transactions")
async def list_transactions(
    type: str = None,
    account_id: str = None,
    category_id: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = 100,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """Get transactions with optional filtering"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    query = {"type": {"$in": ["income", "expense"]}}  # Exclude transfers/adjustments
    
    if type:
        query["type"] = type
    if account_id:
        query["account_id"] = account_id
    if category_id:
        query["category_id"] = category_id
    if start_date:
        query["date"] = {"$gte": start_date}
    if end_date:
        if "date" in query:
            query["date"]["$lte"] = end_date
        else:
            query["date"] = {"$lte": end_date}
    
    total = await db.treasury_transactions.count_documents(query)
    
    transactions = await db.treasury_transactions.find(
        query, {"_id": 0, "receipt_data": 0}  # Exclude large receipt data from list
    ).sort("date", -1).skip(offset).limit(limit).to_list(limit)
    
    return {
        "transactions": transactions,
        "total": total,
        "limit": limit,
        "offset": offset
    }


@router.get("/transactions/{transaction_id}")
async def get_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get a single transaction with full details"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    transaction = await db.treasury_transactions.find_one(
        {"id": transaction_id}, {"_id": 0}
    )
    
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    return transaction


@router.post("/transactions")
async def create_transaction(
    transaction: TransactionCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new income or expense transaction"""
    if not check_treasury_permission(current_user, "manage_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    if transaction.type not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Type must be 'income' or 'expense'")
    
    if transaction.amount <= 0:
        raise HTTPException(status_code=400, detail="Amount must be positive")
    
    db = get_db()
    
    # Verify account exists
    account = await db.treasury_accounts.find_one({"id": transaction.account_id})
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    
    # Verify category exists
    category = await db.treasury_categories.find_one({"id": transaction.category_id})
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    
    now = datetime.now(timezone.utc)
    
    transaction_doc = {
        "id": str(uuid.uuid4()),
        "type": transaction.type,
        "account_id": transaction.account_id,
        "account_name": account["name"],
        "category_id": transaction.category_id,
        "category_name": category["name"],
        "amount": transaction.amount,
        "description": transaction.description,
        "date": transaction.date,
        "reference_number": transaction.reference_number,
        "vendor_payee": transaction.vendor_payee,
        "notes": transaction.notes,
        "receipt_filename": None,
        "receipt_data": None,
        "created_at": now.isoformat(),
        "created_by": current_user.get("username", "unknown"),
        "updated_at": None
    }
    
    await db.treasury_transactions.insert_one(transaction_doc)
    
    # Update account balance
    balance_change = transaction.amount if transaction.type == "income" else -transaction.amount
    await db.treasury_accounts.update_one(
        {"id": transaction.account_id},
        {
            "$inc": {"balance": balance_change},
            "$set": {"last_transaction_at": now.isoformat()}
        }
    )
    
    sys.stderr.write(f"[TREASURY] Created {transaction.type}: ${transaction.amount:.2f} - {transaction.description}\n")
    
    return {k: v for k, v in transaction_doc.items() if k not in ["_id", "receipt_data"]}


@router.put("/transactions/{transaction_id}")
async def update_transaction(
    transaction_id: str,
    update: TransactionUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a transaction"""
    if not check_treasury_permission(current_user, "manage_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    transaction = await db.treasury_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["type"] not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Cannot edit this transaction type")
    
    update_data = {k: v for k, v in update.dict().items() if v is not None}
    if not update_data:
        raise HTTPException(status_code=400, detail="No update data provided")
    
    # Handle amount change - adjust account balance
    if "amount" in update_data and update_data["amount"] != transaction["amount"]:
        old_amount = transaction["amount"]
        new_amount = update_data["amount"]
        
        if transaction["type"] == "income":
            balance_diff = new_amount - old_amount
        else:
            balance_diff = old_amount - new_amount
        
        await db.treasury_accounts.update_one(
            {"id": transaction["account_id"]},
            {"$inc": {"balance": balance_diff}}
        )
    
    # Update category name if category changed
    if "category_id" in update_data:
        category = await db.treasury_categories.find_one({"id": update_data["category_id"]})
        if category:
            update_data["category_name"] = category["name"]
    
    update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    update_data["updated_by"] = current_user.get("username", "unknown")
    
    await db.treasury_transactions.update_one(
        {"id": transaction_id},
        {"$set": update_data}
    )
    
    return {"success": True, "message": "Transaction updated"}


@router.delete("/transactions/{transaction_id}")
async def delete_transaction(
    transaction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a transaction and reverse balance change"""
    if not check_treasury_permission(current_user, "manage_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    transaction = await db.treasury_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    if transaction["type"] not in ["income", "expense"]:
        raise HTTPException(status_code=400, detail="Cannot delete this transaction type")
    
    # Reverse the balance change
    if transaction["type"] == "income":
        balance_change = -transaction["amount"]
    else:
        balance_change = transaction["amount"]
    
    await db.treasury_accounts.update_one(
        {"id": transaction["account_id"]},
        {"$inc": {"balance": balance_change}}
    )
    
    await db.treasury_transactions.delete_one({"id": transaction_id})
    
    sys.stderr.write(f"[TREASURY] Deleted {transaction['type']}: ${transaction['amount']:.2f} - {transaction['description']}\n")
    
    return {"success": True, "message": "Transaction deleted"}


@router.post("/transactions/{transaction_id}/receipt")
async def upload_receipt(
    transaction_id: str,
    file: UploadFile = File(...),
    current_user: dict = Depends(get_current_user)
):
    """Upload a receipt/invoice for a transaction"""
    if not check_treasury_permission(current_user, "manage_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    transaction = await db.treasury_transactions.find_one({"id": transaction_id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    
    # Validate file type
    allowed_types = ["image/jpeg", "image/png", "image/webp", "application/pdf"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="File must be an image or PDF")
    
    # Read and encode file
    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5MB limit
        raise HTTPException(status_code=400, detail="File too large (max 5MB)")
    
    encoded = base64.b64encode(content).decode()
    
    await db.treasury_transactions.update_one(
        {"id": transaction_id},
        {"$set": {
            "receipt_filename": file.filename,
            "receipt_content_type": file.content_type,
            "receipt_data": encoded,
            "updated_at": datetime.now(timezone.utc).isoformat()
        }}
    )
    
    return {"success": True, "message": "Receipt uploaded"}


@router.get("/transactions/{transaction_id}/receipt")
async def get_receipt(
    transaction_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get receipt/invoice for a transaction"""
    if not check_treasury_permission(current_user, "view_treasury"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    db = get_db()
    
    transaction = await db.treasury_transactions.find_one(
        {"id": transaction_id},
        {"receipt_data": 1, "receipt_filename": 1, "receipt_content_type": 1}
    )
    
    if not transaction or not transaction.get("receipt_data"):
        raise HTTPException(status_code=404, detail="Receipt not found")
    
    from fastapi.responses import Response
    
    content = base64.b64decode(transaction["receipt_data"])
    
    return Response(
        content=content,
        media_type=transaction.get("receipt_content_type", "application/octet-stream"),
        headers={
            "Content-Disposition": f"inline; filename={transaction.get('receipt_filename', 'receipt')}"
        }
    )
