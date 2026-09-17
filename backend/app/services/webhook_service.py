"""
NumberGuard — Webhook Event Service (Phase 2)
Tracks outbound webhook deliveries and inbound provider callbacks.
"""
import json
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models.models import WebhookEvent


def calculate_next_retry(attempt: int, base_delay_sec: int = 300) -> datetime:
    """
    Pure helper: compute next_retry_at using exponential backoff.
    next_retry = now + base_delay * 2^(attempt-1), capped at 6 hours.
    Exported so it can be unit-tested independently.
    """
    import math
    cap_sec = 6 * 3600
    delay = min(base_delay_sec * (2 ** (attempt - 1)), cap_sec)
    return datetime.now(timezone.utc) + timedelta(seconds=delay)


async def record_webhook_event(
    db: AsyncSession,
    event_type: str,
    provider_id: Optional[str] = None,
    notification_id: Optional[str] = None,
    direction: str = "OUTBOUND",
    target_url: Optional[str] = None,
    request_payload: Optional[dict] = None,
    response_payload: Optional[dict] = None,
    http_status_code: Optional[int] = None,
    latency_ms: Optional[int] = None,
    delivery_status: str = "PENDING",
    error_message: Optional[str] = None,
    attempt_number: int = 1,
) -> WebhookEvent:
    """Records a webhook delivery event."""
    event = WebhookEvent(
        direction=direction,
        provider_id=provider_id,
        notification_id=notification_id,
        event_type=event_type,
        target_url=target_url,
        http_method="POST",
        request_payload=json.dumps(request_payload) if request_payload else None,
        response_payload=json.dumps(response_payload) if response_payload else None,
        http_status_code=http_status_code,
        latency_ms=latency_ms,
        delivery_status=delivery_status,
        attempt_number=attempt_number,
        next_retry_at=(
            datetime.now(timezone.utc) + timedelta(minutes=5 * attempt_number)
            if delivery_status == "FAILED" else None
        ),
        error_message=error_message,
        triggered_at=datetime.now(timezone.utc),
    )
    db.add(event)
    await db.flush()
    return event


async def retry_webhook(
    db: AsyncSession,
    webhook_event_id: str,
) -> WebhookEvent:
    """Marks a failed webhook for retry (increments attempt counter)."""
    res = await db.execute(select(WebhookEvent).where(WebhookEvent.id == webhook_event_id))
    event = res.scalars().first()
    if not event:
        raise ValueError(f"WebhookEvent {webhook_event_id} not found")
    if event.delivery_status not in ("FAILED", "TIMED_OUT"):
        raise ValueError(f"Only FAILED/TIMED_OUT events can be retried (current: {event.delivery_status})")

    event.delivery_status = "RETRYING"
    event.attempt_number += 1
    event.next_retry_at = datetime.now(timezone.utc) + timedelta(minutes=5 * event.attempt_number)
    await db.commit()
    await db.refresh(event)
    return event


async def list_webhook_events(
    db: AsyncSession,
    provider_id: Optional[str] = None,
    delivery_status: Optional[str] = None,
    direction: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[WebhookEvent]:
    query = select(WebhookEvent).order_by(WebhookEvent.triggered_at.desc())
    if provider_id:
        query = query.where(WebhookEvent.provider_id == provider_id)
    if delivery_status:
        query = query.where(WebhookEvent.delivery_status == delivery_status)
    if direction:
        query = query.where(WebhookEvent.direction == direction)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    return result.scalars().all()
