"""
NumberGuard — Mock Telecom Switch Adapter (Phase 3)
Simulates Telecom HLR (Home Location Register) / MSC interfaces:
- Query network status
- Quarantine lock
- Pool release
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any

from app.adapters.base import TelecomProviderAdapter
from app.core.config import settings


class MockTelecomProvider(TelecomProviderAdapter):
    """
    Mock Telecom adapter simulating network switch operations.
    """
    def __init__(self):
        self._quarantined_hashes: set[str] = set()

    def reset_state(self):
        self._quarantined_hashes.clear()

    async def get_number_status(
        self,
        phone_hash: str,
        carrier: str
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        is_quarantined = phone_hash in self._quarantined_hashes
        return {
            "phone_hash": phone_hash,
            "carrier": carrier,
            "hlr_state": "QUARANTINED" if is_quarantined else "DISCONNECTED",
            "ims_provisioned": False,
            "sim_icc_status": "DEACTIVATED",
            "last_active_mcc_mnc": "404-45",
            "switch_response": "200_HLR_OK"
        }

    async def notify_quarantine_start(
        self,
        phone_hash: str,
        carrier: str,
        cooling_days: int
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        self._quarantined_hashes.add(phone_hash)
        return {
            "status": "SUCCESS",
            "carrier": carrier,
            "phone_hash": phone_hash,
            "cooling_days": cooling_days,
            "action": "HLR_MSISDN_BARRED_FOR_REALLOCATION",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }

    async def notify_release(
        self,
        phone_hash: str,
        carrier: str
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)

        self._quarantined_hashes.discard(phone_hash)
        return {
            "status": "SUCCESS",
            "carrier": carrier,
            "phone_hash": phone_hash,
            "action": "HLR_MSISDN_UNBARRED_RETURNED_TO_POOL",
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
