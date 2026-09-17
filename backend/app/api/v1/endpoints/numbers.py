from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import DecommissionedNumber, ProviderNotification, ServiceProvider, AuditLog, User, RiskEvaluation
from app.schemas.schemas import (
    NumberOut,
    NumberDetailOut,
    NumberCreate,
    NumberImportRequest,
    NumberImportResponse,
    NumberStatusUpdate,
    NotificationBrief,
    RiskFactorBreakdown,
    AuditLogOut
)
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.lifecycle import ingest_decommissioned_number
from app.services.risk_engine import calculate_risk
from app.services.audit import record_audit_log

router = APIRouter()

@router.get("", response_model=List[NumberOut])
async def list_numbers(
    search: Optional[str] = None,
    carrier: Optional[str] = None,
    status: Optional[str] = None,
    risk_level: Optional[str] = None,
    eligibility: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    # Service providers cannot browse raw telecom number queues directly
    if current_user.role in ["SERVICE_PROVIDER_ADMIN", "SERVICE_PROVIDER_OPERATOR"]:
        raise HTTPException(
            status_code=403,
            detail="Service providers must access assigned disassociation cases via the Provider Portal."
        )

    query = select(DecommissionedNumber).options(
        selectinload(DecommissionedNumber.notifications)
    ).order_by(desc(DecommissionedNumber.created_at))

    # Tenant scoping for Telecom users
    if current_user.role in ["TELECOM_ADMIN", "TELECOM_OPERATOR"] and current_user.organization_id:
        query = query.where(DecommissionedNumber.organization_id == current_user.organization_id)

    if search:
        query = query.where(DecommissionedNumber.masked_number.ilike(f"%{search}%"))
    if carrier and carrier != "ALL":
        query = query.where(DecommissionedNumber.carrier == carrier)
    if status and status != "ALL":
        query = query.where(DecommissionedNumber.status == status)
    if risk_level and risk_level != "ALL":
        query = query.where(DecommissionedNumber.risk_level == risk_level)
    if eligibility and eligibility != "ALL":
        query = query.where(DecommissionedNumber.allocation_eligibility == eligibility)

    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    numbers = result.scalars().all()

    out = []
    for num in numbers:
        total_notifs = len(num.notifications)
        remediated_count = sum(1 for n in num.notifications if n.status in ["REMEDIATED", "ACKNOWLEDGED"])
        remediation_pct = round((remediated_count / total_notifs * 100.0), 1) if total_notifs > 0 else 100.0

        out.append(NumberOut(
            id=num.id,
            masked_number=num.masked_number,
            carrier=num.carrier,
            status=num.status,
            decommissioned_at=num.decommissioned_at,
            cooling_end_date=num.cooling_end_date,
            risk_score=num.risk_score,
            risk_level=num.risk_level,
            allocation_eligibility=num.allocation_eligibility,
            provider_count=total_notifs,
            remediation_percentage=remediation_pct,
            hold_reason=num.hold_reason,
            created_at=num.created_at,
            updated_at=num.updated_at or num.created_at
        ))
    return out

@router.get("/{id}", response_model=NumberDetailOut)
async def get_number_detail(
    id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    if current_user.role in ["SERVICE_PROVIDER_ADMIN", "SERVICE_PROVIDER_OPERATOR"]:
        raise HTTPException(
            status_code=403,
            detail="Service providers must access assigned disassociation cases via the Provider Portal."
        )

    query = select(DecommissionedNumber).options(
        selectinload(DecommissionedNumber.notifications).selectinload(ProviderNotification.provider),
        selectinload(DecommissionedNumber.risk_evaluations)
    ).where(DecommissionedNumber.id == id)
    
    res = await db.execute(query)
    number = res.scalars().first()
    if not number:
        raise HTTPException(status_code=404, detail="Number record not found")

    # Tenant check
    if current_user.role in ["TELECOM_ADMIN", "TELECOM_OPERATOR"] and current_user.organization_id:
        if number.organization_id and number.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied to numbers from other telecom organizations")

    # Fetch audit logs for this number
    audit_res = await db.execute(
        select(AuditLog).where(AuditLog.entity_id == id).order_by(desc(AuditLog.timestamp))
    )
    audit_logs = audit_res.scalars().all()

    total_notifs = len(number.notifications)
    remediated_count = sum(1 for n in number.notifications if n.status in ["REMEDIATED", "ACKNOWLEDGED"])
    remediation_pct = round((remediated_count / total_notifs * 100.0), 1) if total_notifs > 0 else 100.0

    notif_briefs = []
    for n in number.notifications:
        notif_briefs.append(NotificationBrief(
            id=n.id,
            provider_id=n.provider_id,
            provider_name=n.provider.name if n.provider else "Unknown Provider",
            provider_category=n.provider.category if n.provider else "GENERAL",
            pseudonym_ref=n.pseudonym_ref,
            status=n.status,
            sent_at=n.sent_at,
            acknowledged_at=n.acknowledged_at,
            remediated_at=n.remediated_at,
            error_message=n.error_message
        ))

    # Evaluate factors
    _, _, _, factors = calculate_risk(
        decommissioned_at=number.decommissioned_at,
        cooling_end_date=number.cooling_end_date,
        notifications=number.notifications,
        historical_recycles=0
    )

    factor_breakdowns = [
        RiskFactorBreakdown(
            name=f["name"],
            weight=f["weight"],
            score_contribution=f["score_contribution"],
            description=f["description"]
        ) for f in factors
    ]

    audit_outs = [
        AuditLogOut(
            id=a.id,
            actor_email=a.actor_email,
            actor_role=a.actor_role,
            organization_name=a.organization_name,
            action=a.action,
            entity_type=a.entity_type,
            entity_id=a.entity_id,
            correlation_id=a.correlation_id,
            ip_address=a.ip_address,
            result=a.result,
            details=a.details,
            timestamp=a.timestamp
        ) for a in audit_logs
    ]

    return NumberDetailOut(
        id=number.id,
        masked_number=number.masked_number,
        carrier=number.carrier,
        status=number.status,
        decommissioned_at=number.decommissioned_at,
        cooling_end_date=number.cooling_end_date,
        risk_score=number.risk_score,
        risk_level=number.risk_level,
        allocation_eligibility=number.allocation_eligibility,
        provider_count=total_notifs,
        remediation_percentage=remediation_pct,
        hold_reason=number.hold_reason,
        created_at=number.created_at,
        updated_at=number.updated_at or number.created_at,
        notifications=notif_briefs,
        risk_factors=factor_breakdowns,
        audit_events=audit_outs
    )

@router.post("", response_model=NumberOut)
async def create_number(
    req: NumberCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_IMPORT))
):
    org_name = current_user.organization.name if current_user.organization else "Telecom Carrier Ops"
    number = await ingest_decommissioned_number(
        db=db,
        raw_phone=req.raw_phone,
        carrier=req.carrier,
        organization_id=current_user.organization_id,
        notes=req.notes,
        custom_cooling_days=req.custom_cooling_days,
        associated_provider_codes=req.associated_provider_codes,
        actor_email=current_user.email,
        actor_role=current_user.role,
        org_name=org_name
    )
    return NumberOut(
        id=number.id,
        masked_number=number.masked_number,
        carrier=number.carrier,
        status=number.status,
        decommissioned_at=number.decommissioned_at,
        cooling_end_date=number.cooling_end_date,
        risk_score=number.risk_score,
        risk_level=number.risk_level,
        allocation_eligibility=number.allocation_eligibility,
        provider_count=0,
        remediation_percentage=0.0,
        hold_reason=number.hold_reason,
        created_at=number.created_at,
        updated_at=number.updated_at or number.created_at
    )

