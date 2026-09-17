"""
NumberGuard — Twilio Phone Intelligence Adapter (Phase 3)
Optional real provider integrating with Twilio Lookup v2 API.
Gated by settings.PHONE_LOOKUP_PROVIDER == "twilio" and credentials presence.
"""
from __future__ import annotations

from typing import Dict, Any, Optional
import httpx

from app.adapters.base import PhoneIntelligenceAdapter
from app.core.config import settings


class TwilioPhoneIntelAdapter(PhoneIntelligenceAdapter):
    """
    Twilio Lookup API integration for line type, carrier, and SIM-swap risk intelligence.
    Note: Twilio lookup requires E.164. In privacy mode, if raw number is withheld,
    this adapter flags that direct external lookup is skipped or queries partner cache.
    """
    def __init__(self, account_sid: Optional[str] = None, auth_token: Optional[str] = None):
        self.account_sid = account_sid or settings.TWILIO_ACCOUNT_SID
        self.auth_token = auth_token or settings.TWILIO_AUTH_TOKEN
        self.base_url = "https://lookups.twilio.com/v2/PhoneNumbers"

    async def lookup_number_signals(
        self,
        phone_hash: str,
        pseudonym_ref: Optional[str] = None
    ) -> Dict[str, Any]:
        if not self.account_sid or not self.auth_token:
            # Fallback if credentials not populated
            return {
                "spam_score": 0.0,
                "fraud_score": 0.0,
                "line_type": "mobile",
                "carrier_name": "TwilioLookup (Unconfigured)",
                "risk_flags": ["TWILIO_NOT_CONFIGURED_FALLBACK"],
                "valid": True
            }

        # Query Twilio API
        lookup_target = pseudonym_ref or phone_hash
        url = f"{self.base_url}/{lookup_target}?Fields=line_type_intelligence,sim_swap"
        try:
            async with httpx.AsyncClient(auth=(self.account_sid, self.auth_token), timeout=5.0) as client:
                res = await client.get(url)
                if res.status_code == 200:
                    data = res.json()
                    lt = data.get("line_type_intelligence", {})
                    sim = data.get("sim_swap", {})
                    flags = []
                    if sim.get("swapped_period"):
                        flags.append("RECENT_SIM_SWAP_DETECTED")
                    return {
                        "spam_score": 0.1,
                        "fraud_score": 0.8 if flags else 0.1,
                        "line_type": lt.get("type", "mobile"),
                        "carrier_name": lt.get("carrier_name", "Unknown"),
                        "risk_flags": flags,
                        "valid": data.get("valid", True)
                    }
                else:
                    return {
                        "spam_score": 0.0,
                        "fraud_score": 0.0,
                        "line_type": "mobile",
                        "carrier_name": "Unknown",
                        "risk_flags": [f"LOOKUP_HTTP_{res.status_code}"],
                        "valid": False
                    }
        except Exception as e:
            return {
                "spam_score": 0.0,
                "fraud_score": 0.0,
                "line_type": "mobile",
                "carrier_name": "Unknown",
                "risk_flags": [f"LOOKUP_ERROR_{str(e)[:30]}"],
                "valid": False
            }
