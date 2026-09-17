from datetime import datetime, timezone
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.models.models import ProviderNotification, DecommissionedNumber, ServiceProvider, User
from app.schemas.schemas import NotificationOut, NotificationAcknowledgeRequest
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.audit import record_audit_log
from app.services.risk_engine import calculate_risk

router = APIRouter()

@router.get("", response_model=List[NotificationOut])
async def list_notifications(
    status: Optional[str] = None,
    provider_id: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NUMBERS_READ))
):
    query = select(ProviderNotification).options(
        selectinload(ProviderNotification.provider),
        selectinload(ProviderNotification.number)
    ).order_by(desc(ProviderNotification.sent_at))

    # Tenant scoping for Service Providers
    if current_user.role in ["SERVICE_PROVIDER_ADMIN", "SERVICE_PROVIDER_OPERATOR"]:
        prov_res = await db.execute(
            select(ServiceProvider).where(
                (ServiceProvider.organization_id == current_user.organization_id) |
                (ServiceProvider.name == (current_user.organization.name if current_user.organization else ""))
            )
        )
        user_provider = prov_res.scalars().first()
        if user_provider:
            query = query.where(ProviderNotification.provider_id == user_provider.id)
        else:
            return []

    # Tenant scoping for Telecom users
    elif current_user.role in ["TELECOM_ADMIN", "TELECOM_OPERATOR"] and current_user.organization_id:
        query = query.join(ProviderNotification.number).where(
            DecommissionedNumber.organization_id == current_user.organization_id
        )

    if status and status != "ALL":
        query = query.where(ProviderNotification.status == status)
    if provider_id and provider_id != "ALL" and current_user.role not in ["SERVICE_PROVIDER_ADMIN", "SERVICE_PROVIDER_OPERATOR"]:
        query = query.where(ProviderNotification.provider_id == provider_id)

    query = query.offset(skip).limit(limit)
    res = await db.execute(query)
    notifications = res.scalars().all()

    out = []
    for n in notifications:
        out.append(NotificationOut(
            id=n.id,
            number_id=n.number_id,
            masked_number=n.number.masked_number if n.number else None,
            provider_id=n.provider_id,
            provider_name=n.provider.name if n.provider else "Unknown",
            provider_category=n.provider.category if n.provider else "GENERAL",
            pseudonym_ref=n.pseudonym_ref,
            notification_type=n.notification_type,
            status=n.status,
            sent_at=n.sent_at,
            acknowledged_at=n.acknowledged_at,
            remediated_at=n.remediated_at,
            retry_count=n.retry_count,
            error_message=n.error_message
        ))
    return out

@router.post("/{id}/acknowledge", response_model=NotificationOut)
async def acknowledge_notification(
    id: str,
    req: NotificationAcknowledgeRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.NOTIFICATIONS_ACKNOWLEDGE))
):
    query = select(ProviderNotification).options(
        selectinload(ProviderNotification.provider),
        selectinload(ProviderNotification.number).selectinload(DecommissionedNumber.notifications)
    ).where(ProviderNotification.id == id)
    res = await db.execute(query)
    notif = res.scalars().first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")

    now = datetime.now(timezone.utc)
    notif.status = req.status
    if not notif.acknowledged_at:
        notif.acknowledged_at = now
    if req.status == "REMEDIATED":
        notif.remediated_at = now
    
    if req.response_payload:
        notif.response_payload = req.response_payload

    # Update provider unresolved count if remediated
    if notif.provider and notif.provider.unresolved_count > 0:
        notif.provider.unresolved_count -= 1

    # Recalculate associated number risk score
    if notif.number:
        score, level, eligibility, _ = calculate_risk(
            decommissioned_at=notif.number.decommissioned_at,
            cooling_end_date=notif.number.cooling_end_date,
            notifications=notif.number.notifications,
            historical_recycles=0
        )
        notif.number.risk_score = score
        notif.number.risk_level = level
        notif.number.allocation_eligibility = eligibility

    await db.commit()
    await db.refresh(notif)

    await record_audit_log(
        db=db,
        actor_email=current_user.email,
        actor_role=current_user.role,
        organization_name=notif.provider.name if notif.provider else "Service Provider",
        action="NOTIFICATION_ACKNOWLEDGED",
        entity_type="NOTIFICATION",
        entity_id=notif.id,
        details=f"Provider marked notification {notif.pseudonym_ref} as {req.status}"
    )

    return NotificationOut(
        id=notif.id,
        number_id=notif.number_id,
        masked_number=notif.number.masked_number if notif.number else None,
        provider_id=notif.provider_id,
        provider_name=notif.provider.name if notif.provider else "Unknown",
        provider_category=notif.provider.category if notif.provider else "GENERAL",
        pseudonym_ref=notif.pseudonym_ref,
        notification_type=notif.notification_type,
        status=notif.status,
        sent_at=notif.sent_at,
        acknowledged_at=notif.acknowledged_at,
        remediated_at=notif.remediated_at,
        retry_count=notif.retry_count,
        error_message=notif.error_message
    )