@router.post("/import", response_model=NumberImportResponse)
async def import_numbers(
    req: NumberImportRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_IMPORT))
):
    successful = 0
    failed = 0
    errors = []
    org_name = current_user.organization.name if current_user.organization else "Telecom Import System"

    for item in req.numbers:
        try:
            await ingest_decommissioned_number(
                db=db,
                raw_phone=item.raw_phone,
                carrier=item.carrier,
                organization_id=current_user.organization_id,
                notes=item.notes,
                custom_cooling_days=item.custom_cooling_days,
                associated_provider_codes=item.associated_provider_codes,
                actor_email=current_user.email,
                actor_role=current_user.role,
                org_name=org_name
            )
            successful += 1
        except Exception as e:
            failed += 1
            errors.append(f"Failed to ingest: {str(e)}")

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name=org_name,
        action="BATCH_NUMBERS_IMPORTED",
        entity_type="BATCH",
        entity_id="IMPORT-JOB",
        details=f"Batch processed {len(req.numbers)} numbers: {successful} successful, {failed} failed"
    )

    return NumberImportResponse(
        total_processed=len(req.numbers),
        successful_count=successful,
        failed_count=failed,
        errors=errors[:10]
    )

@router.patch("/{id}", response_model=NumberOut)
async def update_number_status(
    id: str,
    req: NumberStatusUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_UPDATE))
):
    res = await db.execute(select(DecommissionedNumber).where(DecommissionedNumber.id == id))
    number = res.scalars().first()
    if not number:
        raise HTTPException(status_code=404, detail="Number not found")

    if current_user.role in ["TELECOM_ADMIN", "TELECOM_OPERATOR"] and current_user.organization_id:
        if number.organization_id and number.organization_id != current_user.organization_id:
            raise HTTPException(status_code=403, detail="Access denied to modify numbers from other organizations")

    if req.status:
        number.status = req.status
    if req.allocation_eligibility:
        number.allocation_eligibility = req.allocation_eligibility
    if req.hold_reason is not None:
        number.hold_reason = req.hold_reason
    if req.notes is not None:
        number.notes = req.notes

    number.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(number)

    org_name = current_user.organization.name if current_user.organization else "Telecom Operator"
    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name=org_name,
        action="NUMBER_STATUS_UPDATED",
        entity_type="NUMBER",
        entity_id=number.id,
        details=f"Updated status to {number.status}, eligibility to {number.allocation_eligibility}"
    )

    return NumberOut(
        id=number.id,
        masked_number=number.masked_number,
        carrier=number.carrier,
        status=number.status,
        decommissioned_at=number.decommissioned_at,
        cooling_end_date=number.cooling_end_date,
        risk_score=number.risk_score,
        risk_level=number.risk_level,
        allocation_eligibility=number.allocation_eligibility,
        hold_reason=number.hold_reason,
        created_at=number.created_at,
        updated_at=number.updated_at
    )
