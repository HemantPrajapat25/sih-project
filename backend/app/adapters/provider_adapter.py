import asyncio
import json
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime, timezone
import httpx
from app.core.config import settings

class ProviderNotificationAdapter(ABC):
    @abstractmethod
    async def dispatch_decommission_event(
        self,
        provider_name: str,
        webhook_url: Optional[str],
        pseudonym_ref: str,
        carrier: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        """Dispatches event to provider endpoint or sandbox"""
        pass

class SandboxProviderAdapter(ProviderNotificationAdapter):
    """
    Realistic Sandbox adapter simulating digital service provider endpoints.
    Handles webhooks or returns simulated provider acknowledgement without exposing raw data.
    """
    async def dispatch_decommission_event(
        self,
        provider_name: str,
        webhook_url: Optional[str],
        pseudonym_ref: str,
        carrier: str,
        timestamp: datetime
    ) -> Dict[str, Any]:
        payload = {
            "event": "NUMBER_DECOMMISSIONED",
            "reference_id": pseudonym_ref,
            "carrier": carrier,
            "timestamp": timestamp.isoformat(),
            "cooling_mode": "STANDARD_QUARANTINE",
            "instructions": "Revoke active session tokens, unlink unverified recovery methods, and mark profile on hold."
        }

        # If real webhook URL provided and not in mock mode, attempt HTTP post
        if webhook_url and not settings.MOCK_EXTERNAL_SERVICES:
            try:
                async with httpx.AsyncClient(timeout=5.0) as client:
                    resp = await client.post(webhook_url, json=payload)
                    return {
                        "status": "SENT" if resp.status_code < 400 else "FAILED",
                        "response_payload": resp.text[:500],
                        "http_status": resp.status_code,
                        "adapter": "LIVE_HTTP_WEBHOOK"
                    }
            except Exception as e:
                return {
                    "status": "FAILED",
                    "error_message": str(e),
                    "adapter": "LIVE_HTTP_WEBHOOK"
                }

        # Sandbox Mock Behavior: simulate network latency and return valid ack
        await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 1000.0)
        return {
            "status": "SENT",
            "response_payload": json.dumps({
                "provider": provider_name,
                "ack": True,
                "remediation_ticket": f"REM-{pseudonym_ref[-8:]}",
                "simulated_action": "Subscription queued for unlinking within 24h SLA",
                "received_at": datetime.now(timezone.utc).isoformat()
            }),
            "adapter": "SANDBOX_MOCK"
        }

provider_adapter = SandboxProviderAdapter()
