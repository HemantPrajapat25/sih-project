"""
NumberGuard — Case Management Service (Phase 2)
Handles creation, assignment, and resolution of decommissioning cases.
"""
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.models import DecommissioningCase, RemediationAction, MobileNumber


def _gen_case_number() -> str:
    uid = uuid.uuid4().hex[:8].upper()
    return f"CASE-{uid}"


async def create_case(
    db: AsyncSession,
    mobile_number_id: str,
    priority: str = "NORMAL",
    case_type: str = "STANDARD",
    assigned_to: Optional[str] = None,
    organization_id: Optional[str] = None,
    sla_hours: int = 72,
    created_by: str = "SYSTEM",
) -> DecommissioningCase:
    """Creates a new decommissioning case for a mobile number."""
    # Verify mobile number exists
    res = await db.execute(select(MobileNumber).where(MobileNumber.id == mobile_number_id))
    if not res.scalars().first():
        raise ValueError(f"MobileNumber {mobile_number_id} not found")

    now = datetime.now(timezone.utc)
    case = DecommissioningCase(
        case_number=_gen_case_number(),
        mobile_number_id=mobile_number_id,
        case_status="OPEN",
        priority=priority,
        case_type=case_type,
        assigned_to=assigned_to,
        organization_id=organization_id,
        sla_due_at=now + timedelta(hours=sla_hours),
        created_at=now,
        updated_at=now,
    )
    db.add(case)
    await db.commit()
    await db.refresh(case)
    return case


async def update_case(
    db: AsyncSession,
    case_id: str,
    updates: dict,
    updated_by: str = "SYSTEM",
) -> DecommissioningCase:
    """Updates a case and automatically handles dispute flag and resolution."""
    res = await db.execute(select(DecommissioningCase).where(DecommissioningCase.id == case_id))
    case = res.scalars().first()
    if not case:
        raise ValueError(f"Case {case_id} not found")

    now = datetime.now(timezone.utc)
    for field, value in updates.items():
        setattr(case, field, value)

    # Auto-set dispute_filed_at when dispute_flag is set
    if updates.get("dispute_flag") and not case.dispute_filed_at:
        case.dispute_filed_at = now

    # Auto-set resolved_at when resolving
    if updates.get("case_status") in ("RESOLVED", "CLOSED") and not case.resolved_at:
        case.resolved_at = now

    case.updated_at = now
    await db.commit()
    await db.refresh(case)
    return case


async def add_remediation_action(
    db: AsyncSession,
    case_id: str,
    action_type: str,
    description: str,
    performed_by: str,
    evidence_ref: Optional[str] = None,
) -> RemediationAction:
    """Adds a remediation action to a case."""
    res = await db.execute(select(DecommissioningCase).where(DecommissioningCase.id == case_id))
    if not res.scalars().first():
        raise ValueError(f"Case {case_id} not found")

    action = RemediationAction(
        case_id=case_id,
        action_type=action_type,
        description=description,
        performed_by=performed_by,
        performed_at=datetime.now(timezone.utc),
        result="SUCCESS",
        evidence_ref=evidence_ref,
    )
    db.add(action)

    # Update case status to IN_PROGRESS if still OPEN
    case_res = await db.execute(select(DecommissioningCase).where(DecommissioningCase.id == case_id))
    case = case_res.scalars().first()
    if case and case.case_status == "OPEN":
        case.case_status = "IN_PROGRESS"
        case.updated_at = datetime.now(timezone.utc)

    await db.commit()
    await db.refresh(action)
    return action


async def list_cases(
    db: AsyncSession,
    case_status: Optional[str] = None,
    priority: Optional[str] = None,
    case_type: Optional[str] = None,
    assigned_to: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[DecommissioningCase]:
    """Lists decommissioning cases with optional filters."""
    query = select(DecommissioningCase).order_by(
        DecommissioningCase.created_at.desc()
    )
    if case_status:
        query = query.where(DecommissioningCase.case_status == case_status)
    if priority:
        query = query.where(DecommissioningCase.priority == priority)
    if case_type:
        query = query.where(DecommissioningCase.case_type == case_type)
    if assigned_to:
        query = query.where(DecommissioningCase.assigned_to == assigned_to)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
