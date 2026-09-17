"""
NumberGuard — Decommissioning Cases API (Phase 2)
CRUD endpoints for case management lifecycle.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.db.session import get_db
from app.models.models import DecommissioningCase, RemediationAction, User
from app.schemas.schemas import (
    CaseCreate, CaseUpdate, CaseOut, CaseDetailOut,
    RemediationActionCreate, RemediationActionOut
)
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.case_service import (
    create_case, update_case, add_remediation_action, list_cases
)
from app.services.audit import record_audit_log

router = APIRouter()


@router.get("", response_model=List[CaseOut])
async def list_decommissioning_cases(
    case_status: Optional[str] = None,
    priority: Optional[str] = None,
    case_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """List all decommissioning cases with optional filters."""
    cases = await list_cases(
        db, case_status=case_status, priority=priority,
        case_type=case_type, assigned_to=assigned_to,
        skip=skip, limit=limit
    )
    return cases


@router.post("", response_model=CaseOut, status_code=201)
async def create_decommissioning_case(
    req: CaseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_UPDATE)),
):
    """Create a new decommissioning case for a mobile number."""
    try:
        case = await create_case(
            db=db,
            mobile_number_id=req.mobile_number_id,
            priority=req.priority,
            case_type=req.case_type,
            assigned_to=req.assigned_to,
            organization_id=current_user.organization_id,
            sla_hours=req.sla_hours or 72,
            created_by=current_user.email,
        )
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="NumberGuard",
        action="CASE_CREATED",
        entity_type="CASE",
        entity_id=case.id,
        details=f"Created {case.case_type} case {case.case_number} with priority {case.priority}",
    )
    return case


@router.get("/{case_id}", response_model=CaseDetailOut)
async def get_case_detail(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """Get a decommissioning case with all remediation actions."""
    res = await db.execute(
        select(DecommissioningCase)
        .options(selectinload(DecommissioningCase.remediation_actions))
        .where(DecommissioningCase.id == case_id)
    )
    case = res.scalars().first()
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")
    return case


@router.patch("/{case_id}", response_model=CaseOut)
async def update_case_status(
    case_id: str,
    req: CaseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_UPDATE)),
):
    """Update a decommissioning case."""
    updates = req.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=422, detail="No update fields provided")
    try:
        case = await update_case(db, case_id, updates, updated_by=current_user.email)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="NumberGuard",
        action="CASE_UPDATED",
        entity_type="CASE",
        entity_id=case.id,
        details=f"Updated case {case.case_number}: {updates}",
    )
    return case


@router.post("/{case_id}/actions", response_model=RemediationActionOut, status_code=201)
async def add_case_action(
    case_id: str,
    req: RemediationActionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_UPDATE)),
):
    """Add a remediation action to a case."""
    try:
        action = await add_remediation_action(
            db=db,
            case_id=case_id,
            action_type=req.action_type,
            description=req.description,
            performed_by=current_user.email,
            evidence_ref=req.evidence_ref,
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    return action


@router.get("/{case_id}/actions", response_model=List[RemediationActionOut])
async def list_case_actions(
    case_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ)),
):
    """List all remediation actions for a case."""
    res = await db.execute(
        select(RemediationAction)
        .where(RemediationAction.case_id == case_id)
        .order_by(RemediationAction.performed_at)
    )
    return res.scalars().all()
