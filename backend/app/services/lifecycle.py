"""
NumberGuard — Number Lifecycle State Machine Service (Phase 2)

Formal lifecycle state transitions with event sourcing.
Every transition is recorded in number_lifecycle_events and number_status_history.

State Machine:
  ACTIVE → DECOMMISSIONED → COOLING_HOLD → NOTIFYING_PROVIDERS
                                        ↓            ↓
                                    BLOCKED    MANUAL_REVIEW
                                                    ↓
                                               ELIGIBLE → REALLOCATED
"""
import json
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional, List, Dict, Any, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.models import (
    DecommissionedNumber, CoolingRule, RiskEvaluation,
    MobileNumber, NumberLifecycleEvent, NumberStatusHistory,
    CoolingPeriod
)
from app.core.privacy import compute_phone_hash, mask_phone_number, normalize_phone_number, generate_pseudonym_ref
from app.services.risk_engine import calculate_risk
from app.services.notification import dispatch_notifications_for_number
from app.services.audit import record_audit_log


# ---------------------------------------------------------------------------
# Valid lifecycle state transitions (from → {allowed tos})
# ---------------------------------------------------------------------------
VALID_TRANSITIONS: Dict[str, List[str]] = {
    "ACTIVE":               ["DECOMMISSIONED"],
    "DECOMMISSIONED":       ["COOLING_HOLD"],
    "COOLING_HOLD":         ["NOTIFYING_PROVIDERS", "MANUAL_REVIEW", "ELIGIBLE", "BLOCKED"],
    "NOTIFYING_PROVIDERS":  ["COOLING_HOLD", "MANUAL_REVIEW", "ELIGIBLE", "BLOCKED"],
    "MANUAL_REVIEW":        ["ELIGIBLE", "BLOCKED", "COOLING_HOLD"],
    "ELIGIBLE":             ["REALLOCATED", "BLOCKED", "MANUAL_REVIEW"],
    "BLOCKED":              ["MANUAL_REVIEW"],
    "REALLOCATED":          ["ACTIVE"],   # Number re-enters active state after reallocation
    "DISPUTED":             ["MANUAL_REVIEW", "BLOCKED"],
}

# Maps event_type → expected to_status
EVENT_STATUS_MAP: Dict[str, str] = {
    "NUMBER_DECOMMISSIONED":        "DECOMMISSIONED",
    "COOLING_STARTED":              "COOLING_HOLD",
    "PROVIDER_NOTIFIED":            "NOTIFYING_PROVIDERS",
    "PROVIDER_ACKNOWLEDGED":        "NOTIFYING_PROVIDERS",  # stays in same phase
    "PROVIDER_REMEDIATED":          "NOTIFYING_PROVIDERS",
    "COOLING_EXTENDED":             "COOLING_HOLD",
    "COOLING_COMPLETED":            "ELIGIBLE",
    "MANUAL_REVIEW_TRIGGERED":      "MANUAL_REVIEW",
    "MANUAL_REVIEW_RESOLVED":       "ELIGIBLE",
    "ALLOCATION_APPROVED":          "ELIGIBLE",
    "ALLOCATION_BLOCKED":           "BLOCKED",
    "NUMBER_REALLOCATED":           "REALLOCATED",
    "RISK_SCORE_UPDATED":           None,  # no status change, just record
    "CASE_OPENED":                  None,
    "CASE_CLOSED":                  None,
    "DISPUTE_FILED":                "DISPUTED",
    "DISPUTE_RESOLVED":             "MANUAL_REVIEW",
}


def _gen_correlation_id() -> str:
    return f"CORR-{uuid.uuid4().hex[:16].upper()}"


async def record_lifecycle_event(
    db: AsyncSession,
    mobile_number: MobileNumber,
    event_type: str,
    to_status: str,
    triggered_by: str,
    triggered_by_role: Optional[str] = None,
    notes: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
    correlation_id: Optional[str] = None,
) -> NumberLifecycleEvent:
    """
    Records a lifecycle state transition event and updates status history.
    """
    corr_id = correlation_id or _gen_correlation_id()
    from_status = mobile_number.lifecycle_status

    event = NumberLifecycleEvent(
        mobile_number_id=mobile_number.id,
        event_type=event_type,
        from_status=from_status,
        to_status=to_status,
        triggered_by=triggered_by,
        triggered_by_role=triggered_by_role,
        correlation_id=corr_id,
        payload=json.dumps(payload) if payload else None,
        notes=notes,
        occurred_at=datetime.now(timezone.utc),
    )
    db.add(event)

    # Update status history
    history = NumberStatusHistory(
        mobile_number_id=mobile_number.id,
        previous_status=from_status,
        new_status=to_status,
        change_reason=notes or event_type,
        changed_by=triggered_by,
        changed_at=datetime.now(timezone.utc),
    )
    db.add(history)

    # Apply new status to mobile number
    if to_status != from_status:
        mobile_number.lifecycle_status = to_status
        mobile_number.updated_at = datetime.now(timezone.utc)

    await db.flush()
    return event


