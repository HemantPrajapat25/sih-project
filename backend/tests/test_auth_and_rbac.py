import pytest
from app.core.rbac import Role, Permission, has_permission

def test_rbac_matrix_permissions():
    # SUPER_ADMIN has full permissions
    assert has_permission(Role.SUPER_ADMIN.value, Permission.NUMBERS_REALLOCATE)
    assert has_permission(Role.SUPER_ADMIN.value, Permission.SETTINGS_MANAGE)

    # TELECOM_ADMIN can reallocate and manage cooling
    assert has_permission(Role.TELECOM_ADMIN.value, Permission.NUMBERS_REALLOCATE)
    assert has_permission(Role.TELECOM_ADMIN.value, Permission.RISK_OVERRIDE)

    # TELECOM_OPERATOR can ingest/update, but CANNOT reallocate numbers
    assert has_permission(Role.TELECOM_OPERATOR.value, Permission.NUMBERS_IMPORT)
    assert not has_permission(Role.TELECOM_OPERATOR.value, Permission.NUMBERS_REALLOCATE)

    # AUDITOR is read-only
    assert has_permission(Role.AUDITOR.value, Permission.AUDIT_READ)
    assert not has_permission(Role.AUDITOR.value, Permission.NUMBERS_IMPORT)
    assert not has_permission(Role.AUDITOR.value, Permission.RISK_OVERRIDE)

    # SERVICE_PROVIDER_OPERATOR can acknowledge notifications
    assert has_permission(Role.SERVICE_PROVIDER_OPERATOR.value, Permission.NOTIFICATIONS_ACKNOWLEDGE)
    assert not has_permission(Role.SERVICE_PROVIDER_OPERATOR.value, Permission.NUMBERS_IMPORT)

@pytest.mark.asyncio
async def test_auth_demo_login_and_me(client):
    resp = await client.post("/api/v1/auth/demo-login?role=TELECOM_ADMIN")
    assert resp.status_code == 200
    data = resp.json()
    assert "access_token" in data
    assert data["role"] == "TELECOM_ADMIN"
    token = data["access_token"]

    # Call /me endpoint with bearer token
    me_resp = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["role"] == "TELECOM_ADMIN"
    assert "email" in me_data
