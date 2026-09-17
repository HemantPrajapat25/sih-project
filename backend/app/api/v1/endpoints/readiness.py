from datetime import datetime, timezone
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.db.session import get_db
from app.models.models import DecommissionedNumber, User
from app.schemas.schemas import ReadinessSummaryOut, ReadinessReleaseRequest, NumberOut
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.audit import record_audit_log

router = APIRouter()

@router.get("/summary", response_model=ReadinessSummaryOut)
async def get_readiness_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    res = await db.execute(
        select(DecommissionedNumber.allocation_eligibility, func.count(DecommissionedNumber.id))
        .group_by(DecommissionedNumber.allocation_eligibility)
    )
    counts = dict(res.all())

    # Calculate blocked reasons:
    blocked_res = await db.execute(
        select(DecommissionedNumber.hold_reason, func.count(DecommissionedNumber.id))
        .where(DecommissionedNumber.allocation_eligibility.in_(["BLOCKED", "MANUAL_REVIEW_REQUIRED"]))
        .group_by(DecommissionedNumber.hold_reason)
    )
    blocked_reasons = {}
    for reason, count in blocked_res.all():
        r_name = reason or "Active high-risk service hold"
        blocked_reasons[r_name] = count

    return ReadinessSummaryOut(
        total_eligible=counts.get("ELIGIBLE", 0),
        total_cooling_hold=counts.get("COOLING_HOLD", 0),
        total_blocked=counts.get("BLOCKED", 0),
        total_manual_review=counts.get("MANUAL_REVIEW_REQUIRED", 0),
        blocked_reasons=blocked_reasons
    )

@router.post("/batch-release")
async def batch_release_numbers(
    req: ReadinessReleaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_REALLOCATE))
):
    query = select(DecommissionedNumber).where(DecommissionedNumber.id.in_(req.number_ids))
    res = await db.execute(query)
    numbers = res.scalars().all()

    released_count = 0
    now = datetime.now(timezone.utc)
    for num in numbers:
        num.status = "REALLOCATED"
        num.allocation_eligibility = "REALLOCATED"
        num.notes = f"Approved for carrier reallocation by {current_user.email}. {req.notes or ''}"
        num.updated_at = now
        released_count += 1

    await db.commit()

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name="Telecom Operator",
        action="NUMBERS_BATCH_REALLOCATED",
        entity_type="BATCH_REALLOCATION",
        entity_id=f"BATCH-{len(req.number_ids)}",
        details=f"Released {released_count} numbers for telecom subscriber reallocation."
    )

    return {"message": f"Successfully released {released_count} numbers for carrier reallocation", "released_count": released_count}
