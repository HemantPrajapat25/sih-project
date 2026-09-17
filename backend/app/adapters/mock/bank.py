"""
NumberGuard — Mock Bank Provider Adapter (Phase 3)
Simulates a Tier-1 Bank (e.g., HDFC, SBI, Chase) with core banking unlinking SLA (48h).
Maintains in-memory state of tickets for sandbox testing.
"""
from __future__ import annotations

import asyncio
import json
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional

from app.adapters.base import DigitalServiceProviderAdapter
from app.core.config import settings


class MockBankProvider(DigitalServiceProviderAdapter):
    """
    Mock Bank adapter with 48h SLA unlinking simulation and realistic compliance responses.
    """
    def __init__(self):
        # In-memory ticket store for mock persistence
        self._tickets: Dict[str, Dict[str, Any]] = {}

    def reset_state(self):
        """Clears test tickets."""
        self._tickets.clear()

    async def dispatch_decommission_event(
        self,
        provider_name: str,
        webhook_url: Optional[str],
        pseudonym_ref: str,
        carrier: str,
        timestamp: datetime,
        service_category: str = "BANKING"
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        ticket_id = f"BNK-TKT-{abs(hash(pseudonym_ref)) % 900000 + 100000}"
        sla_deadline = timestamp + timedelta(hours=48)

        record = {
            "ticket": ticket_id,
            "provider": provider_name,
            "pseudonym_ref": pseudonym_ref,
            "carrier": carrier,
            "status": "IN_PROGRESS",
            "sla_deadline": sla_deadline.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "actions_queued": [
                "Freeze NetBanking SMS OTP channel",
                "Unlink mobile from primary checking account",
                "Flag for customer step-up verification at ATM/Branch",
            ]
        }
        self._tickets[ticket_id] = record

        response_body = {
            "ack": True,
            "provider": provider_name,
            "category": "BANKING",
            "remediation_ticket": ticket_id,
            "sla_hours": 48,
            "remediation_status": "IN_PROGRESS",
            "message": "Decommission notice acknowledged. NetBanking 2FA disabled; unlinking initiated.",
            "received_at": datetime.now(timezone.utc).isoformat()
        }

        return {
            "status": "SENT",
            "ack": True,
            "remediation_ticket": ticket_id,
            "response_payload": json.dumps(response_body),
            "http_status": 200,
            "adapter": "MOCK_BANK"
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
                "details": "Remediation verified: Mobile successfully detached from banking core."
            }

        return {
            "ticket": remediation_ticket,
            "status": ticket.get("status", "COMPLETED"),
            "resolved_at": ticket.get("resolved_at", datetime.now(timezone.utc).isoformat()),
            "details": "Banking profile unlinked. Primary auth switched to verified backup method."
        }

    def simulate_resolution(self, ticket_id: str):
        """Helper to force mark a ticket as completed for test scenarios."""
        if ticket_id in self._tickets:
            self._tickets[ticket_id]["status"] = "COMPLETED"
            self._tickets[ticket_id]["resolved_at"] = datetime.now(timezone.utc).isoformat()
