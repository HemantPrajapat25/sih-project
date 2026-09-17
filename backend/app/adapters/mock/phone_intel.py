"""
NumberGuard — Mock Phone Intelligence Provider (Phase 3)
Simulates carrier lookup & risk intelligence (like Twilio Lookup v2, Telesign, Ekata).
Generates deterministic, privacy-preserving reputation signals from phone_hash.
"""
from __future__ import annotations

import asyncio
from typing import Dict, Any, Optional

from app.adapters.base import PhoneIntelligenceAdapter
from app.core.config import settings


class MockPhoneIntelligenceProvider(PhoneIntelligenceAdapter):
    """
    Mock Phone Intelligence Adapter.
    Uses deterministic hashing on phone_hash to produce reproducible test signals.
    """
    def __init__(self):
        # Override dict to allow explicit test case mocking
        self._overrides: Dict[str, Dict[str, Any]] = {}

    def set_override(self, phone_hash: str, signals: Dict[str, Any]):
        """Sets a test fixture override for a specific phone hash."""
        self._overrides[phone_hash] = signals

    def clear_overrides(self):
        self._overrides.clear()

    async def lookup_number_signals(
        self,
        phone_hash: str,
        pseudonym_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 2000.0)

        # Check explicit test override
        if phone_hash in self._overrides:
            return self._overrides[phone_hash]

        # Deterministic simulation from hash integer
        h_val = int(phone_hash[:8], 16) if len(phone_hash) >= 8 else hash(phone_hash)
        spam_mod = (h_val % 100) / 100.0
        fraud_mod = ((h_val // 100) % 100) / 100.0

        risk_flags = []
        if spam_mod > 0.6:
            risk_flags.append("HIGH_ROBOCALL_VOLUME")
        if fraud_mod > 0.6:
            risk_flags.append("SIM_SWAP_RECENT")
        if fraud_mod > 0.8:
            risk_flags.append("SUSPECTED_FINANCIAL_FRAUD_RING")

        line_types = ["mobile", "mobile", "mobile", "voip", "landline"]
        line_type = line_types[h_val % len(line_types)]

        carrier_names = ["Airtel India", "Jio Infocomm", "Vodafone Idea", "BSNL", "Verizon Wireless"]
        carrier_name = carrier_names[h_val % len(carrier_names)]

        return {
            "spam_score": round(spam_mod, 2),
            "fraud_score": round(fraud_mod, 2),
            "line_type": line_type,
            "carrier_name": carrier_name,
            "risk_flags": risk_flags,
            "valid": True
        }
