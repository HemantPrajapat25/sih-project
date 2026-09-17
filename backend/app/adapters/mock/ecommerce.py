"""
NumberGuard — Mock E-Commerce Adapter (Phase 3)
Simulates e-commerce and delivery platforms (e.g. Amazon, Flipkart, Uber, Swiggy).
72h SLA, address book phone updates, unlinking order notification channels.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.adapters.base import DigitalServiceProviderAdapter
from app.core.config import settings


class MockEcommerceProvider(DigitalServiceProviderAdapter):
    """
    Mock E-Commerce adapter with 72h unlinking SLA.
    """
    def __init__(self):
        self._tickets: Dict[str, Dict[str, Any]] = {}

    def reset_state(self):
        self._tickets.clear()

    async def dispatch_decommission_event(
        self,
        provider_name: str,
        webhook_url: Optional[str],
        pseudonym_ref: str,
        carrier: str,
        timestamp: datetime,
        service_category: str = "ECOMMERCE"
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        ticket_id = f"ECM-TKT-{abs(hash(pseudonym_ref)) % 900000 + 100000}"
        sla_deadline = timestamp + timedelta(hours=72)

        record = {
            "ticket": ticket_id,
            "provider": provider_name,
            "pseudonym_ref": pseudonym_ref,
            "carrier": carrier,
            "status": "IN_PROGRESS",
            "sla_deadline": sla_deadline.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actions_queued": [
                "Unbind phone from primary delivery address book",
                "Disable SMS OTP login; require email link sign-in",
                "Mask phone in order fulfillment notifications",
            ]
        }
        self._tickets[ticket_id] = record

        response_body = {
            "ack": True,
            "provider": provider_name,
            "category": "ECOMMERCE",
            "remediation_ticket": ticket_id,
            "sla_hours": 72,
            "remediation_status": "IN_PROGRESS",
            "message": "E-Commerce decommission event queued. Account communication channels updated.",
            "received_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "status": "SENT",
            "ack": True,
            "remediation_ticket": ticket_id,
            "response_payload": json.dumps(response_body),
            "http_status": 200,
            "adapter": "MOCK_ECOMMERCE"
        }

    async def check_remediation_status(
        self,
        provider_name: str,
        remediation_ticket: str
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        ticket = self._tickets.get(remediation_ticket)
        if not ticket:
            return {
                "ticket": remediation_ticket,
                "status": "COMPLETED",
                "resolved_at": datetime.now(timezone.utc).isoformat(),
                "details": "Customer profile decoupled from retired phone number."
            }

        return {
            "ticket": remediation_ticket,
            "status": ticket.get("status", "COMPLETED"),
            "resolved_at": ticket.get("resolved_at", datetime.now(timezone.utc).isoformat()),
            "details": "E-Commerce unlinking complete; customer notified via email."
        }

    def simulate_resolution(self, ticket_id: str):
        if ticket_id in self._tickets:
            self._tickets[ticket_id]["status"] = "COMPLETED"
            self._tickets[ticket_id]["resolved_at"] = datetime.now(timezone.utc).isoformat()
