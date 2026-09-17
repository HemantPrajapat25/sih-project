"""
NumberGuard — Mock Provider HTTP Endpoints (Phase 3)
Allows testing webhook integration and simulates external third-party provider systems.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from app.adapters.factory import (
    get_provider_adapter,
    get_telecom_adapter,
    get_phone_intel_adapter,
    get_email_adapter,
    reset_all_mock_states,
)

router = APIRouter()


class DecommissionEventPayload(BaseModel):
    provider_name: str
    pseudonym_ref: str
    carrier: str = "Airtel"
    service_category: Optional[str] = "BANKING"
    webhook_url: Optional[str] = None


class TelecomStatusQuery(BaseModel):
    phone_hash: str
    carrier: str = "Airtel"


class EmailSendRequest(BaseModel):
    to_email: str
    subject: str
    body_text: str
    body_html: Optional[str] = None


@router.post("/bank/decommission-event")
async def mock_bank_event(payload: DecommissionEventPayload):
    """
    Simulates Tier-1 Core Banking system receiving a decommission webhook.
    """
    adapter = get_provider_adapter("BANKING")
    res = await adapter.dispatch_decommission_event(
        provider_name=payload.provider_name,
        webhook_url=payload.webhook_url,
        pseudonym_ref=payload.pseudonym_ref,
        carrier=payload.carrier,
        timestamp=datetime.now(timezone.utc),
        service_category="BANKING"
    )
    return res


@router.post("/fintech/decommission-event")
async def mock_fintech_event(payload: DecommissionEventPayload):
    """
    Simulates digital wallet / payment UPI gateway receiving a decommission event.
    """
    adapter = get_provider_adapter("FINTECH")
    res = await adapter.dispatch_decommission_event(
        provider_name=payload.provider_name,
        webhook_url=payload.webhook_url,
        pseudonym_ref=payload.pseudonym_ref,
        carrier=payload.carrier,
        timestamp=datetime.now(timezone.utc),
        service_category="FINTECH"
    )
    return res


@router.post("/ecommerce/decommission-event")
async def mock_ecommerce_event(payload: DecommissionEventPayload):
    """
    Simulates e-commerce / delivery service unlinking phone association.
    """
    adapter = get_provider_adapter("ECOMMERCE")
    res = await adapter.dispatch_decommission_event(
        provider_name=payload.provider_name,
        webhook_url=payload.webhook_url,
        pseudonym_ref=payload.pseudonym_ref,
        carrier=payload.carrier,
        timestamp=datetime.now(timezone.utc),
        service_category="ECOMMERCE"
    )
    return res


@router.post("/telecom/number-status")
async def mock_telecom_status(payload: TelecomStatusQuery):
    """
    Simulates carrier HLR/MSC status lookup.
    """
    adapter = get_telecom_adapter()
    return await adapter.get_number_status(payload.phone_hash, payload.carrier)


@router.get("/phone-intel/lookup/{pseudonym}")
async def mock_phone_intel(pseudonym: str):
    """
    Simulates phone reputation intelligence lookup (spam score, fraud risk).
    """
    adapter = get_phone_intel_adapter()
    return await adapter.lookup_number_signals(pseudonym, pseudonym)


@router.post("/email/send")
async def mock_email_send(req: EmailSendRequest):
    """
    Simulates sending transactional email.
    """
    adapter = get_email_adapter()
    return await adapter.send_email(req.to_email, req.subject, req.body_text, req.body_html)


@router.post("/reset")
async def mock_reset():
    """
    Resets in-memory state of all mock adapters (useful in automated tests).
    """
    reset_all_mock_states()
    return {"status": "ok", "message": "All mock provider states cleared."}
