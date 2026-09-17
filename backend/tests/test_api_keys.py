"""
NumberGuard — Test Suite for API Key Management (Phase 3)
Tests:
- API key creation and hashing
- Scope validation
- Key rotation
- Key revocation
"""
import pytest
from app.db.session import AsyncSessionLocal
from app.services.api_key_service import ApiKeyService
from app.models.models import Organization


import time

@pytest.mark.asyncio
async def test_api_key_lifecycle():
    async with AsyncSessionLocal() as db:
        # Create test organization
        org = Organization(name=f"Test Telco Partner {int(time.time())}", org_type="TELECOM")
        db.add(org)
        await db.commit()
        await db.refresh(org)

        # 1. Create key
        api_key, raw_key = await ApiKeyService.create_key(
            db=db,
            organization_id=org.id,
            name="CI Pipeline Key",
            scopes="numbers:read,providers:write",
            expires_in_days=30
        )
        assert raw_key.startswith("ng_live_")
        assert api_key.key_prefix == raw_key[:12]
        assert api_key.hashed_key != raw_key
        assert api_key.is_active is True

        # 2. Validate valid key
        validated = await ApiKeyService.validate_key(db, raw_key, required_scope="numbers:read")
        assert validated is not None
        assert validated.id == api_key.id

        # 3. Validate with unauthorized scope
        rejected_scope = await ApiKeyService.validate_key(db, raw_key, required_scope="admin:full_access")
        assert rejected_scope is None

        # 4. Rotate key
        rotated = await ApiKeyService.rotate_key(db, api_key.id, org.id)
        assert rotated is not None
        new_key, new_raw_key = rotated
        assert new_raw_key != raw_key
        assert new_key.is_active is True

        # Old key should no longer validate
        old_val = await ApiKeyService.validate_key(db, raw_key)
        assert old_val is None

        # New key should validate
        new_val = await ApiKeyService.validate_key(db, new_raw_key, required_scope="providers:write")
        assert new_val is not None

        # 5. Revoke new key
        revoked = await ApiKeyService.revoke_key(db, new_key.id, org.id)
        assert revoked is True
        revoked_val = await ApiKeyService.validate_key(db, new_raw_key)
        assert revoked_val is None
