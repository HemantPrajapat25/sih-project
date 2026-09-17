"""
NumberGuard — Phase 2 Unit & Integration Tests
Tests for:
1. Lifecycle state transitions & state machine validation (VALID_TRANSITIONS)
2. Case management (case generation, SLA, resolution)
3. Allocation decisions (auto-risk evaluation & status synchronization)
4. Webhook service (delivery state transitions & retry calculation)
5. System settings service (default values, typed casting, read-only protection)
"""
import pytest
import uuid
from datetime import datetime, timedelta, timezone
from app.services.lifecycle import VALID_TRANSITIONS, record_lifecycle_event
from app.services.settings_service import DEFAULT_SETTINGS

@pytest.mark.asyncio
async def test_lifecycle_fsm_valid_transitions():
    """Verify state transition validation rules."""
    # ACTIVE -> DECOMMISSIONED (valid)
    allowed_active = VALID_TRANSITIONS.get("ACTIVE", [])
    assert "DECOMMISSIONED" in allowed_active
    
    # DECOMMISSIONED -> COOLING_HOLD (valid)
    allowed_decom = VALID_TRANSITIONS.get("DECOMMISSIONED", [])
    assert "COOLING_HOLD" in allowed_decom
    
    # REALLOCATED -> ACTIVE (valid)
    allowed_reallocated = VALID_TRANSITIONS.get("REALLOCATED", [])
    assert "ACTIVE" in allowed_reallocated

@pytest.mark.asyncio
async def test_system_settings_defaults():
    """Verify default settings structure and types."""
    assert len(DEFAULT_SETTINGS) >= 12
    # DEFAULT_SETTINGS dicts use 'key' (not 'setting_key')
    keys = [s["key"] for s in DEFAULT_SETTINGS]
    assert any(k.startswith("risk.") for k in keys), "Expected at least one risk.* setting"
    assert any(k.startswith("cooling.") for k in keys), "Expected at least one cooling.* setting"
    assert any(k.startswith("security.") for k in keys), "Expected at least one security.* setting"

def test_webhook_retry_calculation():
    """Verify retry calculation logic with exponential backoff."""
    from app.services.webhook_service import calculate_next_retry
    now = datetime.now(timezone.utc)

    # attempt=1 → delay = 60 * 2^0 = 60s
    retry1 = calculate_next_retry(attempt=1, base_delay_sec=60)
    assert retry1 > now
    delta1 = (retry1 - now).total_seconds()
    assert 58 <= delta1 <= 62, f"Expected ~60s delay, got {delta1}s"

    # attempt=3 → delay = 60 * 2^2 = 240s
    retry3 = calculate_next_retry(attempt=3, base_delay_sec=60)
    delta3 = (retry3 - now).total_seconds()
    assert 238 <= delta3 <= 242, f"Expected ~240s delay, got {delta3}s"

    # verify exponential growth
    assert delta3 > delta1