async def transition_number_status(
    db: AsyncSession,
    mobile_number_id: str,
    event_type: str,
    triggered_by: str,
    triggered_by_role: Optional[str] = None,
    notes: Optional[str] = None,
    payload: Optional[Dict[str, Any]] = None,
) -> Tuple[MobileNumber, NumberLifecycleEvent]:
    """
    Core state machine transition function.
    Validates the transition, records the event, and updates the number.
    """
    result = await db.execute(
        select(MobileNumber).where(MobileNumber.id == mobile_number_id)
    )
    mobile_number = result.scalars().first()
    if not mobile_number:
        raise ValueError(f"MobileNumber {mobile_number_id} not found")

    to_status = EVENT_STATUS_MAP.get(event_type)
    if to_status is None:
        to_status = mobile_number.lifecycle_status  # no-op status events

    current = mobile_number.lifecycle_status
    allowed = VALID_TRANSITIONS.get(current, [])
    if to_status != current and to_status not in allowed:
        raise ValueError(
            f"Invalid transition: {current} → {to_status} "
            f"(event: {event_type}, allowed: {allowed})"
        )

    event = await record_lifecycle_event(
        db=db,
        mobile_number=mobile_number,
        event_type=event_type,
        to_status=to_status,
        triggered_by=triggered_by,
        triggered_by_role=triggered_by_role,
        notes=notes,
        payload=payload,
    )
    await db.commit()
    await db.refresh(mobile_number)
    return mobile_number, event


async def get_or_create_mobile_number(
    db: AsyncSession,
    phone_hash: str,
    masked_number: str,
    carrier: str,
    organization_id: Optional[str] = None,
    circle: Optional[str] = None,
    number_type: str = "POSTPAID",
) -> MobileNumber:
    """
    Returns existing MobileNumber record or creates a new one.
    Used to maintain cross-cycle history.
    """
    result = await db.execute(
        select(MobileNumber).where(MobileNumber.phone_hash == phone_hash)
    )
    existing = result.scalars().first()
    if existing:
        if organization_id and not existing.organization_id:
            existing.organization_id = organization_id
        return existing

    mobile = MobileNumber(
        phone_hash=phone_hash,
        masked_number=masked_number,
        carrier=carrier,
        organization_id=organization_id,
        circle=circle,
        number_type=number_type,
        lifecycle_status="ACTIVE",
        total_recycling_count=0,
    )
    db.add(mobile)
    await db.flush()
    return mobile


async def create_cooling_period(
    db: AsyncSession,
    mobile_number: MobileNumber,
    cooling_days: int,
    cooling_rule_id: Optional[str] = None,
) -> CoolingPeriod:
    """Creates a new cooling period instance for a mobile number."""
    now = datetime.now(timezone.utc)
    period = CoolingPeriod(
        mobile_number_id=mobile_number.id,
        cooling_rule_id=cooling_rule_id,
        status="ACTIVE",
        started_at=now,
        scheduled_end_at=now + timedelta(days=cooling_days),
        extended_by_days=0,
    )
    db.add(period)
    await db.flush()
    return period


