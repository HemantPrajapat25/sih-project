from abc import ABC, abstractmethod
from typing import Dict, Any, List
from datetime import datetime, timezone

class TelecomIngestionAdapter(ABC):
    @abstractmethod
    async def parse_lifecycle_batch(self, raw_data: Any) -> List[Dict[str, Any]]:
        """Parses batch carrier feed into standard decommission records"""
        pass

class StandardTelecomAdapter(TelecomIngestionAdapter):
    """
    Adapter for telecom carrier feeds (CSV, JSON, Webhook)
    """
    async def parse_lifecycle_batch(self, raw_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        normalized = []
        for item in raw_data:
            normalized.append({
                "raw_phone": item.get("phone") or item.get("msisdn") or item.get("raw_phone"),
                "carrier": item.get("carrier", "Jio"),
                "decommissioned_date": item.get("date") or datetime.now(timezone.utc).isoformat(),
                "circle": item.get("circle", "NATIONAL"),
                "plan_type": item.get("type", "PREPAID")
            })
        return normalized

telecom_adapter = StandardTelecomAdapter()
