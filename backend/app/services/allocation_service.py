"""
NumberGuard — Allocation Decision Service (Phase 2)
Handles creation and retrieval of final allocation decisions.
"""
import uuid
from datetime import datetime, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import AllocationDecision, MobileNumber, DecommissionedNumber, ProviderNotification
from app.services.risk_engine import calculate_risk


def _gen_decision_number() -> str:
    uid = uuid.uuid4().hex[:8].upper()
    return f"DEC-{uid}"


async def create_allocation_decision(
    db: AsyncSession,
    mobile_number_id: str,
    decision: str,
    decided_by: str,
    decided_by_role: str,
    decision_notes: Optional[str] = None,
    override_justification: Optional[str] = None,
) -> AllocationDecision:
    """
    Creates a final allocation decision for a mobile number.
    Computes current risk context automatically.
    """
    # Fetch mobile number
    res = await db.execute(select(MobileNumber).where(MobileNumber.id == mobile_number_id))
    mobile = res.scalars().first()
    if not mobile:
        raise ValueError(f"MobileNumber {mobile_number_id} not found")

    now = datetime.now(timezone.utc)

    # Try to find linked DecommissionedNumber for risk context
    decomm_res = await db.execute(
        select(DecommissionedNumber).where(DecommissionedNumber.phone_hash == mobile.phone_hash)
    )
    decomm = decomm_res.scalars().first()

    risk_score = 0
    risk_level = "LOW"
    cooling_completed = False
    banking_cleared = False
    all_providers_cleared = False

    if decomm:
        # Re-evaluate notifications
        notif_res = await db.execute(
            select(ProviderNotification).where(ProviderNotification.number_id == decomm.id)
        )
        notifications = notif_res.scalars().all()

        score, level, eligibility, _ = calculate_risk(
            decommissioned_at=decomm.decommissioned_at,
            cooling_end_date=decomm.cooling_end_date,
            notifications=notifications,
            historical_recycles=mobile.total_recycling_count,
        )
        risk_score = score
        risk_level = level
        cooling_completed = now >= decomm.cooling_end_date

        banking_notifs = [n for n in notifications if hasattr(n, "provider") and n.provider and n.provider.category in ("BANKING", "FINTECH")]
        banking_cleared = all(n.status in ("REMEDIATED", "ACKNOWLEDGED") for n in banking_notifs)
        all_providers_cleared = all(n.status in ("REMEDIATED", "ACKNOWLEDGED") for n in notifications)
    else:
        risk_score = 0
        risk_level = "LOW"
        cooling_completed = True
        banking_cleared = True
        all_providers_cleared = True

    dec = AllocationDecision(
        decision_number=_gen_decision_number(),
        mobile_number_id=mobile_number_id,
        decision=decision,
        risk_score_at_decision=risk_score,
        risk_level_at_decision=risk_level,
        cooling_completed=cooling_completed,
        banking_cleared=banking_cleared,
        all_providers_cleared=all_providers_cleared,
        decided_by=decided_by,
        decided_by_role=decided_by_role,
        decision_notes=decision_notes,
        override_justification=override_justification,
        decided_at=now,
    )
    db.add(dec)
    await db.commit()
    await db.refresh(dec)
    return dec


async def list_decisions(
    db: AsyncSession,
    decision_filter: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[AllocationDecision]:
    query = select(AllocationDecision).order_by(AllocationDecision.decided_at.desc())
    if decision_filter:
        query = query.where(AllocationDecision.decision == decision_filter)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