async def ingest_decommissioned_number(
    db: AsyncSession,
    raw_phone: str,
    carrier: str = "Jio",
    organization_id: Optional[str] = None,
    notes: Optional[str] = None,
    custom_cooling_days: Optional[int] = None,
    associated_provider_codes: Optional[List[str]] = None,
    actor_email: str = "system@telecom.operator",
    actor_role: str = "TELECOM_OPERATOR",
    org_name: str = "Telecom Operator",
    circle: Optional[str] = None,
    number_type: str = "POSTPAID",
) -> DecommissionedNumber:
    """
    Ingests a newly decommissioned number.
    - Creates/updates the canonical MobileNumber record
    - Creates the operational DecommissionedNumber record
    - Records lifecycle events
    - Dispatches provider notifications
    - Calculates initial risk assessment
    """
    normalized = normalize_phone_number(raw_phone)
    phone_h = compute_phone_hash(normalized)
    masked = mask_phone_number(normalized)

    # Resolve cooling rule
    cooling_days = custom_cooling_days or 60
    cooling_rule = None
    rule_query = select(CoolingRule).where(
        CoolingRule.is_active == True,
        (CoolingRule.carrier == carrier) | (CoolingRule.carrier == "ALL"),
    )
    rule_res = await db.execute(rule_query)
    rule = rule_res.scalars().first()
    if rule and not custom_cooling_days:
        cooling_days = rule.min_cooling_days
        cooling_rule = rule

    now = datetime.now(timezone.utc)
    cooling_end = now + timedelta(days=cooling_days)

    # --- 1. Canonical mobile number registry ---
    mobile = await get_or_create_mobile_number(
        db, phone_h, masked, carrier, organization_id=organization_id, circle=circle, number_type=number_type
    )
    mobile.total_recycling_count += 1
    mobile.last_decommissioned_at = now

    # Transition: ACTIVE → DECOMMISSIONED
    corr_id = _gen_correlation_id()
    await record_lifecycle_event(
        db=db,
        mobile_number=mobile,
        event_type="NUMBER_DECOMMISSIONED",
        to_status="DECOMMISSIONED",
        triggered_by=actor_email,
        triggered_by_role=actor_role,
        notes=notes or f"Decommissioned by {actor_email} ({carrier})",
        correlation_id=corr_id,
    )

    # --- 2. Create cooling period ---
    await create_cooling_period(
        db, mobile, cooling_days,
        cooling_rule_id=cooling_rule.id if cooling_rule else None,
    )

    # Transition: DECOMMISSIONED → COOLING_HOLD
    await record_lifecycle_event(
        db=db,
        mobile_number=mobile,
        event_type="COOLING_STARTED",
        to_status="COOLING_HOLD",
        triggered_by="SYSTEM",
        triggered_by_role="SYSTEM",
        notes=f"{cooling_days}-day quarantine initiated",
        payload={"cooling_days": cooling_days, "cooling_end": cooling_end.isoformat()},
        correlation_id=corr_id,
    )

    # --- 3. Operational DecommissionedNumber record (backward compat) ---
    number = DecommissionedNumber(
        phone_hash=phone_h,
        masked_number=masked,
        carrier=carrier,
        organization_id=organization_id,
        status="COOLING_HOLD",
        decommissioned_at=now,
        cooling_end_date=cooling_end,
        risk_score=50,
        risk_level="MEDIUM",
        allocation_eligibility="COOLING_HOLD",
        notes=notes,
    )
    db.add(number)
    await db.commit()
    await db.refresh(number)

    # --- 4. Dispatch provider notifications ---
    notifications = await dispatch_notifications_for_number(
        db=db,
        number=number,
        target_provider_codes=associated_provider_codes,
    )

    if notifications:
        await record_lifecycle_event(
            db=db,
            mobile_number=mobile,
            event_type="PROVIDER_NOTIFIED",
            to_status="NOTIFYING_PROVIDERS",
            triggered_by="SYSTEM",
            triggered_by_role="SYSTEM",
            notes=f"Notified {len(notifications)} providers",
            payload={"provider_count": len(notifications)},
            correlation_id=corr_id,
        )

    # --- 5. Calculate initial risk ---
    score, level, eligibility, factors = calculate_risk(
        decommissioned_at=number.decommissioned_at,
        cooling_end_date=number.cooling_end_date,
        notifications=notifications,
        historical_recycles=mobile.total_recycling_count,
    )

    number.risk_score = score
    number.risk_level = level
    number.allocation_eligibility = eligibility

    eval_rec = RiskEvaluation(
        number_id=number.id,
        score=score,
        risk_level=level,
        factor_banking_weight=factors[0]["score_contribution"],
        factor_cooling_weight=factors[1]["score_contribution"],
        factor_sla_weight=factors[2]["score_contribution"],
        factor_velocity_weight=factors[3]["score_contribution"],
        details_json=json.dumps(factors),
        evaluated_at=now,
    )
    db.add(eval_rec)
    await db.commit()
    await db.refresh(number)

    # --- 6. Audit log ---
    await record_audit_log(
        db=db,
        actor_email=actor_email,
        actor_role=actor_role,
        organization_name=org_name,
        action="NUMBER_DECOMMISSIONED",
        entity_type="NUMBER",
        entity_id=number.id,
        details=(
            f"Decommissioned {masked} ({carrier}) | "
            f"{cooling_days}-day quarantine | "
            f"{len(notifications)} provider notifications dispatched | "
            f"Risk: {score}/100 ({level})"
        ),
    )

    return number


async def get_lifecycle_events(
    db: AsyncSession,
    mobile_number_id: str,
    limit: int = 100,
) -> List[NumberLifecycleEvent]:
    """Returns lifecycle event log for a given mobile number."""
    result = await db.execute(
        select(NumberLifecycleEvent)
        .where(NumberLifecycleEvent.mobile_number_id == mobile_number_id)
        .order_by(NumberLifecycleEvent.occurred_at)
        .limit(limit)
    )
    return result.scalars().all()


async def get_status_history(
    db: AsyncSession,
    mobile_number_id: str,
) -> List[NumberStatusHistory]:
    """Returns status history timeline for a given mobile number."""
    result = await db.execute(
        select(NumberStatusHistory)
        .where(NumberStatusHistory.mobile_number_id == mobile_number_id)
        .order_by(NumberStatusHistory.changed_at)
    )
    return result.scalars().all()
