"""
NumberGuard — Inbound Webhook Infrastructure (Phase 3)
Secure inbound webhook endpoint for receiving provider unlinking acknowledgments and remediation callbacks.
Features:
- HMAC-SHA256 verification (X-Signature-256)
- Replay attack mitigation via timestamp drift checks (X-Timestamp within ±300s)
- Idempotency deduplication via event_id
- Updates ProviderNotification & ProviderNumberAssociation
- Triggers risk recalculation for the affected number
"""
from __future__ import annotations

import hmac
import hashlib
import json
import time
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Request, Header, HTTPException, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.db.session import get_db
from app.core.config import settings
from app.models.models import (
    WebhookEvent,
    ProviderNotification,
    ProviderNumberAssociation,
    ServiceProvider,
    DecommissionedNumber,
)
from app.services.risk.assessment import RiskAssessmentService

router = APIRouter()


def verify_hmac_signature(body: bytes, signature_header: Optional[str], secret: str) -> bool:
    """Verifies HMAC-SHA256 signature of request body."""
    if not signature_header:
        return False
    # Signature header could be "sha256=<hex>" or just "<hex>"
    clean_sig = signature_header.replace("sha256=", "").strip()
    expected = hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(clean_sig, expected)


@router.post("/inbound")
async def receive_provider_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_signature_256: Optional[str] = Header(None, alias="X-Signature-256"),
    x_timestamp: Optional[str] = Header(None, alias="X-Timestamp"),
):
    """
    Receives unlinking status callbacks from external digital service providers.
    Enforces HMAC-SHA256 signature, replay prevention, and idempotency.
    """
    body_bytes = await request.body()

    # 1. Replay prevention: timestamp validation
    if x_timestamp:
        try:
            ts = float(x_timestamp)
            current_time = time.time()
            if abs(current_time - ts) > 300:  # 5 minutes drift allowed
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Webhook timestamp outside allowable window (replay prevention)"
                )
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid X-Timestamp header")

    # 2. HMAC verification (if secret configured or signature provided)
    if settings.WEBHOOK_HMAC_SECRET:
        if not verify_hmac_signature(body_bytes, x_signature_256, settings.WEBHOOK_HMAC_SECRET):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or missing HMAC signature (X-Signature-256)"
            )

    # 3. Parse payload
    try:
        payload = json.loads(body_bytes.decode("utf-8"))
    except Exception:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid JSON payload")

    event_id = payload.get("event_id") or payload.get("remediation_ticket")
    event_type = payload.get("event_type", "UNLINK_STATUS_UPDATE")
    provider_slug = payload.get("provider_slug")
    pseudonym_ref = payload.get("pseudonym_ref")
    action_status = payload.get("status", "REMEDIATED")  # ACKNOWLEDGED, REMEDIATED, FAILED

    # 4. Idempotency check
    if event_id:
        stmt = select(WebhookEvent).where(
            WebhookEvent.direction == "INBOUND",
            WebhookEvent.id == event_id
        )
        existing = (await db.execute(stmt)).scalar_one_or_none()
        if existing:
            return {"status": "ok", "message": "Duplicate event ignored (idempotent)", "event_id": event_id}

    # 5. Log inbound webhook event
    webhook_log = WebhookEvent(
        id=event_id if event_id and len(event_id) <= 36 else None,
        direction="INBOUND",
        event_type=event_type,
        target_url=str(request.url),
        http_method="POST",
        request_payload=body_bytes.decode("utf-8")[:2000],
        delivery_status="DELIVERED",
        http_status_code=200,
        triggered_at=datetime.now(timezone.utc)
    )
    db.add(webhook_log)

    # 6. Update ProviderNotification & Association if found
    updated_notifications = 0
    updated_associations = 0

    if pseudonym_ref:
        # Match notifications
        stmt_notif = select(ProviderNotification).where(
            ProviderNotification.pseudonym_ref == pseudonym_ref
        )
        notifs = (await db.execute(stmt_notif)).scalars().all()
        for notif in notifs:
            if action_status in ("REMEDIATED", "COMPLETED", "SUCCESS"):
                notif.status = "REMEDIATED"
                notif.remediated_at = datetime.now(timezone.utc)
            elif action_status in ("ACKNOWLEDGED", "IN_PROGRESS"):
                notif.status = "ACKNOWLEDGED"
                notif.acknowledged_at = datetime.now(timezone.utc)
            updated_notifications += 1

        # Match associations
        stmt_assoc = select(ProviderNumberAssociation).where(
            ProviderNumberAssociation.pseudonym_token == pseudonym_ref
        )
        assocs = (await db.execute(stmt_assoc)).scalars().all()
        for assoc in assocs:
            if action_status in ("REMEDIATED", "COMPLETED", "SUCCESS"):
                assoc.association_status = "UNLINKED"
                assoc.unlinked_at = datetime.now(timezone.utc)
                updated_associations += 1

        await db.commit()

        # 7. Trigger risk recalculation if number exists
        stmt_num = select(DecommissionedNumber).where(
            DecommissionedNumber.phone_hash == pseudonym_ref
        )
        num_row = (await db.execute(stmt_num)).scalar_one_or_none()
        if num_row:
            try:
                assessment = await RiskAssessmentService(db).assess(
                    number=num_row,
                    triggered_by="WEBHOOK_CALLBACK"
                )
                num_row.risk_score = assessment.score
                await db.commit()
            except Exception:
                pass

    return {
        "status": "ok",
        "event_type": event_type,
        "action_status": action_status,
        "updated_notifications": updated_notifications,
        "updated_associations": updated_associations,
        "processed_at": datetime.now(timezone.utc).isoformat()
    }
