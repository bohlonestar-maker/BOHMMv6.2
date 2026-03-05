"""
Treasury Module - Audit Log API

Provides endpoints for viewing Treasury audit logs:
- List audit logs with filtering
- Export audit logs
"""
from fastapi import APIRouter, HTTPException, Depends
from typing import Optional

from .utils import (
    get_current_user, check_treasury_permission, get_audit_logs, AUDIT_ACTIONS
)

router = APIRouter()


@router.get("/audit")
async def list_audit_logs(
    entity_type: Optional[str] = None,
    entity_id: Optional[str] = None,
    action: Optional[str] = None,
    username: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    current_user: dict = Depends(get_current_user)
):
    """
    Get Treasury audit logs with optional filtering
    
    Filters:
    - entity_type: 'account', 'transaction', 'category', 'budget'
    - entity_id: Specific entity ID
    - action: Action type (e.g., 'transaction_created')
    - username: Filter by username (partial match)
    - start_date: ISO date string
    - end_date: ISO date string
    """
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied. Treasury admin access required.")
    
    result = await get_audit_logs(
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        username=username,
        start_date=start_date,
        end_date=end_date,
        limit=min(limit, 200),  # Max 200 per request
        offset=offset
    )
    
    return result


@router.get("/audit/actions")
async def list_audit_action_types(
    current_user: dict = Depends(get_current_user)
):
    """Get all available audit action types"""
    if not check_treasury_permission(current_user, "treasury_admin"):
        raise HTTPException(status_code=403, detail="Permission denied")
    
    return {
        "actions": [
            {"key": key, "display": display}
            for key, display in AUDIT_ACTIONS.items()
        ]
    }
