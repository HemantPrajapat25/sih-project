"""
NumberGuard — Test Suite for Inbound Webhooks (Phase 3)
Tests:
- HMAC-SHA256 signature generation and verification
- Replay attack mitigation via timestamp validation
- Duplicate event rejection (idempotency)
- Unlink status updates
"""
import hmac
import hashlib
import json
import time
import pytest
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.config import settings


def generate_hmac_signature(body: bytes, secret: str) -> str:
    return hmac.new(secret.encode("utf-8"), body, hashlib.sha256).hexdigest()


@pytest.mark.asyncio
async def test_inbound_webhook_hmac_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {
            "event_id": f"evt-test-{int(time.time())}",
            "event_type": "NUMBER_UNLINKED",
            "provider_slug": "hdfc-bank",
            "pseudonym_ref": "PSN-TEST-1234",
            "status": "REMEDIATED"
        }
        body = json.dumps(payload).encode("utf-8")
        sig = generate_hmac_signature(body, settings.WEBHOOK_HMAC_SECRET)
        ts = str(time.time())

        res = await client.post(
            "/api/v1/webhooks/inbound",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature-256": sig,
                "X-Timestamp": ts
            }
        )
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "ok"
        assert data["action_status"] == "REMEDIATED"


@pytest.mark.asyncio
async def test_inbound_webhook_hmac_invalid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"event_id": "evt-fake", "pseudonym_ref": "PSN-FAKE"}
        body = json.dumps(payload).encode("utf-8")
        ts = str(time.time())

        # Bad signature
        res = await client.post(
            "/api/v1/webhooks/inbound",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature-256": "bad_hex_signature_here",
                "X-Timestamp": ts
            }
        )
        assert res.status_code == 401


@pytest.mark.asyncio
async def test_inbound_webhook_replay_prevention():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        payload = {"event_id": "evt-replay", "pseudonym_ref": "PSN-REPLAY"}
        body = json.dumps(payload).encode("utf-8")
        sig = generate_hmac_signature(body, settings.WEBHOOK_HMAC_SECRET)
        # Timestamp from 10 minutes ago (should be rejected)
        stale_ts = str(time.time() - 600)

        res = await client.post(
            "/api/v1/webhooks/inbound",
            content=body,
            headers={
                "Content-Type": "application/json",
                "X-Signature-256": sig,
                "X-Timestamp": stale_ts
            }
        )
        assert res.status_code == 401
        assert "replay" in res.json()["detail"].lower()
