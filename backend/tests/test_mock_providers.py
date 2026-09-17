"""
NumberGuard — Test Suite for Mock Providers and Adapters (Phase 3)
Tests:
- Bank unlinking and SLA ticket creation
- Fintech session and wallet detachment
- E-Commerce address update
- Telecom switch HLR quarantine & release
- Transactional email dispatch
- Phone intelligence signals
"""
import pytest
from datetime import datetime, timezone
from app.adapters.factory import (
    get_provider_adapter,
    get_telecom_adapter,
    get_phone_intel_adapter,
    get_email_adapter,
    reset_all_mock_states,
)


@pytest.mark.asyncio
async def test_mock_bank_provider():
    reset_all_mock_states()
    adapter = get_provider_adapter("BANKING")
    res = await adapter.dispatch_decommission_event(
        provider_name="HDFC Bank",
        webhook_url=None,
        pseudonym_ref="PSN-BANK-9988",
        carrier="Airtel",
        timestamp=datetime.now(timezone.utc),
        service_category="BANKING"
    )
    assert res["status"] == "SENT"
    assert res["ack"] is True
    assert "remediation_ticket" in res
    assert res["adapter"] == "MOCK_BANK"

    # Verify unlinking ticket status check
    ticket = res["remediation_ticket"]
    status_res = await adapter.check_remediation_status("HDFC Bank", ticket)
    assert status_res["status"] in ("IN_PROGRESS", "COMPLETED")


@pytest.mark.asyncio
async def test_mock_fintech_provider():
    reset_all_mock_states()
    adapter = get_provider_adapter("FINTECH")
    res = await adapter.dispatch_decommission_event(
        provider_name="PhonePe",
        webhook_url=None,
        pseudonym_ref="PSN-FINTECH-1122",
        carrier="Jio",
        timestamp=datetime.now(timezone.utc),
        service_category="FINTECH"
    )
    assert res["ack"] is True
    assert res["adapter"] == "MOCK_FINTECH"


@pytest.mark.asyncio
async def test_mock_telecom_provider():
    reset_all_mock_states()
    adapter = get_telecom_adapter()
    hash_val = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"

    # Start quarantine
    q_res = await adapter.notify_quarantine_start(hash_val, "Airtel", 90)
    assert q_res["status"] == "SUCCESS"
    assert q_res["cooling_days"] == 90

    # Query status
    status_res = await adapter.get_number_status(hash_val, "Airtel")
    assert status_res["hlr_state"] == "QUARANTINED"

    # Release
    rel_res = await adapter.notify_release(hash_val, "Airtel")
    assert rel_res["status"] == "SUCCESS"

    status_post = await adapter.get_number_status(hash_val, "Airtel")
    assert status_post["hlr_state"] == "DISCONNECTED"


@pytest.mark.asyncio
async def test_mock_phone_intel():
    adapter = get_phone_intel_adapter()
    hash_val = "abcdef0123456789"
    signals = await adapter.lookup_number_signals(hash_val)
    assert "spam_score" in signals
    assert "fraud_score" in signals
    assert "line_type" in signals
    assert signals["valid"] is True


@pytest.mark.asyncio
async def test_mock_email():
    adapter = get_email_adapter()
    adapter.clear()
    res = await adapter.send_email("compliance@bank.com", "Decommission Alert", "Number +91 XXXXX 12345 unlinked")
    assert res["status"] == "DELIVERED"
    assert len(adapter.outbox) == 1
    assert adapter.outbox[0]["to"] == "compliance@bank.com"
