"""
NumberGuard — Webhook Events API (Phase 2)
Endpoints for querying webhook delivery history and triggering retries.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.models import User
from app.schemas.schemas import WebhookEventOut
from app.api.deps import get_current_user, require_permission
from app.core.rbac import Permission
from app.services.webhook_service import list_webhook_events, retry_webhook

router = APIRouter()


@router.get("/events", response_model=List[WebhookEventOut])
async def list_webhook_delivery_events(
    provider_id: Optional[str] = None,
    delivery_status: Optional[str] = None,
    direction: Optional[str] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROVIDERS_READ)),
):
    """
    List webhook events (outbound deliveries and inbound callbacks).
    
    Filter by:
    - provider_id: Specific provider
    - delivery_status: PENDING, DELIVERED, FAILED, TIMED_OUT, RETRYING
    - direction: OUTBOUND or INBOUND
    """
    return await list_webhook_events(
        db,
        provider_id=provider_id,
        delivery_status=delivery_status,
        direction=direction,
        skip=skip,
        limit=limit,
    )


@router.post("/retry/{event_id}", response_model=WebhookEventOut)
async def retry_webhook_event(
    event_id: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_permission(Permission.PROVIDERS_WRITE)),
):
    """
    Schedule a failed webhook event for retry.
    Only FAILED or TIMED_OUT events can be retried.
    Increments attempt counter and schedules next_retry_at.
    """
    try:
        event = await retry_webhook(db, event_id)
    except ValueError as e:
        raise HTTPException(status_code=422, detail=str(e))
    return event
