"""
NumberGuard — Base Adapter Interfaces (Phase 3)
Defines abstract contracts for third-party integrations and external services.
No provider-specific logic here; all adapters implement these interfaces.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from datetime import datetime


class DigitalServiceProviderAdapter(ABC):
    """
    Interface for dispatching decommission lifecycle notifications to
    digital service providers (banks, fintechs, e-commerce, aggregators).
    """

    @abstractmethod
    async def dispatch_decommission_event(
        self,
        provider_name: str,
        webhook_url: Optional[str],
        pseudonym_ref: str,
        carrier: str,
        timestamp: datetime,
        service_category: str = "GENERAL"
    ) -> Dict[str, Any]:
        """
        Dispatches decommission event to provider.
        Returns:
            {
                "status": "SENT" | "FAILED" | "PENDING",
                "ack": bool,
                "remediation_ticket": Optional[str],
                "response_payload": str,
                "http_status": Optional[int],
                "adapter": str
            }
        """
        pass

    @abstractmethod
    async def check_remediation_status(
        self,
        provider_name: str,
        remediation_ticket: str
    ) -> Dict[str, Any]:
        """
        Polls or checks remediation status of an unlinking ticket.
        Returns:
            {
                "ticket": str,
                "status": "COMPLETED" | "IN_PROGRESS" | "FAILED" | "PENDING",
                "resolved_at": Optional[str],
                "details": str
            }
        """
        pass


class TelecomProviderAdapter(ABC):
    """
    Interface for telecom network / HLR / billing interactions.
    """

    @abstractmethod
    async def get_number_status(
        self,
        phone_hash: str,
        carrier: str
    ) -> Dict[str, Any]:
        """
        Queries carrier network status for number (HLR active, suspended, disconnected).
        """
        pass

    @abstractmethod
    async def notify_quarantine_start(
        self,
        phone_hash: str,
        carrier: str,
        cooling_days: int
    ) -> Dict[str, Any]:
        """
        Notifies telecom switch/HLR that quarantine cooling period has started.
        """
        pass

    @abstractmethod
    async def notify_release(
        self,
        phone_hash: str,
        carrier: str
    ) -> Dict[str, Any]:
        """
        Notifies telecom switch that number is approved for reallocation pool.
        """
        pass


class EmailAdapter(ABC):
    """
    Interface for transactional notification emails.
    """

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Sends an email notification (e.g. alerts to security/compliance teams).
        """
        pass


class PhoneIntelligenceAdapter(ABC):
    """
    Interface for telecom & threat intelligence reputation lookup.
    Never exposes raw PII; operates on hash or pseudonym.
    """

    @abstractmethod
    async def lookup_number_signals(
        self,
        phone_hash: str,
        pseudonym_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Retrieves reputation, spam score, line type, and fraud risk signals.
        Returns:
            {
                "spam_score": float,       # 0.0 to 1.0
                "fraud_score": float,      # 0.0 to 1.0
                "line_type": str,          # "mobile" | "voip" | "landline" | "toll-free"
                "carrier_name": str,
                "risk_flags": list[str],
                "valid": bool
            }
        """
        pass
