"""
NumberGuard — Lifecycle Events API (Phase 2)
Endpoints for querying lifecycle events and triggering state transitions
on the canonical MobileNumber registry.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import MobileNumber, NumberLifecycleEvent, NumberStatusHistory, User
from app.schemas.schemas import LifecycleEventOut, LifecycleTransitionRequest, StatusHistoryOut, MobileNumberOut
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.lifecycle import (
    transition_number_status, get_lifecycle_events, get_status_history
)

router = APIRouter()


@router.get("", response_model=List[MobileNumberOut])
async def list_mobile_numbers(
    carrier: Optional[str] = None,
    lifecycle_status: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """List all canonical mobile numbers in the registry."""
    query = select(MobileNumber).order_by(MobileNumber.created_at.desc())
    if carrier:
        query = query.where(MobileNumber.carrier == carrier)
    if lifecycle_status:
        query = query.where(MobileNumber.lifecycle_status == lifecycle_status)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{mobile_number_id}", response_model=MobileNumberOut)
async def get_mobile_number(
    mobile_number_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """Get a single canonical mobile number record."""
    res = await db.execute(select(MobileNumber).where(MobileNumber.id == mobile_number_id))
    mn = res.scalars().first()
    if not mn:
        raise HTTPException(status_code=404, detail="Mobile number not found")
    return mn


@router.get("/{mobile_number_id}/events", response_model=List[LifecycleEventOut])
async def get_number_lifecycle_events(
    mobile_number_id: str,
    limit: int = Query(100, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """
    Returns the full immutable event log for a mobile number.
    Events are ordered chronologically (oldest first).
    """
    res = await db.execute(select(MobileNumber).where(MobileNumber.id == mobile_number_id))
    if not res.scalars().first():
        raise HTTPException(status_code=404, detail="Mobile number not found")

    events = await get_lifecycle_events(db, mobile_number_id, limit=limit)
    return events


@router.get("/{mobile_number_id}/history", response_model=List[StatusHistoryOut])
async def get_number_status_history(
    mobile_number_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """
    Returns the status change history timeline for a mobile number.
    Simpler query than events — just from/to status pairs.
    """
    res = await db.execute(select(MobileNumber).where(MobileNumber.id == mobile_number_id))
    if not res.scalars().first():
        raise HTTPException(status_code=404, detail="Mobile number not found")

    history = await get_status_history(db, mobile_number_id)
    return history


@router.post("/{mobile_number_id}/transition", response_model=LifecycleEventOut)
async def trigger_lifecycle_transition(
    mobile_number_id: str,
    req: LifecycleTransitionRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_UPDATE)),
):
    """
    Triggers a lifecycle state transition for a mobile number.
    The FSM validates the transition before applying it.

    Valid event types:
    - NUMBER_DECOMMISSIONED, COOLING_STARTED, PROVIDER_NOTIFIED
    - PROVIDER_ACKNOWLEDGED, PROVIDER_REMEDIATED, COOLING_EXTENDED
    - COOLING_COMPLETED, MANUAL_REVIEW_TRIGGERED, MANUAL_REVIEW_RESOLVED
    - ALLOCATION_APPROVED, ALLOCATION_BLOCKED, NUMBER_REALLOCATED
    - DISPUTE_FILED, DISPUTE_RESOLVED, CASE_OPENED, CASE_CLOSED
    """
    try:
        mobile, event = await transition_number_status(
            db=db,
            mobile_number_id=mobile_number_id,
            event_type=req.event_type,
            triggered_by=current_user.email,
            triggered_by_role=current_user.role,
            notes=req.notes,
            payload=req.payload,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return event
