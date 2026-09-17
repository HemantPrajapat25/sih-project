"""
NumberGuard — Mock Email Provider Adapter (Phase 3)
Simulates transactional email delivery without contacting external SMTP or SendGrid servers.
Stores delivered emails in-memory for testing assertions.
"""
from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from app.adapters.base import EmailAdapter
from app.core.config import settings


class MockEmailProvider(EmailAdapter):
    """
    Mock Email delivery service with in-memory outbox.
    """
    def __init__(self):
        self.outbox: List[Dict[str, Any]] = []

    def clear(self):
        self.outbox.clear()

    async def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None
    ) -> Dict[str, Any]:
        if settings.MOCK_EXTERNAL_SERVICES:
            await asyncio.sleep(settings.SANDBOX_WEBHOOK_LATENCY_MS / 2000.0)

        message_id = f"msg_{abs(hash(to_email + subject + str(len(self.outbox)))) % 1000000:06d}"
        record = {
            "message_id": message_id,
            "to": to_email,
            "subject": subject,
            "body_text": body_text,
            "body_html": body_html,
            "sent_at": datetime.now(timezone.utc).isoformat(),
            "status": "DELIVERED"
        }
        self.outbox.append(record)

        return {
            "status": "DELIVERED",
            "message_id": message_id,
            "adapter": "MOCK_EMAIL"
        }
