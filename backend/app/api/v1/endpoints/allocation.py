"""
NumberGuard — Allocation Decisions API (Phase 2)
Endpoints for creating and querying allocation decisions.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.models.models import AllocationDecision, MobileNumber, User
from app.schemas.schemas import AllocationDecisionCreate, AllocationDecisionOut
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.allocation_service import create_allocation_decision, list_decisions
from app.services.audit import record_audit_log
from app.services.lifecycle import transition_number_status

router = APIRouter()


@router.get("/decisions", response_model=List[AllocationDecisionOut])
async def list_allocation_decisions(
    decision: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """List all allocation decisions, optionally filtered by decision type."""
    return await list_decisions(db, decision_filter=decision, skip=skip, limit=limit)


@router.get("/decisions/{decision_id}", response_model=AllocationDecisionOut)
async def get_allocation_decision(
    decision_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """Get a single allocation decision by ID."""
    res = await db.execute(select(AllocationDecision).where(AllocationDecision.id == decision_id))
    dec = res.scalars().first()
    if not dec:
        raise HTTPException(status_code=404, detail="Allocation decision not found")
    return dec


@router.post("/decide/{mobile_number_id}", response_model=AllocationDecisionOut, status_code=201)
async def create_decision(
    mobile_number_id: str,
    req: AllocationDecisionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_RELEASE)),
):
    """
    Create an allocation decision for a mobile number.
    Automatically computes risk context at time of decision.
    
    Required permission: NUMBERS_RELEASE (TELECOM_ADMIN or SUPER_ADMIN)
    
    Decision types:
    - APPROVED: Number cleared for reallocation
    - BLOCKED: Number blocked from reallocation
    - DEFERRED: Decision deferred, cooling period extended
    - MANUAL_OVERRIDE_APPROVED: Admin override approval despite risk
    - MANUAL_OVERRIDE_REJECTED: Admin override rejection
    """
    try:
        dec = await create_allocation_decision(
            db=db,
            mobile_number_id=req.mobile_number_id,
            decision=req.decision,
            decided_by=current_user.email,
            decided_by_role=current_user.role,
            decision_notes=req.decision_notes,
            override_justification=req.override_justification,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    # Trigger lifecycle transition based on decision
    event_type_map = {
        "APPROVED": "ALLOCATION_APPROVED",
        "MANUAL_OVERRIDE_APPROVED": "ALLOCATION_APPROVED",
        "BLOCKED": "ALLOCATION_BLOCKED",
        "MANUAL_OVERRIDE_REJECTED": "ALLOCATION_BLOCKED",
    }
    event_type = event_type_map.get(req.decision)
    if event_type:
        try:
            await transition_number_status(
                db=db,
                mobile_number_id=mobile_number_id,
                event_type=event_type,
                triggered_by=current_user.email,
                triggered_by_role=current_user.role,
                notes=req.decision_notes,
                payload={"decision_id": dec.id, "decision": req.decision},
            )
        except ValueError:
            pass  # MobileNumber may not exist yet — non-fatal

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="NumberGuard",
        action="ALLOCATION_DECISION_CREATED",
        entity_type="ALLOCATION",
        entity_id=dec.id,
        details=(
            f"Decision {dec.decision_number}: {dec.decision} | "
            f"Risk: {dec.risk_score_at_decision}/{dec.risk_level_at_decision} | "
            f"Cooling: {'✓' if dec.cooling_completed else '✗'} | "
            f"Banking: {'✓' if dec.banking_cleared else '✗'}"
        ),
    )
    return dec
