import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.core.security import get_password_hash
from app.db.session import AsyncSessionLocal
from app.models.models import User, Organization

@pytest.mark.asyncio
async def test_multi_tenant_auth_and_isolation():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        # 1. Super Admin Demo Login
        res = await ac.post("/api/v1/auth/demo-login?role=SUPER_ADMIN")
        assert res.status_code == 200, res.text
        super_token = res.json()["access_token"]
        super_headers = {"Authorization": f"Bearer {super_token}"}
        
        # Super Admin should list organizations
        orgs_res = await ac.get("/api/v1/organizations", headers=super_headers)
        assert orgs_res.status_code == 200
        orgs = orgs_res.json()
        assert len(orgs) >= 7
        org_names = [o["name"] for o in orgs]
        assert "NumberGuard Platform" in org_names
        assert "DemoTel Telecom" in org_names
        assert "SecureBank" in org_names

        # 2. Telecom Admin Demo Login
        res_tel = await ac.post("/api/v1/auth/demo-login?role=TELECOM_ADMIN")
        assert res_tel.status_code == 200
        tel_data = res_tel.json()
        tel_token = tel_data["access_token"]
        tel_headers = {"Authorization": f"Bearer {tel_token}"}
        assert tel_data["user"]["organization_name"] == "DemoTel Telecom"
        assert tel_data["user"]["organization_type"] == "TELECOM"

        # Telecom Admin can list numbers
        num_res = await ac.get("/api/v1/numbers", headers=tel_headers)
        assert num_res.status_code == 200
        numbers = num_res.json()
        assert len(numbers) >= 1

        # 3. Bank Admin Demo Login
        res_bank = await ac.post("/api/v1/auth/demo-login?email=bank.admin@securebank.demo")
        assert res_bank.status_code == 200
        bank_data = res_bank.json()
        bank_token = bank_data["access_token"]
        bank_headers = {"Authorization": f"Bearer {bank_token}"}
        assert bank_data["user"]["organization_name"] == "SecureBank"
        assert bank_data["user"]["organization_type"] == "BANK"

        # Bank Admin is FORBIDDEN from direct raw number list
        bank_num_res = await ac.get("/api/v1/numbers", headers=bank_headers)
        assert bank_num_res.status_code == 403

        # Bank Admin CAN access provider notifications for SecureBank
        notif_res = await ac.get("/api/v1/notifications", headers=bank_headers)
        assert notif_res.status_code == 200
        notifs = notif_res.json()
        for n in notifs:
            assert n["provider_name"] == "SecureBank"

        # 4. Auditor Demo Login
        res_auditor = await ac.post("/api/v1/auth/demo-login?role=AUDITOR")
        assert res_auditor.status_code == 200
        auditor_token = res_auditor.json()["access_token"]
        auditor_headers = {"Authorization": f"Bearer {auditor_token}"}

        # Auditor can view audit logs
        audit_res = await ac.get("/api/v1/audit", headers=auditor_headers)
        assert audit_res.status_code == 200
