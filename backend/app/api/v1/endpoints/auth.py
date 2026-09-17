from datetime import timedelta
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from app.db.session import get_db
from app.core.security import verify_password, create_access_token, get_password_hash
from app.core.rbac import Role, get_role_permissions
from app.models.models import User, Organization
from app.schemas.schemas import Token, LoginRequest, UserOut
from app.api.deps import get_current_user

router = APIRouter()

DEMO_ACCOUNTS = [
    {
        "email": "superadmin@numberguard.demo",
        "role": "SUPER_ADMIN",
        "name": "Platform Lead Admin",
        "org": "NumberGuard Platform",
        "org_type": "PLATFORM",
        "description": "Global administrator with multi-tenant oversight, provider registry control, and system configuration.",
    },
    {
        "email": "telecom.admin@demotel.demo",
        "role": "TELECOM_ADMIN",
        "name": "Telecom Lead Admin",
        "org": "DemoTel Telecom",
        "org_type": "TELECOM",
        "description": "Carrier administrator managing decommissioned numbers, cooling policies, and reallocation pipelines.",
    },
    {
        "email": "operator@demotel.demo",
        "role": "TELECOM_OPERATOR",
        "name": "Carrier Operations Specialist",
        "org": "DemoTel Telecom",
        "org_type": "TELECOM",
        "description": "Day-to-day carrier operator handling batch imports, manual review queues, and release workflows.",
    },
    {
        "email": "bank.admin@securebank.demo",
        "role": "SERVICE_PROVIDER_ADMIN",
        "name": "Security & Fraud Officer",
        "org": "SecureBank",
        "org_type": "BANK",
        "description": "Banking partner administrator managing unlinking webhooks, API tokens, and compliance responses.",
    },
    {
        "email": "bank.operator@securebank.demo",
        "role": "SERVICE_PROVIDER_OPERATOR",
        "name": "Remediation Analyst",
        "org": "SecureBank",
        "org_type": "BANK",
        "description": "Bank operations specialist resolving masked number disassociation tasks and customer safety holds.",
    },
    {
        "email": "fintech.admin@payflow.demo",
        "role": "SERVICE_PROVIDER_ADMIN",
        "name": "Fintech Risk Lead",
        "org": "PayFlow Fintech",
        "org_type": "FINTECH",
        "description": "Payment app partner resolving wallet decoupling, OTP invalidation, and session revocations.",
    },
    {
        "email": "analyst@numberguard.demo",
        "role": "ANALYST",
        "name": "Risk Engine Analyst",
        "org": "NumberGuard Platform",
        "org_type": "PLATFORM",
        "description": "Analytics specialist reviewing platform-wide risk scoring telemetry, trends, and factor weights.",
    },
    {
        "email": "auditor@numberguard.demo",
        "role": "AUDITOR",
        "name": "Compliance Auditor",
        "org": "Telecom Regulatory Authority",
        "org_type": "REGULATOR",
        "description": "Independent auditor reviewing immutable lifecycle audit trails, compliance reports, and integrity proofs.",
    },
]

# Legacy alias mapping
LEGACY_EMAIL_MAP = {
    "super.admin@numberguard.gov": "superadmin@numberguard.demo",
    "admin@jio.telecom": "telecom.admin@demotel.demo",
    "operator@airtel.telecom": "operator@demotel.demo",
    "admin@hdfcbank.com": "bank.admin@securebank.demo",
    "ops@paytm.com": "bank.operator@securebank.demo",
    "auditor@deloitte.compliance": "auditor@numberguard.demo",
    "analyst@telecom.insights": "analyst@numberguard.demo",
}

@router.post("/login", response_model=Token)
async def login(req: LoginRequest, db: AsyncSession = Depends(get_db)):
    lookup_email = LEGACY_EMAIL_MAP.get(req.email.lower(), req.email.lower())
    
    result = await db.execute(
        select(User).options(selectinload(User.organization)).where(User.email == lookup_email)
    )
    user = result.scalars().first()
    
    if not user or not verify_password(req.password, user.hashed_password):
        # Demo master password fallback
        if req.password in ["numberguard2026", "password123"] and user:
            pass
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

    token = create_access_token(
        subject=user.id,
        role=user.role,
        organization_id=user.organization_id
    )

    org_name = user.organization.name if user.organization else None
    org_type = user.organization.org_type if user.organization else None

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org_name,
        organization_type=org_type,
        permissions=get_role_permissions(user.role),
        is_active=user.is_active,
        created_at=user.created_at
    )

    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user=user_out
    )

@router.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: AsyncSession = Depends(get_db)):
    req = LoginRequest(email=form_data.username, password=form_data.password)
    return await login(req, db)

@router.post("/demo-login", response_model=Token)
async def demo_login(role: Optional[str] = None, email: Optional[str] = None, db: AsyncSession = Depends(get_db)):
    """
    Developer sandbox route enabling rapid 1-click preview across all B2B tenant personas.
    """
    target = None
    if email:
        target = next((acc for acc in DEMO_ACCOUNTS if acc["email"].lower() == email.lower()), None)
    
    if not target and role:
        target = next((acc for acc in DEMO_ACCOUNTS if acc["role"].upper() == role.upper()), None)
    
    if not target:
        target = DEMO_ACCOUNTS[1]  # fallback to TELECOM_ADMIN

    result = await db.execute(
        select(User).options(selectinload(User.organization)).where(User.email == target["email"])
    )
    user = result.scalars().first()

    if not user:
        # Check or create demo org
        org_res = await db.execute(select(Organization).where(Organization.name == target["org"]))
        org = org_res.scalars().first()
        if not org:
            org = Organization(name=target["org"], org_type=target["org_type"])
            db.add(org)
            await db.commit()
            await db.refresh(org)

        user = User(
            email=target["email"],
            hashed_password=get_password_hash("numberguard2026"),
            full_name=target["name"],
            role=target["role"],
            organization_id=org.id,
            is_active=True
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        # re-fetch with org
        result = await db.execute(
            select(User).options(selectinload(User.organization)).where(User.id == user.id)
        )
        user = result.scalars().first()

    token = create_access_token(
        subject=user.id,
        role=user.role,
        organization_id=user.organization_id
    )

    org_name = user.organization.name if user.organization else target["org"]
    org_type = user.organization.org_type if user.organization else target["org_type"]

    user_out = UserOut(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        role=user.role,
        organization_id=user.organization_id,
        organization_name=org_name,
        organization_type=org_type,
        permissions=get_role_permissions(user.role),
        is_active=user.is_active,
        created_at=user.created_at
    )

    return Token(
        access_token=token,
        token_type="bearer",
        role=user.role,
        user=user_out
    )

@router.get("/demo-roles", response_model=List[Dict[str, Any]])
async def get_demo_roles():
    """Returns available demo accounts and role permissions for testing"""
    roles_list = []
    for acc in DEMO_ACCOUNTS:
        roles_list.append({
            **acc,
            "permissions": get_role_permissions(acc["role"])
        })
    return roles_list

@router.get("/me", response_model=UserOut)
async def get_me(current_user: User = Depends(get_current_user)):
    org_name = current_user.organization.name if current_user.organization else None
    org_type = current_user.organization.org_type if current_user.organization else None

    return UserOut(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        role=current_user.role,
        organization_id=current_user.organization_id,
        organization_name=org_name,
        organization_type=org_type,
        permissions=get_role_permissions(current_user.role),
        is_active=current_user.is_active,
        created_at=current_user.created_at
    )

